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

*(Write 2–3 sentences interpreting the numbers. What stood out? What was expected vs. surprising?)*

**Orders endpoint:**

**Payments endpoint:**

**Products endpoint:**

**Pinning events:**

---

## Raw Output

Link to the raw k6 JSON output file: `results/run-XXvus-TIMESTAMP.json`