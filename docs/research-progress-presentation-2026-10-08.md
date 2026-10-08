# Research Progress Presentation — 8 October 2026

## 1. What I completed

- Reframed the study as a bounded Java 21 Spring MVC case study.
- Added a reproducibility manifest schema for benchmark runs.
- Added endpoint smoke tests for `/orders`, `/payments`, and `/products`.
- Added a concurrency test for the refactored payment lock.
- Preserved the distinction between correctness evidence and performance/pinning evidence.

## 2. Why this matters

The earlier benchmark files contained useful pilot observations, but a raw k6 or JFR file is not sufficient by itself. The result must also identify the source commit, Java/framework versions, machine, workload model, configuration, and validity status. The new manifest makes those dependencies explicit.

## 3. What the tests demonstrate

The smoke test verifies the endpoint contracts. The concurrency test releases four payment calls together and verifies that:

- every call completes;
- every order identifier is preserved;
- the critical section remains serialized after replacing intrinsic synchronization with `ReentrantLock`.

This prevents a performance improvement from being mistaken for a valid refactoring if behavior has changed.

## 4. What remains unclaimed

The tests do not prove that the refactored version is faster or that it eliminates pinning. Those claims require controlled Java 21 benchmark runs, JFR stack classification, endpoint-isolated workloads, and mapped raw artifacts.

Historical figures such as “63% throughput loss” and “97.5% pinning reduction” remain preliminary until they are connected to exact raw files and manifests.

## 5. Next progress step

Complete one benchmark pilot with the new manifest, record the exact JFR configuration and raw-output hashes, then compare the result with the existing historical observations. Any result that cannot be traced or reproduced will be reported as exploratory or removed from the definitive analysis.
