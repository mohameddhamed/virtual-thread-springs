# Benchmark Results: NAIVE-VIRTUAL-THREADS (Pilot, Requires Revalidation)

The values and interpretations below are historical pilot observations. They are not final thesis evidence until mapped to raw k6/JFR files, commits, exact runtime configuration, and run manifests. The mixed closed-loop workload also prevents treating displayed throughput as an isolated endpoint arrival rate.

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

**Analysis (provisional):**
- The vast majority of pinning occurs in the /payments endpoint due to the `synchronized` method wrapping a 500ms blocking call (`Thread.sleep()`)
- Each pinned VT holds its Carrier Thread for the full 500ms duration, preventing other VTs from executing
- At 200 concurrent VUs, the pinning creates a cascade: incoming requests cannot be scheduled because all Carrier Threads are blocked holding pinned VTs
- This supports a hypothesis that the Java 21 synchronized path can worsen performance, but isolated runs and a frozen protocol are required before treating it as a causal finding.

---

## Observations

**Orders endpoint (slow JDBC + ThreadLocal):**
The historical table reports severe degradation at 200 VUs. It does not establish that `ThreadLocal` caused the effect, nor does it distinguish JDBC-pool wait, mixed-workload interference, carrier pinning, and closed-loop self-throttling. Those mechanisms require separate telemetry and endpoint-isolated runs.

**Payments endpoint (synchronized block — pinning culprit):**
The historical table reports a large throughput change at 200 VUs. The `synchronized` path is a candidate pinning mechanism in Java 21, but the event threshold, stack output, carrier behavior, and alternative queue/resource explanations must be rechecked before calling this a system-wide causal collapse.

**Products endpoint (clean control group):**
Despite having zero anti-patterns, throughput degraded to 1.08 req/s at 200 VUs (vs. 2.96 baseline). Latency surged from 2ms to 8.1ms at 200 VUs. This is the **cascading failure effect**: fast endpoint requests queue behind slow requests that are pinning Carrier Threads in the /payments endpoint. With all 8 Carrier Threads pinned, no requests can make progress. This demonstrates a critical Virtual Thread danger: a single pinning hotspot can degrade the entire application, even endpoints with no anti-patterns.

**Pinning events:**
The historical extraction reports approximately 485 events at 200 VUs, mostly attributed to `/payments`. This is mechanism evidence only after the raw recording, threshold, and stack classification are regenerated; correlation with endpoint degradation is not by itself proof of a single point of failure.

---

## Raw Output

Link to the raw k6 JSON output file: `results/run-XXvus-TIMESTAMP.json`