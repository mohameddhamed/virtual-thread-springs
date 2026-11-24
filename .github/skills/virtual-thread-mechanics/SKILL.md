---
name: virtual-thread-mechanics
description: "Diagnose, isolate, reproduce, and resolve Java 21 Virtual Thread runtime anomalies, carrier starvation, monitor pinning, native boundaries, and Spring Boot concurrency bottlenecks."
triggers:
  - virtual threads
  - Project Loom
  - carrier thread
  - carrier starvation
  - monitor pinning
  - jdk.VirtualThreadPinned
  - synchronized
  - ReentrantLock
  - ForkJoinPool
  - JEP 444
  - JEP 491
  - HikariCP
  - SQLTransientConnectionException
  - Amdahl's law
  - Little's law
  - Bernstein conditions
  - AQS tail dispersion
  - NonfairSync
  - FairSync
  - traceVirtualThreadLocals
  - ThreadMXBean
  - LaunchedClassLoader
---

# Virtual Thread Mechanics: Diagnostic, Reproduction, & Remediation Protocol

This skill provides an authoritative, fact-checked protocol for analyzing, reproducing, and fixing Java 21 LTS Virtual Thread runtime anomalies in enterprise Spring Boot and JVM applications.

---

## 4-Phase Diagnostic & Resolution Protocol

```
+-------------------------------------------------------------------------+
| Phase 1: Rapid Symptom Triage                                           |
| -> Map symptoms to root JVM mechanisms via references/symptom-to-mechanism-map.md |
| -> Check library version boundaries in references/invariant-ledger.md   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Phase 2: Invariant Check & Theoretical Bounds                           |
| -> Amdahl's Law ceiling: X_max <= 1 / D_critical                        |
| -> Little's Law / Interactive Response Time: X = N / R                  |
| -> Bernstein's Conditions vs CALM fallacy                               |
| -> HotSpot Invariants: JEP 444, JFR 20ms suppression, Native C capture   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Phase 3: Standalone Minimal Reproduction                                |
| -> Select/adapt from examples/:                                         |
|    * MinimalCarrierStarvation.java  (Monitor Pinning vs ReentrantLock)  |
|    * MinimalJniCarrierCapture.java  (Silent C nanosleep + JFR 0 events) |
|    * MinimalPoolQueueShift.java     (Front-end vs Downstream DB Pool)   |
|    * MinimalAqsTailDispersion.java  (AQS Direct-CAS Barging vs FIFO)    |
| -> Enforce single-carrier isolation (-Djdk.virtualThreadScheduler.parallelism=1) |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Phase 4: Surgical Remediation & Upstream Maintainer PR                  |
| -> Apply surgical diff (try-finally, ReentrantLock, Condition)          |
| -> Generate GitHub Issue/PR via references/maintainer-issue-template.md |
| -> Defend JDK 21 LTS backport necessity against JDK 24 objections       |
+-------------------------------------------------------------------------+
```

---

## Phase 1: Rapid Symptom Triage

When encountering unexpected latency spikes, carrier stalls, or connection timeouts under virtual threads:

1. **Consult the Symptom Map:** Read [references/symptom-to-mechanism-map.md](references/symptom-to-mechanism-map.md). Identify which of the 9 canonical symptoms matches the observed runtime behavior:
   - `SYM-01`: Monitor Pinning (`synchronized` on I/O or sleep)
   - `SYM-02`: Silent Native Carrier Capture (JNI / Panama / DNS `getaddrinfo` with 0 JFR events)
   - `SYM-03`: JFR 20ms Suppression (high-frequency microservice pinning hidden by default profile)
   - `SYM-04`: Serialization Bottleneck (Amdahl's law capping throughput despite `ReentrantLock`)
   - `SYM-05`: Downstream Pool Queue Shifting (`SQLTransientConnectionException` at HikariCP)
   - `SYM-06`: Tail Latency Dispersion (AQS `NonfairSync` direct-CAS barging)
   - `SYM-07`: Shutdown Evaporation (Daemon virtual threads destroyed without graceful shutdown)
   - `SYM-08`: Memory & GC Bloat (`ThreadLocal`, Jackson buffer recyclers, `StackChunk` heap allocation)
   - `SYM-09`: Cold-Start Stalls (Class loading & `<clinit>` monitor pinning)

2. **Verify Ecosystem Boundaries:** Consult the compatibility matrix in [references/invariant-ledger.md](references/invariant-ledger.md):
   - PostgreSQL JDBC: $\ge 42.6.0$ required
   - MySQL Connector/J: $\ge 9.0.0$ required (**8.4 LTS still pins on socket reads**)
   - Apache HttpClient 5: $\ge 5.4.0$ required (**5.3.x still pins**)
   - Apache Commons Pool 2: **Unremediated in 2.12.x**; migrate to HikariCP
   - Logback: $\ge 1.3.15$ / $1.4.15$ / $1.5.0$ or use `AsyncAppender`

---

## Phase 2: Invariant Check & Theoretical Bounds

Before proposing architectural refactorings, verify that expectations do not violate fundamental mathematical and HotSpot laws:

1. **Amdahl's Law Ceiling:**
   $$X_{max} \le \frac{1}{D_{critical}}$$
   If a synchronized method performs 500 ms of serialized state updates, replacing `synchronized` with `ReentrantLock` **will not increase throughput beyond 2.0 req/s**. It only frees the carrier to execute unrelated requests.
2. **Interactive Response Time Law:**
   $$X = \frac{N}{R}$$
   In closed-loop workloads (e.g. k6 VUs), throughput $X$ is bounded by client count $N$ and response time $R$.
3. **HotSpot Carrier Compensation Fallacy:**
   Under [JEP 444](https://openjdk.org/jeps/444), ForkJoinPool **never** expands carrier parallelism to compensate for `synchronized` pinning or native JNI execution. Under container cgroup quotas ($\le 1.0\text{ CPU}$), `parallelism=1`, meaning a single pin halts the JVM scheduler.
4. **JFR Diagnostic Blindspot:**
   Zero recorded events in standard JFR profiles does not prove absence of pinning (suppressed if $< 20\text{ ms}$) or carrier capture (JNI / DNS emit 0 events).

---

## Phase 3: Standalone Minimal Reproduction

Never file an upstream bug or alter production code without a deterministic, single-file reproduction.

Use or adapt the verified reproductions in [examples/](examples/):
- **Carrier Starvation & Unpinning:** [examples/MinimalCarrierStarvation.java](examples/MinimalCarrierStarvation.java)
- **Silent JNI Carrier Capture:** [examples/MinimalJniCarrierCapture.java](examples/MinimalJniCarrierCapture.java)
- **Downstream Pool Shifting:** [examples/MinimalPoolQueueShift.java](examples/MinimalPoolQueueShift.java)
- **AQS Barging vs Fair FIFO:** [examples/MinimalAqsTailDispersion.java](examples/MinimalAqsTailDispersion.java)

**Reproduction Guidelines:**
- Single self-contained `.java` file runnable via `java Foo.java`.
- Safe self-invoking single-carrier isolation:
  Enforce `-Djdk.virtualThreadScheduler.parallelism=1`, guarded by `-Drepro.forked=true` to prevent fork bombs.
- Deterministic gates (such as `lock.hasQueuedThread(thread)`) to eliminate timing races.
- Assertions that fail loudly if the mechanism is absent, and exit code 0 when verified.

---

## Phase 4: Surgical Remediation & Upstream PR

When delivering fixes for carrier pinning or concurrency bottlenecks:

1. **Adhere to Surgical Diff Rules:**
   - Follow patterns in [references/maintainer-issue-template.md](references/maintainer-issue-template.md).
   - Use `private final ReentrantLock lock = new ReentrantLock()`.
   - Wrap in strict `lock.lock(); try { ... } finally { lock.unlock(); }`.
   - Replace `wait()`/`notifyAll()` with `Condition.await()`/`Condition.signalAll()`.
   - Maintain 100% backward API compatibility; never add public dependencies.
2. **Document JFR Verification:**
   - Execute test suite with custom `.jfc` (`threshold=0ms`) or `-Djdk.tracePinnedThreads=full`.
   - Confirm 0 `jdk.VirtualThreadPinned` events.
3. **Defend JDK 21 LTS Backport:**
   - Use the 4-point defense in [references/maintainer-issue-template.md](references/maintainer-issue-template.md) to answer objections regarding JDK 24 / JEP 491.
4. **Distribution & Cross-Agent Installation:**
   - Install to Antigravity, Claude Code, GitHub Copilot, or Gemini using `scripts/install-skill.sh`.
