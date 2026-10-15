# Research Synthesis: How the Project Fits Together

**Project:** Migrating a Spring Boot MVC application to Java 21 Virtual Threads  
**Purpose:** Explain the application, the experimental variants, the evidence
pipeline, the results, and the engineering meaning of the study in one place.

This document is the map of the repository. The iteration notes remain the
authoritative trial-by-trial record; this document explains how those records
fit together and which conclusions are supported by them.

## 1. The central idea

Virtual Threads make blocking request code cheaper to suspend and resume, but
they do not make every blocking operation harmless. The study separates four
different mechanisms that are often conflated:

1. **Monitor pinning:** a Java 21 Virtual Thread remains mounted on its carrier
   while blocked inside an intrinsic monitor (`synchronized`).
2. **Application serialization:** a lock, monitor, or semaphore may correctly
   allow only one request at a time. Replacing the primitive does not remove
   that business bottleneck.
3. **Finite-resource contention:** requests can wait for a database connection
   or another bounded resource without any Virtual Thread pinning.
4. **Carrier occupation at a boundary:** long native/JNI execution can occupy a
   carrier even when `jdk.VirtualThreadPinned` does not report a monitor event.

The project is designed to measure these mechanisms separately instead of
calling every slow Virtual Thread run “pinning.”

## 2. Research questions and scope

### RQ1

**How do legacy synchronization mechanisms in Spring Boot data layers affect
throughput due to thread pinning?**

The primary answer is deliberately narrow: in the tested Java 21 condition,
intrinsic synchronization around a 500 ms blocking operation produced direct
`jdk.VirtualThreadPinned` evidence. Replacing the monitor with
`ReentrantLock` removed those events, but did not remove the serialized
critical-section bottleneck.

### RQ2

**What architectural anti-patterns must be refactored before enabling Virtual
Threads to prevent performance degradation?**

The study evaluates several patterns, but they are not equivalent:

| Pattern | What must be audited | What this study established |
|---|---|---|
| `synchronized` around blocking work | Monitor pinning and critical-section scope | Confirmed Java 21 monitor-pinning treatment |
| `ThreadLocal` request context | Cleanup, lifecycle, context correctness, memory retention | Cleanup was present; no pinning claim was made |
| JDBC/database access | Connection-pool capacity and queueing | No pool-size effect was exposed in the tested synthetic H2/PostgreSQL workloads |
| Long JNI/native call | Carrier occupation and native residency | Behavioral carrier-occupation evidence; zero JFR pinning events |
| Fairness/interruptibility/ownership | Whether a replacement preserves semantics | These are contract properties, not simple performance substitutions |

## 3. Application architecture

The repository is a Spring Boot MVC application with deliberately controlled
workload paths:

```text
HTTP request
    |
    v
Controller
    |
    v
Service treatment  <--- lock mode, ThreadLocal, native boundary, delay
    |
    v
Repository/JDBC ---> H2 locally or PostgreSQL in Docker
```

### Endpoint roles

| Endpoint | Role | Treatment |
|---|---|---|
| `GET /orders` | Slow data-path workload | JDBC-shaped access, approximately 300 ms blocking delay, cleaned-up request `ThreadLocal` |
| `POST /payments` | Primary synchronization treatment | Approximately 500 ms operation protected by `synchronized`, `ReentrantLock`, semaphore, or diagnostic no-lock mode |
| `GET /products` | Clean control | Fast database-backed endpoint without the intentional payment synchronization treatment |
| `GET /cpu` | CPU control | CPU-only work without blocking or pinning treatment |
| `GET /native` | Native-boundary treatment | JNI call containing approximately 500 ms native `nanosleep` |
| `GET /native-short` | Native transition control | Short JNI/no-op call used to separate transition cost from long native residency |

### Execution modes

- **Virtual Threads:** enabled with `spring.threads.virtual.enabled=true`.
- **Platform threads:** Virtual Threads disabled for the baseline control.
- **Constrained scheduler:** selected experiments used
  `-Djdk.virtualThreadScheduler.parallelism=1` and
  `-Djdk.virtualThreadScheduler.maxPoolSize=1` to amplify mechanism differences.
  This is a stress condition, not a production recommendation.

## 4. The evidence model

Every experiment should be understood as a chain:

```text
source/configuration
        |
        v
frozen artifact + runtime identity
        |
        v
orchestrated process run
        |
        +--> k6 raw request records
        +--> JFR recording and event extraction
        +--> process/thread/CPU telemetry
        +--> run manifest and hashes
        |
        v
trial-level normalization
        |
        v
validation + written interpretation
        |
        v
dashboard and thesis-ready claim
```

The canonical dashboard dataset is generated, never manually typed:

```bash
python3 scripts/normalize_evidence.py
python3 scripts/validate_normalized_evidence.py
```

The evidence classes are:

- **Measured:** read directly from k6, JFR, telemetry, or manifests.
- **Derived:** calculated from measured values, such as percentiles or ranges.
- **Interpretive:** a mechanism explanation consistent with the measurements.
- **Conceptual:** background material or a model, not an observation.
- **Unestablished:** a plausible claim for which this study lacks sufficient
  direct evidence.

The provenance requirements and admission rules are documented in
`docs/artifact-provenance-ledger.md`.

## 5. Experiment families and how they connect

### A. Java 21 synchronization matrix — primary evidence

This is the central RQ1 experiment. It isolates `/payments`, uses 10
closed-loop k6 VUs, a 500 ms operation, and one Virtual Thread carrier.
Each condition was repeated three times.

| Condition | Mean requests | Mean p50 | Mean p95 | Pinning evidence |
|---|---:|---:|---:|---:|
| Virtual Threads + `synchronized` | 110.0 | 3,923.86 ms | 7,957.50 ms | 110 events/run |
| Virtual Threads + `ReentrantLock` | 108.7 | 4,941.99 ms | 4,967.54 ms | 0 events/run |
| Virtual Threads + no-lock diagnostic | 710.7 | 507.66 ms | 512.84 ms | 0 events/run |
| Platform threads + `synchronized` | 110.0 | 3,936.42 ms | 9,002.48 ms | Not applicable |

All runs had zero HTTP failures.

**What it means:** Java 21 monitor pinning is directly distinguished from
ordinary queueing. `ReentrantLock` removes the observed monitor-pinning events,
but the 500 ms serialized operation still limits throughput. The no-lock run
is an unsafe diagnostic upper bound because it removes the mutual-exclusion
invariant.

Detailed records:

- `docs/java21-synchronization-matrix-results-2026-10-08.md`
- `docs/research-iteration-2026-10-15-java21-primary-replication.md`
- `docs/research-iteration-2026-10-15-java21-primary-matrix.md`

### B. Synchronization semantics

The lock replacement was tested for more than speed:

- fair `ReentrantLock` produced perfect FIFO ordering in the controlled probe;
- non-fair locking allowed barging in the adversarial probe;
- `lockInterruptibly()` prevented cancelled waiters from entering;
- timed `tryLock()` allowed acquisition timeout;
- wrong-thread `ReentrantLock.unlock()` failed with
  `IllegalMonitorStateException`;
- wrong-thread semaphore release was accepted;
- atomic CAS completed a bounded reservation state machine, but is not a
  replacement for a blocking payment critical section.

**What it means:** a migration must preserve the synchronization contract.
`ReentrantLock`, `Semaphore`, and atomics are not interchangeable merely
because they can all limit concurrency.

Detailed records:

- `docs/research-iteration-2026-10-15-locks-semaphores-atomics.md`
- `docs/research-iteration-2026-10-15-adversarial-fairness.md`

### C. Endpoint isolation

The `/orders` and `/products` experiments test whether ordinary blocking,
JDBC-shaped work, or `ThreadLocal` usage should automatically be labelled
pinning.

- `/orders` used approximately 300 ms blocking work and cleaned its
  `ThreadLocal` in `finally`; Virtual Thread and platform-thread behavior was
  similar, with zero Virtual Thread pinning events.
- `/products` was a fast clean control, typically approximately 2–3 ms, with
  no meaningful execution-mode difference and zero pinning events.

**What it means:** slow blocking work is not proof of monitor pinning. The
mechanism must be established separately.

Detailed record: `docs/research-iteration-2026-10-15-endpoint-isolation.md`.

### D. CPU control

The `/cpu` control used three repetitions for Virtual Threads and platform
threads. In this local protocol:

- Virtual Threads: mean approximately 9.85–10.01 ms; p95 approximately
  13.78–14.21 ms.
- Platform threads: mean approximately 14.20–14.51 ms; p95 approximately
  20.49–20.69 ms.
- All runs produced zero pinning events.

**What it means:** this is a local control observation, not a universal claim
that Virtual Threads improve CPU-bound work. CPU scheduling, executor
configuration, and hardware must be matched before generalizing.

Detailed record: `docs/research-iteration-2026-10-15-cpu-control.md`.

### E. Native/JNI boundary

The native experiment separates three cases:

1. pure Java `Thread.sleep(500 ms)`;
2. blocking JNI/native `nanosleep(500 ms)`;
3. short JNI/no-op transition.

With one carrier and 10 VUs, repeated Java 21, 24, and 25 runs showed:

- pure Java sleep: approximately 713–714 requests;
- blocking JNI: approximately 108–109 requests, with roughly 4.95 s median
  latency;
- short JNI: approximately 4,185–4,212 requests, with approximately 1 ms
  median latency.

All 27 repeated recordings reported zero `jdk.VirtualThreadPinned` events.

**What it means:** long native residency behaved consistently with carrier
occupation, while JNI transition overhead alone was small. Because JFR did not
report monitor-pinning events, this must be described as behavioral evidence
consistent with carrier capture, not JFR-confirmed monitor pinning.

Detailed record: `docs/native-jni-boundary-results-2026-10-08.md`.

### F. JDK boundary

The same Java-21-targeted artifact was run on Java 21, 24, and 25. Java 24/25
are boundary evidence, not replacements for the Java 21 primary study.

- Java 21 reported monitor-pinning events for the synchronized treatment.
- Java 24/25 tested cases reported zero such events.
- The application-level serialized bottleneck remained on newer runtimes.

**What it means:** runtime generation is a causal variable. A Java 21
monitor-pinning result must not be silently generalized to Java 24 or 25.

Detailed record: `docs/research-iteration-2026-10-15-jdk24-fairness.md`.

### G. Hikari and database sensitivity

The `/orders` workload was run with 50 closed-loop VUs and pool sizes 1 and
10, first against H2 and then against Dockerized PostgreSQL.

| Database | Pool | Requests/run | Mean latency range | Pinning |
|---|---:|---:|---:|---:|
| H2 | 1 | 5,242–5,287 | 304.2–306.3 ms | 0 |
| H2 | 10 | 5,258–5,284 | 304.7–305.5 ms | 0 |
| PostgreSQL | 1 | 5,187–5,233 | 308.4–312.0 ms | Not recorded in this run |
| PostgreSQL | 10 | 5,181–5,226 | 308.6–312.3 ms | Not recorded in this run |

All PostgreSQL runs passed correctness checks with zero HTTP failures.

**What it means:** no material pool-size effect was exposed under this
synthetic, closed-loop, CPU-limited protocol. This is negative evidence for
this setup, not proof that pool size is irrelevant in production.

Detailed record: `docs/research-iteration-2026-10-15-hikari-scheduler.md`.

### H. Scheduler handoff probe

`scripts/SchedulerHandoffProbe.java` measures repeated two-thread
`LockSupport.park`/`unpark` handoffs after warm-up:

- platform threads: approximately 4.3–8.6 microseconds;
- Virtual Threads: approximately 0.4–1.5 microseconds.

This is a mechanism microbenchmark, not an isolated operating-system context
switch measurement and not a direct application-throughput prediction.

## 6. What the results say together

The experiments form a causal progression:

```text
Virtual Threads can unmount during ordinary Java blocking
        |
        +--> /orders and pure Java sleep remain serviceable
        |
        +--> but intrinsic monitor + blocking work pins in Java 21
        |        |
        |        +--> ReentrantLock removes monitor-pinning evidence
        |                 but not serialized business capacity
        |
        +--> long native residency remains a separate boundary risk
        |
        +--> database pools and ThreadLocal require lifecycle/capacity audits,
             not automatic “pinning” labels
```

The most important practical conclusion is therefore not “enable Virtual
Threads” or “replace every synchronized block.” It is:

> Enable Virtual Threads only after identifying which operations are ordinary
> unmountable blocking, which are protected by intrinsic monitors, which are
> limited by finite resources, and which cross boundaries that require
> separate treatment.

## 7. Migration procedure derived from the evidence

1. **Freeze a baseline.** Record source revision, JDK, Spring Boot, workload,
   scheduler settings, hardware, OS, and artifact hashes.
2. **Enable Virtual Threads without refactoring.** This preserves the causal
   comparison with the legacy application.
3. **Observe mechanism evidence.** Use JFR `jdk.VirtualThreadPinned` and stack
   attribution; do not infer pinning from latency alone.
4. **Audit critical-section scope.** If a monitor surrounds blocking work,
   determine whether the lock protects state or accidentally protects the
   external call itself.
5. **Choose a semantic replacement.** Preserve ownership, reentrancy,
   fairness, interruption, timeout, and mutual-exclusion requirements.
6. **Audit request context.** Ensure every manually managed `ThreadLocal` has
   bounded scope and guaranteed cleanup; consider request scope or framework
   context facilities where appropriate.
7. **Audit finite resources.** Measure Hikari acquisition, active/pending
   connections, timeouts, database capacity, and query latency before tuning.
8. **Audit native and external boundaries.** Test long native calls separately
   and isolate them when their carrier behavior cannot be bounded.
9. **Repeat correctness gates.** Confirm response correctness, mutual
   exclusion, ordering, cancellation, ownership, and error behavior.
10. **Repeat the benchmark.** Compare trial-level distributions, not only
    averages, and retain invalid runs with their exclusion reason.

The operational checklist is in `docs/migration-guidelines.md`; this document
provides the evidence behind it.

## 8. What is not established

This repository does not establish:

- that Virtual Threads are always faster;
- that `ReentrantLock` is faster than `synchronized`;
- that every JNI/native call pins a carrier;
- that Java 25 universally fixes native blocking;
- that Hikari pool size is irrelevant;
- that lower CPU usage implies lower energy use;
- that the local macOS results generalize to Windows or Linux;
- that a one-carrier stress condition represents production deployment;
- that a scheduler handoff microbenchmark is a universal context-switch cost.

Energy measurement was deferred because `powermetrics` required privileged
access that was unavailable. Cross-OS comparison was deferred because no
second reproducible operating-system environment was available.

## 9. Repository reading order

For a new researcher or thesis reader:

1. `README.md` — project entry point and commands.
2. `docs/detailed-research-plan.md` — formal research design.
3. `docs/research-synthesis.md` — this map of the complete study.
4. `docs/artifact-provenance-ledger.md` — evidence identity and claim rules.
5. `docs/research-iteration-*.md` — iteration-level records.
6. `docs/research-dashboard.md` — generated evidence explorer.
7. `docs/migration-guidelines.md` — engineering procedure derived from results.
8. `scripts/normalize_evidence.py` and
   `scripts/validate_normalized_evidence.py` — reproducibility pipeline.

## 10. Glossary

| Term | Meaning in this project |
|---|---|
| Carrier thread | Platform thread that temporarily runs a Virtual Thread |
| Mount/unmount | Scheduling a Virtual Thread onto or off a carrier |
| Pinning | A Virtual Thread remains mounted while blocked, especially in the tested Java 21 intrinsic-monitor case |
| Serialization | Correctly limiting access so only one operation proceeds at a time |
| Closed-loop load | Each k6 VU starts its next iteration after its previous request completes |
| JFR | Java Flight Recorder, used here for runtime event and stack evidence |
| Hikari pool | Bounded JDBC connection pool used by the application |
| JNI boundary | Java-to-native transition used by the native blocking experiment |
| Mechanism evidence | Direct observation tied to a runtime mechanism, such as a JFR event |
| Diagnostic upper bound | A deliberately unsafe control that shows capacity after removing a constraint |

