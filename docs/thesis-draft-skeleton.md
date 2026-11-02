# Thesis Draft Skeleton

## Working title

**Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture,
Risks, and Engineering Guidelines**

> **Writing rule for this document:** this is a thinking and drafting
> scaffold. Section notes describe what the final text should establish; they
> do not substitute for the student's own explanation, argument, or wording.

## Document status

- **Programme:** MSc Computer Science, Software Architecture
- **Draft purpose:** initial full-documentation silhouette
- **Evidence basis:** current repository revision and retained research artifacts
- **Primary artifact:** Spring Boot MVC demonstration application
- **Primary runtime:** Java 21
- **Research mode:** empirical engineering/system study
- **Current limitations to keep visible:** thesis prose is not complete; final
  provenance freeze and AI/integrity package remain open

## How to use this skeleton

For every subsection:

1. Read the subsection purpose.
2. Write the explanation in your own words.
3. Add exact artifact, source, citation, or result pointers.
4. Separate observation, interpretation, limitation, and implication.
5. Mark unresolved questions instead of silently filling gaps.

## Copilot note index

The numbered notes below preserve the author's preliminary remarks and connect
each one to the scaffold location prepared for it.

1. Performance symptom versus mechanism.
2. Research gap wording and evidence boundary.
3. Before/after measurement of the migration guidance.
4. Unmounting, carrier threads, serialization, and comparison with other
   programming models.
5. Whether the benchmark design measures the claimed lock/pinning effect.
6. Synchronization in other paradigms and Java's design choices.
7. Closed-loop versus open-loop workload realism.
8. Graphs and visual presentation of results.
9. History and rationale of `ReentrantLock`.
10. A decision tree in addition to the migration decision table.

---

# Front matter

## Title page

State the approved title, degree programme, specialization, author,
supervisor, institution, and submission context using the official template.

## Declaration and AI-use disclosure

Insert the required ELTE declaration and describe AI-assisted activities,
verification, point-of-use disclosure, and retained interaction-log location.
Do not complete or sign this section automatically.

## Abstract

Summarize the problem, research questions, artifact, methodology, principal
evidence, contribution, and limitations in a tightly bounded format. Avoid
introducing claims that are not supported in the results chapter.

## Keywords

Choose terms that represent the thesis scope rather than every extension:
Virtual Threads, Java 21, Spring Boot MVC, monitor pinning, synchronization,
JFR, blocking workloads, migration, architectural risk.

## List of abbreviations and terms

Define VT, JFR, JVM, MVC, JDBC, JNI, H2, PostgreSQL, VU, p50, p95, p99, and
any project-specific shorthand. Distinguish carrier thread, platform thread,
Virtual Thread, monitor pinning, serialization, and carrier occupation.

## List of figures, tables, and listings

Reserve entries for the architecture diagram, experimental workflow,
synchronization matrix, endpoint roles, result tables, evidence pipeline,
migration checklist, and selected code/configuration listings.

---

# 1. Introduction

## 1.1 Background and motivation

Explain why existing Spring Boot MVC systems are relevant to Virtual Thread
migration and why simply enabling a runtime feature is not a complete
architectural migration.

## 1.2 Problem statement *(Copilot note #1)*

Define the practical problem: legacy blocking, synchronization, context, and
finite-resource patterns may interact differently with Virtual Threads.
Clarify the difference between a performance symptom and its mechanism.
(copilot note #1: give me this)

### 1.2.1 Symptom-to-mechanism vocabulary

Create a small vocabulary table that separates observed symptoms such as
lower throughput or higher tail latency from candidate mechanisms such as
monitor pinning, application serialization, finite-resource waiting, CPU
work, or native carrier occupation. For each mechanism, state the direct
evidence required before using it as an explanation.

## 1.3 Research gap *(Copilot note #2)*

Position this work against the official JDK model and related studies. State
the narrower gap addressed by this thesis: a reproducible Java 21 Spring MVC
case study connecting controlled treatments, JFR evidence, correctness
checks, and migration guidance. (copilot note #2: give me this)

### 1.3.1 Gap-to-contribution alignment

Map each claimed gap to one artifact, experiment family, or analysis decision.
Use this subsection to prevent a broad “Virtual Threads are under-researched”
claim and to identify which parts are established, bounded, or outside scope.

**Evidence/source prompts:**

- `docs/detailed-research-plan.md`
- JEP 444 and JEP 491
- `docs/bibliography-review-revised.md`
- verified literature and official framework documentation

## 1.4 Research questions

State RQ1 and RQ2 exactly as approved. Define the terms used in each question
and explain which mechanisms are inside and outside the intended scope.

## 1.5 Objectives

List the objectives for the software artifact, measurement infrastructure,
mechanism analysis, correctness validation, evidence pipeline, and migration
guidance.

## 1.6 Contributions

Describe the intended contributions without overstating generality:

- controlled research software;
- reproducible measurement and observability workflow;
- mechanism-focused evidence;
- correctness-aware synchronization comparison;
- migration guidance tied to evidence and limitations.
- (copilot note #3: maybe after we finally come up with the migration guidlines we need to measure the before and after to prove yes this is indeed worth applying the rules)

### 1.6.1 Before-and-after validation of the migration guidance *(Copilot note #3)*

Reserve a comparison showing the legacy condition before applying a
mechanism-specific migration rule and the corresponding refactored condition
afterward. Define which rules can be tested with the existing evidence, which
require a new controlled run, and which cannot be validated by this thesis.
Compare correctness, mechanism evidence, and performance under the same
protocol rather than treating a faster result alone as proof that the guidance
is worthwhile.

## 1.7 Scope and boundaries

State the single-application, single-primary-machine, Java 21, synthetic
workload, closed-loop, and mechanism-focused boundaries. Identify secondary
tracks as supporting evidence rather than additional primary research
questions.

## 1.8 Thesis structure

Give the reader a short roadmap of the remaining chapters and explain how
the implementation, experiment, evidence, and guidance chapters connect.

---

# 2. Background and related work

## 2.1 Java threads before Virtual Threads *(Copilot note #4)*

Introduce platform threads, operating-system scheduling, thread pools, and
the thread-per-request model needed to understand the migration context.
(copilot note #4: yes this important, need to also explain what unmounting
[small tangent on how other language have unmounting by default where java
doesn't and why it deliberately doesn't] and serialization is, what is a
carrier thread)

### 2.1.1 Execution-model vocabulary and historical design choices

Define platform threads, Virtual Threads, carrier threads, mounting,
unmounting, blocking, and serialization before using them in the thesis.
Include a bounded comparison with languages or runtimes that expose
continuation-like scheduling more directly, while keeping the main argument
focused on Java's compatibility and thread-per-request design choices.

## 2.2 Java 21 Virtual Threads

Explain the JVM-managed thread model, carrier threads, mounting/unmounting,
blocking behavior, scheduler context, and the intended scalability benefit.

## 2.3 Monitor pinning

Define pinning precisely and distinguish it from ordinary blocking,
application-level queueing, lock contention, and finite-resource waiting.

## 2.4 JDK-version boundary

Explain why Java 21 results must not be silently generalized to Java 24/25,
and how JEP 491 motivates treating later JDKs as a separate boundary track.

## 2.5 Synchronization mechanisms

Introduce intrinsic monitors, `ReentrantLock`, semaphores, fairness,
interruptibility, ownership, reentrancy, and atomic state transitions.
Frame these as semantic contracts as well as performance mechanisms.

## 2.6 Blocking I/O, JDBC, and connection pools

Explain why a blocking database call, a bounded connection pool, and monitor
pinning are separate possible mechanisms requiring separate evidence.

## 2.7 ThreadLocal and request context

Describe the lifecycle, cleanup, context-correctness, and retention questions
that arise when request state is stored in ThreadLocal structures.

## 2.8 JNI/native boundaries

Explain why long native execution is a distinct carrier-occupation question
and why zero `jdk.VirtualThreadPinned` events do not prove that a carrier was
not occupied.

## 2.9 Observability and JFR

Introduce JFR recordings, `jdk.VirtualThreadPinned`, stack attribution,
thresholds, diagnostic versus measurement configurations, and the limits of
event absence.

## 2.10 Performance measurement concepts *(Copilot note #5)*

Define throughput, latency percentiles, errors, timeouts, closed-loop load,
offered versus achieved rate, warm-up, process-level replication, and
experimental unit.
(copilot note #5: what do you think of this claim: One important qualification for your thesis
The conclusion depends on what your benchmark actually measured.

If you have eight carriers and a single lock guarding a one-second operation, that critical section can still admit only one thread at a time. Freeing carriers won't eliminate the lock's throughput limit.

However, if the lock protects a short operation and the rest of the request performs independent work, eliminating pinning could improve overall throughput even though serialization remains within the critical section.
maybe our research mindset is too narrow? we're not measuring correctly? can you think with me?)

### 2.10.1 Causal model: serialization, pinning, and remaining work

Use a simple request decomposition to state what the benchmark can and cannot
measure:

```text
request time = queueing + critical-section time + independent work + response overhead
```

Explain why freeing carriers cannot remove a one-at-a-time critical-section
capacity limit, while still allowing a benefit when the critical section is
short and requests contain independent work. Compare this model with the
actual `/payments` protocol and identify which workload dimensions remain
unmeasured or deliberately controlled.

### 2.10.2 Measurement-design review

Before presenting the primary result, check whether the selected workload,
carrier setting, closed-loop model, critical-section duration, and controls
isolate the intended causal factor. Record what a different workload would
test rather than silently generalizing the current result.

## 2.11 Related empirical studies

Summarize the selected literature by topic and explain what each source
contributes to the thesis argument. Do not turn the bibliography into a list
of unrelated Virtual Thread claims.

## 2.12 Related-work synthesis

Identify the specific design choices inherited from prior work and the
remaining gap that motivates the controlled application study.

---

# 3. Research design and methodology

## 3.1 Research paradigm

Describe the work as an empirical engineering/system study and explain why a
controlled application artifact is appropriate for the research questions.

## 3.2 Research questions and operational constructs

Map each research question to independent variables, dependent variables,
mechanism indicators, correctness invariants, and decision rules.

**Suggested table:** RQ → treatment → control → metric → direct evidence →
interpretation rule → limitation.

## 3.3 Experimental artifact

Describe the purpose of the deliberately realistic Spring Boot MVC system,
including which anti-patterns are intentional controls and which variants
represent refactoring treatments.

## 3.4 System architecture

Document the request path:

```text
HTTP request -> controller -> service treatment -> repository/JDBC -> database
```

Explain the roles of the application layers, configuration, H2, PostgreSQL,
Docker Compose, native library, and benchmark runner.

**Evidence pointers:**

- `src/main/java/com/thesis/virtualthreadsdemo/`
- `pom.xml`
- `application.yml`
- `Dockerfile`
- `docker-compose.yml`

## 3.5 Endpoint and treatment design

Describe `/orders`, `/payments`, `/products`, `/cpu`, `/native`, and
`/native-short`. For each, state its role, workload, intended mechanism, and
what it must not be used to prove.

## 3.6 Primary synchronization matrix *(Copilot note #6)*

Define the platform-thread synchronized control, Virtual Thread synchronized
treatment, Virtual Thread `ReentrantLock` treatment, and no-lock diagnostic
condition. Explain why the no-lock condition is an unsafe upper bound rather
than a recommended implementation. (copilot note #6: tangent on some other
ways other programming paradigms handle synchronization, and why/when java
decided opinianatedly not to go in that direction "not the java way")

### 3.6.1 Synchronization design comparison

Compare Java monitors, explicit locks, semaphores, actors/message passing,
immutability, transactional or database-mediated coordination, and
lock-free/atomic state transitions only where they clarify the thesis
contract. State which alternatives are implemented in this project and which
remain conceptual context. Avoid presenting another paradigm as automatically
superior without matching semantics and evidence.

## 3.7 Secondary experiment families

Introduce the bounded extension tracks:

- endpoint isolation;
- CPU-only control;
- JNI/native boundary;
- H2/PostgreSQL and Hikari sensitivity;
- synchronization semantics;
- Java 21 versus Java 24/25;
- scheduler handoff probe.

State which are primary evidence, supporting evidence, or external-validity
evidence.

## 3.8 Workload protocol *(Copilot note #7)*

Describe k6 scenarios, VU counts, stages, duration, closed-loop behavior
(copilot note #7: should we not test open loop? would it not be more realistic?),
endpoint isolation, request correctness checks, and any differences between
historical and final protocols.

### 3.8.1 Closed-loop and open-loop workload decision

Explain why the existing closed-loop protocol is useful for controlled
mechanism isolation, how slow responses reduce its achieved request rate, and
what an open-loop arrival-rate experiment would add for saturation and
capacity claims. State whether an open-loop run is required for the thesis
questions, a useful extension, or outside the current evidence package.
Do not present an open-loop design as completed unless its raw artifacts exist.

## 3.9 Runtime and environment control

List JDK vendor/build, compiler target, Spring Boot, database, k6, operating
system, hardware, memory, JVM flags, scheduler settings, and relevant
configuration values.

## 3.10 Observability protocol

Describe JFR startup, event extraction, stack classification, telemetry,
manifest generation, raw k6 capture, SHA-256 hashing, normalization, and
validation.

## 3.11 Correctness gates

Define the checks required before interpreting performance:

- HTTP response correctness;
- mutual exclusion;
- ordering where relevant;
- interruption/cancellation behavior;
- ownership and permit semantics;
- resource cleanup;
- error behavior.

## 3.12 Replication and analysis unit

Explain why an independent process run is the experimental unit and how
trial-level results, variation, medians, percentiles, and uncertainty are
handled.

## 3.13 Claim-admission rules

Define the difference between measured, derived, interpretive, conceptual,
behavioral, and unestablished claims. State when a JFR event is sufficient for
a pinning claim and when it is not.

## 3.14 Threats to validity and mitigations

Organize internal, construct, measurement, external, statistical, and
reproducibility threats. Include closed-loop self-throttling, one-carrier
stress, JFR thresholds, synthetic delays, H2/PostgreSQL separation, local
hardware, and historical artifact mapping.

---

# 4. Implementation and research infrastructure

## 4.1 Application implementation

Describe the controllers, services, repositories, configuration, test
fixtures, and intentional anti-pattern locations.

## 4.2 Payment synchronization treatments

Explain the implementation variants and the semantic conditions that must
remain invariant when changing the synchronization primitive.

## 4.3 Request context and ThreadLocal lifecycle

Describe where request context is created, read, and cleaned up, and what the
implementation allows the study to inspect or not establish.

## 4.4 JDBC and database environments

Describe H2 local execution, PostgreSQL Docker execution, schema differences,
connection-pool configuration, and the separation between environments.

## 4.5 Native boundary implementation

Describe the C library, JNI loading, long native treatment, short transition
control, build requirements, and portability limitations.

## 4.6 Benchmark orchestration

Explain `run-benchmark.sh`, command-line controls, startup checks, JFR,
telemetry, k6 output, manifests, cleanup, and exit-status handling.

## 4.7 Test and validation infrastructure

Describe application tests, synchronization tests, native tests, dataset
normalization, evidence validation, Docker configuration checks, and formatting
checks.

## 4.8 Evidence dashboard

Explain the generated normalized dataset and the research dashboard. State
that the dashboard is a presentation and exploration layer, not a replacement
for raw artifacts or provenance.

---

# 5. Experimental results *(Copilot note #8)*

> This chapter should contain tables and observations first. Mechanism
> explanations and broader implications should be kept separate and moved to
> the discussion chapter where appropriate. (copilot note #8: eventually
> graphs would be needed too, wherever appropriate)

## 5.0.1 Planned figures and graph-selection rules *(Copilot note #8)*

List the figures needed to make the results inspectable: trial-level
throughput comparison, latency distributions or percentile plots, pinning
event counts/durations, endpoint-isolation comparison, pool sensitivity, and
selected mechanism diagrams. For every figure, state its source artifacts,
unit of analysis, aggregation rule, uncertainty display, and whether it is
measured, derived, or conceptual. Do not create a graph merely because a
metric exists.

## 5.1 Dataset and run inventory

Report the number of retained trial-level records, run families, valid and
excluded artifacts, runtime identities, and the criteria used to admit a run.

## 5.2 Correctness results

Present HTTP success, response checks, mutual exclusion, synchronization
semantics, cleanup behavior, and any failed or diagnostic conditions before
performance tables.

## 5.3 Java 21 synchronized Virtual Thread baseline

Present trial-level k6 metrics and selected JFR evidence for the legacy
`synchronized` payment treatment. Include raw artifact identifiers and
runtime/configuration identity.

**Primary evidence pointers:**

- `docs/research-iteration-2026-10-15-java21-primary-replication.md`
- `results/run-manifest-20261015-142222.json`
- `results/jfr/recording-20261015-142222.jfr`

## 5.4 Java 21 ReentrantLock comparison *(Copilot note #9)*

Present the matched refactoring condition and compare performance, JFR
events, and correctness without assuming that event removal equals speedup.
(copilot note #9: please include a tangent on when was reentrant lock
introduced, and why)

### 5.4.1 Historical and design context for `ReentrantLock`

Add a short, sourced context section covering the introduction of
`ReentrantLock` in Java, the problem it was designed to address relative to
intrinsic monitors, and the features relevant to this study: fairness,
interruptible acquisition, timed acquisition, ownership, and reentrancy.
Connect the history to the experimental comparison without turning historical
context into evidence that the lock is faster.

## 5.5 Platform-thread control

Present the platform control as a matched execution-model baseline. Explain
what can and cannot be inferred from the absence of Virtual Thread events.

## 5.6 No-lock diagnostic upper bound

Present the no-lock condition only as a diagnostic separation of serialization
from the other mechanisms. State the correctness reason it is excluded from
production recommendations.

## 5.7 Primary matrix summary

Provide a single trial-level and aggregate table for the primary matrix.
Report throughput, p50, p95, p99 where available, errors, and pinning counts.
Keep closed-loop interpretation visible.

## 5.8 Endpoint isolation

Report `/orders`, `/products`, and other isolated endpoint observations.
Explain which results are controls, which are mechanism observations, and
which claims remain unestablished.

## 5.9 CPU-only control

Present the CPU control and explain what it contributes to separating CPU
work from blocking and pinning.

## 5.10 JNI/native boundary

Present pure Java, long JNI, and short JNI conditions. Keep behavioral
carrier-occupation interpretation separate from JFR-confirmed monitor pinning.

## 5.11 Hikari and database sensitivity

Present H2 and PostgreSQL results separately, including pool settings,
correctness, trial spread, and the limits of the closed-loop protocol.

## 5.12 Synchronization semantics

Present fairness, interruption, ownership, semaphore, and atomic observations
as semantic evidence rather than only performance comparisons.

## 5.13 JDK boundary

Present Java 24/25 observations separately from the Java 21 primary results.
State compiler/runtime identity and avoid importing conclusions across JDK
generations.

## 5.14 Scheduler handoff probe

Describe the probe definition, distributions, and why it is mechanism support
rather than an application throughput result or universal context-switch
constant.

## 5.15 Negative and null findings

Collect explicit zero-event, no-effect, unavailable, deferred, and
not-established results. Explain why retaining negative evidence matters.

---

# 6. Analysis and answers to the research questions

## 6.1 Analysis strategy

Explain how observations are converted into qualified interpretations, how
trial-level variation is handled, and how correctness and mechanism evidence
constrain conclusions.

## 6.2 RQ1: synchronization and monitor pinning

Answer RQ1 using the primary matrix. The final section should connect the
intrinsic-monitor stack evidence, serialized critical-section behavior,
`ReentrantLock` comparison, platform control, and workload limitations.

**Required distinction:** monitor pinning versus application serialization.

## 6.3 RQ2: architectural risks before enabling Virtual Threads

Organize the answer by mechanism:

- intrinsic synchronization around blocking work;
- ThreadLocal lifecycle and context correctness;
- JDBC and finite-resource capacity;
- native boundaries;
- synchronization semantics;
- observability and correctness gates.

For each pattern, state whether the study confirmed pinning, identified a
separate risk, found no effect under the tested protocol, or left the claim
unestablished.

## 6.4 What the study did not establish

Explicitly list claims that cannot be made from this evidence: universal
Virtual Thread superiority, universal pool-size guidance, JNI always pinning,
energy benefits, cross-OS effects, production-scale capacity, and universal
lock-replacement rules.

## 6.5 Contribution to Software Architecture

Explain how the work relates to architecture decisions, boundaries, resource
capacity, concurrency contracts, observability, deployment, and migration
risk—not only to Java syntax or benchmark numbers.

---

# 7. Migration guidance

## 7.1 Intended audience and use

Define which engineers and systems the checklist is intended for and which
systems require additional validation.

## 7.2 Pre-migration inventory

Describe the source, runtime, endpoint, synchronization, context, database,
native, and framework inventory to perform before enabling Virtual Threads.

## 7.3 Mechanism-specific audit procedure

Provide a sequence for identifying monitor pinning, serialization,
finite-resource contention, ThreadLocal lifecycle issues, and native
carrier-occupation risks.

## 7.4 Correctness-preserving refactoring

Describe how to compare alternatives by ownership, reentrancy, fairness,
interruption, cancellation, ordering, and resource semantics before measuring
performance.

## 7.5 Measurement and observability checklist

Specify JFR, k6, telemetry, manifests, hashes, endpoint isolation, repeated
process runs, and correctness gates.

## 7.6 Post-migration validation

Describe how to repeat the baseline and compare results without changing
workload, runtime identity, or interpretation rules.

## 7.7 Decision table and decision tree *(Copilot note #10)*

Create a practical table with columns such as: (copilot note #10: maybe even
a decision tree, why not)

```text
Observed pattern | Direct evidence | Risk classification |
Required check | Safe next action | Remaining uncertainty
```

### 7.7.1 Migration decision tree

Design a concise flow from observed symptom to mechanism evidence, semantic
correctness check, intervention, and re-measurement. Include explicit branches
for: confirmed monitor pinning, serialization without pinning, finite-resource
waiting, ThreadLocal lifecycle concern, native carrier occupation, no observed
effect, and insufficient evidence.

## 7.8 Limits of the checklist

State which decisions require production workload data, service-owner
knowledge, database capacity analysis, or supervisor/engineering review.

---

# 8. Discussion

## 8.1 Main findings

Synthesize the primary and secondary results without repeating every result
table. Explain which findings are central and which are supporting.

## 8.2 Relationship to prior work

Compare the observations with JEPs, official documentation, and selected
literature. Explain agreement, disagreement, and differences in workload,
runtime, measurement, and scope.

## 8.3 Architectural interpretation

Discuss why Virtual Thread migration is an architectural audit rather than
only an executor configuration change.

## 8.4 Engineering implications

Discuss practical implications for Spring MVC teams, application owners,
database/resource owners, and observability practices.

## 8.5 Limitations

Group the limitations by application realism, workload model, hardware,
runtime, repetition count, observability thresholds, database environment,
and provenance completeness.

## 8.6 Reproducibility and transferability

Explain what another student can reproduce directly, what requires the same
environment, and what should be repeated before applying the guidance to a
different production system.

## 8.7 Future work

Keep future work bounded and distinguish necessary closure from optional
extensions:

- final provenance freeze;
- thesis-table reconciliation;
- open arrival-rate workloads;
- broader production-like resource experiments;
- energy measurement with suitable privileges;
- cross-OS validation;
- further JDK boundary work;
- reactive comparison only if justified.

---

# 9. Conclusion

## 9.1 Answer summary

Provide concise final answers to RQ1 and RQ2, using only claims established in
the analysis chapter.

## 9.2 Contributions

Restate the software, evidence, methodological, and engineering contributions
in proportion to the study's actual scope.

## 9.3 Practical recommendation

State the migration decision procedure that follows from the evidence:
measure, attribute, preserve semantics, refactor where justified, and
re-measure.

## 9.4 Final limitations statement

End with the most important boundary conditions so the conclusion cannot be
read as a universal Virtual Thread performance claim.

---

# References

## Reference management checklist

- Verify every citation against an authoritative source.
- Use one consistent citation style.
- Separate JDK/JEP, Spring, database, benchmarking, and research-literature
  sources.
- Remove sources that are mentioned only in planning documents but not used in
  the final argument.
- Add exact version/date information where the claim depends on runtime
  behavior.

---

# Appendices

## Appendix A: Repository and artifact map

Map thesis sections to source paths, experiment notes, raw artifacts,
manifests, scripts, hashes, and generated evidence.

## Appendix B: Runtime and environment records

Provide the final runtime, operating-system, hardware, compiler, framework,
database, k6, JVM-flag, and scheduler records.

## Appendix C: Workload definitions

Include or reference the relevant k6 scripts, endpoint scenarios, stages,
thresholds, closed-loop assumptions, and correctness checks.

## Appendix D: Run manifests and hashes

Include the final admitted run table and artifact hashes. Exclude unmapped
artifacts from definitive claims or label them explicitly as retained raw
material.

## Appendix E: JFR extraction and classification

Document commands, event thresholds, selected stack traces, event counts,
classification decisions, and zero-event interpretations.

## Appendix F: Correctness and synchronization tests

List the tests for endpoint behavior, mutual exclusion, fairness,
interruption, ownership, semaphore permits, atomic transitions, and native
loading.

## Appendix G: Additional experiment records

Include secondary-track notes for Hikari, PostgreSQL, JNI, JDK boundaries,
CPU, scheduler, and endpoint isolation.

## Appendix H: AI-use records and declaration

Store the completed declaration, point-of-use disclosures, verification
record, and interaction-log reference according to the applicable ELTE rules.

---

# Open questions to resolve while writing

1. Which exact thesis title and formatting template are officially approved?
2. Which result set will be frozen as the final primary evidence package?
3. Which historical artifacts can be mapped completely to source revisions and
   manifests?
4. Which claims need another experiment versus clearer explanation?
5. Which figures and tables are necessary for the thesis argument?
6. Which supervisor comments or course requirements affect the methodology
   chapter?
7. Which AI-assisted sections require explicit point-of-use disclosure?
8. What is the final deadline and required submission format?
