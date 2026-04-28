# Benchmark Results: REFACTORED-VIRTUAL-THREADS

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

*(Write 2–3 sentences interpreting the numbers. What stood out? What was expected vs. surprising?)*

**Orders endpoint:**

**Payments endpoint:**

**Products endpoint:**

**Pinning events:**

---

## Raw Output

Link to the raw k6 JSON output file: `results/run-XXvus-TIMESTAMP.json`