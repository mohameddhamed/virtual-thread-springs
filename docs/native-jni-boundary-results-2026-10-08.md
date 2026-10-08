# JNI Boundary Experiment — 8 October 2026

## Purpose

This is a bounded extension of the Java 21 Virtual Thread study. It tests
whether a long-running JNI call can capture a carrier thread on Java 21 and
whether that behavior persists on Java 25 after the Java 24 monitor-pinning
change. It does **not** test whether Java 21 is generally faster than newer
JDKs.

The native implementation is intentionally small and deterministic:
`native/native_blocking.c` calls `nanosleep` for 500 ms. The Spring endpoint is
`GET /native`, enabled only for this experiment.

## Artifact and protocol

- Application JAR: `target/virtual-threads-demo-0.0.1-SNAPSHOT.jar`
- Application JAR SHA-256:
  `8f05fc41fc747ee103ba66a33c395f9c08ba9b465f643a98f975d17efd4d693f`
- Native library: `target/native/libnativeblocking.dylib`
- Workload: isolated `GET /native`
- Load: 10 k6 VUs; 15-second ramp-up, 30-second hold, 10-second ramp-down
- Native delay: 500 ms
- Virtual-thread scheduler stress condition:
  `-Djdk.virtualThreadScheduler.parallelism=1`
  `-Djdk.virtualThreadScheduler.maxPoolSize=1`
- JFR: `settings=profile`, with `jdk.tracePinnedThreads=full`
- JDK 21, JDK 24, and JDK 25 ran the same Java-21-targeted application JAR
- JDK 24.0.2 was used as the post-JEP-491 boundary runtime and JDK 25 as a
  persistence check

The constrained scheduler condition is deliberate: it makes carrier capture
observable at low concurrency. It is a mechanism-isolation stress test, not a
claim about the default scheduler configuration.

## Repeated process-level matrix

The protocol was then repeated three times for each of three runtimes and
three conditions: pure-Java `Thread.sleep(500 ms)`, blocking JNI
(`nanosleep(500 ms)`), and a short JNI no-op. Every run used 10 VUs, the same
one-carrier scheduler constraint, the same Java-21-targeted JAR, and the same
native-library hash. All 27 runs completed with zero HTTP failures. The
manifests are grouped under `run_set =
native-boundary-20261008-repeated` and include trial identifiers and SHA-256
hashes for the k6, JFR, and independent telemetry artifacts.

The table reports the mean across the three process-level repetitions. Latency
values are endpoint-request medians or p95 values calculated from each raw k6
JSONL file and then averaged across repetitions.

| Runtime | Condition | Runs | Mean requests | Mean median latency | Mean p95 latency |
|---|---|---:|---:|---:|---:|
| Java 21.0.8 | Pure-Java sleep | 3 | 714.0 | 505.38 ms | 508.74 ms |
| Java 21.0.8 | Blocking JNI | 3 | 108.7 | 4954.43 ms | 4985.09 ms |
| Java 21.0.8 | Short JNI | 3 | 4186.7 | 1.13 ms | 4.67 ms |
| Java 24.0.2 | Pure-Java sleep | 3 | 714.0 | 505.58 ms | 510.17 ms |
| Java 24.0.2 | Blocking JNI | 3 | 109.0 | 4951.99 ms | 4983.83 ms |
| Java 24.0.2 | Short JNI | 3 | 4185.0 | 1.20 ms | 4.85 ms |
| Java 25 | Pure-Java sleep | 3 | 713.0 | 505.60 ms | 512.39 ms |
| Java 25 | Blocking JNI | 3 | 108.3 | 4957.63 ms | 5012.97 ms |
| Java 25 | Short JNI | 3 | 4212.3 | 0.87 ms | 3.77 ms |

The repeated data strengthens the mechanism-level interpretation. Ordinary
Java sleep completed about 713–714 requests in the 55-second closed-loop
workload because sleeping virtual threads could unmount and free the sole
carrier. Blocking JNI completed only about 108–109 requests, with roughly
4.95-second median latency, across all three runtimes. The short JNI control
completed about 4,185–4,212 requests with approximately 1 ms median latency,
separating JNI transition cost from long native residency. The Java 21, 24,
and 25 blocking-JNI results overlap substantially; this experiment does not
show a Java 21 performance advantage.

## Initial constrained result

| Runtime | Requests | HTTP failures | Median latency | p95 latency | Throughput |
|---|---:|---:|---:|---:|---:|
| Java 21, one carrier | 109 | 0% | 4.94 s | 4.95 s | 1.97 req/s |
| Java 25, one carrier | 109 | 0% | 4.94 s | 4.95 s | 1.97 req/s |

The near-2 requests/second ceiling is consistent with one carrier being
occupied for approximately 500 ms per native call. Java 21 and Java 25 were
effectively indistinguishable in this first pilot under the constrained
condition.

For reference, unconstrained 10-VU runs completed 694 requests on Java 21 and
693 requests on Java 25, with median endpoint latencies of 518.5 ms and
512.0 ms respectively. Those runs show successful native execution but are
not sufficient by themselves to establish carrier starvation.

## JFR interpretation

The extracted `jdk.VirtualThreadPinned` count was zero in all 27 repeated
recordings, including:

- `results/jfr/recording-20261008-143638.jfr`
- `results/jfr/recording-20261008-144930.jfr`
- `results/jfr/recording-20261008-150222.jfr`

This means that this JFR event did not report the native residency in these
recordings; it does not prove that the native call was unpinned. The controlled
one-carrier throughput ceiling is the current evidence of carrier occupation.
The result must therefore be described as **behavioral evidence consistent with
native carrier capture**, not as a JFR-confirmed pinning count.

## Current conclusion

This experiment does **not** support the hoped-for claim that Java 21 plus
refactoring outperforms Java 25 for native execution. Under the tested
blocking-JNI condition, Java 21 and Java 25 showed the same constrained
throughput and tail latency.

It does support a narrower result: application-level monitor refactoring and
JEP 491 address monitor-related pinning, but they should not be assumed to
remove carrier occupation caused by long-running native execution. The
repeated controls show that this is not explained by JNI transition overhead
alone. The result also demonstrates why native carrier occupation must be
evaluated separately from ordinary `synchronized`-monitor pinning.

## Required follow-up before thesis claims

1. Add direct carrier/scheduler identification if a stronger causal
   attribution than the constrained behavioral result is required.
2. Repeat the experiment on a second machine or operating system before
   generalizing beyond this Apple Silicon host.
3. Keep these Java 24/25 results as external-validity evidence, separate from
   the primary Java 21 monitor-pinning result table.
