# Research Iteration Note: Hikari Sensitivity and Scheduler Handoffs

**Date:** 2026-10-15  
**Status:** H2, PostgreSQL, and scheduler evidence complete

## H2 connection-pool sensitivity

The `/orders` endpoint was run with 50 closed-loop VUs, four virtual-thread
carriers, and three process-level repetitions at Hikari maximum pool sizes 1
and 10.

| H2 pool | Requests/run | p50 range | p95 range | Mean range |
|---|---:|---:|---:|---:|
| 1 | 5,242-5,287 | 303.4-305.4 ms | 307.7-312.4 ms | 304.2-306.3 ms |
| 10 | 5,258-5,284 | 304.3-304.9 ms | 308.4-311.3 ms | 304.7-305.5 ms |

All six runs returned successful responses and all reported zero
`jdk.VirtualThreadPinned` events.

### Interpretation

Under this H2, 50-VU, 300 ms simulated-query protocol, changing the maximum
pool size from 1 to 10 did not materially change request counts or latency.
The result does not establish that pool size is irrelevant: the query is
synthetic, the H2 database is embedded, and the closed-loop workload may not
apply enough offered load to expose acquisition queueing. PostgreSQL is being
tested separately rather than pooled with this result.

## PostgreSQL connection-pool sensitivity

The Docker Compose PostgreSQL deployment was tested with the same `/orders`
endpoint, 50 closed-loop VUs, and three process-level repetitions at Hikari
maximum pool sizes 1 and 10. Each k6 run passed its correctness checks and
reported zero failed HTTP requests.

| PostgreSQL pool | Requests/run | p50 range | p95 range | Mean range |
|---|---:|---:|---:|---:|
| 1 | 5,187-5,233 | 303.1-303.9 ms | 334.3-360.0 ms | 308.4-312.0 ms |
| 10 | 5,181-5,226 | 303.9-304.8 ms | 334.0-359.7 ms | 308.6-312.3 ms |

The raw k6 artifacts are
`results/docker-pg-orders-pool{1,10}-trial{1,2,3}.json`. The PostgreSQL
container remained healthy throughout the tested runs. These runs did not
capture application JFR files, so no PostgreSQL-specific pinning claim is
made from them.

### Interpretation

Under this Dockerized PostgreSQL, 50-VU, 300 ms simulated-query protocol,
changing the maximum Hikari pool size from 1 to 10 produced nearly identical
request counts and latency distributions. This did not establish that pool
size is irrelevant: the workload is closed-loop, the application container
was CPU-limited, and the simulated query delay may dominate connection
acquisition. The result is useful negative evidence against attributing this
specific run's behavior to an exposed pool-size bottleneck.

## Scheduler handoff probe

A standalone Java 21 probe measured repeated two-thread `LockSupport.park`
and `unpark` handoffs after warm-up. It compared platform threads and virtual
threads over five repetitions and 100,000 rounds.

| Execution | Approximate handoff cost |
|---|---:|
| Platform threads | 4.3-8.6 microseconds |
| Virtual threads | 0.4-1.5 microseconds |

### Interpretation

The virtual-thread protocol completed this particular park/unpark handoff
with a lower measured cost than the platform-thread protocol on this machine.
This is a measured microbenchmark observation, not an isolated OS context
switch measurement. It includes scheduler, parking, wake-up, synchronization,
and measurement effects. It must not be converted directly into a production
throughput prediction or treated as the origin of the application benchmark
results.

The probe is mechanism support only. The application-level `/payments`,
`/orders`, and `/products` results remain the primary evidence.

## Limitations

- The scheduler probe is not JMH and reports wall-clock process timings.
- It does not expose OS context-switch counters or CPU performance counters.
- The H2 comparison does not represent PostgreSQL or a remote database.
- The PostgreSQL comparison used the same synthetic delay and closed-loop
  workload; it does not represent a remote or query-intensive production
  database.
- Energy and cross-OS measurements remain separate feasibility tracks.
