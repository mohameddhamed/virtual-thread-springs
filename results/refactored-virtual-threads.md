# Benchmark Results: REFACTORED-VIRTUAL-THREADS (Pilot, Requires Revalidation)

The values and interpretations below are historical pilot observations. They are not final thesis evidence until mapped to raw k6/JFR files, commits, exact versions, and run manifests. The refactoring comparison also requires endpoint-contract and mutual-exclusion tests before it can be described as behavior-preserving.

## Run Configuration

| Field | Value |
|---|---|
| Date | |
| Thread mode | Platform Threads / Virtual Threads (naive) / Virtual Threads (refactored) |
| `spring.threads.virtual.enabled` | true / false |
| Tomcat thread pool size | 200 (platform) / N/A (virtual) |
| JFR enabled | Yes / No |
| Java version | 21.x.x |
| Machine | e.g. MacBook Pro M3, 16GB RAM |

---

## Results by Endpoint

### GET /orders *(slow JDBC + ThreadLocal)*
| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 308 | 318 | 344 | 0% |
| 100 | 1.87 | 308 | 321 | 536 | 0% |
| 200 | 2.84 | 309 | 439 | 713 | 0% |

### POST /payments *(ReentrantLock — fixed)*
| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 23233 | 24787 | 24795 | 0% |
| 100 | 1.87 | 31234 | 50019 | 50039 | 0% |
| 200 | 2.84 | 53406 | 60001 | 60003 | ~13.6% (Timeouts) |

### GET /products *(clean control group)*
| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 2 | 5 | 64 | 0% |
| 100 | 1.87 | 3 | 6 | 22 | 0% |
| 200 | 2.84 | 3 | 14 | 53 | 0% |

---

## JFR Pinning Events

| Event | Count | Max Duration (ms) | Source (stack trace) |
|---|---|---|---|
| `jdk.VirtualThreadPinned` | ~12 | 3 | Minimal framework-level pinning (not user code) |

**Analysis (provisional):**
- Pinning events reduced from ~485 to ~12, a **97.5% reduction**
- Remaining pinning must be classified from regenerated stack traces before being attributed to framework internals
- By replacing `synchronized` with `ReentrantLock`, VT unmounting is restored, allowing Carrier Threads to be reused effectively
- The slight residual pinning is acceptable and inherent to Tomcat/Spring internals

---

## Observations

**Orders endpoint (slow JDBC + ThreadLocal):**
The historical values suggest recovery relative to the naive condition, but they do not identify whether synchronization, JDBC-pool capacity, mixed-workload interference, or run selection produced the change. The final analysis must separate context lifecycle, JDBC wait, and pinning mechanisms.

**Payments endpoint (ReentrantLock — fixed):**
The historical table reports recovery in throughput but also a p50 near 53 seconds. A 500 ms service delay does not by itself predict that latency, and mixed closed-loop throughput cannot determine endpoint queueing. Recompute with isolated offered/achieved rates, timeout censoring, and queue/resource telemetry before interpreting the result.

**Products endpoint (clean control group):**
The historical mixed-workload values are consistent with reduced interference, but isolated `/products` runs and scheduler/resource evidence are required before attributing the change to carrier reuse.

**Pinning events:**
The historical extraction reports approximately 12 events versus approximately 485 in the naive condition. The percentage and stack attribution must be regenerated with the same JFR configuration. Correlation with throughput recovery is not proof that refactoring eliminated the sole root cause, and this pilot does not support a claim about handling millions of Virtual Threads.

---

## Raw Output

Link to the raw k6 JSON output file: `results/run-XXvus-TIMESTAMP.json`