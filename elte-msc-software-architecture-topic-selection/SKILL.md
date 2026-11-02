---
name: elte-msc-software-architecture-topic-selection
description: Select thesis-related final-examination subjects for ELTE Computer Science MSc Software Architecture (Software and Service Architecture / Szoftvertechnológia). Audit a proposal, engineering design, research plan, repository, tests or thesis against all 19 subjects in the supplied Neptun catalog plus the status-uncertain Advanced Software Technology appendix. Use Boolean atomic C/P/N evidence decisions to calculate exact breadth ranges, apply the established BSc selector's anchor cutoff, rank subjects, recommend the safest three and assess preferred alternatives. Use for this specialization only, not other MSc specializations, BSc selection, thesis grading, exam-study alone or Neptun submission/certification.
---

# ELTE MSc Software Architecture Topic Selection

Audit authentic thesis relationships at MSc depth. Recommend three subjects for human review; never certify or submit them. Preserve all 19 exact dropdown names and order, with Advanced Software Technology as a separate supplemental entry.

## Read before classifying

Read these required references completely:

1. `references/authorities-and-method.md`: authority, availability, C/P/N, BSc-compatible anchors and ranking.
2. `references/topic-map.json`: immutable atom denominator, subject anchors and official source pointers.
3. `references/per-topic-guidance.md`: MSc fit, false-positive traps and natural evidence.
4. `references/input-schema.md`: assessment JSON, evidence ledger and administrative gates.
5. `references/report-contract.md`: report and comparison requirements.

Use `references/software-architecture-study-guide.md` as explanatory context, not an official exam question bank or an extra denominator. Read its introduction and maintenance notes; retrieve relevant topic sections with `rg -n '^## Topic|^## Appendix|^## Source'` and targeted ranges. Do not treat illustrative methods as additional mandatory syllabus items.

## Establish scope and current eligibility

Locate the proposal/research goal, specialization and applicable curriculum, current Neptun subject choices, subject completion or other applicable eligibility constraints, preferred choices, selection deadline, thesis stage and available evidence. Ask only for missing information that materially changes the audit; proceed provisionally when implementation or administrative evidence is incomplete.

Recheck current official MSc registration guidance and the specialization syllabus index when doing a real selection audit. Follow newer applicable requirements, not merely a newer date from a different curriculum. Record inspected URLs, dates, applicability and conflicts. If browsing is unavailable, disclose that the bundle is a 2026-10-08 snapshot and keep unverified administrative status explicit.

Keep relationship and eligibility separate:

- Audit all 19 catalog subjects, even if unavailable to the current student.
- Audit entry 20, Advanced Software Technology, but exclude it from ordinary recommendations unless the current student's form or faculty confirmation establishes eligibility.
- Never infer selectability from being a specialization course. The supplied dropdown establishes a dated catalog, not universal eligibility.
- Do not substitute other index courses for the supplied 19 subjects. Do not alias or merge the two algorithm or distributed-system subjects.
- Treat Advanced Java's older syllabus as a flagged provisional scope until the applicable course version is confirmed. Do not invent a current public syllabus.

## Inspect thesis evidence

Inventory and version the proposal, requirements/SRS, research questions, literature argument, architectural decisions and alternatives, formal specifications/proofs, source code, experiments, tests, results and completion plan. Use exact pointers: artifact ID plus section, requirement, diagram, symbol, test, result table or revision.

Distinguish the student's contribution from a larger project, dependencies and framework defaults. A proposal can establish a clear analysis/design relationship already written, but cannot establish future implementation, a proof not supplied or unperformed validation. For research-only theses, accept substantive models, derivations, proofs and experiments; do not demand an unnecessary application or user manual.

## Classify every atom

Generate the full input skeleton:

```bash
python3 scripts/score_topics.py --template assessment.json
```

Fill every entry exactly once, without partial credit or guessed percentages:

- **C:** current, inspectable thesis-specific use, design, analysis, proof, implementation or evaluation. Give exact ledger-backed evidence and justify the substantive relationship.
- **P:** future work made credible by current approved scope/design/milestone. Specify the minimum in-scope work, acceptance artifact and feasibility before the deadline. Cite its present basis; do not count a wish as P.
- **N:** not evidenced, incidental, generic, unsupported or artificial/out of scope. Give a reason; do not claim absence without inspection.

Fill each topic's `minimum_work`. Prefer improvements already justified by the thesis. If no natural link is available, write `Do not choose this topic on the present scope.` Never add unused features, forced textbook sections or fake subject headings to pass the cutoff.

Do not change the atom denominator for an individual thesis. If a verified applicable syllabus changes, disclose the version conflict and use a separately versioned map with updated source references and revalidated anchors. Never silently omit irrelevant atoms or expand denominators using practice prompts.

## Calculate and recommend

```bash
python3 scripts/score_topics.py assessment.json \
  --output topic-selection-report.md \
  --json-output topic-selection-summary.json
```

Use the deterministic result unchanged: lower = C/n, upper = (C+P)/n; BSc-compatible Strong now / Conditionally defensible / Below cutoff; same anchor-and-count ranking. Percentages describe thesis-linked breadth, not an official score, acceptance probability or reduced exam syllabus.

Recommend the highest-ranked three above-cutoff candidates that pass the recommendation availability gate. Mark regular catalog entries of unknown eligibility as provisional; do not claim a registration-ready set until all three are verified. If fewer than three qualify, say so without filling the set with a failed topic. Conditional links must name remaining decisive work.

Permit a preferred alternative only if it passes the same relationship and availability gates. Compare it with a displaced recommended subject, citing thesis centrality, decisive anchors and remaining work. Below-cutoff, unavailable or unconfirmed supplemental selections are stop conditions for human review. Do not call a mere proposed preference an approved choice.

## Deliver and retain audit state

Return the self-contained report in `references/report-contract.md`; preserve assessment JSON for repeatable updates. Include all 19 ranked subjects, the supplemental status panel, every atom's state and reason, current-source ledger, eligibility caveats, strongest three (or not-ready verdict), preferred-subject comparison and prioritized natural next work.

Remind the student that the final exam covers **all concepts, methods and connections of each chosen subject**, not only thesis-linked atoms. Re-run after material scope/design/proof/implementation/test changes and before submission for human approval. Consider the actual deadline before advising delay.

Keep reports anonymized by default: use a project title or neutral identifier, not student names, Neptun codes or personal contact data. Do not include private source content in public artifacts without authorization.

Do not grade the thesis, choose for another specialization, alter the study guide, submit to Neptun or provide certification.
