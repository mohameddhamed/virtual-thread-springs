# Research Iteration Note: Java 21 Primary Synchronization Replication

**Date:** 2026-10-15  
**Status:** Exploratory replication evidence  
**Related plan:** `docs/ultimate-research-program-plan-2026-10-15.md`

## Purpose

This iteration repeated the primary Spring `/payments` synchronization
comparison under Java 21. The goal was to determine whether the earlier
single-run observation generalizes across process-level repetitions, while
separating monitor pinning from the endpoint's intentionally serialized
500 ms critical section.

## Frozen conditions

- Java runtime: Azul Zulu 21.0.8
- Spring Boot: 3.5.12
- Existing Java 21-targeted application artifact
- Virtual Threads enabled
- Scheduler:
  - `-Djdk.virtualThreadScheduler.parallelism=1`
  - `-Djdk.virtualThreadScheduler.maxPoolSize=1`
- Endpoint: `POST /payments`
- Workload: 10 closed-loop k6 VUs
- Simulated payment operation: 500 ms
- Measurement stage: existing isolated k6 workload
- JFR enabled for every process run
- Three process-level repetitions per treatment

The synchronized and `ReentrantLock` conditions differed only in the
coordination primitive. The application-level critical section remained
serialized in both conditions.

## Results

### Synchronized monitor

| Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---:|---:|---:|---:|---:|---:|
| 20261015-142222 | 108 | 4,957 ms | 4,977 ms | 4,982 ms | 4,045 ms | 108 |
| 20261015-142326 | 108 | 4,955 ms | 4,988 ms | 4,990 ms | 4,043 ms | 108 |
| 20261015-142430 | 108 | 4,962 ms | 4,978 ms | 4,981 ms | 4,048 ms | 108 |

### Non-fair `ReentrantLock`

| Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---:|---:|---:|---:|---:|---:|
| 20261015-142534 | 108 | 4,961 ms | 4,972 ms | 4,975 ms | 4,043 ms | 0 |
| 20261015-142638 | 108 | 4,981 ms | 5,001 ms | 5,004 ms | 4,065 ms | 0 |
| 20261015-142742 | 108 | 4,986 ms | 5,011 ms | 5,020 ms | 4,068 ms | 0 |

All runs completed with successful HTTP responses and no observed correctness
failure. The request counts and latency distributions are close between the
treatments. The synchronized condition emitted 108
`jdk.VirtualThreadPinned` events per run; the lock condition emitted none.

## Interpretation

### Measured

Under this one-carrier Java 21 protocol, replacing the monitor with
`ReentrantLock` removed the JFR-confirmed monitor-pinning events. It did not
materially increase completed requests or reduce request latency during the
30-second measurement stage.

### Mechanism-supported interpretation

The result is consistent with two independent effects:

1. `synchronized` around the blocking call pins the carrier while the
   virtual thread sleeps.
2. Both treatments still serialize the 500 ms payment operation, so the
   application-level service capacity remains approximately one payment at a
   time.

Removing monitor pinning is therefore not equivalent to removing the
serialization bottleneck. With one carrier and a closed-loop workload, the
serialized critical section dominates the observed request behavior.

### Not established

This iteration does not establish that `ReentrantLock` and `synchronized`
have identical performance in general. It also does not establish the
behavior at multiple carriers, under open-loop offered load, with a shorter
critical section, or for an endpoint whose work can execute concurrently.

## Artifact references

| Treatment | Manifest files | JFR files |
|---|---|---|
| `synchronized` | `results/run-manifest-20261015-142222.json`, `142326.json`, `142430.json` | `results/jfr/recording-20261015-142222.jfr`, `142326.jfr`, `142430.jfr` |
| `reentrant-lock` | `results/run-manifest-20261015-142534.json`, `142638.json`, `142742.json` | `results/jfr/recording-20261015-142534.jfr`, `142638.jfr`, `142742.jfr` |

The corresponding k6 result files are the six
`results/run-10vus-20261015-*.json` files referenced by those manifests.

## Decision

The Java 21 primary synchronization matrix now has repeated mechanism
evidence for the two core treatments:

- retain `synchronized` as the pinning control;
- retain `ReentrantLock` as the non-pinning synchronization treatment;
- do not claim an application throughput improvement from this replacement
  for the current serialized `/payments` workload;
- proceed to the remaining primary controls and endpoint/resource studies
  rather than adding more lock variants to this endpoint.
