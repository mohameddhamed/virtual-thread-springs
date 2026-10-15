# Research Iteration Note: Java 21 Primary Control Matrix

**Date:** 2026-10-15  
**Status:** Exploratory primary-matrix evidence  
**Related note:** `docs/research-iteration-2026-10-15-java21-primary-replication.md`

## Purpose

This iteration completed the remaining two controls for the isolated
`/payments` Java 21 matrix:

- Virtual Threads with no synchronization, retained only as a diagnostic
  upper bound;
- platform threads with the original synchronized treatment.

Together with the preceding repeated Java 21 synchronized and
`ReentrantLock` runs, these controls separate endpoint serialization from
monitor pinning and from the Virtual Thread execution model.

## Frozen conditions

- Java runtime: Azul Zulu 21.0.8
- Spring Boot: 3.5.12
- Same Java 21-targeted application artifact
- Endpoint: `POST /payments`
- Workload: 10 closed-loop k6 VUs
- Simulated payment operation: 500 ms
- JFR enabled for every process
- Three process-level repetitions per condition
- Virtual-thread conditions:
  - `-Djdk.virtualThreadScheduler.parallelism=1`
  - `-Djdk.virtualThreadScheduler.maxPoolSize=1`

The platform-thread condition used the benchmark runner's
`--platform` setting. Scheduler properties were still recorded in the
manifest, but they do not control platform-thread request execution.

## Results

### Virtual Threads with no-lock diagnostic

| Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---:|---:|---:|---:|---:|---:|
| 20261015-143108 | 713 | 507 ms | 509 ms | 522 ms | 507 ms | 0 |
| 20261015-143213 | 713 | 507 ms | 509 ms | 517 ms | 507 ms | 0 |
| 20261015-143318 | 713 | 507 ms | 510 ms | 512 ms | 506 ms | 0 |

The no-lock condition completed approximately 713 requests per run, compared
with approximately 108 requests for the synchronized and `ReentrantLock`
conditions. This is an intentionally unsafe diagnostic upper bound: it
removes the payment mutual-exclusion invariant and must not be presented as a
production treatment.

### Platform threads with synchronized

| Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---:|---:|---:|---:|---:|---:|
| 20261015-143422 | 110 | 3,921 ms | 8,962 ms | 8,973 ms | 4,034 ms | 0 |
| 20261015-143526 | 110 | 3,915 ms | 8,964 ms | 8,976 ms | 4,034 ms | 0 |
| 20261015-143631 | 110 | 3,918 ms | 8,972 ms | 8,981 ms | 4,038 ms | 0 |

The platform-thread condition completed 110 requests per run and reported no
`jdk.VirtualThreadPinned` events. The event count is not evidence that the
blocking operation became non-blocking; the application was not using
Virtual Threads, so there was no Virtual Thread to pin.

## Matrix-level comparison

| Condition | Requests/run | Approximate p50 | Approximate p95 | JFR pinning |
|---|---:|---:|---:|---:|
| Virtual Threads + synchronized | 108 | 4.96 s | 4.98 s | 108/run |
| Virtual Threads + `ReentrantLock` | 108 | 4.96–4.99 s | 4.97–5.01 s | 0/run |
| Virtual Threads + no-lock diagnostic | 713 | 0.51 s | 0.51 s | 0/run |
| Platform threads + synchronized | 110 | 3.92 s | 8.96 s | Not applicable |

The request counts are a direct consequence of the closed-loop workload:
slow responses reduce the number of iterations that each VU can offer during
the fixed test window. They should not be interpreted as a direct estimate of
maximum server capacity.

## Interpretation

### Measured

1. The no-lock diagnostic substantially increased completed requests because
   it allowed the 500 ms simulated operations to overlap.
2. The Java 21 synchronized Virtual Thread treatment emitted pinning events,
   while the `ReentrantLock` treatment emitted none.
3. The platform-thread treatment emitted no Virtual Thread pinning events,
   which is expected because it did not execute requests on Virtual Threads.
4. The synchronized and `ReentrantLock` Virtual Thread conditions had similar
   request counts and latency ranges.

### Mechanism-supported interpretation

The matrix separates two effects:

- **Serialization:** the synchronized and `ReentrantLock` treatments both
  enforce one-at-a-time payment processing, producing roughly the same
  application-level service capacity.
- **Monitor pinning:** only the Java 21 Virtual Thread synchronized treatment
  produced direct `jdk.VirtualThreadPinned` evidence.

The no-lock result is an upper bound showing what becomes possible when the
serialization invariant is removed. It does not show that synchronization is
unnecessary; it shows that the critical section is the dominant throughput
constraint in this synthetic payment workload.

The platform-thread latency shape differs from the Virtual Thread conditions,
but this matrix does not isolate the cause. Possible contributors include
request-executor behavior, queueing, startup/warm-up state, and the
closed-loop load model. The result should be retained as a platform baseline,
not as proof that platform threads are faster or slower in general.

## Correctness status

- Synchronized and `ReentrantLock` conditions retained the payment
  mutual-exclusion implementation and returned successful responses.
- The no-lock condition is explicitly diagnostic and is excluded from
  production-refactoring recommendations.
- No HTTP error or correctness failure was reported in the benchmark runs.

## Artifact references

| Condition | Manifest files | JFR files |
|---|---|---|
| `no-lock-diagnostic` | `results/run-manifest-20261015-143108.json`, `143213.json`, `143318.json` | `results/jfr/recording-20261015-143108.jfr`, `143213.jfr`, `143318.jfr` |
| `platform-synchronized` | `results/run-manifest-20261015-143422.json`, `143526.json`, `143631.json` | `results/jfr/recording-20261015-143422.jfr`, `143526.jfr`, `143631.jfr` |

The corresponding k6 result files are the six
`results/run-10vus-20261015-*.json` files referenced by those manifests.

## Decision

The isolated `/payments` Java 21 control matrix is complete for the current
protocol. The next primary task is not another payment lock variant. It is
to run and attribute the isolated `/orders` and `/products` workloads, then
normalize the evidence and freeze the Java 21 primary result.
