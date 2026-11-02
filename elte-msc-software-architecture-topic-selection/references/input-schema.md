# Assessment input schema

Generate UTF-8 JSON with `python3 scripts/score_topics.py --template assessment.json`. Do not start from a partial hand-made atom list.

## Top level

- `schema_version`: `2.0`.
- `map_version`: exact bundled map version; mismatch is an error.
- `project`: anonymous `title`, `assessor_role`, ISO `as_of`, concrete `stage`, applicable `curriculum`, `selection_deadline`, `missing_artifacts`, `notes` and optional `implementation_percent`. A completion estimate is context only.
- `artifacts`: unique IDs with `kind`, `path_or_name`, `version_or_date`, `status`. Describe approved/current/partial/planned accurately. Do not include secrets or personal identifiers.
- `current_sources`: each checked administrative/syllabus source with `url`, `checked_on`, `applicability`, `finding`. Record current form evidence in the artifact ledger. If verification was unavailable, leave this list empty and record that limitation in notes.
- `selected_topics`: zero to three distinct catalog numbers (1–20). Treat fewer than three as a partial preference, not a final set.
- `topic_assessments`: all keys `1` through `20`.

## Topic assessment

Include `minimum_work`, `eligibility` and `entries`.

`eligibility` has `status` (`verified`, `unknown`, `unavailable`), an `evidence` array of ledger-backed pointers and a nonempty `reason`. Default unknown for every subject. Verified/unavailable require current administrative evidence; a public syllabus does not verify current-student selectability. Entry 20 is excluded from recommended candidates unless verified.

Each atom entry has:

- `status`: C, P or N;
- `evidence`: exact pointers in the form `ARTIFACT_ID: section / symbol / test / diagram / result`;
- `justification`: why this atom has or lacks a substantial relationship;
- `work`: minimum P-to-C action (required for P);
- `acceptance_evidence`: expected artifact/check proving completion (required for P);
- `feasibility`: why P is in scope and achievable before the relevant deadline (required for P).

C and P require evidence IDs that exist in the artifact ledger. Every N requires a reason. The scorer checks structure, not the truth or adequacy of evidence: the auditor must read artifacts and reject generic, false or incidental claims. The unknown eligibility explanation must not assert approval.

## Commands

```bash
python3 scripts/score_topics.py --check-map
python3 scripts/score_topics.py --template assessment.json
python3 scripts/score_topics.py assessment.json --output topic-selection-report.md --json-output topic-selection-summary.json
```

The script refuses to overwrite an existing output unless `--overwrite` is supplied. Retain the assessment for reruns. The Markdown report includes all atomic decisions; the compact JSON retains exact fractions and candidate/eligibility outcomes.
