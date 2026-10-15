# Research Achievements Presentation

**Title:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads
**Subtitle:** Ready Software, Measurements, Methodology, and Research Answers
**Presenter:** Mohamed Hamed
**Purpose:** Checkpoint 4 research-achievements presentation

> Use the current validated values below. Earlier pilot figures such as
> “63% throughput loss,” “96% recovery,” and “485 pinning events” are
> superseded because their raw-artifact mapping was incomplete.

## Slide 1 — What was delivered

- A runnable Spring Boot MVC research application.
- Intentional synchronization, request-context, JDBC, and JNI/native
  treatments.
- k6 load workloads and process-level benchmark orchestration.
- JFR pinning capture and evidence normalization/validation.
- H2 and Dockerized PostgreSQL deployment paths.
- Repeated measurements, correctness tests, and migration guidance.

## Slide 2 — Research questions

**RQ1:** How does intrinsic synchronization around blocking work affect
throughput, latency, errors, and Virtual Thread pinning compared with platform
threads and a Virtual-Thread-compatible lock?

**RQ2:** How do synchronization, request-context handling, and JDBC
connection capacity affect pinning, context correctness, and finite-resource
contention?

The practical output is a migration procedure, not a separate unsupported
claim that Virtual Threads are universally faster.

## Slide 3 — Ready-to-use software

| Surface | Delivered behavior | Research role |
|---|---|---|
| `GET /orders` | JDBC-shaped work, approximately 300 ms delay, cleaned-up `ThreadLocal` | Blocking/resource/context control |
| `POST /payments` | Approximately 500 ms operation with selectable lock treatment | Primary synchronization treatment |
| `GET /products` | Fast clean endpoint | Control group |
| `GET /cpu` | CPU-only work | CPU control |
| `GET /native` | Long JNI/native sleep | Native-boundary treatment |
| `GET /native-short` | Short JNI transition | Native transition control |

The application can run locally with Maven and as a Docker Compose stack with
PostgreSQL and pgAdmin.

## Slide 4 — Final methodology

- Empirical engineering/system study on one controlled Spring Boot artifact.
- Java 21.0.8 Zulu for the primary study.
- macOS Apple Silicon host with 8 logical CPUs.
- k6 process-level workloads with closed-loop VUs.
- JFR `jdk.VirtualThreadPinned` event extraction for Virtual Thread runs.
- Correctness gates before interpreting performance:
  response validity, mutual exclusion, ordering, interruption, and ownership.
- Trial-level reporting; requests inside a run are not treated as independent
  experimental repetitions.
- Mechanism separation:
  monitor pinning, serialization, finite-resource contention, and native
  carrier occupation are analysed independently.

## Slide 5 — Primary Java 21 synchronization result

Protocol: isolated `POST /payments`, 10 closed-loop VUs, 500 ms operation,
one Virtual Thread carrier, three process repetitions per condition.

| Condition | Mean requests | Mean p50 | Mean p95 | JFR result |
|---|---:|---:|---:|---:|
| Virtual Threads + `synchronized` | 110.0 | 3,923.86 ms | 7,957.50 ms | 110 events/run |
| Virtual Threads + `ReentrantLock` | 108.7 | 4,941.99 ms | 4,967.54 ms | 0 events/run |
| Virtual Threads + no-lock diagnostic | 710.7 | 507.66 ms | 512.84 ms | 0 events/run |
| Platform threads + `synchronized` | 110.0 | 3,936.42 ms | 9,002.48 ms | Not applicable |

All 12 runs completed with zero HTTP failures.

## Slide 6 — What the primary result means

- Java 21 intrinsic synchronization around the blocking operation produced
  direct `jdk.VirtualThreadPinned` evidence.
- `ReentrantLock` removed the observed monitor-pinning events.
- The lock replacement did **not** increase payment capacity because the
  500 ms operation remained serialized.
- The no-lock result is an unsafe diagnostic upper bound, not a proposed
  payment implementation.

**Main lesson:** removing monitor pinning and removing application
serialization are different engineering changes.

## Slide 7 — Supporting measurements

### Endpoint isolation

- `/orders`: Virtual Threads and platform threads behaved similarly; zero
  Virtual Thread pinning events.
- `/products`: approximately 2–3 ms median latency; zero pinning events.
- Ordinary blocking or `ThreadLocal` presence was not treated as pinning
  without mechanism evidence.

### CPU control

- Virtual Threads: mean approximately 9.85–10.01 ms; p95 approximately
  13.78–14.21 ms.
- Platform threads: mean approximately 14.20–14.51 ms; p95 approximately
  20.49–20.69 ms.
- Zero pinning events in all runs.

These are local control observations, not universal performance claims.

## Slide 8 — Native, JDK, and database boundaries

### JNI/native boundary

With one carrier and repeated Java 21/24/25 runs:

- pure Java sleep: approximately 713–714 requests;
- long JNI: approximately 108–109 requests, roughly 4.95 s median latency;
- short JNI: approximately 4,185–4,212 requests, approximately 1 ms median.

All 27 recordings reported zero `jdk.VirtualThreadPinned` events. The result
is behavioral evidence consistent with carrier occupation, not
JFR-confirmed monitor pinning.

### Database sensitivity

H2 and PostgreSQL pool sizes 1 versus 10 produced nearly identical results in
the tested 50-VU, closed-loop, synthetic `/orders` workload. No pool-size
bottleneck was established.

## Slide 9 — Synchronization semantics

The study tested correctness and contract properties, not only latency:

- fair `ReentrantLock`: perfect FIFO ordering in the controlled probe;
- non-fair lock: barging observed in the adversarial probe;
- `lockInterruptibly()` and timed `tryLock()` changed cancellation behavior;
- wrong-thread lock release failed;
- wrong-thread semaphore release was accepted;
- CAS handled a bounded state transition but was not a replacement for a
  blocking payment critical section.

**Migration lesson:** synchronization primitives are not interchangeable.
Ownership, fairness, interruption, timeout, and reentrancy must be preserved.

## Slide 10 — Answers to the research questions

### RQ1 answer

In the tested Java 21 condition, intrinsic synchronization around blocking
work caused direct monitor-pinning evidence. Replacing it with
`ReentrantLock` removed that evidence but did not remove the serialized
business bottleneck.

### RQ2 answer

Before enabling Virtual Threads, audit:

1. intrinsic monitors around blocking work;
2. request-context lifecycle and `ThreadLocal` cleanup;
3. bounded database and external resources;
4. native/JNI boundaries;
5. lock semantics and correctness invariants.

The audits must remain mechanism-specific. This study did not establish a
ThreadLocal leak, a Hikari pool bottleneck, or universal JNI pinning.

## Slide 11 — Practical contribution

The resulting migration procedure is:

1. freeze source, runtime, workload, hardware, and artifact identity;
2. enable Virtual Threads without changing application behavior;
3. use JFR to locate actual monitor-pinning stacks;
4. review critical-section scope and preserve synchronization semantics;
5. audit context lifecycle and finite-resource capacity;
6. test native/external boundaries separately;
7. repeat correctness and performance measurements;
8. retain raw artifacts and report negative results and limitations.

Supporting documents:

- `docs/research-synthesis.md`
- `docs/migration-guidelines.md`
- `docs/artifact-provenance-ledger.md`

## Slide 12 — Remaining packaging work

The research execution is substantially complete. Remaining Checkpoint 4 /
Checkpoint 5 preparation is documentation and provenance work:

- freeze the final source and artifact revision;
- map every headline claim to raw k6/JFR/manifest files and hashes;
- integrate the results into the substantially complete thesis draft;
- complete the signed AI declaration and point-of-use disclosures;
- retain the complete interaction log required by the applicable policy;
- present the final package to the supervisor.

Energy measurement and cross-OS comparison remain explicitly deferred because
the required reproducible environments/access were unavailable.

## Backup — reproducibility commands

```bash
./mvnw test
python3 scripts/normalize_evidence.py
python3 scripts/validate_normalized_evidence.py
./run-benchmark.sh --endpoint payments --vus 10 --lock-mode synchronized
./run-benchmark.sh --endpoint payments --vus 10 --lock-mode reentrant-lock
```

The one-carrier mechanism stress condition requires:

```bash
JAVA_EXTRA_OPTS="-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1"
```

The dashboard is available at `/research-dashboard.html` after starting the
application, but it is an evidence navigator, not a replacement for raw
artifacts or the methodology.
