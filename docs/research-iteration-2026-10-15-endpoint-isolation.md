# Research Iteration Note: Orders and Products Endpoint Isolation

**Date:** 2026-10-15  
**Status:** Exploratory endpoint-isolation evidence  
**Related note:** `docs/research-iteration-2026-10-15-java21-primary-matrix.md`

## Purpose

The `/payments` matrix intentionally serializes a 500 ms operation. This
iteration tested the two non-payment endpoints separately to determine whether
the observed behavior generalizes to the application's JDBC and clean-control
paths:

- `/orders`: simulated 300 ms JDBC latency and cleaned-up `ThreadLocal`;
- `/products`: fast control endpoint without the documented anti-patterns.

Each endpoint was run with Virtual Threads and platform threads.

## Frozen conditions

- Java runtime: Azul Zulu 21.0.8
- Spring Boot: 3.5.12
- Same application artifact and benchmark runner
- 10 closed-loop k6 VUs
- Three process-level repetitions per endpoint/execution mode
- JFR enabled for every process
- Virtual Thread scheduler:
  - `-Djdk.virtualThreadScheduler.parallelism=1`
  - `-Djdk.virtualThreadScheduler.maxPoolSize=1`

The `/orders` service sleeps for approximately 300 ms before executing the
H2 query, but does not place the sleep inside a synchronized region. The
`ThreadLocal` value is removed in a `finally` block.

## Results

### `/orders`

| Execution | Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---|---:|---:|---:|---:|---:|---:|
| Virtual Threads | 20261015-143809 | 1,054 | 308.38 ms | 315.37 ms | 317.75 ms | 308.83 ms | 0 |
| Virtual Threads | 20261015-143913 | 1,043 | 313.58 ms | 321.24 ms | 323.34 ms | 313.44 ms | 0 |
| Virtual Threads | 20261015-144017 | 1,047 | 312.32 ms | 319.51 ms | 321.74 ms | 312.04 ms | 0 |
| Platform Threads | 20261015-144121 | 1,053 | 308.20 ms | 316.31 ms | 318.34 ms | 309.01 ms | Not applicable |
| Platform Threads | 20261015-144225 | 1,059 | 307.00 ms | 310.29 ms | 312.15 ms | 306.90 ms | Not applicable |
| Platform Threads | 20261015-144329 | 1,060 | 306.54 ms | 310.15 ms | 311.97 ms | 306.34 ms | Not applicable |

### `/products`

| Execution | Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---|---:|---:|---:|---:|---:|---:|
| Virtual Threads | 20261015-144433 | 4,165 | 2.38 ms | 6.85 ms | 8.51 ms | 2.81 ms | 0 |
| Virtual Threads | 20261015-144537 | 4,171 | 2.40 ms | 6.17 ms | 8.16 ms | 2.65 ms | 0 |
| Virtual Threads | 20261015-144641 | 4,166 | 2.45 ms | 6.80 ms | 8.35 ms | 2.81 ms | 0 |
| Platform Threads | 20261015-144745 | 4,136 | 2.75 ms | 5.85 ms | 7.29 ms | 2.95 ms | Not applicable |
| Platform Threads | 20261015-144849 | 4,148 | 2.22 ms | 5.71 ms | 7.82 ms | 2.67 ms | Not applicable |
| Platform Threads | 20261015-144952 | 4,136 | 2.72 ms | 6.31 ms | 7.62 ms | 2.97 ms | Not applicable |

All runs completed with successful HTTP responses. The result counts and
percentiles are trial-level observations from the existing closed-loop
workload, not estimates of unconstrained maximum capacity.

## Interpretation

### `/orders`

The Virtual Thread and platform-thread conditions produced similar request
counts and latency distributions. The recordings reported zero
`jdk.VirtualThreadPinned` events for the Virtual Thread runs. This is
consistent with the simulated blocking query being outside a synchronized
region: the `ThreadLocal` usage and ordinary blocking sleep did not provide
direct monitor-pinning evidence.

The result does not establish that Virtual Threads provide no benefit for
real JDBC workloads. This application uses an embedded H2 database, a small
dataset, and a fixed 10-VU closed-loop workload. Hikari pool saturation,
database wait states, and higher offered loads require separate measurement.

### `/products`

The clean control remained fast in both execution modes, with median latency
around 2-3 ms and p95 below approximately 7 ms in all runs. No meaningful
execution-mode difference is established by this small local comparison.

The endpoint is useful as a control because it contains neither the
intentional synchronized blocking treatment nor the simulated slow query and
`ThreadLocal` lifecycle path.

## Mechanism boundaries

This iteration provides negative evidence against several over-broad claims:

- `Thread.sleep` alone is not being labelled monitor pinning;
- `ThreadLocal` presence alone is not being labelled monitor pinning;
- a JDBC-shaped endpoint is not assumed to degrade because Virtual Threads
  are enabled;
- platform-thread and Virtual Thread results are not pooled with the
  `/payments` serialized critical-section results.

## Limitations

- H2 is not PostgreSQL and does not establish connection-pool behavior in the
  Dockerized target environment.
- The workload is closed-loop, so slower responses reduce offered load.
- Only one machine and OS were used.
- No Hikari active/pending/acquisition telemetry was captured in this
  iteration.
- JFR pinning is not applicable to platform-thread runs; their zero count is
  recorded as “not applicable,” not as evidence of non-pinning behavior.

## Artifact references

The manifests, k6 files, telemetry files, and JFR recordings are identified
by the run IDs in the tables above. The corresponding files follow the
existing naming scheme:

```text
results/run-manifest-20261015-<run-id>.json
results/run-10vus-20261015-<run-id>.json
results/telemetry-20261015-<run-id>.csv
results/jfr/recording-20261015-<run-id>.jfr
```

## Decision

The endpoint-isolation evidence is sufficient to keep `/payments`,
`/orders`, and `/products` as separate result families. The next primary
step is evidence normalization and validation, followed by a resource-pool
sensitivity study only if the existing manifests and instrumentation show
that `/orders` can support a defensible Hikari/JDBC question.
