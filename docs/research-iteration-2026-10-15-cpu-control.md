# Research Iteration Note: CPU-Bound Control

**Date:** 2026-10-15  
**Status:** Exploratory control evidence  
**Related note:** `docs/research-iteration-2026-10-15-endpoint-isolation.md`

## Purpose

This iteration measured the CPU-only `/cpu` endpoint under the same Java 21
benchmark protocol used for the endpoint-isolation work. The endpoint performs
deterministic arithmetic without sleeping, JDBC, synchronization, or
`ThreadLocal` state.

The control tests whether the earlier observations should be generalized to
CPU-bound work. Virtual Threads are expected to help primarily with blocking
work; this endpoint is a negative control for that assumption.

## Frozen conditions

- Java runtime: Azul Zulu 21.0.8
- Spring Boot: 3.5.12
- Same application artifact
- Endpoint: `GET /cpu`
- Workload: 10 closed-loop k6 VUs
- Three Virtual Thread process repetitions
- Three platform-thread process repetitions
- JFR enabled for every process
- Virtual Thread scheduler:
  - `-Djdk.virtualThreadScheduler.parallelism=1`
  - `-Djdk.virtualThreadScheduler.maxPoolSize=1`

## Results

| Execution | Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---|---:|---:|---:|---:|---:|---:|
| Virtual Threads | 20261015-145454 | 3,888 | 9.26 ms | 14.10 ms | 32.60 ms | 10.01 ms | 0 |
| Virtual Threads | 20261015-145558 | 3,890 | 9.18 ms | 14.21 ms | 31.38 ms | 9.85 ms | 0 |
| Virtual Threads | 20261015-145702 | 3,893 | 9.03 ms | 13.78 ms | 35.42 ms | 9.88 ms | 0 |
| Platform Threads | 20261015-145806 | 3,726 | 14.16 ms | 20.69 ms | 24.06 ms | 14.51 ms | Not applicable |
| Platform Threads | 20261015-145910 | 3,731 | 13.82 ms | 20.49 ms | 23.41 ms | 14.37 ms | Not applicable |
| Platform Threads | 20261015-150014 | 3,731 | 13.70 ms | 20.53 ms | 24.15 ms | 14.20 ms | Not applicable |

All runs completed with successful HTTP responses. No Virtual Thread pinning
events were reported, as expected for a CPU-only endpoint without a blocking
monitor region.

## Interpretation

The Virtual Thread condition was faster in this local protocol, with mean
latency around 9.9-10.0 ms compared with 14.2-14.5 ms for platform threads.
This is a measured result for this application, machine, scheduler setting,
and closed-loop workload. It is not evidence that Virtual Threads generally
make CPU-bound work faster.

The result may reflect executor and request-dispatch behavior rather than a
fundamental CPU advantage. The one-carrier Virtual Thread scheduler setting
is a mechanism-isolation condition, while platform-thread scheduling used the
application's platform request executor. A matched executor and broader CPU
scaling study would be required for a claim about CPU parallelism.

## Limitations

- The arithmetic workload and iteration count are application-specific.
- The comparison used different request-execution models by design.
- No CPU-performance counters or allocation measurements were collected.
- Closed-loop load does not maintain a constant offered arrival rate.
- No energy conclusion can be drawn from these latency or request-count
  results.

## Artifact references

```text
results/run-manifest-20261015-145454.json
results/run-manifest-20261015-145558.json
results/run-manifest-20261015-145702.json
results/run-manifest-20261015-145806.json
results/run-manifest-20261015-145910.json
results/run-manifest-20261015-150014.json
```

Each manifest links the corresponding k6 JSONL, telemetry CSV, and JFR
recording.

## Decision

The CPU-only control is complete as a bounded negative/control condition. It
does not alter the primary conclusion about Java 21 monitor pinning and
serialized blocking work. It should be reported separately from the blocking
endpoint matrix.
