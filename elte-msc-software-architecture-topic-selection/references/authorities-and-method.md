# Authorities and deterministic method

## Authority and snapshot

Use these independent sources for distinct claims:

1. Current applicable ELTE MSc thesis/final-examination guidance: <https://www.inf.elte.hu/en/guidelines-thesis-final-examination-msc>. Checked 2026-10-08. Registration asks for three thesis-related subjects; the final exam requires all concepts, methods and connections of the chosen subjects. Do not transplant a course's assessment weights into the degree final exam.
2. Applicable curriculum and specialization syllabi: <https://www.inf.elte.hu/th-tematikak-programtervezo-informatikus-msc-2022-szoftvertechnologia-softvare-architecture-specializacio>. Checked 2026-10-08. The index is dated 2025-07-01; Principles of artificial intelligence and Service Science have September 2025 revisions. Direct syllabus links and scope locations are in `topic-map.json`.
3. The current student's actual Neptun form and applicable faculty confirmation control individual availability. The attached study guide records a student-supplied 19-entry dropdown as of 2026-10-08. It is not a universally applicable public final-exam list.
4. The bundled user-provided study guide explains scope and depth; its examples and oral-practice questions are not official extra topics. Advanced Software Technology is an appendix, absent from that dropdown. Advanced Java is present in the dropdown but uses an explicitly older available course description.

Follow newer applicable official evidence in a conflict. Record applicability, not only publication dates. Do not silently replace the 19-entry catalog with every course in the public specialization index. Software Architecture is the user's skill namespace; the faculty also uses Software and Service Architecture and Szoftvertechnológia. Verify the student's curriculum rather than assuming these labels imply identical rules in every cohort.

The atoms are an **advisory decomposition of published syllabus content**, not an official ELTE numbered question list. Anchors and thresholds are inherited operational safety heuristics from the established BSc selector, not faculty requirements. The syllabus is the authority; the study guide is explanation; the scorer performs transparent arithmetic only.

## States and stage-sensitive evidence

Classify every atom C/P/N. Treat them as two Boolean flags: `clear = (state == C)` and `potential = (state == P)`, mutually exclusive. No half points, confidence weights or Likert scores.

- **C:** a direct, inspectable, substantial thesis relationship already exists. Explain why the artifact uses, analyzes, designs, proves, implements or evaluates the specific atom. A current design can support a design atom even before implementation. A future result cannot be C merely because a plan promises it.
- **P:** current evidence supports concrete, feasible, approved-scope future work. Require a ledger pointer, named work, acceptance evidence and a deadline-feasibility statement. Planned additions outside approved scope, vague possibilities and generic learning intentions are N.
- **N:** no substantial relationship is established by the inspected evidence; it is incidental, vague, absent from inspected artifacts or would require distorted scope. Describe epistemic limits honestly.

Do not equate a language, framework, cloud deployment, API endpoint, database, model import or test count with a substantive syllabus relationship. Student-specific design reasoning, alternatives, assumptions, limitations and verification matter at MSc level. Formal research can supply strong evidence without an application.

## Exact breadth

For n fixed atoms, report C/P/N counts and both fractions:

- lower = C/n × 100;
- upper = (C+P)/n × 100.

Retain exact fractions; display percentages rounded to one decimal. They describe established-to-plausibly-future **thesis relationship breadth**, not mastery, faculty marks, approval odds or the part of the subject that must be studied. Repeated syllabus mentions are deduplicated; explanatory examples do not inflate denominators. All atoms have equal weight, fixed across projects.

## BSc-compatible relationship cutoff

Use the same rules as the recovered BSc selector:

- **Strong now:** ≥1 C anchor and ≥2 C atoms.
- **Conditionally defensible:** not Strong now; ≥1 C or P anchor, ≥1 C atom, and ≥2 total C+P atoms.
- **Below cutoff:** everything else, including zero clear evidence or superficial non-anchor overlap.

Broad subjects may have modest breadth despite a deep decisive relationship. Do not invent a faculty percentage requirement. An anchor is a substantive topic-defining relationship, not permission to award C for a keyword. Conditional topics are provisional until the stated work is completed; the cutoff is advisory and does not replace supervisor judgment.

## Exact ranking

Sort descending by tier (Strong, Conditional, Below), C anchor count, C count, P anchor count, P count, lower fraction, upper fraction, then ascending catalog number. Keep the ranking unchanged when discussing a student's preferences. Explain differing denominators and topic breadth rather than presenting the order as an objective faculty judgment of thesis quality.

Rank all 19 catalog entries in the primary table. Show entry 20 separately while its supplemental eligibility is unconfirmed. If entry 20 becomes verified eligible, include it in the candidate ranking without renumbering or merging subjects. Keep every topic's result visible.

## Independent availability gate

Each assessment has `eligibility.status` = `verified`, `unknown`, or `unavailable` and an evidence list plus explanation.

- Default every regular catalog subject to `unknown`: catalog presence alone does not verify current-student eligibility. It may enter a **provisional relationship recommendation** unless specifically unavailable.
- Require exact current-form/faculty evidence for `verified`. Do not verify from a generic syllabus listing, the study guide or a completed course alone when current selection rules are not established.
- Exclude `unavailable` from recommended candidates, regardless of relationship strength.
- Default Advanced Software Technology to `unknown` and exclude it from recommended candidates until `verified`.
- Label a three-subject recommendation administratively provisional if any member is unknown. Report insufficient eligible candidates separately from insufficient relationship evidence.

Recommend at most three above-cutoff candidates passing this gate; never promote a below-cutoff topic to complete a set. Strongly recommend the safest qualifying three while allowing defensible preferred alternatives, subject to a displaced-topic comparison and remaining-work commitments.

## Reruns and privacy

Preserve the versioned assessment, map version, current-source ledger and project snapshot. Update affected decisions and regenerate everything. Never hand-edit computed results. Re-run before human approval and after substantive artifact changes. Use anonymous identifiers by default. Do not reproduce credentials, Neptun codes or unrelated personal details in reports.
