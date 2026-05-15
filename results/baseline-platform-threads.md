# Benchmark Results: BASELINE-PLATFORM-THREADS

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
| 50 | 1.97 | 308 | 311 | 369 | 0% |
| 100 | 2.02 | 307 | 312 | 328 | 0% |
| 200 | 2.96 | 307 | 316 | 373 | 0% |

### POST /payments *(synchronized block — pinning culprit)*
| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 16877 | 41458 | 48951 | 0% |
| 100 | 2.02 | 26706 | 60000 | 60003 | ~5.5% |
| 200 | 2.96 | 51944 | 60001 | 60002 | ~14.1% |

### GET /products *(clean control group)*
| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 2 | 4 | 14 | 0% |
| 100 | 2.02 | 1 | 4 | 10 | 0% |
| 200 | 2.96 | 2 | 5 | 28 | 0% |

---

## JFR Pinning Events

*(Fill in if JFR was enabled)*

| Event | Count | Max Duration (ms) | Source (stack trace) |
|---|---|---|---|
| `jdk.VirtualThreadPinned` | | | |

To extract from JFR file:
```bash
jfr print --events jdk.VirtualThreadPinned results/jfr/recording-TIMESTAMP.jfr
```

---

## Observations

**Orders endpoint (slow JDBC + ThreadLocal):**
With platform threads, the 200-thread pool handles the 300ms query time reasonably well. Throughput stabilizes at ~2-3 req/s across all load levels, indicating the Tomcat thread pool is the limiting factor. All queries complete within acceptable latency (p95 ≤ 316ms), showing predictable behavior. The thread pool prevents cascade failures even under high concurrency, though it also artificially caps throughput. This baseline establishes the maximum performance achievable without Virtual Threads.

**Payments endpoint (synchronized block — pinning culprit):**
Despite simpler business logic (500ms sleep), throughput matches the orders endpoint (~2-3 req/s) because the 200-thread pool is saturated. Latency is severe (p50 jumps from 16.8s at 50 VUs to 51.9s at 200 VUs, with p95 timeout at 60s), indicating heavy request queuing. The synchronized block itself is not the bottleneck here; the thread pool saturation masks the pinning effect. At 200 VUs, error rates reach ~14%, showing the system begins to fail under sustained overload.

**Products endpoint (clean control group):**
The fast query completes in 1-5ms, showing excellent per-request performance. However, throughput (~2-3 req/s) matches the slower endpoints due to the shared Tomcat thread pool constraint. This confirms the thread pool is the system-wide bottleneck, not business logic. This endpoint serves as the performance target for Virtual Threads—we expect similar sub-millisecond latency when VTs remove the thread pool constraint.

**Pinning events:**
No Virtual Threads present, so no JFR pinning events. Platform threads use OS-level scheduling; there is no VT unmounting mechanic to pin or unpin. This is the baseline against which both naive and refactored Virtual Thread runs will be compared.

---

## Raw Output

Link to the raw k6 JSON output file: `results/run-XXvus-TIMESTAMP.json`