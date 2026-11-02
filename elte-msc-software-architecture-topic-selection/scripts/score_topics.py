#!/usr/bin/env python3
"""Validate and score an ELTE MSc Software Architecture topic-selection audit."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = SKILL_ROOT / "references" / "topic-map.json"
TIER_WEIGHT = {"Strong now": 2, "Conditionally defensible": 1, "Below cutoff": 0}
ADMIN_KINDS = {"neptun_form", "faculty_confirmation", "registration_rules"}
CUTOFF = "SUPERVISOR CERTIFICATION CUTOFF - topics below this line should not be selected without new substantive evidence and supervisor review."


class AuditError(ValueError):
    """Invalid or unsafe audit input/output."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AuditError(f"JSON root must be an object: {path}")
    return data


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def strings(value: Any, required: bool = True) -> bool:
    return isinstance(value, list) and (bool(value) or not required) and all(nonempty(v) for v in value)


def iso_date(value: Any) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate_map(topic_map: dict[str, Any]) -> None:
    topics = topic_map.get("topics")
    if not nonempty(topic_map.get("map_version")):
        raise AuditError("Map must have a version")
    if not isinstance(topics, list) or len(topics) != 20 or any(not isinstance(t, dict) for t in topics):
        raise AuditError("Map must contain 19 regular subjects and one supplemental subject")
    if [t.get("number") for t in topics] != list(range(1, 21)):
        raise AuditError("Map numbers must be 1..20 in order")
    seen: set[str] = set()
    for topic in topics:
        n = topic["number"]
        if topic.get("catalog_status") != ("regular" if n <= 19 else "supplemental"):
            raise AuditError(f"Wrong catalog status for subject {n}")
        for field in ("title", "source_status", "scope_locator"):
            if not nonempty(topic.get(field)):
                raise AuditError(f"Subject {n} needs {field}")
        if not strings(topic.get("sources")):
            raise AuditError(f"Subject {n} needs source URLs")
        atoms = topic.get("atoms")
        if not isinstance(atoms, list) or not atoms or any(not isinstance(a, dict) for a in atoms):
            raise AuditError(f"Subject {n} needs atoms")
        ids = []
        for atom in atoms:
            if not nonempty(atom.get("id")) or not nonempty(atom.get("label")):
                raise AuditError(f"Subject {n} has an invalid atom")
            ids.append(atom["id"])
        if len(set(ids)) != len(ids) or seen.intersection(ids):
            raise AuditError(f"Subject {n} has duplicate atom IDs")
        seen.update(ids)
        anchors = topic.get("anchors")
        if not strings(anchors) or len(set(anchors)) != len(anchors) or not set(anchors).issubset(ids):
            raise AuditError(f"Subject {n} has invalid anchors")


def build_template(topic_map: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "2.0", "map_version": topic_map["map_version"],
        "project": {"title": "", "assessor_role": "student", "as_of": str(date.today()),
                    "stage": "", "curriculum": "Not supplied — provisional", "implementation_percent": None,
                    "selection_deadline": "", "missing_artifacts": [], "notes": ""},
        "artifacts": [], "current_sources": [], "selected_topics": [],
        "topic_assessments": {str(t["number"]): {
            "minimum_work": "",
            "eligibility": {"status": "unknown", "evidence": [],
                            "reason": "Current-student selectability has not been confirmed."},
            "entries": {a["id"]: {"status": None, "evidence": [], "justification": "", "work": "",
                                     "acceptance_evidence": [], "feasibility": ""} for a in t["atoms"]}
        } for t in topic_map["topics"]}
    }


def validate_assessment(data: dict[str, Any], topic_map: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "2.0" or data.get("map_version") != topic_map["map_version"]:
        errors.append("schema_version/map_version does not match this map")
    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object")
    else:
        for field in ("title", "assessor_role", "stage", "curriculum"):
            if not nonempty(project.get(field)):
                errors.append(f"project.{field} must be nonempty text")
        if not iso_date(project.get("as_of")):
            errors.append("project.as_of must be an ISO date")
        if not strings(project.get("missing_artifacts"), required=False):
            errors.append("project.missing_artifacts must be a string array")
        pct = project.get("implementation_percent")
        if pct is not None and (type(pct) not in (int, float) or not 0 <= pct <= 100):
            errors.append("implementation_percent must be null or a number from 0 to 100")
    ledger: dict[str, dict] = {}
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be an array")
    else:
        for i, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifacts[{i}] must be an object")
                continue
            for field in ("id", "kind", "path_or_name", "version_or_date", "status"):
                if not nonempty(artifact.get(field)):
                    errors.append(f"artifacts[{i}] needs {field}")
            aid = artifact.get("id")
            if nonempty(aid):
                if ":" in aid or aid in ledger:
                    errors.append(f"Duplicate or colon-containing artifact ID: {aid}")
                ledger[aid] = artifact
    current = data.get("current_sources")
    if not isinstance(current, list):
        errors.append("current_sources must be an array")
    else:
        for i, source in enumerate(current):
            if not isinstance(source, dict):
                errors.append(f"current_sources[{i}] must be an object")
                continue
            for field in ("url", "applicability", "finding"):
                if not nonempty(source.get(field)):
                    errors.append(f"current_sources[{i}] needs {field}")
            if not iso_date(source.get("checked_on")):
                errors.append(f"current_sources[{i}] needs ISO checked_on")
    selected = data.get("selected_topics")
    if not isinstance(selected, list) or any(type(n) is not int or n not in range(1, 21) for n in selected):
        errors.append("selected_topics must be integers from 1 to 20")
    elif len(selected) > 3 or len(set(selected)) != len(selected):
        errors.append("selected_topics must contain at most three distinct subjects")

    def check_pointers(value: Any, context: str, administrative: bool = False) -> None:
        if not strings(value):
            errors.append(f"{context} requires ledger-backed exact pointers")
            return
        for pointer in value:
            aid, sep, location = pointer.partition(":")
            if not sep or aid.strip() not in ledger or not location.strip():
                errors.append(f"{context}: invalid evidence pointer {pointer!r}; use ID: location")
            elif administrative and ledger[aid.strip()].get("kind") not in ADMIN_KINDS:
                errors.append(f"{context}: eligibility requires a current-form/faculty/rules artifact, not syllabus evidence")

    assessments = data.get("topic_assessments")
    if not isinstance(assessments, dict):
        return errors + ["topic_assessments must be an object"]
    expected_keys = {str(n) for n in range(1, 21)}
    if set(assessments) != expected_keys:
        errors.append(f"Topic keys must be exactly 1..20; missing={sorted(expected_keys-set(assessments))}, extra={sorted(set(assessments)-expected_keys)}")
    for topic in topic_map["topics"]:
        key = str(topic["number"])
        assessment = assessments.get(key)
        if not isinstance(assessment, dict):
            errors.append(f"Subject {key}: assessment must be an object")
            continue
        if not nonempty(assessment.get("minimum_work")):
            errors.append(f"Subject {key}: minimum_work is required")
        eligible = assessment.get("eligibility")
        if not isinstance(eligible, dict):
            errors.append(f"Subject {key}: eligibility is required")
        else:
            if eligible.get("status") not in ("verified", "unknown", "unavailable") or not nonempty(eligible.get("reason")):
                errors.append(f"Subject {key}: invalid eligibility status/reason")
            if not strings(eligible.get("evidence"), required=False):
                errors.append(f"Subject {key}: eligibility evidence must be a string array")
            if eligible.get("status") in ("verified", "unavailable"):
                check_pointers(eligible.get("evidence"), f"Subject {key} eligibility", administrative=True)
        entries = assessment.get("entries")
        if not isinstance(entries, dict):
            errors.append(f"Subject {key}: entries must be an object")
            continue
        expected_ids = {a["id"] for a in topic["atoms"]}
        if set(entries) != expected_ids:
            errors.append(f"Subject {key}: missing/extra atoms: {sorted(expected_ids-set(entries))} / {sorted(set(entries)-expected_ids)}")
        for atom_id in sorted(expected_ids.intersection(entries)):
            entry = entries[atom_id]
            if not isinstance(entry, dict):
                errors.append(f"{atom_id}: entry must be an object")
                continue
            status = entry.get("status")
            if status not in ("C", "P", "N"):
                errors.append(f"{atom_id}: status must be C, P or N")
            if not nonempty(entry.get("justification")):
                errors.append(f"{atom_id}: justification is required")
            if status in ("C", "P"):
                check_pointers(entry.get("evidence"), atom_id)
            if status == "P":
                for field in ("work", "feasibility"):
                    if not nonempty(entry.get(field)):
                        errors.append(f"{atom_id}: P requires {field}")
                if not strings(entry.get("acceptance_evidence")):
                    errors.append(f"{atom_id}: P requires acceptance evidence")
    return errors


def analyze(data: dict[str, Any], topic_map: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for topic in topic_map["topics"]:
        assessment = data["topic_assessments"][str(topic["number"])]
        entries = assessment["entries"]
        by_status = {s: [a for a in topic["atoms"] if entries[a["id"]]["status"] == s] for s in ("C", "P", "N")}
        c, p, n = (len(by_status[s]) for s in ("C", "P", "N"))
        ca = [a["id"] for a in by_status["C"] if a["id"] in topic["anchors"]]
        pa = [a["id"] for a in by_status["P"] if a["id"] in topic["anchors"]]
        tier = ("Strong now" if ca and c >= 2 else "Conditionally defensible"
                if (ca or pa) and c >= 1 and c+p >= 2 else "Below cutoff")
        availability = assessment["eligibility"]["status"]
        permitted = availability != "unavailable" and (topic["catalog_status"] == "regular" or availability == "verified")
        results.append({**topic, "tier": tier, "counts": {"C": c, "P": p, "N": n, "total": c+p+n},
                        "lower": Fraction(c, c+p+n), "upper": Fraction(c+p, c+p+n),
                        "c_anchor_ids": ca, "p_anchor_ids": pa, "by_status": by_status,
                        "entries": entries, "eligibility": assessment["eligibility"],
                        "candidate": permitted and tier != "Below cutoff", "minimum_work": assessment["minimum_work"]})
    return sorted(results, key=lambda r: (-TIER_WEIGHT[r["tier"]], -len(r["c_anchor_ids"]), -r["counts"]["C"],
                  -len(r["p_anchor_ids"]), -r["counts"]["P"], -r["lower"], -r["upper"], r["number"]))


def recommendation(ranked: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    chosen = [r for r in ranked if r["candidate"]][:3]
    if len(chosen) < 3:
        state = "NOT READY FOR THREE SAFE SUBJECTS"
    elif any(r["eligibility"]["status"] != "verified" for r in chosen):
        state = "ADMINISTRATIVELY PROVISIONAL"
    elif any(r["tier"] == "Conditionally defensible" for r in chosen):
        state = "CONDITIONAL LINKS — COMPLETE DECISIVE WORK"
    else:
        state = "READY FOR HUMAN REVIEW — NOT CERTIFIED"
    return chosen, state


def md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def range_text(r: dict[str, Any]) -> str:
    c = r["counts"]
    return f"{c['C']}/{c['total']} to {c['C']+c['P']}/{c['total']} ({float(r['lower'])*100:.1f}% to {float(r['upper'])*100:.1f}%)"


def make_report(data: dict[str, Any], topic_map: dict[str, Any], ranked: list[dict[str, Any]]) -> str:
    project = data["project"]
    chosen, state = recommendation(ranked)
    by_number = {r["number"]: r for r in ranked}
    lines = [f"# ELTE MSc Software Architecture topic selection — {md(project['title'])}", "", "## Audit basis", ""]
    for key in ("assessor_role", "as_of", "stage", "curriculum", "selection_deadline"):
        lines.append(f"- {key.replace('_', ' ')}: {md(project.get(key, '')) or 'Not supplied'}")
    lines += [f"- Map version: {topic_map['map_version']}",
              f"- Implementation estimate (context only): {md(project.get('implementation_percent'))}",
              f"- Missing/stale artifacts: {md('; '.join(project.get('missing_artifacts', []))) or 'None recorded'}",
              f"- Notes: {md(project.get('notes', '')) or 'None'}",
              "- Method: Boolean C/P/N decisions; exact fractions and one-decimal breadth ranges, not faculty marks or approval probabilities.",
              "- Cutoff: the BSc-compatible anchor safety rule is advisory, not an ELTE percentage requirement.",
              f"- Official guidance: {topic_map['guidelines_url']}", f"- Syllabus index: {topic_map['index_url']}",
              "", "### Evidence ledger", "", "| ID | Kind | Artifact | Version/date | Status |", "| --- | --- | --- | --- | --- |"]
    for a in data["artifacts"]:
        lines.append("| " + " | ".join(md(a[k]) for k in ("id", "kind", "path_or_name", "version_or_date", "status")) + " |")
    if not data["artifacts"]:
        lines.append("No artifacts supplied; no positive relationship can be evidenced.")
    lines += ["", "### Current source checks", ""]
    if not data["current_sources"]:
        lines.append("**Current official requirements were not independently refreshed.** Use the dated bundle provisionally and confirm before registration.")
    for source in data["current_sources"]:
        lines.append(f"- {md(source['url'])} — checked {md(source['checked_on'])}; applicability: {md(source['applicability'])}; finding: {md(source['finding'])}")

    lines += ["", "## Recommendation", "", f"**{state}**", ""]
    if len(chosen) < 3:
        relation_count = sum(r["tier"] != "Below cutoff" for r in ranked)
        lines.append(f"Only {len(chosen)} subject(s) pass both recommendation gates; {relation_count} have above-cutoff relationships across the catalog and appendix. Do not fill the set with failed or unavailable subjects.")
    else:
        lines.append("Strongly recommend these three under the established deterministic ranking:")
    for i, r in enumerate(chosen, 1):
        decisive = r["c_anchor_ids"] or r["p_anchor_ids"]
        pointers = [pointer for aid in decisive for pointer in r["entries"][aid]["evidence"]]
        lines.append(f"{i}. **{r['number']}. {md(r['title'])}** — {r['tier']}; {range_text(r)}; eligibility {r['eligibility']['status']}. Decisive anchors: {', '.join(decisive)}. Evidence: {md('; '.join(pointers))}.")
        if r["tier"] == "Conditionally defensible":
            lines.append(f"   Decisive completion work: {md(r['minimum_work'])}. P anchors: {', '.join(r['p_anchor_ids']) or 'None; strengthen clear evidence to the cutoff'}.")

    primary = [r for r in ranked if r["catalog_status"] == "regular" or r["eligibility"]["status"] == "verified"]
    ranks = {r["number"]: i+1 for i, r in enumerate(primary)}
    header = ["| Rank | Subject | Relation tier | C/P/N | Exact breadth range | C anchors | P anchors | Eligibility | Gap/work |",
              "| ---: | --- | --- | ---: | --- | --- | --- | --- | --- |"]

    def row(r: dict[str, Any], rank: Any) -> str:
        counts = r["counts"]
        return f"| {rank} | {r['number']}. {md(r['title'])} | {r['tier']} | {counts['C']}/{counts['P']}/{counts['N']} | {range_text(r)} | {', '.join(r['c_anchor_ids']) or '—'} | {', '.join(r['p_anchor_ids']) or '—'} | {r['eligibility']['status']} | {md(r['minimum_work'])} |"

    lines += ["", "## All 19 catalog subjects — relationship ranking", "", "Availability is independent of relationship tier. Verified supplemental entry 20 joins the candidate ranking without renumbering.", ""] + header
    for r in primary:
        if r["tier"] != "Below cutoff":
            lines.append(row(r, ranks[r["number"]]))
    lines += ["", f"> **{CUTOFF}**", ""] + header
    for r in primary:
        if r["tier"] == "Below cutoff":
            lines.append(row(r, ranks[r["number"]]))
    supplemental = [r for r in ranked if r not in primary]
    if supplemental:
        lines += ["", "### Supplemental subject — selection eligibility unconfirmed", ""] + header
        for r in supplemental:
            lines += [row(r, "Supplement"), "", f"**Not a recommendation candidate:** {md(r['eligibility']['reason'])}"]

    lines += ["", "## Preferred-selection check", ""]
    selected = data["selected_topics"]
    chosen_numbers = {r["number"] for r in chosen}
    if not selected:
        lines.append("No preferences supplied. Use the safest qualifying three, subject to the displayed caveats.")
    elif len(selected) != 3:
        lines.append(f"Partial preference only ({len(selected)} subject(s)); the final registration set requires three.")
    for number in selected:
        r = by_number[number]
        if not r["candidate"]:
            lines.append(f"- **STOP: {number}. {md(r['title'])}** — {r['tier']}; eligibility {r['eligibility']['status']}. {md(r['eligibility']['reason'])} {md(r['minimum_work'])}")
        elif number not in chosen_numbers:
            displaced = next((d for d in reversed(chosen) if d["number"] not in selected), None)
            target = f"{displaced['number']}. {md(displaced['title'])}" if displaced else "a displaced recommended subject"
            lines.append(f"- {number}. {md(r['title'])} qualifies as an alternative. **Unresolved comparison required against {target}:** justify actual thesis centrality with its decisive anchor, compare evidence/breadth and commit to remaining P work. Do not certify the alternative until this human-reviewed comparison is supplied.")
        else:
            lines.append(f"- {number}. {md(r['title'])}: within the safest qualifying set; {r['tier']}; eligibility {r['eligibility']['status']}.")
        if r["candidate"] and r["eligibility"]["status"] == "unknown":
            lines.append("  Administrative status remains provisional; confirm the current student's form/faculty eligibility.")

    lines += ["", "## Complete atomic audits — 19 subjects plus Appendix A", ""]
    for number in range(1, 21):
        r = by_number[number]
        lines += [f"### {number}. {r['title']}", "", f"- Relation: **{r['tier']}**; C/P/N = {r['counts']['C']}/{r['counts']['P']}/{r['counts']['N']}; n={r['counts']['total']}; {range_text(r)}",
                  f"- Eligibility: {r['eligibility']['status']} — {md(r['eligibility']['reason'])}",
                  f"- Eligibility evidence: {md('; '.join(r['eligibility']['evidence'])) or 'Not supplied'}",
                  f"- Source scope: {md(r['source_status'])}; {md(r['scope_locator'])}",
                  f"- Syllabi: {' ; '.join(r['sources'])}",
                  f"- C anchors: {', '.join(r['c_anchor_ids']) or 'None'}; P anchors: {', '.join(r['p_anchor_ids']) or 'None'}", ""]
        for status, title in (("C", "Clearly linked"), ("P", "Potentially linked"), ("N", "No established link")):
            lines += [f"#### {title}", ""]
            if not r["by_status"][status]:
                lines += ["None.", ""]
                continue
            columns = ["Atom", "Syllabus-derived item", "Justification"]
            if status in ("C", "P"):
                columns.append("Current evidence")
            if status == "P":
                columns += ["Work", "Acceptance evidence", "Feasibility"]
            lines += ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
            for atom in r["by_status"][status]:
                e = r["entries"][atom["id"]]
                values = [atom["id"], atom["label"], e["justification"]]
                if status in ("C", "P"):
                    values.append("; ".join(e["evidence"]))
                if status == "P":
                    values += [e["work"], "; ".join(e["acceptance_evidence"]), e["feasibility"]]
                lines.append("| " + " | ".join(md(v) for v in values) + " |")
            lines.append("")
        lines += [f"**Minimum natural work:** {md(r['minimum_work'])}", ""]
    lines += ["## Action plan and reruns", "", "Prioritize better pointers for existing evidence, then natural P-to-C work for decisive anchors, then outstanding current-form/faculty confirmation. Reject artificial scope expansion. Re-run after material scope, design, proof, implementation or evaluation changes and before human approval, respecting the actual deadline.", "", "**Full-subject study obligation:** prepare all concepts, methods and connections of each selected subject, not only linked atoms. This report neither grades the thesis nor certifies or submits a Neptun selection."]
    return "\n".join(lines).rstrip() + "\n"


def summary_json(ranked: list[dict[str, Any]], map_version: str) -> dict[str, Any]:
    chosen, state = recommendation(ranked)
    def clean(r: dict[str, Any]) -> dict[str, Any]:
        c = r["counts"]
        return {"topic": r["number"], "title": r["title"], "catalog_status": r["catalog_status"], "tier": r["tier"],
                "counts": c, "range_fraction": {"lower": f"{c['C']}/{c['total']}", "upper": f"{c['C']+c['P']}/{c['total']}"},
                "range_percent": {"lower": round(float(r["lower"])*100, 1), "upper": round(float(r["upper"])*100, 1)},
                "clear_anchors": r["c_anchor_ids"], "potential_anchors": r["p_anchor_ids"],
                "eligibility": r["eligibility"], "recommendation_candidate": r["candidate"]}
    return {"schema_version": "2.0", "map_version": map_version, "recommendation_state": state,
            "recommended_topics": [r["number"] for r in chosen],
            "ranking": [clean(r) for r in ranked if r["catalog_status"] == "regular" or r["eligibility"]["status"] == "verified"],
            "supplemental": [clean(r) for r in ranked if r["catalog_status"] == "supplemental" and r["eligibility"]["status"] != "verified"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--map", dest="map_path", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--check-map", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        topic_map = load_json(args.map_path)
        validate_map(topic_map)
        destinations = [p for p in (args.template, args.output, args.json_output) if p is not None]
        resolved = [p.resolve() for p in destinations]
        if len(set(resolved)) != len(resolved):
            raise AuditError("Output destinations must be distinct")
        for path in destinations:
            if path.resolve() == args.map_path.resolve() or (args.input and path.resolve() == args.input.resolve()) or path.resolve().is_relative_to(SKILL_ROOT):
                raise AuditError(f"Refusing to overwrite an input or bundled skill resource: {path}")
            if path.exists() and not args.overwrite:
                raise AuditError(f"Output exists: {path}; choose a new filename or pass --overwrite")
        def write(path: Path, content: str) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        if args.check_map:
            print(f"OK: 19 regular subjects + 1 supplemental; {sum(len(t['atoms']) for t in topic_map['topics'])} atoms; {topic_map['map_version']}")
            return 0
        if args.template:
            write(args.template, json.dumps(build_template(topic_map), ensure_ascii=False, indent=2) + "\n")
            print(f"Wrote template: {args.template}")
            if args.input is None:
                return 0
        if args.input is None:
            raise AuditError("Provide an input, --template or --check-map")
        data = load_json(args.input)
        errors = validate_assessment(data, topic_map)
        if errors:
            raise AuditError("Assessment validation failed:\n" + "\n".join(f"- {e}" for e in errors))
        ranked = analyze(data, topic_map)
        report = make_report(data, topic_map, ranked)
        if args.output:
            write(args.output, report)
            print(f"Wrote report: {args.output}")
        else:
            sys.stdout.write(report)
        if args.json_output:
            write(args.json_output, json.dumps(summary_json(ranked, topic_map["map_version"]), ensure_ascii=False, indent=2) + "\n")
            print(f"Wrote summary: {args.json_output}", file=sys.stderr if not args.output else sys.stdout)
        return 0
    except (AuditError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
