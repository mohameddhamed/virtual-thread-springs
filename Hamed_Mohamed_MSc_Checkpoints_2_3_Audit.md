# ELTE IK MSc consultation audit: bibliography review and detailed research plan

**Student:** Hamed Mohamed (DG1EWF)
**Programme/track:** MSc in Computer Science - Software Architecture
**Thesis:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*
**Supervisor:** Gregory Reynolds Morse
**Audit date:** 2026-09-17
**Research mode:** Empirical engineering/system study

## Decisions at a glance

| Checkpoint | Required decision | Plain-language result | Main reason |
|---|---|---|---|
| Checkpoint 2 - bibliography review | **Insufficient** | Fail pending revision | The four-page product and approximate source count are present, but several references are incomplete or unverifiable, current closest work is missing, the review does not critically establish the claimed gap, and the thesis-specific artifacts are not stable literature citations. |
| Checkpoint 3 - detailed research plan | **Insufficient** | Fail pending revision | RQ1 and the evidence-preservation idea are promising, but the plan body is about nine pages rather than 3-5, the literature-grounded gap is not cited, RQ2 is not operationally closed, the repetition/statistical protocol is inadequate, and the schedule cannot reach the apparent 1 October checkpoint-4 deadline. |

These are consultation-checkpoint decisions, not a thesis grade. Both submissions are repairable. The strongest material to retain is the plan's separation of pinning from context/resource risks, its JFR attribution rule, its raw-evidence fallback, and its refusal to claim universal Virtual Thread superiority.

## Evidence and audit basis

### Student artifacts reviewed

- `bibliography-review-first-consultation.pdf`: 4 pages, dated 2026-07-12.
- Approved topic-registration form: 1 page, dated 2026-07-02.
- `Hamed_Mohamed_Detailed_Research_Plan_Prism.zip`: editable LaTeX source received 2026-09-17.
- The research-plan source compiled to 12 physical pages: title, abstract, contents page, and approximately 9 pages of plan body (numbered pages 2-10).
- `references.bib` in the plan package contains only three template/policy entries; none of the thesis literature from the bibliography review is incorporated or cited in `main.tex`.
- The project repository, source code, benchmark scripts, raw k6 output, JFR recordings, and run manifests named in bibliography entries 13-15 were not supplied. Their existence and claim support could not be checked.

### Rules used

- [ELTE IK MSc thesis guidance](https://inf.elte.hu/en/guidelines-thesis-final-examination-msc)
- [ELTE IK MSc consultation deadlines and products](https://inf.elte.hu/dstore/document/227130/MSc%20Thesis%20consultations%20-%20deadlines%20-%20PTI-ARI-ADAT.pdf)
- [ELTE IK AI-usage policy](https://www.inf.elte.hu/en/ai-usage-policy)
- Gregory Morse's additional supervision standards, where applicable, including the later-thesis bibliography target. These are supervisor-specific standards, not faculty-wide checkpoint gates.

---

# Checkpoint 2 - bibliography review

## 1. Result

**Insufficient**

## 2. Deadline status

Assuming the student is following the January-final-exam schedule, checkpoint 2 was due **2026-07-01**. The PDF is dated **2026-07-12**, so it is **11 days late**. If the intended final-exam period is June instead, the applicable checkpoint-2 deadline is 1 December; the supervisor should confirm the track rather than infer it.

The PDF labels this as the "First Consultation Milestone," but the submitted product is the official bibliography-review product assessed here as checkpoint 2.

## 3. Scope and evidence reviewed

The review is correctly focused on a Java 21 Spring Boot MVC migration study. It uses 12 externally identifiable platform/framework/research sources plus three local project artifacts. The source mix is appropriate in principle for an engineering/system study: normative JDK material, framework/runtime documentation, measurement tools, and systems research. The decisive limitations are that several entries do not contain stable bibliographic identities, the local artifacts were unavailable, and the review omits recent work close enough to affect both novelty and experimental design.

## 4. Executive reason

The submission satisfies the visible format and approximate-count requirements, and its thematic organization is better than a bare annotated list. It does not yet establish a defensible research frontier. Most of the evidence is documentation or foundational work from 2001-2003; it omits recent empirical Virtual Thread studies and, critically, [JEP 491](https://openjdk.org/jeps/491), which removed monitor-related pinning from `synchronized` code beginning with JDK 24. The thesis can still study Java 21 LTS, but any migration checklist must be explicitly version-bounded. The review must also separate literature from the student's unpublished evidence artifacts and cite all material claims at the point of use.

## 5. Mandatory-gate table

| ID | Gate | Status | Evidence | Finding |
|---|---|---|---|---|
| C1 | Required 3-5 page review | Pass | PDF pp. 1-4 | Four substantive pages are present. |
| C2 | Approximately ten substantive sources | Pass | Entries 1-12 | Twelve external sources are identifiable. Entries 13-15 are evidence artifacts and are not counted as literature. The three preview/final JEPs are related but not duplicates when used for design history. |
| C3 | Alignment | Pass | PDF pp. 1-2; topic form | The review addresses the approved Java 21/Spring MVC topic, pinning, framework configuration, database limits, and measurement. |
| C4 | Bibliographic authenticity | Fail | Entries 7, 8, 13-15; dynamic "Current" entries | HikariCP combines two unnamed sources without URLs; the JFR item does not identify the page that defines the event; the three local artifacts have no repository, revision, or archive identifier and were unavailable. Several live-doc entries lack version/access dates. |
| C5 | Source quality and primary evidence | Fail | Entries 1-12 | Official documentation is useful, but only three old research papers provide scholarly evidence. No recent empirical Spring/Virtual Thread or database-driven server study is reviewed. |
| C6 | Field and closest-work coverage | Fail | Sections 2.4 and 4 | Missing JEP 491 and recent closest work, including database-driven server, framework-integration, Spring, and Java benchmarking studies. Section 4 itself says empirical Loom studies still need to be sought. |
| C7 | Critical synthesis | Fail | Sections 2.1-2.4 | Sources are grouped thematically, but assumptions, workloads, versions, metrics, findings, and limitations are not compared. The prose mostly states what each source is useful for. |
| C8 | Research gap | Fail | PDF p. 4; plan's Related Work chapter | The gap is asserted before the closest modern work is identified. The omitted JDK 24+ change materially narrows the relevance of the proposed synchronized-to-`ReentrantLock` guidance. |
| C9 | Method/evaluation landscape | Fail | Section 2.3 | JFR and k6 are identified, but the review does not cover open versus closed load models, JVM warm-up/steady state, run randomization, repetition planning, uncertainty, effect sizes, or database-pool measurement. |
| C10 | Claim-citation fidelity | Fail | Throughout thematic review | Material claims are not supported with conventional in-text citations at the sentence or paragraph of use. The JFR discussion overstates causal inference: a pinning event and a performance change require a controlled comparison before causality is supported. |
| C11 | Balance and limitations | Fail | Sections 2.1-2.4 | Resource bottlenecks are acknowledged, but contrary/current evidence is not synthesized. JEP 491 and the fact that Virtual Threads target throughput rather than lower single-request latency must be central limitations. |
| C12 | Citation mechanics and reuse | Fail | Entries 5-9 and 13-15 | Incomplete entries, "Current" dates, missing versions, two HikariCP pages collapsed into one item, and local paths prevent reliable one-to-one reuse in a thesis bibliography. |
| C13 | Integrity, AI, and checkpoint consistency | Unverified | Topic form; bibliography; absent disclosure/artifacts | No fabricated external source was found, but local artifacts and claimed measurements could not be checked. The topic form groups `ThreadLocal` misuse and blocking I/O with pinning; the later plan correctly separates these mechanisms. Actual AI use or non-use is not declared in this checkpoint package. |

## 6. Source-audit table

| No. | Source/type | Identity | Claim support checked | Relevance/quality | Required action |
|---:|---|---|---|---|---|
| 1 | JEP 444, final Virtual Threads specification | Verified | Yes - Java 21 semantics, throughput goal, pinning, and observability | Authoritative primary platform source | Cite Ron Pressler/OpenJDK accurately and use a stable access date. |
| 2 | JEP 425, first preview | Verified | Partly - historical design only | Authoritative, but secondary to the final JEP for Java 21 claims | State the exact design difference being traced; otherwise omit to avoid padding. |
| 3 | JEP 436, second preview | Verified | Partly - historical design only | Authoritative, but secondary to JEP 444 | Compare a specific changed constraint with JEP 444 or omit. |
| 4 | Oracle Java 21 Virtual Threads guide | Verified | Yes - pinning, `ReentrantLock`, JFR event, 20 ms default threshold, ThreadLocal cautions | Authoritative operational guidance | Cite the specific subsections used. This is also the correct source for the event semantics currently attributed to entry 8. |
| 5 | Spring Boot Virtual Threads documentation | Verified as a live page | Yes - `spring.threads.virtual.enabled` | Authoritative but version-dynamic; current page is not necessarily the tested release | Cite the exact Spring Boot version used and its versioned reference page. Distinguish async task execution from the embedded server's request executor. |
| 6 | Tomcat HTTP Connector documentation | Verified as a live page | Yes - platform-thread limits and connector settings | Authoritative but version-dynamic | Freeze the tested Tomcat version and cite exact settings such as `maxThreads`, executor choice, and `useVirtualThreads`. |
| 7 | HikariCP configuration and pool-sizing guidance | Unverified as written | No | Relevant official implementation guidance | Split into two complete citations with URLs, version/commit, and access dates: configuration knobs and *About Pool Sizing*. |
| 8 | Oracle `jfr` command documentation | Incomplete/mismatched | No - the named command page is not the identified semantic source | Tool documentation is relevant, but the citation does not support the event-definition claim | Replace or supplement it with the Oracle Java 21 Virtual Threads guide and cite the exact recording/printing command used. |
| 9 | Grafana k6 documentation | Verified as a broad documentation set | Partly | Authoritative tool documentation, but too broad for a reproducible protocol | Cite versioned pages for scenarios, open/closed models, metrics, thresholds, and JSON output. |
| 10 | von Behren, Condit, and Brewer (2003), *Why Events Are A Bad Idea* | Verified | Yes - threads/events argument and user-level-thread evidence | Peer-reviewed foundational context, not current closest work | Retain, but explicitly state its 2003 runtime/workload limits and compare it with modern JVM Virtual Threads. |
| 11 | Welsh, Culler, and Brewer (2001), SEDA, DOI 10.1145/502034.502057 | Verified | Bibliographic identity and central architecture claim checked | Peer-reviewed foundational systems work | Retain for overload/backpressure, but do not treat it as direct evidence about Java 21. |
| 12 | Adya et al. (2002), cooperative task management | Verified | Yes - control-flow/stack-management motivation | Peer-reviewed foundational context | Retain for programming-model history; distinguish it from evidence about current JVM performance. |
| 13 | `run-benchmark.sh` | Unverified | No artifact supplied | Potential primary research artifact, not literature | Move to an artifact/provenance ledger; add repository URL, commit/tag, checksum, licence, and archived copy. |
| 14 | `k6/load-test.js` | Unverified | No artifact supplied | Potential primary research artifact, not literature | Move to artifact ledger and identify the exact revision plus generated workload manifest. |
| 15 | `results/*.json` and `results/jfr/*.jfr` | Unverified | No artifact supplied | Raw evidence, not a bibliography source | Move to evidence inventory; freeze run IDs, checksums, configuration, and analysis mapping. |

### High-priority missing closest work

At minimum, the revised review should position the study against the following current or close work and explain what remains different:

- [JEP 491: Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491) - essential version boundary; delivered in JDK 24.
- Beronić et al., *On Analyzing Virtual Threads - a Structured Concurrency Model for Scalable Applications on the JVM*, DOI [10.23919/MIPRO52101.2021.9596855](https://doi.org/10.23919/MIPRO52101.2021.9596855).
- Navarro et al., *Considerations for integrating virtual threads in a Java framework: a Quarkus example in a resource-constrained environment*, DOI [10.1145/3583678.3596895](https://doi.org/10.1145/3583678.3596895).
- Lašić et al., *Assessing the Efficiency of Java Virtual Threads in Database-Driven Server Applications*, DOI [10.1109/MIPRO60963.2024.10569754](https://doi.org/10.1109/MIPRO60963.2024.10569754).
- Likus and Krużel, *Analysis of Virtual Threads in Spring Applications*, ECMS 2025, pp. 555-561.
- Charlak, Brzeziński, and Kozieł, *Comparative analysis of reactive programming and Java virtual threads*, DOI [10.35784/jcsi.9409](https://doi.org/10.35784/jcsi.9409), published 2026-06-30.
- Traini et al., *Towards effective assessment of steady state performance in Java software: Are we there yet?*, DOI [10.1007/s10664-022-10247-x](https://doi.org/10.1007/s10664-022-10247-x), for JVM measurement validity.

## 7. Coverage map

| Question/contribution | Closest prior work currently used | Unresolved gap claimed | Missing evidence needed |
|---|---|---|---|
| RQ1: effect of blocking under intrinsic synchronization on Java 21 Virtual Threads | JEP 444; Oracle Java 21 guide; foundational thread/event papers | Mechanism-focused Spring MVC comparison with JFR attribution | JEP 491 boundary; recent Spring/Virtual Thread studies; full comparison of their versions, workloads, metrics, and findings; JVM benchmark-validity literature |
| RQ2: architecture risks to audit before migration | Spring/Tomcat/HikariCP docs; Oracle adoption guide | Practical anti-pattern classification and migration checklist | A defined universe of patterns; evidence for `ThreadLocal`, JDBC/pool, native calls, and remaining pinning cases; recent production/framework studies; per-pattern validation criteria |
| Reproducible evaluation | JFR and k6 documentation | Three-condition measured demonstration | Load-model literature, warm-up/steady-state method, repetition/power rationale, randomization, hardware/OS controls, JFR threshold/configuration, database-pool telemetry |
| Engineering guidance | Foundational concurrency papers | Evidence-bounded six-step checklist | Explicit Java-version applicability, comparison with JDK 24/25 behavior, negative/contrary findings, and transfer limits beyond one H2 demonstration application |

## 8. Required corrections

| Defect | Impact | Exact repair | Recheck evidence |
|---|---|---|---|
| JDK 24+ change absent | The central migration warning is outdated if presented beyond Java 21 | Add JEP 491 and state that monitor-related pinning is a Java 21-specific concern removed in JDK 24+. Either keep the thesis explicitly scoped to Java 21 LTS or add a JDK 25 boundary comparison. | Revised synthesis and scope paragraph with citations and explicit version table |
| Closest recent studies absent | Novelty/gap cannot be defended | Review and compare the high-priority works above by runtime/framework version, workload, hardware, metrics, repetitions, and limits. | Closest-work comparison table and revised gap |
| Incomplete citations | Source identity and claim support cannot be audited | Correct entries 5-9; split Hikari sources; add authors/versions/years/identifiers/access dates; remove `Current`. | Complete `.bib`/RIS plus verified link ledger |
| Local artifacts counted as bibliography | Inflates source set and hides provenance | Move entries 13-15 to a separate artifact/evidence inventory with immutable revision and checksums. | Artifact manifest and accessible archive/repository revision |
| Weak critical synthesis | Gap is asserted by omission | Replace descriptive paragraphs with comparisons of assumptions, mechanisms, empirical design, findings, and limitations. | Revised 3-5 page review with synthesis table |
| Missing point-of-use citations | Readers cannot trace material claims | Add citations to every technical, causal, quantitative, novelty, and methodological claim. | PDF and editable source with one-to-one citation mapping |
| Mechanism conflation in topic narrative | `ThreadLocal`, database contention, and pinning risk being treated as the same phenomenon | Preserve the plan's corrected classification: confirmed pinning source; resource/context risk; or not demonstrated. Explicitly reconcile this with the topic form. | Consistency note approved by supervisor |
| AI/provenance status absent | Integrity gate cannot be verified | State either no generative AI use or the exact tools/models, purposes, affected locations, verification, and retained-log location, as applicable. | Checkpoint disclosure and retained log if used |

## 9. Suggestions

- Keep the thematic structure, but reduce the three JEP entries to one central JEP 444 discussion plus a short preview-history note.
- Use a compact table for closest empirical studies; this will create space while staying within four pages.
- Treat production reports such as the Netflix pinning case as practitioner evidence, clearly separated from peer-reviewed research.
- For the final thesis, build toward the supervisor-specific target of at least 30 relevant sources, with around 50 strongly recommended. This is not a checkpoint-2 raw-count gate.

## 10. Integrity and consistency notes

- No fabricated external citation was identified among entries 1-12.
- Entries 7 and 8 are not sufficiently specified to be auditable; entries 13-15 are unavailable local paths and therefore unverified.
- The topic form reports `-63% throughput` and `+96% recovery` as if they are established results. The research plan later calls such historical figures unreconciled. Until the raw runs are verified, label these numbers **preliminary pilot observations**, not results or expected confirmation targets.
- The approved synopsis implies that `ThreadLocal` misuse and blocking I/O cause pinning. The plan correctly narrows direct pinning to supported mechanisms and treats context/resource problems separately. The revised literature review should make this correction explicit.
- Actual AI use or non-use is unknown. No inference has been made from style.

## 11. Recheck package

Submit all of the following together:

1. Revised 3-5 page bibliography review with point-of-use citations and a defensible current gap.
2. Complete editable source plus `.bib` or citation-manager export.
3. Source-verification ledger with a stable identifier for every entry.
4. Approved topic form and explicit reconciliation of the pinning/`ThreadLocal` wording.
5. Separate artifact manifest for scripts, code, raw k6 outputs, JFR files, commit/tag, checksums, and licences.
6. Actual AI-use/non-use disclosure and retained log if applicable.

---

# Checkpoint 3 - detailed research plan

## 1. Result

**Insufficient**

## 2. Deadline status

Assuming the January-final-exam schedule, checkpoint 3 was due **2026-09-10**. The supplied package is dated **2026-09-17**, so it is **7 days late**. More importantly, checkpoint 4 is due **2026-10-01** on that schedule. A seven-week research programme beginning now cannot produce the required checkpoint-4 evidence in about two weeks. If the student is instead on the June-final-exam schedule, checkpoint 3 is due 10 February; confirm the intended track immediately.

## 3. Scope and evidence reviewed

- Programme/track: MSc Computer Science, Software Architecture.
- Mode: empirical engineering/system study.
- Primary planned artifact: versioned Spring Boot MVC application, Maven configuration, H2 data, k6 scripts, benchmark orchestration, JFR recordings, raw k6 JSON, and analysis documents.
- Planned treatments: platform threads with legacy synchronization; Java 21 Virtual Threads with the same synchronization; Java 21 Virtual Threads with `ReentrantLock`.
- Planned endpoints: `/orders`, `/payments`, and `/products`.
- Limitations: code, pilot runs, raw measurements, JFR recordings, and exact deployed versions/configurations were not supplied. The plan can therefore be audited as a design, not as verified execution evidence.
- Format: the source compiles to 12 physical pages; the plan body occupies about 9 pages, exceeding the required 3-5 pages.

## 4. Executive reason

The plan contains a viable core study, especially RQ1, but it is not execution-ready. The strongest causal rule is sensible: call degradation pinning-related only when JFR identifies the application lock, the refactoring changes pinning, and the performance difference reproduces under the same protocol. However, RQ2 asks which architecture patterns must be audited without defining the pattern set or an experiment/audit capable of answering that broad question. The plan also lacks literature citations, ignores the JDK 24+ removal of monitor pinning, proposes only three repetitions while claiming bootstrap 95% intervals, leaves warm-up/run-order/load-model/JFR settings under-specified, and uses a relative seven-week schedule incompatible with the apparent checkpoint-4 date.

## 5. Mandatory-gate table

| ID | Gate | Status | Evidence | Finding |
|---|---|---|---|---|
| C1 | Required 3-5 page detailed plan | Fail | Compiled PDF: 12 physical pages; body about 9 pages | The plan substantially exceeds the checkpoint product. Title/abstract/contents do not explain the nine-page body. |
| C2 | Aims and exact questions | Fail | Plan pp. 2-3 | RQ1 is bounded and measurable. RQ2 is too broad: it does not define the universe of architecture patterns, selection method, or what evidence would justify "must be audited." |
| C3 | Literature-grounded gap | Fail | Plan p. 4; `references.bib` | The gap has no in-text citations; the plan bibliography contains only unused policy/template entries; JEP 491 and close empirical studies are absent. |
| C4 | End-to-end traceability | Fail | Plan pp. 5-7 | RQ1 has a partial chain. RQ2 lacks per-pattern method, evidence, baseline/control, analysis, and decision rules. |
| C5 | Method detail | Fail | Plan pp. 5-7 | Exact JDK/Spring/Tomcat/Hikari/k6 versions, JVM flags, hardware/OS controls, lock settings/scope, database configuration, run-order randomization, warm-up criterion, timeout policy, and JFR event configuration are missing. |
| C6 | Mode-specific design | Fail | Engineering/system mode | Correctness equivalence after refactoring is not tested; workload realism and the current-JDK boundary are not adequately handled; one demo/H2 system cannot support a general architecture checklist without narrower claims. |
| C7 | Baselines, controls, success criteria | Fail | Plan pp. 5-7 | Three useful conditions and a clean endpoint exist, but a full 2x2 thread-mode/lock matrix is absent. Materiality thresholds are unexplained, and no non-inferiority/equivalence rule defines "recovery." |
| C8 | Data/sampling protocol | Fail | Plan pp. 6-7 | No run inclusion/exclusion rule, exact workload model, stable-state rule, event threshold, run manifest schema, or pre-specified handling of failed/time-out runs is given. |
| C9 | Analysis and uncertainty | Fail | Plan p. 7 | A bootstrap 95% interval from as few as three runs is not credible. No pilot-based sample-size rationale, blocked/randomized runs, effect-size plan, multiple-load analysis, or sensitivity protocol is specified. |
| C10 | Validity, bias, negative results | Fail | Plan p. 7 | Several threats and a good evidence-preserving fallback are named, but confirmation bias from pre-announced results, run order, JIT/GC/thermal drift, closed-model coordinated omission, and lock-semantic confounding lack mitigation. |
| C11 | Reproducibility/artifact plan | Pass | Plan pp. 5-8 | The intended source/configuration/raw-output/JFR/run-manifest package is strong in outline. It still needs an exact schema, environment lock, checksums, commands, licences, and accessible revision. |
| C12 | Feasibility, ethics, resources, licences | Pass | Plan p. 8 | The plan uses public software and synthetic H2 records, with no human participants or personal/confidential data. Freeze exact dependency licences and machine/compute access before execution. |
| C13 | Schedule, risks, fallback | Fail | Plan p. 8 | Relative weeks have no dates, owners, buffers, or checkpoint mapping. On the apparent January-exam schedule, the work extends far beyond the 1 October checkpoint-4 milestone. |
| C14 | Reuse, consistency, AI transparency | Fail | Plan pp. 4, 7, 9; topic form; `references.bib` | The plan is structurally reusable, but it is not literature-linked; it silently changes the topic form's pinning characterization; preliminary figures are unreconciled; and the AI chapter states policy rather than the student's actual use/non-use. |

## 6. Question-to-method matrix

| RQ | Construct/hypothesis | Current method | Data/evidence | Baseline/control | Metric | Analysis | Decision rule | Answer artifact/status |
|---|---|---|---|---|---|---|---|---|
| RQ1 | In Java 21, blocking while holding an intrinsic monitor pins a carrier and can reduce system throughput; a Virtual-Thread-compatible lock should remove the pinning mechanism while preserving intended mutual exclusion | Three-condition comparison plus mixed and isolated endpoints | k6 raw output, JFR files/events/stacks, source revision, configuration | Platform+`synchronized`; VT+`synchronized`; VT+`ReentrantLock`; clean endpoint | Throughput, p50/p95/p99, error rate, pinned-event count/duration | Planned median/IQR/bootstrap | Degradation is pinning-related only if the application lock appears in JFR, refactoring changes pinning, and performance changes reproducibly | **Partly traceable.** Add platform+`ReentrantLock` for a 2x2 matrix, exact event settings, adequate repetitions, correctness tests, and version boundary. |
| RQ2 | Defined legacy architecture patterns create either pinning, context-lifecycle, or finite-resource risks | Current text proposes a code audit and observes three endpoints, but no explicit per-pattern protocol | Source audit, JFR, pool-wait/connection telemetry, memory/context checks, correctness tests, raw runs | Per-pattern removal/ablation and clean implementation | Mechanism-specific: JFR for pinning; pool wait/saturation for JDBC; leakage/lifecycle tests for context; functional invariants | No complete analysis is specified | Classify only when a pre-defined indicator and controlled comparison support the category; otherwise "not demonstrated" | **Not traceable.** Narrow RQ2 to the evaluated patterns or add a documented pattern-selection and per-pattern validation protocol. |

### Recommended bounded rewrite of RQ2

> **RQ2:** In the demonstration application, how do (a) intrinsic synchronization around blocking work, (b) request-context handling with `ThreadLocal`, and (c) JDBC connection-pool saturation affect pinning, context correctness, and finite-resource contention under the specified Java 21 Virtual Thread workloads?

This wording matches what the artifact can actually demonstrate. A broader migration checklist may be an evidence-bounded synthesis, but not a claim that the experiment has identified every pattern in legacy Spring MVC systems.

## 7. Validity and feasibility register

| Threat/dependency | Consequence | Required mitigation | Fallback | Owner/evidence |
|---|---|---|---|---|
| JEP 491/JDK 24+ removes monitor pinning | Java 21 result may be obsolete when generalized | State Java 21 scope; add at least one JDK 25 VT+`synchronized` boundary run if feasible | Keep a Java 21 LTS case study and explicitly limit guidance | Student + supervisor; versioned scope and run matrix |
| RQ2 construct too broad | Evidence cannot answer the question | Narrow to three named patterns or define a systematic pattern-selection protocol | Report only evaluated mechanisms | Student; revised RQ and traceability matrix |
| JFR default threshold is 20 ms | Short pins are censored; counts across configurations may be misleading | Freeze a custom JFR configuration and exact extraction command; record threshold and event settings | Restrict claims to events above the configured threshold | Student; `.jfc`, command log, JFR files |
| Three repetitions with bootstrap CI | Unstable uncertainty estimates and false precision | Use pilot variance to justify sample size; ordinarily use substantially more independent runs and report effect sizes/intervals | Label results exploratory and omit inferential confidence claims | Student; pilot and analysis plan |
| JIT, GC, warm-up, CPU frequency, thermal drift | Configuration/order effects can masquerade as treatment effects | Predefine warm-up/stability rule; randomize or block run order; record GC/JIT/CPU/temperature where feasible | Narrow to descriptive single-machine evidence | Student; run manifest and logs |
| Closed k6 VU model | Throughput drops as response time rises, complicating overload interpretation | State whether the model is closed; add a constant-arrival-rate scenario or justify the closed model; record dropped iterations | Limit conclusions to the chosen workload model | Student; k6 scenario files |
| Mixed endpoints | Cross-endpoint interference hides the causal path | Use isolated runs as primary causal evidence and mixed runs as system-level validation | Report mixed results only as aggregate behavior | Student; per-endpoint and mixed run IDs |
| Lock replacement semantics | Performance gain may accompany changed fairness, scope, or correctness | Keep identical critical section; specify `ReentrantLock` fairness; add concurrency/correctness tests | Claim only carrier release, not equivalent application behavior | Student; source diff and tests |
| H2/simulated delays | Weak production and database external validity | Frame as mechanism case study; measure pool waits; optionally replicate one configuration with PostgreSQL | Do not claim production-scale transfer | Student; limitations and optional sensitivity run |
| Pre-announced `-63%` and `+96%` figures | Confirmation bias and possible circular success criteria | Treat as pilot observations, blind/freeze the new protocol before rerun, retain all valid runs | Retract unreproducible figures and report null/negative result | Student + supervisor; preregistered protocol/run ledger |
| Relative seven-week schedule | Misses checkpoint 4 on apparent January track | Replace with calendar dates and minimum viable scope immediately | Defer optional pool study and broad checklist | Student + supervisor; dated schedule |
| Missing exact artifacts/licences | Reproduction and review blocked | Freeze repository/tag, dependency lock, licences, checksums, environment, and commands | Provide an authorized private archive if public release is impossible | Student; artifact manifest |

## 8. Required corrections

| Defect | Scientific consequence | Exact repair | Recheck evidence |
|---|---|---|---|
| Plan is too long | Fails the required checkpoint product and obscures execution decisions | Reduce to 3-5 pages excluding at most a brief cover. Remove abstract/contents/chapter-opening whitespace; use compact tables for RQs, run matrix, validity, and schedule. | Revised compiled PDF with page count |
| Gap is uncited and outdated | Contribution cannot be defended | Import the verified bibliography; cite every related-work claim; discuss JEP 491 and recent empirical work; state the exact remaining gap. | Revised plan source/PDF and `.bib` |
| RQ2 is unanswerable as written | The study could only produce anecdotes | Adopt the bounded RQ2 above or define a systematic architecture-pattern population, inclusion rule, and per-pattern validation protocol. | Revised RQ-to-method matrix |
| Version scope is unclear | Java 21 advice may be misapplied to JDK 24/25 | Freeze JDK distribution and patch. Add a version-applicability table and preferably one JDK 25 boundary condition. | Environment manifest and run matrix |
| Experimental matrix is incomplete | Thread-mode and lock effects are not fully separated | Use a 2x2 core matrix: platform/VT x `synchronized`/`ReentrantLock`; keep clean/isolated endpoint controls. Add JDK 25 VT+`synchronized` only as a boundary test if feasible. | Pre-registered condition table |
| Protocol lacks execution detail | Runs cannot be reproduced or fairly compared | Freeze all software/hardware/configuration values, critical-section code, Hikari/Tomcat settings, k6 scenario, request mix, timeouts, warm-up, run order, validity/exclusion rules, and JFR configuration. | Versioned protocol and sample run manifest |
| Statistical plan is not credible | Three-run bootstrap intervals imply unjustified precision | Run a pilot, justify the final number of independent repetitions, use randomized/blocked order, report effect sizes and intervals, and label underpowered results exploratory. | Pilot variance summary and analysis script |
| Success criteria are arbitrary | Results invite post-hoc interpretation | Justify materiality thresholds; define baseline recovery as a pre-specified equivalence/non-inferiority rule; define per-pattern classification indicators for RQ2. | Frozen decision-rule table before final runs |
| Correctness is not tested | Refactoring may change behavior while improving measurements | Add unit/integration/concurrency tests demonstrating identical intended mutual-exclusion and endpoint semantics. | Test report tied to the tested commit |
| Schedule misses milestone | Checkpoint 4 cannot be reached honestly | Replace weeks with dates, owners, outputs, dependencies, and a minimum viable checkpoint-4 scope. Defer optional PostgreSQL/pool sensitivity if necessary. | Dated schedule approved by supervisor |
| Actual AI status absent | Transparency gate remains unresolved | Replace the generic policy chapter with a concise factual disclosure or no-use statement; retain the interaction log if applicable. | Point-of-use notes and retained log/declaration plan |

## 9. Suggestions

- Keep the plan's causal triad for RQ1; it is the best sentence in the design.
- Keep the categories "confirmed pinning source," "resource/context risk," and "not demonstrated." They prevent mechanism inflation.
- Keep endpoint-isolated runs as the primary causal test and mixed-endpoint runs as a secondary system-behavior test.
- Record carrier-pool parallelism, CPU utilization, GC pauses, Hikari acquisition wait, and Tomcat executor configuration. These will make negative results interpretable.
- The 300/500 ms simulated delays are acceptable for a mechanism experiment, but describe them as synthetic and do not call the workload "realistic" without an empirical basis.
- The package's `make` command required an EPS-to-PDF conversion utility in the audit environment. Include a PDF/PNG logo or explicitly document the dependency so a clean build is predictable.

## 10. Consistency and integrity notes

- **Topic versus plan:** the title and broad contribution are consistent. The plan correctly retreats from the topic form's implication that `ThreadLocal` misuse and all blocking I/O cause pinning; document this as a scientific clarification.
- **Preliminary numbers:** the topic form's `-63%` and `+96%` figures are not verified by the supplied package. They must not become target values or confirmed results.
- **Current platform state:** JEP 491 materially changes the synchronized-pinning mechanism after Java 21. This does not invalidate a Java 21 LTS case study, but it changes its external validity and practical contribution.
- **Ethics/privacy:** no human-subject, personal, or confidential data is planned. Synthetic H2 data is appropriate.
- **Provenance:** the plan promises good evidence retention, but the evidence is not yet supplied. No claim of execution or reproduction is made in this audit.
- **AI:** the chapter explains policy but does not say what this student actually used. No inference has been made.

## 11. Recheck package

Submit all of the following together:

1. Revised 3-5 page research plan in editable form and compiled PDF.
2. Revised verified bibliography and in-text citations, including JEP 491 and closest empirical work.
3. Final RQ wording and question-to-method-to-evidence-to-decision matrix.
4. Frozen experiment protocol and condition matrix, including exact versions/configurations, JFR event settings, workload model, warm-up, randomization, validity/exclusion rules, and correctness tests.
5. Pilot results used only to justify repetition count and analysis; preserve all pilot raw data.
6. Calendar-dated schedule aligned to the actual final-exam track and checkpoint-4 deadline.
7. Accessible repository/archive revision with code, scripts, run-manifest schema, licences, and checksums.
8. Actual AI-use/non-use disclosure and retained log if applicable.

---

# Minimum revision path to a pass

The shortest credible route is:

1. Explicitly scope the contribution to **Java 21 LTS** and add JEP 491/current closest work.
2. Rebuild the bibliography as a 3-5 page critical comparison, with local artifacts moved to a provenance ledger.
3. Narrow RQ2 to the three mechanisms actually represented in the artifact.
4. Compress the plan to 3-5 pages using four tables: RQs, experiment matrix, validity/decision rules, and dated schedule.
5. Replace the three-run bootstrap proposal with a pilot-justified repetition plan and freeze exact workload/JFR settings.
6. Make the topic form's existing percentages explicitly preliminary until reproduced from traceable raw artifacts.

After these changes, checkpoint 2 and checkpoint 3 should be resubmitted together because the plan's scientific validity depends directly on the corrected literature gap.
