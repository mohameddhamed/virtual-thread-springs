# Evidence and decision protocol

## Evidence hierarchy

Prefer, in order:

1. inspectable primary artifact or raw evidence from the exact submitted revision;
2. paper text that points to an inspectable method, result, proof, or artifact;
3. authoritative registration, policy, ethics, license, or provenance record;
4. credible secondary description;
5. unsupported assertion.

An assertion cannot substitute for the artifact needed to verify it. Evidence
outside the paper may support verification but must be labeled as external.

## Status decisions

Use `awarded` only when affirmative evidence satisfies the whole Boolean item.
Use `not_awarded` when inspected material shows the item fails. Use `unverified`
when evidence may exist but is absent, inaccessible, unreadable, or
version-ambiguous. Use `pending` for an explicitly unfinished action or future
human check.

Every item must have a concise evidence citation. Cite exact pages and sections
for the paper; use repository path and revision, dataset identifier, theorem,
figure, table, log, or record for other evidence.

## Score states

For each criterion report:

- awarded points;
- unresolved items (`unverified` + `pending`);
- fixed maximum;
- a final subtotal only when every item in the criterion is resolved.

For the paper as a whole:

- complete review: integer awarded points out of 50;
- incomplete review: defensible range `[awarded, awarded + unresolved] / 50`.

Do not average incomplete reviewer ranges.

## Blockers and integrity risks

Blockers do not change the arithmetic automatically. Report them separately and
state the required human action. Do not declare plagiarism, authorship fraud,
ethics violation, or legal non-compliance solely from an automated audit.

## Version discipline

Record hashes, timestamps, or exact filenames when possible. Check that the PDF,
editable source, artifacts, abstract, result statement, declarations, and
reviewed evidence describe the same revision. When ELTE IK MSc acceptance or an
OTDK workflow requires identity with the institutional TDK paper, any material
post-conference change is a version blocker even if it improves the document.

## Missing-information language

Use factual formulations:

- “No raw measurement file was supplied; V05 is unverified.”
- “Section 4 reports only the best run although the method promises five seeds;
  V06 is not awarded.”
- “The proof certificate is planned but not generated; V07 is pending.”

Avoid implying that missing evidence does not exist.
