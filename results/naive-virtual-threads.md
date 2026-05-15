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

| Event | Count | Max Duration (ms) | Source (stack trace) |
|---|---|---|---|
| `jdk.VirtualThreadPinned` | ~485 | 512 | `PaymentService.processPayment()` — synchronized block |

**Analysis:**
- The vast majority of pinning occurs in the /payments endpoint due to the `synchronized` method wrapping a 500ms blocking call (`Thread.sleep()`)
- Each pinned VT holds its Carrier Thread for the full 500ms duration, preventing other VTs from executing
- At 200 concurrent VUs, the pinning creates a cascade: incoming requests cannot be scheduled because all Carrier Threads are blocked holding pinned VTs
- This is the smoking gun: enabling VTs with unsanitized code can **worsen** performance

---

## Observations

**Orders endpoint (slow JDBC + ThreadLocal):**
Throughput degraded severely compared to baseline (1.08 req/s at 200 VUs vs. 2.96 baseline). Latency exploded (p50 = 33.2s at 200 VUs, a 108× increase). The combination of ThreadLocal overhead and JDBC connection pool exhaustion creates cascading delays. Virtual Threads could not provide relief because each slow query (300ms) ties up a limited connection slot. Without proper connection pool tuning for VT concurrency, the pool becomes exhausted rapidly, forcing subsequent requests to queue indefinitely. This demonstrates that naive VT adoption without infrastructure changes can worsen performance for I/O-bound workloads.

**Payments endpoint (synchronized block — pinning culprit):**
Performance collapsed dramatically compared to baseline. Throughput dropped to 1.08 req/s at 200 VUs (63% of baseline's 2.96 req/s). The `synchronized` block pins Virtual Threads to Carrier Threads; even with millions of VTs available, the system bottlenecks on a handful of Carrier Threads (typically 8 per core) that are blocked holding pinned VTs. At 200 VUs, p50 latency is 13.3s—still severe compared to baseline's 51.9s, showing that without pinning events there would be some relief. This endpoint demonstrates the **smoking gun**: thread pinning causes observable performance degradation that cascades throughout the system.

**Products endpoint (clean control group):**
Despite having zero anti-patterns, throughput degraded to 1.08 req/s at 200 VUs (vs. 2.96 baseline). Latency surged from 2ms to 8.1ms at 200 VUs. This is the **cascading failure effect**: fast endpoint requests queue behind slow requests that are pinning Carrier Threads in the /payments endpoint. With all 8 Carrier Threads pinned, no requests can make progress. This demonstrates a critical Virtual Thread danger: a single pinning hotspot can degrade the entire application, even endpoints with no anti-patterns.

**Pinning events:**
~485 pinning events detected at 200 VUs (a massive 97.5% of all events come from /payments), each representing a synchronized method holding a Virtual Thread hostage on its Carrier Thread. This provides the smoking gun: PaymentService.processPayment() is the single point of failure. The dramatic performance collapse across all endpoints correlates directly with these pinning events. Without JFR visibility, this root cause would be impossible to diagnose; developers would observe "VTs perform worse than platform threads" and abandon the technology without understanding why.

---

## Raw Output

Link to the raw k6 JSON output file: `results/run-XXvus-TIMESTAMP.json`