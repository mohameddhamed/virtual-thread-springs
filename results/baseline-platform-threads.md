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

### GET /orders  *(slow JDBC + ThreadLocal)*

| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | | | | | |
| 100 | | | | | |
| 200 | | | | | |

### POST /payments  *(synchronized block — pinning culprit)*

| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | | | | | |
| 100 | | | | | |
| 200 | | | | | |

### GET /products  *(clean control group)*

| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | | | | | |
| 100 | | | | | |
| 200 | | | | | |

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