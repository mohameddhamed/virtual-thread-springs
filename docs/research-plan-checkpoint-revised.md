# Detailed Research Plan — Checkpoint Version

**Programme:** MSc Computer Science
**Track:** Computer Science (Software Architecture)
**Student:** Hamed Mohamed (DG1EWF)
**Supervisor:** Gregory Reynolds Morse
**Title:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*

## Aim, scope, and gap

This empirical engineering study evaluates a controlled Spring Boot MVC application on **Java 21 LTS**. Virtual Threads are intended to improve the scalability of highly concurrent blocking workloads, not to make an individual request intrinsically faster (OpenJDK, 2023, JEP 444). Java 21 can pin a Virtual Thread when blocking occurs while it owns an intrinsic monitor; JEP 491 changes this behavior in JDK 24 (Pressler, 2024). Therefore the primary claims are explicitly Java-21-specific, and JDK 24+ is an external-validity boundary rather than an implicit generalization.

Recent work has examined Virtual Threads in framework integration, database-driven servers, Spring applications, reactive comparisons, and steady-state Java benchmarking (Beronić et al., 2021; Navarro et al., 2023; Lašić et al., 2024; Likus & Krużel, 2025; Charlak et al., 2026; Traini et al., 2022). The findings are not uniformly positive: framework integration and reactive execution can outperform a Virtual-Thread setup under particular resource constraints, while workload type and database backend materially affect outcomes. The remaining bounded gap is a reproducible Java 21 Spring MVC case study that combines a blocking intrinsic-monitor treatment, a lock-refactored treatment with correctness checks, endpoint-isolated and mixed workloads, and JFR stack attribution. The study does not claim to identify every legacy anti-pattern.

## Research questions and evidence map

| Question | Manipulation/construct | Evidence | Decision rule |
|---|---|---|---|
| **RQ1.** In Java 21 Spring MVC, how does intrinsic synchronization around blocking work affect throughput, latency, errors, and Virtual Thread pinning compared with platform threads and a compatible lock? | Execution mode: platform or Virtual Threads; payment lock: `synchronized` or `ReentrantLock` where feasible | k6 raw output; JFR `jdk.VirtualThreadPinned`; stack traces; CPU/GC; source commit | Call a difference pinning-related only if the application monitor is attributed in JFR, the refactoring removes that attribution, correctness is preserved, and the effect repeats under the frozen protocol |
| **RQ2.** In the demonstration application, how do (a) intrinsic synchronization around blocking work, (b) request-context handling with `ThreadLocal`, and (c) JDBC connection-pool saturation affect pinning, context correctness, and finite-resource contention under Java 21 Virtual Thread workloads? | Three named patterns only; no universal inventory claim | JFR for pinning; context cleanup/correctness tests; pool wait/saturation and timeout data; isolated endpoint runs | Classify each pattern as confirmed pinning source, resource/context risk, or not demonstrated; do not infer pinning from blocking or ThreadLocal presence alone |

## Artifact and experimental design

The application contains `/orders` (simulated 300 ms data-path blocking and request context), `/payments` (simulated 500 ms blocking call protected by the legacy synchronization treatment), and `/products` (clean control). H2 and simulated delays are deliberately synthetic; they support a mechanism case study, not a claim of production-scale database realism.

The core conditions are:

| Condition | Threads | Payment synchronization | Role |
|---|---|---|---|
| P-S | Platform | `synchronized` | Baseline |
| V-S | Virtual | `synchronized` | Java 21 naive migration |
| V-R | Virtual | `ReentrantLock` | Refactoring treatment |
| P-R | Platform | `ReentrantLock` | Optional fourth cell for factor separation |

The fourth cell is preferred if time permits but is not allowed to displace reproducible P-S, V-S, and V-R runs. A small Java 24/25 V-S boundary run is also preferred; if omitted, the thesis will state that monitor-pinning conclusions are limited to Java 21.

Primary causal measurements use isolated `/orders`, `/payments`, and `/products` scenarios. The existing mixed workload is retained as secondary system-level interference evidence. The load model, offered/achieved rate, stages, think time, timeout, dropped iterations, and endpoint order will be recorded explicitly. If overload and tail latency are central, a constant-arrival-rate scenario will be added; otherwise conclusions will remain limited to the closed model.

## Protocol and analysis

Each run records the Git commit, exact JDK/vendor/build, Spring Boot/Tomcat/HikariCP/H2/k6 versions, OS/CPU/memory, JVM flags, scheduler parallelism, pool and connector settings, workload model, JFR configuration, and SHA-256 hashes of raw outputs. Warm-up is discarded only after a pre-registered convergence/stability rule; its duration and iteration data are retained. Conditions are randomized or alternated in blocks to reduce thermal, JIT, and machine-order effects.

The experimental unit is an independent application process/run, not an individual correlated request. A pilot determines the final number of independent repetitions and precision target. Three historical runs, if that is all that can be traced, are exploratory and do not justify strong bootstrap inference. Final reports use run-level medians/IQR, throughput and latency effect sizes with uncertainty intervals, p95/p99 (not maximum-as-p99), errors/timeouts, and offered versus achieved throughput. A practical-effect threshold is fixed before final collection and is not treated as a target result.

JFR is recorded in two modes: a consistent low-overhead measurement configuration for all compared conditions, and a diagnostic configuration with stack traces and a documented `jdk.VirtualThreadPinned` threshold. The default/profile threshold is 20 ms; absence below that threshold is not evidence that shorter pins did not occur. Pinning counts and durations are therefore interpreted with the exact JDK and configuration.

Lock refactoring must pass endpoint-contract tests and concurrent mutual-exclusion tests before performance results are interpreted. JDBC waits, connection-pool saturation, and ThreadLocal lifecycle are reported as separate mechanisms. A historical value such as “−63% throughput” remains a preliminary pilot observation until it is mapped to raw files, a commit, and a manifest.

## Validity, feasibility, and output

Main threats are JIT/warm-up and thermal drift, closed-model self-throttling, mixed-endpoint interference, H2/synthetic-delay external validity, database-pool confounding, JFR threshold censoring, and semantic changes during lock replacement. Mitigations are isolated runs, fixed manifests, run-order blocking, explicit load-model reporting, pool telemetry, source-level correctness tests, and an evidence ledger. Unmapped or failed runs remain archived but are excluded using pre-specified rules.

The minimum viable outputs are: (1) revised bibliography and verified citation ledger; (2) frozen Java 21 protocol and run manifest; (3) traceable P-S, V-S, and V-R measurements; (4) JFR stack classification; (5) correctness tests; (6) bounded RQ answers and a migration checklist. PostgreSQL sensitivity, a full 2×2 matrix, and a JDK 24/25 boundary run are extensions. The final thesis will report the actual AI tools, purposes, affected locations, verification, and retained interaction log in the required ELTE declaration.

## Selected references

OpenJDK (2023), *JEP 444: Virtual Threads*, https://openjdk.org/jeps/444; Pressler (2024), *JEP 491*, https://openjdk.org/jeps/491; Beronić et al. (2021), DOI `10.23919/MIPRO52101.2021.9596855`; Navarro et al. (2023), DOI `10.1145/3583678.3596895`; Lašić et al. (2024), DOI `10.1109/MIPRO60963.2024.10569754`; Likus & Krużel (2025), DOI `10.7148/2025-0555`; Charlak et al. (2026), DOI `10.35784/jcsi.9409`; Traini et al. (2022), DOI `10.1007/s10664-022-10247-x`; Georges, Buytaert, & Eeckhout (2007), DOI `10.1145/1297027.1297033`; Kalibera & Jones (2013), DOI `10.1145/2555670.2464160`; Schroeder, Wierman, & Harchol-Balter (2006), USENIX NSDI.
