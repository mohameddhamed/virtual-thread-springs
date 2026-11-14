---
name: elte-ik-tdk-50-point-audit
description: Audit an ELTE Faculty of Informatics TDK written paper and its supporting evidence against the current official seven-criterion, 50-point review. Use for institutional TDK paper preflight, reviewer-style scoring, OTDK written-submission readiness, evidence-linked correction planning, or comparison of two written reviews. Do not include the separate oral-presentation score, invent grade bands, or use this as a substitute for plagiarism, ethics, or authorship adjudication.
---

# ELTE IK TDK 50-Point Audit

## Outcome

Produce a conservative, evidence-linked written-paper audit with exactly 50
one-point Boolean items grouped under the current 8/8/8/6/6/6/8 allocation.
Treat the paper as research work: trace problem and gap through question, method,
evidence, analysis or proof, result, answer, and contribution.

## Required references

Read these before scoring:

1. `references/authorities.md` for source precedence and scope.
2. `references/rubric.md` for the fixed 50-item rubric.
3. `references/evidence-protocol.md` for statuses, blockers, and evidence rules.
4. `references/research-modes.md` for mode-specific evidence.
5. `references/report-template.md` for the report structure.

Do not alter item IDs, weights, or the denominator. If a mode makes an item's
literal wording inapplicable, assess its mode-equivalent purpose; do not mark it
N/A.

## Evidence intake

Request or inspect, when available:

- final paper PDF and editable source from the same revision;
- registered title, delegating institutional-conference record, and destination;
- abstract, student-result statement, AI declaration, and submission metadata;
- code, data, proofs, notebooks, models, experiments, logs, instruments, or
  other artifacts needed to verify central claims;
- licenses, ethics/consent records, data-access constraints, and provenance;
- publication or submission evidence when publication value is claimed;
- supervisor or collaborator contribution boundaries;
- one or two existing reviewer sheets when comparison is requested.

Inventory what is present, missing, unreadable, version-mismatched, or outside
scope. Never infer access to evidence that was not supplied.

## Inspection workflow

1. Identify the current governing call and paper version. Apply newer official
   rules over older ones and record any unresolved conflict.
2. Render and visually inspect every PDF page. Check cover/title metadata,
   hierarchy, figures, tables, equations, citations, appendices, placeholders,
   clipping, and final-page integrity.
3. Inspect editable source and artifacts for parity with the PDF, when supplied.
4. Select all materially relevant research modes from
   `references/research-modes.md`.
5. Build a claim-to-evidence ledger for every central result and contribution.
6. Record critical blockers before calculating points.
7. Score all 50 rubric items using the status rules below.
8. Run `scripts/score_tdk.py` on the completed JSON ledger. Use the script's
   subtotals and range; do not hand-recalculate a conflicting total.
9. Write the report using `references/report-template.md`. Order corrections by
   recoverable points, blocker severity, research validity, and effort.

## Boolean status rules

Use exactly one status per item:

- `awarded`: the supplied evidence satisfies the item; worth 1 point.
- `not_awarded`: inspected evidence contradicts or fails the item; worth 0.
- `unverified`: evidence may exist but was not supplied or could not be checked;
  unresolved and worth no present point.
- `pending`: planned, incomplete, or awaiting a future artifact or human check;
  unresolved and worth no present point.

No partial points. Cite a page, section, figure, table, theorem, file, commit,
dataset, log, or explicit missing-evidence note for every status. Do not convert
`unverified` or `pending` into `not_awarded` merely because the audit package is
incomplete.

If every item is resolved, report the final integer score out of 50. Otherwise,
report only the defensible range:

`awarded points` to `awarded + unresolved items`, out of 50.

Never invent a passing score, grade conversion, award threshold, or competitive
rank.

## Blockers

Keep blocker findings separate from the 50-point arithmetic. Flag at least:

- suspected plagiarism or self-plagiarism requiring human adjudication;
- student contribution that cannot be separated from supervisor, collaborator,
  research-group, prior, reused, or AI-assisted work;
- central results that cannot be independently checked from available evidence;
- unlawful, unethical, unlicensed, confidential, or improperly disclosed data;
- missing required abstract, result statement, or AI declaration;
- version mismatch where institutional, OTDK, or MSc acceptance requires
  identity of the submitted paper.

Do not make a misconduct finding. State observed evidence, risk, and required
human decision.

## Two-reviewer handling

When two complete written reviews are supplied, audit each independently and
then report their arithmetic mean. If the absolute difference between the two
final totals is strictly greater than 15 points, flag the current OTDK
reconciliation/third-review requirement. Do not invent how a third review is
combined when the governing call does not state it.

Do not average score ranges or incomplete reviews. Keep the separate oral 50
points outside this skill.

## Scoring script

Prepare one JSON file per reviewer:

```json
{
  "reviewer": "R1",
  "items": {
    "N01": {"status": "awarded", "evidence": "p. 3, Section 1.1"},
    "N02": {"status": "unverified", "evidence": "Closest-work search not supplied"}
  }
}
```

Include all 50 IDs. Run:

```bash
python scripts/score_tdk.py review-r1.json --format markdown
python scripts/score_tdk.py review-r1.json --second review-r2.json --format markdown
```

The script rejects missing, duplicate, extra, or invalid items. Preserve its
validation errors in the working notes and correct the ledger before reporting.

## Quality rules

- Distinguish paper evidence from evidence outside the paper.
- Distinguish absent evidence from demonstrated failure.
- Separate result, interpretation, novelty claim, limitation, and publication
  potential.
- Prefer primary sources and exact artifact versions.
- Assess software only as evidence-bearing research where appropriate; do not
  force an implementation model onto theoretical or non-software work.
- Calibrate claims to evidence and surface negative or boundary results.
- Keep the report anonymized unless the user expressly requests names.
- Exclude credentials, private keys, prohibited personal data, participant data,
  and confidential material from reports and packages.
