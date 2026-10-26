# Software Lab Baseline Measurements

**Planned date:** 22 October 2026  
**Submission status:** delayed progress artifact  
**Measurement date:** 15 October 2026  
**Project:** Spring Boot MVC and Java 21 Virtual Threads

## What was completed

The controlled `/payments` baseline was executed as an isolated, closed-loop
10-VU workload with a 500 ms simulated payment operation. The same application
artifact and protocol were used for:

1. Java 21 Virtual Threads with the legacy `synchronized` treatment;
2. platform threads with the same `synchronized` treatment.

Each condition was repeated at process level. The runner captured raw k6
JSONL output, a run manifest, process telemetry, and a Java Flight Recorder
recording. The Java 21 Virtual Thread runs used one scheduler carrier:

```text
-Djdk.virtualThreadScheduler.parallelism=1
-Djdk.virtualThreadScheduler.maxPoolSize=1
```

This is a mechanism-isolation stress condition, not a production deployment
recommendation.

## Selected observations

| Condition | Requests | p50 | p95 | JFR observation |
|---|---:|---:|---:|---|
| Virtual Threads + `synchronized` | 108 | 4,957 ms | 4,977 ms | 108 `jdk.VirtualThreadPinned` events |
| Platform threads + `synchronized` | 110 | 3,921 ms | 8,962 ms | Not applicable |

Both selected runs reported zero HTTP failures. The Virtual Thread recording
contains `jdk.VirtualThreadPinned` stack traces through
`PaymentService.simulatePaymentCall()` and `Thread.sleep`.

The result supports a narrow interpretation: in this Java 21 condition,
blocking inside the intrinsic monitor produced direct monitor-pinning evidence.
The platform control cannot emit Virtual Thread pinning events because it does
not execute requests on Virtual Threads. The closed-loop workload and
one-carrier scheduler mean these values are not universal capacity claims.

## Runtime and source identity

| Field | Value |
|---|---|
| Source revision used by the runs | `1ccb617b6beecb250e534d758d4f0eb1ea67e2d2` |
| Java | Azul Zulu 21.0.8 |
| Spring Boot | 3.5.12 |
| k6 | 1.7.1 |
| OS | macOS Darwin 25.2.0, Apple M1, 8 logical CPUs, 8 GB |
| Load model | Closed-loop, 10 VUs, 15 s ramp / 30 s hold / 10 s ramp-down |

## Evidence files

The following selected artifacts are included beside this note:

| Artifact | Purpose | SHA-256 |
|---|---|---|
| `results/run-10vus-20261015-142222.json` | Virtual Thread synchronized raw k6 output | `be6cfcc160b00cb3fe206e59380889514333f26bc110d92f3f8d92bab151ac57` |
| `results/run-manifest-20261015-142222.json` | Virtual Thread run identity and configuration | `a49ceb23e45a2df3737b7d8b0dabc6a1b427c3528faeda3000722a34261dcc46` |
| `results/jfr/recording-20261015-142222.jfr` | Selected JFR pinning recording | `0a8b65ddaf3218a463027862e419ccc16803626c6a6728d4f207d7e3c5718ab1` |
| `results/run-10vus-20261015-143422.json` | Platform synchronized raw k6 output | `77660ccd3bb42cc9b5da3d5ca0b2f671f073e63401baef83790b603876815109` |
| `results/run-manifest-20261015-143422.json` | Platform control identity and configuration | `c21add889e7a4242abcaa9f8fa8b97d743530798788113b72fe1f8f478266326` |
| `results/jfr/recording-20261015-143422.jfr` | Platform control JFR recording | `3d8df5eeb999bfaf28afb5b09a08c057497a96f5a081e61a27fcb67592aac40c` |

The complete three-trial matrix and its interpretation are documented in
`docs/research-iteration-2026-10-15-java21-primary-replication.md` and
`docs/research-iteration-2026-10-15-java21-primary-matrix.md`.
