# ELTE IK MSc consultation checkpoint 4: research-achievements audit

**Student:** Hamed Mohamed (DG1EWF)  
**Programme/track:** MSc in Computer Science — Software Architecture  
**Thesis:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
**Supervisor:** Gregory Reynolds Morse  
**Research mode:** Empirical engineering/system study  
**Audit date:** 2026-10-15 (Europe/Budapest)  
**Repository:** [mohameddhamed/virtual-thread-springs](https://github.com/mohameddhamed/virtual-thread-springs)  
**Audited revision:** [`a9bd454a26e4b8336a65c16c6c6597182a5d82a8`](https://github.com/mohameddhamed/virtual-thread-springs/tree/a9bd454a26e4b8336a65c16c6c6597182a5d82a8)  
**Audit standard:** `elte-msc-audit-achievements` from the supplied ELTE IK MSc checkpoint suite; suite SHA-256 `a8c4959913593a6fddbc2d780b6789417d694e45e2f24c2189f7d96220395e76`

## 1. Result

**Insufficient**

Plain-language checkpoint verdict: **FAIL pending correction and recheck**.

This is a checkpoint-4 content verdict, not a course grade, final-thesis grade, defence decision, or authorship finding. Under the supplied audit standard, all 15 mandatory gates must pass; any `Fail` or `Unverified` makes the overall result `Insufficient`.

## 2. Deadline status

Checkpoint 4 is the final content milestone used for Thesis Consultation course fulfilment. The official retained schedule sets the research-achievements deadline at **1 October** for a January final examination and **1 March** for a June final examination. The repository presents this as an October 2026 checkpoint, so this audit provisionally assumes the **January 2027** examination track. On that assumption, the checkpoint is **14 calendar days late** on 15 October 2026.

If the intended examination period is June 2027, the applicable deadline is 1 March 2027 and the submission is not late. The student and supervisor should confirm the examination track rather than relying on inference.

Official basis:

- [ELTE IK MSc Thesis Consultation deadlines](https://www.inf.elte.hu/dstore/document/227130/MSc%20Thesis%20consultations%20-%20deadlines%20-%20PTI-ARI-ADAT.pdf)
- [ELTE IK MSc thesis and final-examination guidance](https://www.inf.elte.hu/en/guidelines-thesis-final-examination-msc)

## 3. Scope and evidence reviewed

### Submitted and prior evidence

- Approved topic-registration form and the earlier checkpoint-2/3 audit retained in the repository.
- Revised bibliography, compact checkpoint research plan, detailed plan, audit-response register, provenance ledger, iteration notes, research synthesis, migration guidelines, presentation outline, and checkpoint-4 self-assessment.
- Spring Boot application source, Maven build, Docker Compose deployment, k6 workloads, benchmark runner, JNI probe, evidence-normalization scripts, dashboard, and seven JUnit test methods.
- Git history through the audited SHA, including 16 commits by the repository author.
- Committed result material: six PostgreSQL k6 JSONL files, older April k6/JFR artifacts, narrative result files, and the committed 76-record normalized dashboard dataset.
- Official ELTE schedule, live MSc guidance, live AI-policy page, and Dean’s Directive No. 1/2026.

### Audit actions actually performed

- Cloned the public `main` branch and froze the audited SHA before inspection.
- Inspected source, configuration, tests, benchmark orchestration, analysis scripts, raw-result inventory, hashes, documentation, and repository history.
- Ran the repository’s documented evidence rebuild:

  ```text
  python3 scripts/normalize_evidence.py
  -> wrote normalized-evidence.json (0 trial-level records)

  python3 scripts/validate_normalized_evidence.py
  -> validation failed
  ```

- Checked every provenance path in the committed 76-record dataset against the audited Git tree: **75/75 manifest references, 76/76 k6-result references, and 75/75 JFR references are absent**.
- Independently recomputed request counts, HTTP failures, mean latency, p50, and p95 from all six committed PostgreSQL files. The values match the ranges stated in `docs/research-iteration-2026-10-15-hikari-scheduler.md`; all six files contain zero failed HTTP-request points. Their SHA-256 values also match `docs/current-artifact-freeze.md`.
- Attempted `./mvnw test`. Independent execution was not possible in the audit environment because only JDK 17 was installed while the project requires Java 21, and Maven Central was unreachable. Docker, k6, and the JFR CLI were also unavailable. This is an **audit-environment limitation**, not a claimed project test failure. No CI run or retained test transcript in the repository could substitute for independent execution.

### Important boundary

The repository’s narrative claims, code, and retained summaries were inspected deeply. The central Java 21/JFR runs were **not independently executed or verified**, because their referenced raw artifacts are absent. No supervisor presentation or administrative acceptance evidence was supplied.

## 4. Executive reason

The submission contains substantial and often thoughtful engineering work. The application, endpoint-specific workloads, benchmark runner, JNI extension, source-level treatments, correctness tests, negative-result reporting, JDK 24+ boundary discussion, and mechanism-specific distinction between pinning, serialization, finite-resource contention, and native carrier occupation are meaningful achievements. The six committed PostgreSQL runs are real, parseable primary evidence and their reported descriptive metrics check out.

The checkpoint nevertheless fails for four decisive reasons:

1. **There is no substantially complete thesis.** `docs/thesis-outline.md` is a 1,383-word outline, not an editable near-complete thesis; no thesis PDF is supplied. The repository’s own checkpoint-4 self-assessment explicitly records this as missing.
2. **The central evidence chain is broken.** The dashboard claims 76 trial records, but every manifest and JFR file and every referenced k6 result file is absent from the audited commit. The project’s own clean rebuild therefore produces zero records and fails validation.
3. **The final method and analysis are not closed.** Most headline conditions use only three process repetitions and are still labelled exploratory; no pilot-based precision justification, frozen run-order scheme, final uncertainty analysis, or complete primary artifact bundle is preserved. RQ2’s claimed connection-pool saturation construct is not actually exercised by sleeping before the JDBC query and collecting no Hikari acquisition/active/pending telemetry.
4. **Identity and integrity closure are missing.** The freeze record names an older dirty revision rather than the audited HEAD; protocol descriptions conflict across documents; and no actual AI-use/no-use declaration, point-of-use disclosure, or retained-log reference is supplied.

The student’s own [`docs/checkpoint-4-achievements.md`](https://github.com/mohameddhamed/virtual-thread-springs/blob/a9bd454a26e4b8336a65c16c6c6597182a5d82a8/docs/checkpoint-4-achievements.md) already reaches the same high-level conclusion: research execution is substantial, but the checkpoint package is not closed.

## 5. Mandatory-gate table

| ID | Gate | Status | Evidence | Finding |
|---|---|---|---|---|
| C1 | Approved-scope ledger | **Unverified** | Approved topic; prior audit; `docs/audit-response-and-revision-register.md`; checkpoint-4 achievement ledger | A useful ledger exists, and missing thesis/provenance items are admitted. However, checkpoints 2 and 3 were previously `Insufficient`, and no supervisor approval is supplied for the revised RQs, scope narrowing, or later extensions (JNI, CPU, JDK boundary, fairness/semaphore work). |
| C2 | Ready primary artifact | **Pass** | `src/`, `pom.xml`, `Dockerfile`, `docker-compose.yml`, `k6/`, `run-benchmark.sh`, `scripts/` | Static inspection shows a usable engineering artifact capable of generating measurements. This pass does not certify a successful clean build; independent build execution remained unavailable. |
| C3 | Final methodology | **Fail** | Detailed plan; checkpoint plan; iteration notes; runner; thesis outline | The actual method is fragmented and inconsistent: 10 versus 50/100/200 VUs, 55-second staged runs versus “60 seconds,” mixed versus isolated workloads, and different condition sets. Three-run sets remain exploratory, final precision is not justified, run order is not preserved, and manifest fields contain placeholders/default descriptions rather than exact settings. |
| C4 | Performed evidence | **Unverified** | Six committed PostgreSQL JSONL files; 76-record dataset; result narratives | The PostgreSQL family is verified as performed. The central synchronization, endpoint, JNI, CPU, and JDK-boundary runs cannot be checked because their manifests, k6 streams, telemetry, and JFR files are absent. |
| C5 | Every research question answered | **Fail** | `docs/research-synthesis.md`; `docs/checkpoint-4-achievements.md` | Explicit provisional answers exist, but RQ1’s central JFR chain is not traceable and RQ2’s pool-saturation branch is not validly tested. An answer unsupported by preserved primary evidence does not pass. |
| C6 | Contribution substantiated | **Fail** | Revised bibliography; synthesis; migration guidelines | The proposed contribution—a mechanism-specific Java 21 migration method—is plausible and differentiated from closest work, but its central empirical support cannot be independently checked and it is not integrated into a substantially complete thesis. |
| C7 | Valid analysis | **Fail** | Primary-matrix notes; Hikari note; CPU/JNI notes; normalized dataset | Three-run exploratory sets are presented as headline means without final uncertainty or pilot justification. The closed-loop, one-carrier stress design is honestly bounded, but the JDBC-pool treatment does not hold a connection during the 300 ms delay and captures no pool telemetry, so it cannot test pool saturation. |
| C8 | Negative evidence and limitations | **Pass** | Synthesis §§5, 8; iteration notes; checkpoint-4 §7 | Null findings, one-carrier limits, closed-loop self-throttling, synthetic delays, single-machine scope, zero-JFR JNI interpretation, JDK boundaries, and deferred energy/cross-OS work are reported unusually clearly. |
| C9 | Primary evidence preserved | **Fail** | `.gitignore`; normalized dataset; provenance ledger; `results/` | The six PostgreSQL files are preserved, but all 226 central provenance links in the 76-record dataset point to files absent from Git. `.gitignore` excludes regenerated JFR, k6, manifests, telemetry, and CPU-control evidence. |
| C10 | Cross-artifact identity | **Fail** | `docs/current-artifact-freeze.md`; audited HEAD; normalized records | The freeze record names `1ccb617...` with a dirty tree; audited HEAD is `a9bd454...`. Dataset rows refer to `5f9936c...`, `1ccb617...`, or no commit. Thesis, source, raw runs, tables, and dashboard are not one frozen state. |
| C11 | Reproducibility | **Fail** | `scripts/normalize_evidence.py`; `scripts/validate_normalized_evidence.py`; README commands | A competent reviewer cannot recompute the central result from a clean clone. The advertised rebuild produces zero records and validation fails. The validator checks expected counts/values inside the already-generated JSON but does not verify referenced-file existence or hashes. |
| C12 | Artifact quality | **Fail** | Source/config/tests/runner/validator | The artifact is promising but not yet trustworthy as a research package: Spring settings are mis-indented under `demo`, tests exercise only the default payment lock mode, there is no CI evidence, and the evidence validator permits stale data when the raw sources are missing. |
| C13 | Substantially complete thesis | **Fail** | `docs/thesis-outline.md`; no thesis PDF/source | The only thesis-like file is a 1,383-word outline. It lacks a full related-work chapter, final method, evidence-linked results, figures/tables, complete citations, appendices, and polished conclusion. The official guidance expects an approximately 50-page MSc thesis. |
| C14 | Integrity, ethics, and AI | **Unverified** | AI-policy prose; repository Copilot instructions; no declaration/log | No human-subject or personal-data issue is apparent, and synthetic data are appropriate. Actual AI use or non-use is not declared; no point-of-use disclosures, signed declaration, or retained interaction-log reference are present. No inference is made from repository files or writing style. |
| C15 | Checkpoint-5 transition | **Fail** | Remaining-work list in checkpoint-4 package | Remaining work includes a substantially complete thesis, central raw-evidence recovery or rerun, final methodology/analysis, frozen identity, and integrity documentation. These are core checkpoint-4 items, not merely presentation and packaging. |

## 6. Achievement ledger

| Approved commitment / question | Delivered artifact | Evidence | Thesis location | Status | Defect |
|---|---|---|---|---|---|
| Java 21 Spring MVC migration study | Spring Boot MVC application and Java 21 target | Source, Maven, Docker, configuration | Outline §§1, 4 | **Delivered** | Clean Java 21 build is not independently evidenced in CI; configuration nesting needs correction. |
| RQ1: platform / VT synchronized / VT compatible-lock comparison | Payment lock modes, isolated workload, matrix narratives | `PaymentService`, k6 script, matrix and replication notes | Outline §§5–6 | **Unverifiable** | Central manifests, k6 JSONL, JFR, and telemetry are absent. RQ wording refers to “data layers,” while the treatment is in a service. |
| RQ2(a): intrinsic synchronization around blocking work | `synchronized`, `ReentrantLock`, semaphore, no-lock modes | Source, tests, result narratives | Outline §§4–6 | **Partially delivered** | Mechanism is well modelled; primary raw evidence and final statistics are missing. |
| RQ2(b): `ThreadLocal` context correctness | Cleaned-up request context in `OrderService` | Source and endpoint tests | Outline §§4, 6 | **Partially delivered** | Cleanup exists, but there is no lifecycle/leak/context-propagation experiment. The correct result is “no harmful effect established,” not a demonstrated anti-pattern. |
| RQ2(c): JDBC connection-pool saturation | H2/PostgreSQL pool-size comparisons | Six committed PostgreSQL JSONL files; H2 narrative | Outline §§4, 6 | **Not delivered as the stated construct** | The 300 ms sleep occurs before JDBC acquisition; the query is trivial and no Hikari active/pending/acquisition metrics are recorded. Pool sizes 1 and 10 therefore do not test a held-connection saturation condition. |
| Correctness-preserving refactoring | JUnit smoke, native, and concurrent-payment tests | Seven `@Test` methods | Not integrated into a full thesis | **Partial** | Concurrent semantics are tested only under the default `reentrant-lock` configuration; no parameterized evidence covers all compared modes and invariants. |
| JDK 24/25 applicability boundary | JEP 491 discussion and boundary-run narratives | Revised bibliography, JDK-boundary notes | Outline §§2, 8–9 | **Partially delivered** | Scope correction is strong; boundary raw/JFR artifacts are absent. |
| Migration guideline/checklist | `docs/migration-guidelines.md` and synthesis procedure | Source-linked prose | Outline §7 | **Delivered as a draft** | Must be reconciled with final evidence and version-bounded in the thesis. |
| Current related work and credible bibliography path | Revised review with 19 entries | `docs/bibliography-review-revised.md` | Outline §3 has only broad bullets | **Partial** | No full thesis bibliography or point-of-use citation integration; still below the supervisor-specific final target of at least 30 relevant entries. |
| Frozen evidence and reproducible analysis | Provenance ledger, normalizer, validator, dashboard | Scripts and generated JSON | No appendix | **Missing for central claims** | Clean-clone regeneration fails; source artifacts are ignored and absent. |
| Explicit answers and contribution | Synthesis and checkpoint-4 summary | Narrative RQ answers | Outline §§8–9 | **Partial** | Answers are not backed by a complete traceable primary evidence chain. |
| Substantially complete editable thesis and PDF | `docs/thesis-outline.md` only | 242 lines / 1,383 words | N/A | **Missing** | This is the clearest mandatory-gate failure. |
| AI/integrity package | Policy prose only | No completed declaration, point-of-use notes, or log reference | No actual-use section | **Unverified** | The student must provide a truthful use/no-use record; no stylistic inference is permissible. |

## 7. Result-provenance table

| Claim | Raw source | Analysis / proof | Version identity | Reproducible command / procedure | Verification status |
|---|---|---|---|---|---|
| Java 21 VT + `synchronized` produced about 110 pin events/run and the stated latency | Referenced October k6/JFR/manifests | Normalized JSON and synchronization matrix note | Dataset rows point to earlier/null commits; freeze is not HEAD | `run-benchmark.sh --endpoint payments --vus 10 --lock-mode synchronized` with one-carrier flags | **Unverified:** all referenced central raw files are absent. |
| `ReentrantLock` removed observed pin events but retained serialized capacity | Referenced October k6/JFR/manifests | Matrix and replication notes | Same identity defect | Same command with `--lock-mode reentrant-lock` | **Unverified:** narrative and source are plausible; raw evidence absent. |
| No-lock diagnostic achieved about 711–713 requests | Referenced October k6/JFR/manifests | Primary-matrix notes | Raw revision not frozen | Same workload with `--lock-mode none` | **Unverified:** raw evidence absent; diagnostic is correctly labelled unsafe. |
| `/orders` and `/products` showed no VT pinning | Referenced endpoint-isolation JFR/manifests | Endpoint-isolation note and normalized JSON | Raw revision not frozen | Isolated k6 runs for each endpoint and mode | **Unverified:** all referenced artifacts absent. |
| Long JNI behaved consistently with carrier occupation; 27 JFRs had zero pin events | Referenced JNI k6/JFR/manifests | JNI boundary note and normalized JSON | Raw revision not frozen | Build native library; run `native`, `native-short`, and Java sleep controls | **Unverified:** all 27 JFR streams and related raw files are absent. |
| Java 24/25 removed the tested monitor-pinning event while serialization remained | Referenced JDK-boundary JFR/manifests | JDK boundary iteration note | Raw revision not frozen | Run the same Java-21-targeted artifact on the named runtimes | **Unverified locally:** mechanism is consistent with [JEP 491](https://openjdk.org/jeps/491), but repository raw evidence is absent. |
| Pool 1 versus 10 produced nearly identical PostgreSQL results | Six committed `results/docker-pg-orders-pool*.json` files | Independently recomputed descriptive metrics; Hikari note | Files committed at `2a0a515...`; hashes match freeze record | Parse JSONL request/failure/duration points | **Partially verified:** numbers and zero failures match; no manifest, JFR, pool telemetry, or valid saturation construct. |
| Correctness and mutual exclusion tests pass | JUnit source | Maven/Surefire claimed in freeze record | HEAD source inspected | `./mvnw test` under JDK 21 | **Unverified execution:** test source exists, but no retained CI/Surefire report; audit environment could not resolve/run the build. |
| Dashboard contains 76 validated trial records | Committed generated JSON | Normalizer and validator scripts | Generated at 2026-10-15; source files absent | Run normalizer then validator from a clean clone | **Failed reproduction:** normalizer creates 0 records and validator fails. |

## 8. Required corrections

| Priority | Defect | Consequence | Exact repair | Recheck evidence |
|---|---|---|---|---|
| P0 | No substantially complete thesis | C13 and C15 necessarily fail | Produce the editable thesis and rendered PDF with complete introduction/RQs/contribution, related work, final method, results/evaluation, discussion, conclusion, citations, and reproducibility appendix. Integrate only frozen evidence. | Thesis source + PDF; cross-reference map from every table/figure/claim to artifacts; approximately 50-page credible final path. |
| P0 | Central raw evidence absent | RQ1, most RQ2 evidence, contribution, and reproducibility cannot be checked | Restore or rerun every retained central condition. Publish manifests, k6 JSONL, JFR, telemetry, extraction output, analysis tables, hashes, and exact source revision. If Git is unsuitable for large files, use a versioned release/archive and commit a complete manifest with immutable links and checksums. | Clean checkout plus artifact download; all paths resolve; hashes verify; central result recomputes. |
| P0 | Evidence generator/validator accepts a stale committed product | Dashboard can display unverifiable results | Make normalization fail when required manifest/result/JFR inputs are absent. Extend validation to check file existence, SHA-256, commit identity, schema, nonempty metrics, JFR extraction, and expected condition counts. Never treat the generated JSON as the primary source. | `normalize` + `validate` pass in a clean clone with an empty cache; deliberate deletion causes a clear failure. |
| P0 | No single frozen state | Thesis, code, results, and tables can disagree | Create a checkpoint tag/release from a clean tree. Update the freeze record to the exact commit and artifact-bundle hash. Regenerate every thesis table and dashboard dataset from that state. | Tag, clean `git status`, release hash, generated-table checksums, thesis version ID. |
| P1 | Final methodology and uncertainty are not closed | Three-run exploratory evidence cannot support final claims robustly | Use a pilot to set the number of independent process runs and precision target; block/randomize order; fix warm-up, hold, timeout, inclusion/exclusion, JFR configuration, carrier count, load model, offered load, and exact dependency versions. Report run-level dispersion/effect sizes and justified intervals. | Final protocol, run-order ledger, analysis script, all runs including exclusions, final statistical output. |
| P1 | RQ2 pool-saturation construct is not tested | Pool-size null result cannot answer the RQ | Either (a) implement a condition that holds/acquires a real connection during the delay, such as a controlled PostgreSQL query/transaction, and capture Hikari active/idle/pending/acquisition-time/timeout metrics under sufficient offered load; or (b) narrow the RQ and conclusion to “no pool-size effect exposed by this synthetic pre-query-delay protocol.” | Source diff, exact database workload, pool telemetry, repeated runs, revised RQ/answer. |
| P1 | Correctness tests do not cover the compared treatments | Performance runs may compare semantically different behavior | Parameterize tests for `synchronized`, non-fair/fair `ReentrantLock`, semaphore variants, and diagnostic no-lock. Verify response contract, mutual exclusion/concurrency expectation, cancellation/interruptibility where claimed, and startup configuration. Add CI on JDK 21 and retain the report. | CI run tied to frozen commit; Surefire XML/summary; treatment-specific assertions. |
| P1 | Configuration and documentation drift | Clean executions may not use the described settings | Move `datasource`, `h2`, `jpa`, and `sql` under `spring:` rather than `demo:` in `application.yml`. Reconcile 10 versus 50/100/200 VUs, 55 versus 60 seconds, matrix run sets, and exact runtime flags across plan, outline, README, runner, and thesis. | Configuration-binding test; resolved Spring environment dump; one canonical protocol table reused everywhere. |
| P1 | Thesis outline contains technical overstatements | Weakens accuracy and literature credibility | Correct “Spring Boot 3.2+ enables by default” to the explicit `spring.threads.virtual.enabled=true` opt-in; identify JEP 444 as the final JDK 21 JEP; remove unsupported universal memory/throughput claims or cite and qualify them; state that long JNI residency is not the same as a `jdk.VirtualThreadPinned` event. | Revised thesis with point-of-use citations to [JEP 444](https://openjdk.org/jeps/444), [JEP 491](https://openjdk.org/jeps/491), and [Spring Boot’s virtual-thread documentation](https://docs.spring.io/spring-boot/reference/features/spring-application.html#features.spring-application.virtual-threads). |
| P1 | Actual AI status absent | C14 remains unverified and final submission may be unassessable | Truthfully record use or non-use. Where used, add point-of-use disclosure naming the tool and purpose, complete the signed declaration, verify all outputs, and retain the complete interaction log for supervisor access. | Disclosure locations, completed declaration, retained-log reference, supervisor review. |
| P2 | Revised scope/commitments lack approval evidence | C1 remains unverified | Have the supervisor approve the bounded RQs, Java 21 primary scope, JDK boundary role, minimum viable matrix, and treatment of extensions. Record deviations from the original topic and earlier checkpoint plans. | Dated approved commitment ledger or consultation record. |
| P2 | Final bibliography path is incomplete | Thesis related-work gate remains at risk | Integrate the revised literature at point of use and expand to at least 30 relevant sources under the supervisor-specific standard, prioritizing peer-reviewed closest work and exact versioned primary documentation. | Thesis bibliography, citation audit, source-verification ledger. |

## 9. Suggestions for checkpoint 5

These are useful but do not substitute for the mandatory corrections above.

- Publish a compact research-artifact release containing only admitted runs, manifests, checksums, extraction outputs, and analysis code; keep superseded/pilot material in a clearly labelled archive.
- Add CI jobs for JDK 21 build/tests and a smaller, explicitly secondary JDK 24/25 boundary check. Do not mix boundary-runtime outcomes into the Java 21 primary estimate.
- Make the dashboard display the source tag, artifact-bundle hash, generator version, condition count, and a prominent “primary evidence available” check.
- Add a repository licence and a short artifact-evaluation guide stating storage size, expected runtime, supported OS, and which result is the representative recheck.
- Present PostgreSQL/H2 and one-carrier/default-scheduler results as separate evidence families rather than combining them into one headline table.

## 10. Consistency, validity, and integrity notes

### Scope and claim consistency

- RQ1 refers to synchronization in “data layers,” but the primary treatment is in `PaymentService`. Either change the RQ to “service/application layer” or add an actual data-layer synchronization treatment.
- The repository correctly incorporates the JEP 491 boundary: monitor pinning in this form is a Java 21 result and must not be generalized to JDK 24+.
- The revised documents correctly retreat from the original implication that `ThreadLocal` presence or ordinary blocking is automatically pinning. Preserve this correction in the final thesis.
- The topic form’s earlier `−63% throughput` and `+96% recovery` figures remain preliminary unless mapped to admitted raw evidence. They should not reappear as confirmed results or target outcomes.

### Contradictory or stale identities

- `docs/current-artifact-freeze.md` records `1ccb617...` and a dirty tree; the public audited HEAD is `a9bd454...`.
- The committed dashboard says 76 records were validated, but a clean regeneration from the submitted evidence produces zero.
- The detailed plan and thesis outline still describe 50/100/200-VU and approximately 60-second comparisons, whereas primary iteration notes use 10 VUs and 15+30+10 seconds. Database sensitivity uses 50 VUs. These can all coexist only if labelled as distinct protocols and not silently pooled.
- The checkpoint-4 headline matrix and later replication note describe different run sets and different synchronized latency shapes. Preserve both only with explicit run-set identifiers and raw evidence.

### Source and configuration quality

- In `application.yml`, `datasource`, `h2`, `jpa`, and `sql` are nested under `demo`, so Spring Boot will not interpret them as `spring.datasource`, `spring.h2`, `spring.jpa`, and `spring.sql`. Embedded-H2 defaults may hide the mistake locally; the documented settings are not actually bound.
- The runner comments mention a 10 ms JFR threshold, but the recorded command does not configure that threshold explicitly. Record the effective JFR event settings rather than relying on a comment.
- The manifest’s `connection_pool_size`, timeout, and executor descriptions are placeholders/default statements rather than measured resolved configuration; platform runs can also inherit a misleading virtual-executor description.

### Analysis validity

- Closed-loop k6 VUs self-throttle as latency rises; request counts are not an open-loop server-capacity estimate. The documents mostly acknowledge this correctly.
- A one-carrier scheduler is a valid mechanism stress test, but it is not a production-performance configuration. Conclusions must separate mechanism detection from deployable capacity.
- Three process repetitions can support an exploratory descriptive result, but the earlier plan explicitly required a pilot-justified final repetition count. No final precision target or inferential justification is supplied.
- The PostgreSQL numbers are reproducible from the committed files, but the design does not produce connection saturation because the artificial 300 ms delay occurs before the trivial query. Treat the observed null result narrowly.

### Integrity, ethics, and AI

- No human participants, personal data, confidential partner data, or sensitive production data are evident in the submitted experiment. Synthetic data are suitable for this system study.
- No claim is made about whether AI was or was not used. Repository instructions or prose style are not evidence of use. The live ELTE rules require transparent point-of-use documentation and a thesis declaration; the Dean’s Directive also requires retaining the complete interaction log where applicable. See the [ELTE AI policy](https://www.inf.elte.hu/en/ai-usage-policy) and [Dean’s Directive No. 1/2026](https://www.inf.elte.hu/en/dstore/document/328007/Dean%27s%20Directive_1_2026_On%20Usage%20of%20AI%20Tools_0.pdf).

## 11. Recheck package

Submit one frozen package containing all of the following:

1. Supervisor-approved commitment ledger and confirmed January/June examination track.
2. Substantially complete editable thesis plus rendered PDF.
3. Clean tagged repository revision with corrected configuration and final tests.
4. Immutable evidence bundle containing every admitted manifest, k6 JSONL, JFR file, telemetry file, extraction output, exclusion record, and SHA-256 checksum.
5. Final protocol with exact versions, runtime settings, JFR configuration, load model, run order, warm-up, timeouts, repetitions, validity rules, and analysis plan.
6. Reproducible analysis script and generated tables/figures; no hand-entered headline numbers.
7. Clean-clone transcript showing build/tests, representative benchmark reproduction, normalization, hash validation, and dashboard generation.
8. RQ-to-method-to-evidence-to-thesis map with a supported, qualified answer for every RQ branch.
9. Final bibliography/citation package on a credible path to the supervisor-specific minimum of 30 relevant sources.
10. Truthful AI use/no-use disclosure, point-of-use notes, completed declaration, and retained-log reference where applicable.
11. Short checkpoint-4 presentation/demo record showing the frozen artifact, one central reproduction, result interpretation, negative findings, and remaining checkpoint-5-only work.

### Minimum pass condition

The fastest credible route to a checkpoint-4 pass is to: (1) finish the thesis draft; (2) restore or rerun and freeze the central Java 21 evidence; (3) make the evidence pipeline pass from a clean clone; (4) narrow or validly re-run the connection-pool branch; (5) reconcile all versions/protocol descriptions; and (6) close the AI and supervisor-approval records. Once those items are supplied, every `Fail`/`Unverified` gate should be re-audited rather than simply changing the overall label.
