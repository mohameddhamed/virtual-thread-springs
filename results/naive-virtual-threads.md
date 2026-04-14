# Benchmark Results: NAIVE-VIRTUAL-THREADS

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

*Note: Since `k6` script defaults to outputting `p(90)` and `p(95)` instead of `p(99)`, I have filled the `p99` column with your absolute **Max** response times. For a load test, the max value perfectly illustrates the worst-case queuing delay you are trying to prove.*

### GET /orders  *(slow JDBC + ThreadLocal)*

| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 9471 | 16678 | 18511 | 0% |
| 100 | 1.54 | 22216 | 34165 | 42237 | 0% |
| 200 | 1.08 | 33194 | 60000 | 60000 | ~5.3% |

### POST /payments  *(synchronized block — pinning culprit)*

| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 7029 | 13136 | 16609 | 0% |
| 100 | 1.54 | 9547 | 24106 | 26146 | 0% |
| 200 | 1.08 | 13281 | 28306 | 31169 | 0% |

### GET /products  *(clean control group)*

| Concurrent Users | Throughput (req/s) | p50 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|
| 50 | 1.97 | 2532 | 8627 | 11585 | 0% |
| 100 | 1.54 | 6082 | 19641 | 21179 | 0% |
| 200 | 1.08 | 8100 | 22915 | 25210 | 0% |

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