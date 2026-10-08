# Research Progress — 8 October 2026

**Project:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads
**Student:** Mohamed Hamed
**Related activities:** Thesis consultation research progress; Software Lab reproducibility and testing milestone

## Work completed today

### 1. Reproducibility artifact

Added `results/run-manifest-template.json`. The template records the information needed to connect a benchmark result to its execution context: Git commit, Java and framework versions, machine, execution mode, lock variant, endpoint/workload, load model, timeout, pool configuration, JFR settings, raw-output hashes, and validity status.

This addresses a weakness identified during the thesis-plan audit: a raw k6 JSON file or JFR recording is not independently interpretable without its exact source revision and runtime configuration.

### 2. Endpoint smoke tests

Added `ApplicationBehaviorTests.smokeEndpointsReturnExpectedResponses`, which exercises:

- `GET /orders`;
- `POST /payments?orderId=smoke-order`;
- `GET /products`.

The test verifies successful HTTP responses, JSON response types for the data endpoints, and the exact payment response contract.

### 3. Synchronization and refactoring test

Added `ApplicationBehaviorTests.concurrentPaymentsPreserveEachOrderIdAndSerializeCriticalSection`. Four concurrent payment calls are released together and must:

- all complete successfully;
- preserve their individual order identifiers;
- complete in serialized critical-section time, demonstrating that the refactored `ReentrantLock` still protects the intended critical section rather than merely removing synchronization.

The test therefore checks behavioral equivalence before performance interpretation. It does not claim that the lock is optimal or that the result generalizes beyond this service.

### 4. Traceable benchmark pilot

I executed a 50-VU Java 21 Virtual-Thread pilot using the refactored
`ReentrantLock` implementation and the existing mixed closed-loop workload.
The run captured:

- manifest: `results/run-manifest-20261008-133419.json`;
- raw k6 JSONL: `results/run-50vus-20261008-133419.json`;
- JFR recording: `results/jfr/recording-20261008-133419.jfr`.

The run used Java 21.0.8 (Zulu), Spring Boot 3.5.12, k6 1.7.1, an Apple M1
with 8 logical processors and 8 GB memory, 50 VUs, and the 15-second
ramp-up / 30-second hold / 10-second ramp-down workload. The JFR recording
contained no recorded `jdk.VirtualThreadPinned` events above the active JFR
threshold in this refactored condition.

The pilot completed 150 mixed iterations and 450 HTTP requests with no HTTP
failures. The measured endpoint trends were approximately:

| Endpoint | Median latency | Maximum latency |
|---|---:|---:|
| `/orders` | 306 ms | 310 ms |
| `/payments` | 23.2 s | 24.8 s |
| `/products` | 1.1 ms | 6.1 ms |

The k6 process returned status 99 because the pre-existing reference threshold
`http_req_duration: p(95)<5000` was crossed by the intentionally serialized
500 ms payment path and its queueing delay. This is a threshold warning, not
an HTTP correctness failure. The manifest records the non-zero status and
classifies the run as exploratory rather than hiding the result.

### 5. Added controls and isolated workload support

The application now supports explicit `synchronized`, `reentrant-lock`, and
`none` payment-lock modes, plus a deterministic CPU-only control at `GET /cpu`.
The benchmark runner accepts `--lock-mode`, `--platform`, and
`--endpoint`; isolated workloads can target `/orders`, `/payments`,
`/products`, or `/cpu` without changing source code.

As a protocol check, an isolated 10-VU CPU-control run completed 3,888
iterations and 3,888 successful requests with 0% HTTP failures. Its median
latency was 9.4 ms and p95 latency was 12.6 ms. This is a control observation,
not yet a comparative claim: the synchronized, refactored, and platform
conditions still require repeated process-level runs under the same manifest
protocol.

## Research interpretation

The current application should be treated as a mechanism-focused Java 21 case study. The tests separate two questions that were previously mixed in the result narrative:

1. **Correctness:** does replacing the implementation preserve the payment response and mutual-exclusion behavior?
2. **Performance mechanism:** does the replacement alter Virtual Thread pinning and system behavior under a controlled benchmark?

The tests alone cannot establish a pinning or throughput effect. That requires the frozen benchmark protocol, endpoint-isolated workloads, and JFR stack classification described in the revised research plan.

## Evidence produced

| Artifact | Purpose |
|---|---|
| `src/test/java/com/thesis/virtualthreadsdemo/ApplicationBehaviorTests.java` | Endpoint smoke and concurrency/mutual-exclusion tests |
| `results/run-manifest-template.json` | Reproducibility metadata schema |
| `results/cpu-control-20261008.json` | Isolated CPU-control raw k6 output |
| `results/jfr/cpu-control-20261008.jfr` | CPU-control JFR recording |
| `k6/isolated-load-test.js` | Endpoint-isolated workload driver |
| `docs/research-progress-2026-10-08.md` | Progress record and interpretation |
| `docs/research-plan-checkpoint-revised.md` | Updated bounded research protocol |
| `docs/bibliography-review-revised.md` | Updated critical literature synthesis |

## Java 21 synchronization matrix completed

The focused Java 21 synchronization matrix was then repeated three times for
each condition: `synchronized`, `ReentrantLock`, no-lock diagnostic, and
platform-thread execution. All 12 runs used isolated `/payments`, 10 VUs, the
same 500 ms critical-section delay, and complete hashed manifests. Every run
completed with zero HTTP failures.

| Condition | Mean requests | Mean median latency | Mean p95 latency |
|---|---:|---:|---:|
| Virtual Threads + `synchronized` | 110.0 | 3923.86 ms | 7957.50 ms |
| Virtual Threads + `ReentrantLock` | 108.7 | 4941.99 ms | 4967.54 ms |
| Virtual Threads + no-lock diagnostic | 710.7 | 507.66 ms | 512.84 ms |
| Platform threads + `synchronized` | 110.0 | 3936.42 ms | 9002.48 ms |

The result must not be summarized as “`synchronized` is faster.” Both
serialized conditions completed approximately the same number of requests;
the difference is in queueing and latency distribution under this artificial
one-carrier stress configuration. The no-lock control confirms that the
approximately 500 ms service time is not intrinsically slow. The Java 21
`synchronized` runs reported 110 `jdk.VirtualThreadPinned` events per
recording, while the `ReentrantLock`, no-lock, and platform-thread runs
reported none. This is the clearest direct evidence so far that monitor
pinning occurred in the intended Java 21 treatment.

## Native-boundary follow-up completed

The planned cross-JDK native-boundary follow-up was completed as a separate
external-validity experiment. A matrix runner executed three process-level
trials for each of Java 21.0.8, Java 24.0.2, and Java 25 across:

- pure-Java `Thread.sleep(500 ms)`;
- blocking JNI `nanosleep(500 ms)`;
- short JNI no-op.

All 27 runs used the same Java-21-targeted application artifact, one virtual
thread scheduler carrier, 10 VUs, and the same closed-loop workload. All
completed with zero HTTP failures. Ordinary Java sleep produced approximately
714 requests per run, while blocking JNI produced approximately 108–109
requests with approximately 4.95-second median latency on every runtime.
The short JNI control produced approximately 4,185–4,212 requests with
approximately 1 ms median latency. No repeated recording reported a
`jdk.VirtualThreadPinned` event, so the result remains behavioral evidence
consistent with native carrier occupation rather than JFR-confirmed pinning.

This strengthens the defensible conclusion that long-running native execution
is a separate migration risk after the Java 24 monitor-pinning change. It does
not support the stronger claim that Java 21 plus refactoring outperforms Java
24 or Java 25.
