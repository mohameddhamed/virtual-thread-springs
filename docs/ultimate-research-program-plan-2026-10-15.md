# Ultimate Research Programme Plan

**Project:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads
**Repository:** `mohameddhamed/virtual-thread-springs`
**Plan date:** 2026-10-15
**Status:** Research design and execution plan; not a claim that every listed
track will be completed

## 1. Purpose

This document converts the accumulated research notes into a disciplined final
research programme. It expands the existing Java 21 synchronization study
without replacing its approved core or pretending that every interesting idea
is equally necessary.

The programme has one central rule:

> Complete and defend the mechanism-focused Java 21 study first. Add a
> secondary experiment only when it has a clear hypothesis, a valid control,
> an observable outcome, a feasible measurement method, and a defined stopping
> rule.

The final thesis may therefore contain a strong primary study plus a smaller
number of well-supported extensions. A track that fails its feasibility or
validity gate is a useful scoping result and will be documented as deferred,
not forced into the results chapter.

## 2. Research architecture

### 2.1 Primary research questions

The existing questions remain the thesis anchor:

**RQ1.** How does intrinsic synchronization around blocking work affect
throughput, latency, error rate, and Virtual Thread pinning in a Spring Boot
MVC application compared with platform threads and a Virtual-Thread-compatible
lock?

**RQ2.** Which architectural risks in the demonstration application must be
addressed before enabling Java 21 Virtual Threads, and how can pinning,
request-context/resource-lifecycle risk, and finite-resource contention be
distinguished experimentally?

### 2.2 Secondary questions under consideration

These are not automatically promoted to new thesis research questions:

| ID | Candidate question | Role |
|---|---|---|
| SQ1 | How do fair/non-fair locks, interruptible acquisition, and binary semaphores differ when they provide the same bounded mutual-exclusion contract? | Synchronization semantics extension |
| SQ2 | When is an atomic state transition a valid alternative to a lock, and what performance/correctness trade-off does it create? | Purpose-built lock-free control |
| SQ3 | How does a blocking native boundary behave across Java 21, 24, and 25 when the artifact and workload are held constant? | Existing bounded external-validity study |
| SQ4 | How do hardware/OS differences affect the observed mechanism and the portability of conclusions? | External-validity study |
| SQ5 | Can energy per successful request be measured reproducibly enough to compare treatments? | Feasibility-gated sustainability study |
| SQ6 | What part of observed cost is attributable to scheduling, lock handoff, or context switching rather than application serialization? | Mechanism microbenchmark |

SQ1-SQ6 support the primary questions; they do not justify broad claims about
all Java applications, operating systems, or synchronization primitives.

## 3. Evidence hierarchy

Every claim in the final research package must be classified:

1. **Measured:** directly extracted from a retained run artifact.
2. **Derived:** calculated from measured values using a documented formula.
3. **Mechanism-supported:** an interpretation supported by code, JFR,
   telemetry, or an authoritative specification.
4. **Conceptual:** an explanation or diagram, not a benchmark result.
5. **Hypothetical:** a proposed future experiment or expected outcome.

The following distinctions are mandatory:

- Java 21 `jdk.VirtualThreadPinned` evidence is monitor-pinning evidence.
- A slow native call with zero pinning events is behavioral evidence consistent
  with carrier occupation, not JFR-confirmed monitor pinning.
- Serialization around a 500 ms operation is distinct from the lock primitive.
- ThreadLocal lifecycle and JDBC pool saturation are not pinning without direct
  mechanism evidence.
- Lower CPU utilization is not an energy measurement.
- A context-switch estimate is not an application-level throughput result.

## 4. Research tracks and priority

### Tier 0 — non-negotiable primary study

These studies must be complete and reproducible before optional expansion:

1. Java 21 platform-thread baseline.
2. Java 21 Virtual Threads with intentional `synchronized` blocking treatment.
3. Java 21 Virtual Threads with non-fair `ReentrantLock`.
4. No-lock diagnostic upper bound, clearly labelled non-production.
5. JFR stack attribution and correctness/mutual-exclusion checks.
6. Isolated endpoint measurements for payments, orders, products, and controls.
7. Final evidence normalization, manifests, hashes, and limitations.

### Tier 1 — high-value bounded extensions

Run only after Tier 0 is frozen:

1. Fair versus non-fair `ReentrantLock`, if fairness is relevant to the
   application contract.
2. `lock()` versus `lockInterruptibly()` or timed `tryLock`, only with an
   explicit cancellation/timeout scenario.
3. Binary semaphore, only as a semantic comparison with the same one-permit
   mutual-exclusion contract.
4. Java 21-targeted artifact on Java 21, 24, and 25, with JDK behavior
   described as a boundary condition rather than a replacement for the
   primary result.
5. A purpose-built atomic state-transition control, not an indiscriminate
   replacement for the payment critical section.

### Tier 2 — external validity and feasibility studies

These may strengthen the discussion but must not destabilize the core:

1. Replication on another OS or machine.
2. Cross-OS comparison across Windows, macOS, and Linux.
3. Energy/power measurement.
4. Context-switch or scheduler microbenchmark.
5. PostgreSQL/Hikari sensitivity study.

If resources or instrumentation are insufficient, Tier 2 becomes a documented
limitation and future-work section.

## 5. Controlled experiment protocol

### 5.1 Common constants

Every retained comparison must record:

- Git revision and application JAR SHA-256;
- JDK vendor, full version, compiler JDK, and bytecode target;
- Spring Boot, Maven, k6, and native compiler versions;
- OS release, CPU model, core/SMT configuration, memory, and power mode;
- Virtual Thread scheduler parallelism and maximum pool size;
- endpoint, workload model, load level, warm-up, measurement window, and
  repetition number;
- application configuration, database type, connection-pool size, and data
  state;
- JFR settings, pinning threshold, extraction command, and recording hash;
- k6 summary, telemetry, logs, and all validity notes.

### 5.2 Repetition and analysis

Use process-level repetitions, not individual requests, as the experimental
replicates. Use at least three for an exploratory condition and increase the
count for a central claim when variability makes the conclusion unstable.
Report every trial, the median, spread, and an uncertainty interval suitable
for the retained sample.

The primary metrics are:

- successful requests per second;
- p50, p95, and p99 latency;
- HTTP error rate and dropped iterations;
- `jdk.VirtualThreadPinned` count and duration;
- lock acquisition/service latency where instrumented;
- CPU and process-thread context as supporting telemetry;
- resource-pool active/pending/acquisition measures where applicable.

### 5.3 Correctness gates

A performance comparison is invalid unless all treatments preserve the
specified application contract:

- response schema and status code;
- payment mutual exclusion;
- no lost or duplicated state transitions;
- interruption, timeout, and cancellation behavior where tested;
- resource release on success, failure, and cancellation;
- request-context isolation and cleanup.

The no-lock condition is a diagnostic upper bound and must not be described as
a safe production implementation if it violates these invariants.

## 6. Primary study execution plan

### Phase P0 — Freeze and audit

**Objective:** establish a trustworthy starting point.

Tasks:

- freeze the current application and benchmark scripts at a named commit;
- reconcile historical result documents with raw manifests and recordings;
- mark untraceable values as exploratory or remove them from headline tables;
- validate endpoint smoke, mutual exclusion, native controls, and evidence
  normalization;
- record the exact Java 21 runtime used for the primary study.

**Exit gate:** every retained headline result has a source artifact, commit,
configuration, and validity status.

### Phase P1 — Isolated mechanism matrix

**Objective:** remove mixed-endpoint ambiguity.

Treatments:

- platform threads plus synchronized;
- Virtual Threads plus synchronized;
- Virtual Threads plus non-fair `ReentrantLock`;
- no-lock diagnostic control.

Workloads:

- payments under blocking contention;
- orders under JDBC/blocking-resource conditions;
- products as a clean control;
- CPU-only control where relevant.

**Exit gate:** the synchronized Java 21 condition has JFR attribution, the
lock variant has correctness evidence, and endpoint-specific results are
available separately from mixed-workload results.

### Phase P2 — Mechanism interpretation

**Objective:** distinguish causes that can produce similar throughput curves.

For each treatment, correlate:

- JFR pinning stacks;
- lock acquisition and service time;
- achieved versus offered load;
- Hikari/database metrics;
- process CPU, thread count, and garbage collection;
- endpoint-specific error and timeout behavior.

**Exit gate:** each conclusion is labelled pinning, serialization, resource
contention, context/lifecycle risk, or not established.

### Phase P3 — Primary synthesis

**Objective:** answer RQ1 and RQ2 before adding optional tracks.

Deliverables:

- final Java 21 comparison tables;
- finding records with evidence paths and hashes;
- migration checklist mapped to findings;
- threats-to-validity section;
- reproducibility instructions that work from a clean checkout.

**Decision:** freeze the primary thesis result. Later studies are extensions
and cannot silently rewrite the primary result.

## 7. Synchronization semantics extension

### 7.1 Fairness

**Hypothesis:** fair acquisition may reduce starvation and tail-latency
variance while reducing throughput relative to a non-fair lock.

**Treatments:**

- `ReentrantLock(false)`;
- `ReentrantLock(true)`.

**Controls:** identical critical section, workload, carrier settings, runtime,
and correctness checks.

**Metrics:** throughput, p95/p99 acquisition and request latency, wait-time
distribution, starvation indicators, CPU, and error/cancellation behavior.

**Stop rule:** do not continue if fairness has no application-level meaning
for the selected workload or if acquisition order cannot be measured
reliably. Fairness findings apply to the tested lock and load, not to general
thread scheduling.

### 7.2 Interruptibility and timed acquisition

`lockInterruptibly()` is not an equivalent faster version of `lock()`. It
changes the cancellation contract. Study it only with a workload that
deliberately interrupts or times out waiting requests.

Record:

- interruption source and timing;
- whether the request returns, retries, or fails;
- lock/resource cleanup;
- completed work and error rate;
- wait-time and tail-latency effects.

**Stop rule:** if no realistic cancellation path exists in the application,
document the semantic distinction and defer the benchmark.

### 7.3 Binary semaphore

A one-permit semaphore can implement mutual exclusion, but it has no owner
and is not reentrant. Therefore it is a valid comparison only if the
application does not require ownership, reentrancy, or same-thread unlock
validation.

Required tests:

- same-thread re-entry;
- wrong-thread release;
- exception cleanup;
- interruption;
- mutual exclusion under contention.

**Stop rule:** if the payment contract requires lock ownership or reentrancy,
do not present a semaphore as a drop-in refactoring. It may remain a semantic
counterexample.

### 7.4 Atomic and compare-and-set controls

Atomics should be studied through a purpose-built state machine, such as an
inventory reservation or idempotency counter, where the invariant can be
represented as a finite atomic transition. `AtomicInteger.updateAndGet`,
`compareAndSet`, `getAndSet`, `AtomicReference`, or `VarHandle` operations
must use side-effect-free retry functions and explicit retry limits.

Do not replace the payment critical section with an atomic integer merely to
obtain a faster number. A multi-step external call cannot be made safe by an
atomic update unless the state model and compensation protocol are redesigned.

Metrics:

- successful transitions;
- CAS retry count and failure rate;
- correctness violations;
- throughput and tail latency;
- CPU and allocation;
- behavior under contention and backoff.

**Stop rule:** defer if the proposed atomic treatment cannot express the same
invariant and failure semantics as the lock-based treatment.

## 8. JDK compilation/runtime boundary

The programme will distinguish four identities:

1. compiler JDK;
2. bytecode target;
3. runtime JDK;
4. JVM options and scheduler settings.

Minimum boundary matrix:

- Java 21-targeted artifact on Java 21;
- the same artifact on Java 24;
- the same artifact on Java 25;
- optionally, an artifact compiled on a newer JDK with an explicitly recorded
  target, if this answers a concrete compatibility question.

The study must verify from authoritative JDK sources whether a supported
runtime option restores pre-JDK-24 monitor behavior. No such compatibility
mode may be assumed. If no supported switch exists, report the limitation and
keep Java 21 as the primary monitor-pinning runtime.

**Interpretation rule:** JDK 24/25 results are boundary evidence about runtime
behavior, not a substitute for the Java 21 answer. A bytecode-compatible
application does not imply behaviorally identical synchronization semantics.

## 9. Operating-system and hardware study

### 9.1 Feasibility gate

Before cross-OS benchmarking, confirm access to:

- one reproducible Windows environment;
- one reproducible macOS environment;
- one reproducible Linux environment;
- the same or explicitly documented hardware class;
- the same JDK vendor/build where available;
- k6, JFR, native compiler, and telemetry support on each system.

One machine per OS supports an external-validity case comparison, not a
universal OS claim.

### 9.2 Protocol

Use the same application artifact and workload definition. Record OS version,
kernel/build, CPU, SMT, memory, thermal/power mode, background load, JDK,
native compiler, and measurement limitations.

Analyze:

- whether the direction of the Java 21 synchronization effect replicates;
- whether JFR availability and event extraction are equivalent;
- whether native/JNI behavior changes;
- whether throughput or latency differences are attributable to the OS or
  hardware confounders.

**Stop rule:** if instrumentation or hardware differs enough to prevent a
defensible comparison, report the protocol as infeasible and do not pool the
numbers.

## 10. Energy and physical-resource study

### 10.1 Research question

Can energy per successful request be measured reproducibly for the selected
Virtual Thread treatments, and does it add information beyond latency and
CPU telemetry?

### 10.2 Measurement hierarchy

Prefer, in order:

1. direct platform energy counters with documented units and sampling;
2. external power measurement with synchronized workload timing;
3. OS/tool power estimates clearly labelled as proxies;
4. CPU percentage only as supporting context, never as energy.

Record total energy, measurement interval, successful requests, error rate,
warm-up, background load, power mode, thermal state, and uncertainty. Report
energy per successful request and total energy for a fixed workload.

Do not compare macOS, Windows, and Linux energy values directly unless the
measurement instruments and definitions are demonstrably comparable. Energy
is a Tier 2 study and cannot delay the primary thesis result.

**Go/no-go rule:** if a named tool cannot provide a stable, documented
measurement with repeated runs, defer the energy claim and retain only a
future-work protocol.

## 11. Context-switch and scheduler-cost study

The “50 microseconds” note is not accepted as a constant. It is a hypothesis
to verify, and its value may vary with CPU, OS, cache state, scheduler, and
measurement method.

If pursued, separate:

- OS platform-thread context switches;
- Virtual Thread mount/unmount and park/unpark;
- lock handoff;
- scheduler queueing;
- application request latency.

Use JMH or a documented process-level microbenchmark with warm-up,
distributions, and a no-op/control condition. Do not convert a microbenchmark
value directly into a production throughput prediction.

**Stop rule:** if the benchmark cannot identify the event being measured or
the result is dominated by timer resolution and setup overhead, document the
limitation and omit numerical claims.

## 12. Planned artefacts

The final programme should produce:

1. this research programme and a change log;
2. a frozen primary protocol;
3. run manifests and artifact hashes;
4. normalized evidence data;
5. finding records for each supported mechanism;
6. Java 21 primary result tables;
7. selected synchronization-semantic extension results;
8. JDK-boundary results;
9. optional OS/energy/scheduler reports only if their gates pass;
10. migration guidance mapped to evidence;
11. reproducibility instructions and limitations;
12. thesis-ready methodology, results, and discussion material.

## 13. Decision log template

Every new proposed experiment must be logged with:

| Field | Required content |
|---|---|
| Proposal | One-sentence experiment description |
| Hypothesis | Falsifiable expected relationship |
| Research role | RQ1, RQ2, secondary question, or future work |
| Treatment/control | Exact variants and invariant workload |
| Primary metric | One metric that can disconfirm the hypothesis |
| Correctness gate | What must remain equivalent |
| Feasibility | Runtime, OS, instrumentation, and data requirements |
| Stop rule | Condition for deferring or ending the study |
| Outcome | Completed, deferred, infeasible, or not established |

## 14. Final scope decision

The recommended final thesis scope is:

- Tier 0 in full;
- Tier 1 synchronization semantics selectively, only where the application
  contract makes the comparison meaningful;
- the existing JDK 21/24/25 native boundary study as bounded external-validity
  evidence;
- Tier 2 OS, energy, and scheduler work only when its feasibility gate passes.

The thesis should prefer a smaller, reproducible and causally interpretable
result set over a large collection of incomparable benchmark numbers. The
ultimate research outcome is therefore not “test everything,” but a defensible
answer to the primary questions plus clearly classified evidence about which
additional questions can and cannot be answered with this infrastructure.
