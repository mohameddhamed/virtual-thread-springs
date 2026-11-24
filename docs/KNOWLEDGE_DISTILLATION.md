# Knowledge Distillation: Java 21 Virtual Threads & Spring Boot Concurrency Ledger

**Document Classification:** Definitive Engineering & Empirical Research Ledger  
**Target Runtime:** OpenJDK 21 LTS (Azul Zulu 21.0.12 LTS / Linux & macOS arm64/x86_64)  
**Primary References:** [fact-check-jdk-runtime.md](fact-check-jdk-runtime.md), [fact-check-spring-ecosystem.md](fact-check-spring-ecosystem.md), [fact-check-methodology-performance.md](fact-check-methodology-performance.md), [evidence-freeze/claim-evidence-ledger.md](evidence-freeze/claim-evidence-ledger.md), [evidence-freeze/artifact-inventory-summary.md](evidence-freeze/artifact-inventory-summary.md)

---

## 1. Physical Testbed, Runtime Metadata, & Evidence Corpus

The empirical baseline across the research corpus was established on the following verified physical infrastructure:

| Component | Specification | Operational Invariant / Architectural Implication |
|---|---|---|
| **Host Architecture** | Apple Silicon M1 (arm64, 8 cores: 4 Firestorm Performance + 4 Icestorm Efficiency) | Darwin XNU QoS scheduler schedules carrier threads; container CPU quotas model bounded production carriers. |
| **Operating System** | macOS Darwin 24+ / Linux Containers (cgroups v1/v2) | CFS bandwidth quota $\le 1.0\text{ CPU}$ forces HotSpot to default to single-carrier parallelism (`parallelism=1`). |
| **Java Runtime** | OpenJDK 21 LTS (Azul Zulu 21.0.12+1-LTS, mixed mode, sharing) | JEP 444 GA. ObjectMonitor unmounting (JEP 491) is NOT backported. Virtual threads are daemon-immutable. |
| **Framework Baseline** | Spring Boot 3.5.12 (and 3.x baseline), Spring Framework 6.1.x / 6.2.x | Tomcat 10.1 `NioEndpoint` delegates `SocketProcessor` to virtual threads; Acceptor/Poller remain platform threads. |
| **Persistence & Pool** | HikariCP 5.1.0, PostgreSQL 16 (via Docker / `pgjdbc 42.6.0+`) | HikariCP connection handoffs use `SynchronousQueue`/`LockSupport.park()`. Unmounting moves front-end queues downstream. |
| **Load Injection** | k6 (closed-loop VU model, 10 VUs, 55 s profiles: 15s ramp, 30s hold, 10s ramp-down) | Closed-loop VUs self-throttle under high response times ($X = N/R$), preventing unbounded memory queue explosion. |

### 1.1 Epistemic Qualification Framework
Every empirical statement across the corpus is qualified by two dimensions ([claim-evidence-ledger.md](evidence-freeze/claim-evidence-ledger.md)):
1. **`[MEASURED]`**: Directly observed and quantified via instrumented telemetry or JFR event streams from valid physical executions.
2. **`[DERIVED]`**: Mathematically or statistically computed from measured data using formal queueing equations (Amdahl's law, Little's law, steady-state filtration).
3. **`[INTERPRETED]`**: Causal architectural explanations linking measured outcomes to HotSpot C++ mechanics, OS kernel behavior, or framework code.
4. **`[EXTERNALLY SUPPORTED]`**: Established by official OpenJDK JEPs, HotSpot source code, vendor specifications, or peer-reviewed literature.
5. **`[NOT ESTABLISHED]`**: Hypotheses or folk beliefs that empirical evidence refutes (e.g. carrier compensation for monitor pinning).

### 1.2 Partitioned Evidence Strata (125 Total Executions)
All experimental executions in the evidence repository are strictly partitioned into 8 non-overlapping strata ([artifact-inventory-summary.md](evidence-freeze/artifact-inventory-summary.md)):
- **Stratum 1 (12 executions)**: Java 21 Primary Synchronization Matrix (`parallelism=1` mechanism isolation).
- **Stratum 2 (10 executions)**: Java 24 & Java 25 Comparison Experiments (evaluating JEP 491 object monitor unmounting).
- **Stratum 3 (27 executions)**: Multi-JDK Native JNI Boundary Matrix (POSIX nanosleep & JFR blindspot verification).
- **Stratum 4 (18 executions)**: Architectural Diagnostic Controls (endpoint isolation and CPU quotas).
- **Stratum 5 (12 executions)**: Unconstrained 8-Carrier Historical Baseline Matrix.
- **Stratum 6 (27 executions)**: Exploratory, Pilot, and Standalone Diagnostic Executions.
- **Stratum 7 (13 executions)**: Excluded, Defective, or Construct-Flawed Executions (transparently cataloged in discrepancy register).
- **Stratum 8 (6 executions)**: Two-Treatment Factorial Relational Persistence Contention Ablation (HikariCP pool sizing under load).

---

## 2. Core Mathematical & Concurrency Laws

Theoretical reasoning across virtual threads must adhere strictly to formal queueing and concurrency laws, avoiding category errors:

### 2.1 Amdahl's Law & Saturation Throughput Ceiling
For any system where an operation requires a non-parallelizable critical section of duration $D_{critical}$ (or service demand $S$):
$$X_{max} \le \frac{1}{D_{critical}}$$
- **Application:** On an endpoint (e.g., `/payments`) with a 500 ms mutual-exclusion critical section ($D = 0.5\text{ s}$), maximum throughput is strictly capped at $\mu = 1 / 0.5 = 2.0\text{ req/s}$ regardless of whether carrier pinning is present or eliminated via `ReentrantLock`.
- **Pinning vs. Serialization:** Replacing `synchronized` with `ReentrantLock` unmounts virtual threads and frees the underlying carrier to execute independent workloads (e.g., `/products`), but **cannot** increase throughput on the serialized critical section itself.

### 2.2 Interactive Response Time Law (derived from Little's Law)
In a closed queueing network with population $N$ (active concurrent clients / virtual users) and think time $Z$:
$$R = \frac{N}{X} - Z \quad \implies \quad X = \frac{N}{R + Z}$$
- When think time $Z = 0$ (tight loop):
$$X = \frac{N}{R}$$
- **Self-Throttling Dynamics:** At $N = 10$ and $R \approx 5.0\text{ s}$ (10 clients serialized behind a 500 ms lock), throughput is identically $10 / 5.0 = 2.0\text{ req/s}$. Closed-loop arrival rates adapt dynamically to response time, bounded by $N$, preventing queue divergence.

### 2.3 Bernstein's Conditions (1966) vs. CALM Category Fallacy
Local single-process thread concurrency is governed by Bernstein's Conditions for deterministic, coordination-free parallel execution:
Two concurrent code blocks $I_1 \to O_1$ and $I_2 \to O_2$ can execute concurrently without synchronization if and only if:
$$I_1 \cap O_2 = \emptyset, \quad O_1 \cap I_2 = \emptyset, \quad O_1 \cap O_2 = \emptyset$$
- **Refutation of CALM Misuse:** The CALM theorem (Consistency As Logical Monotonicity, Hellerstein & Alvaro 2020) applies exclusively to distributed networks computing monotonic distributed programs without distributed coordination rounds (CRDTs/Paxos). Citing CALM for local JVM in-memory locks is a theoretical category error; local locking is governed strictly by Bernstein's Conditions and Amdahl's Law.

---

## 3. Verified Ecosystem Compatibility Matrix

Every entry below has been verified against official commit logs, issue trackers, and release notes:

| Library / Subsystem | Safe Version Boundary | Pinning / Hazard Mechanism | Verified Primary Source & Fix |
|---|---|---|---|
| **PostgreSQL JDBC** | **$\ge$ 42.6.0** | Socket reads inside `QueryExecutorImpl` synchronized on monitors prior to 42.6.0. | Issue [#1951](https://github.com/pgjdbc/pgjdbc/issues/1951), PR [#2629](https://github.com/pgjdbc/pgjdbc/pull/2629). Refactored to `ReentrantLock`. |
| **MySQL Connector/J** | **$\ge$ 9.0.0** | `NativeProtocol` / `MysqlIO` socket reads synchronized on monitors. **WARNING:** 8.4 LTS still pins carriers! | Bug [#109346](https://bugs.mysql.com/bug.php?id=109346), Bug [#110512](https://bugs.mysql.com/bug.php?id=110512). Merged exclusively into 9.0.0+. |
| **MariaDB Connector/J** | **$\ge$ 4.0.0** | SSL read locks and internal driver synchronization pinned carriers. | JIRA [CONJ-1367](https://mariadb.atlassian.net/browse/CONJ-1367) verified zero pinning via JFR tests in 4.0.0. |
| **SQLite JDBC** | **HAZARDOUS** | Native C downcalls via JNI (`_thread_in_native`) hold carrier threads captive with **0 JFR events**. | JNI boundary architecture; Issue [#1136](https://github.com/xerial/sqlite-jdbc/issues/1136). |
| **Apache HttpClient** | **$\ge$ 5.4.0** | `PoolingHttpClientConnectionManager.lease()` synchronized on `this.pool` throughout 5.3.x. | HttpClient 5.4.0 overhauled connection leasing with `ReentrantLock`. (5.3.x is unsafe!). |
| **Apache Commons Pool** | **UNREMEDIATED (2.12.x)** | `GenericObjectPool` retains synchronized monitors. PR #230 was **never merged** into 2.12.x. | Commons Pool 2 remains monitor-locked. DBCP2 and Jedis are hazardous; migrate to HikariCP. |
| **HikariCP** | **$\ge$ 4.0.0** (All modern) | In-memory handoffs sub-microsecond; connection acquisition parks cleanly via `SynchronousQueue`/`LockSupport`. | Issue [#1463](https://github.com/brettwooldridge/HikariCP/issues/1463), PR [#2055](https://github.com/brettwooldridge/HikariCP/pull/2055). No carrier pinning. |
| **Spring Boot Executable** | **Config Guidance** | `LaunchedClassLoader` / `JarUrlClassLoader` locks on nested jar entry reads during runtime reflection. | Issues **#51463** & **#50925**. Operational remedy: unpack fat JAR (`jar -xf`) in container images. |
| **Spring Framework Core** | **$\ge$ 6.1.1 / 6.2.6** | `ConcurrencyThrottleSupport` adapted to `ReentrantLock` (#32251); non-blocking limit rejection (#34727). | Issues [#32251](https://github.com/spring-projects/spring-framework/issues/32251), [#34727](https://github.com/spring-projects/spring-framework/issues/34727), [#30996](https://github.com/spring-projects/spring-framework/issues/30996) (`SseEmitter`). |
| **Logback** | **$\ge$ 1.3.15 / 1.4.15 / 1.5.0** | Synchronous stream appenders (`OutputStreamAppender`) pin carriers during disk/console writes. | Issue [#737](https://github.com/qos-ch/logback/issues/737). Mandates `AsyncAppender` for heavy logging. |
| **Log4j2** | **$\ge$ 2.21.0** | Synchronized locks in `RollingFileManager` and `OutputStreamManager`. | JBS/JIRA `LOG4J2-3622`, GitHub Issue [#1532](https://github.com/apache/logging-log4j2/issues/1532). |
| **OpenTelemetry Java** | **$\ge$ 1.32.1** | `WeakConcurrentHashMap` expunging in `VirtualField` held locks causing carrier stalls/deadlocks. | Issues [#9534](https://github.com/open-telemetry/opentelemetry-java-instrumentation/issues/9534) and [#10747](https://github.com/open-telemetry/opentelemetry-java-instrumentation/issues/10747). |
| **Jackson Core** | **$\ge$ 2.16.0** | Legacy `ThreadLocal<SoftReference<BufferRecycler>>` caused heap explosion under high virtual thread counts. | Issue [#1089](https://github.com/FasterXML/jackson-core/issues/1089). Added pluggable `JsonRecyclerPools.sharedLockFreePool()`. |
| **Micrometer** | **$\ge$ 1.12.0** | `ThreadMXBean` omits virtual threads; legacy dashboards blind to virtual thread surges. | Module `micrometer-java21` provides `VirtualThreadMetrics` tracking carrier and pinned metrics. |

---

## 4. HotSpot Runtime Invariants & Diagnostic Traps

### 4.1 Carrier Compensation Fallacy (JEP 444)
- **Fallacy:** HotSpot's `ForkJoinPool` scheduler expands carrier worker count to compensate for carrier threads pinned by `synchronized` or native execution up to `maxPoolSize`.
- **Runtime Fact:** [JEP 444](https://openjdk.org/jeps/444) explicitly specifies: *"The scheduler does not compensate for pinning by expanding its parallelism."* The JVM **never** spawns additional carrier threads to offset monitor pinning or JNI execution. Compensation is implemented strictly for `ForkJoinPool.ManagedBlocker` calls (file I/O, `CompletableFuture.get()`). Under `parallelism=1`, any monitor pin completely halts carrier execution for all virtual threads assigned to that scheduler.

### 4.2 JFR 20 ms Suppression & The "Zero Events" Construct Threat
- Both `default.jfc` and `profile.jfc` configure:
  ```xml
  <event name="jdk.VirtualThreadPinned">
    <setting name="threshold">20 ms</setting>
  </event>
  ```
- **Diagnostic Trap:** Pinning durations between $1\text{ ms}$ and $19.999\text{ ms}$ are silently discarded. A service experiencing 1,000 carrier pin events per second lasting 15 ms each will report **zero JFR pinned events** while experiencing 100% carrier saturation.
- **Remedy:** Diagnostic profiling must enforce `threshold=0ms` in custom `.jfc` profiles or pass `-Djdk.tracePinnedThreads=full`.

### 4.3 Silent Carrier Capture via Native Boundaries
- HotSpot emits `jdk.VirtualThreadPinned` inside `java.lang.VirtualThread.parkOnCarrierThread()` when unmounting fails.
- During native C execution (JNI downcalls, Panama foreign function calls, POSIX `getaddrinfo` DNS lookups), the carrier thread executes native machine instructions in state `_thread_in_native`. It never attempts to park or yield; continuation freeze is never invoked.
- **Diagnostic Trap:** Native operations capture carriers for multiple seconds while emitting **zero JFR events**.

### 4.4 `-Djdk.traceVirtualThreadLocals` Production Hazard
- The JVM flag `-Djdk.traceVirtualThreadLocals=true` triggers HotSpot to print a complete Java stack trace to `System.err` on every virtual thread write to a `ThreadLocal`.
- **Trap:** Under concurrent load, standard logging, security contexts, and database transactions flood stderr, causing catastrophic I/O contention and process hangs. It must be restricted strictly to single-threaded deterministic test suites.

### 4.5 `ThreadMXBean` Invisibility (CSR JDK-8303251)
- In OpenJDK 21, `ThreadMXBean.getAllThreadIds()`, `getThreadCount()`, and `getThreadCpuTime(id)` monitor platform threads only.
- Virtual threads are omitted by specification. APM dashboards monitoring JVM thread count flatline at platform thread count (~30–50 threads) even when 500,000 virtual threads are active.
- JVMTI `GetObjectMonitorUsage` was further degraded in JDK 23 (`JDK-8328083`) to return monitor data only for platform threads.

### 4.6 Virtual Thread Daemon Immutability & Graceful Shutdown
- By JEP 444 specification, virtual threads are permanently daemon threads. Invoking `thread.setDaemon(false)` throws `IllegalArgumentException`.
- When all platform threads exit (e.g., Spring Boot shutdown trigger), the JVM halts immediately, instantly terminating in-flight virtual threads without unwinding `try-finally` blocks or committing database transactions.
- **Requirement:** Spring Boot must configure `server.shutdown: graceful` with an explicit `spring.lifecycle.timeout-per-shutdown-phase` to allow virtual thread executors to drain.

### 4.7 JDK 21 LTS vs. JDK 24 (JEP 491) Immutability Boundary
- JEP 491 (*Synchronize Virtual Threads without Pinning*, JDK 24 GA) redesigned the HotSpot `ObjectMonitor` subsystem to allow unmounting inside `synchronized` blocks.
- **LTS Boundary:** Upstream OpenJDK `jdk21u-dev` maintenance rules strictly prohibit backporting invasive HotSpot VM architecture changes touching assembly lock stubs. Java 21 LTS will **never** receive JEP 491.
- Furthermore, diagnostic commands `jcmd <pid> Thread.vthread_scheduler` and `Thread.vthread_pollers` were introduced in JDK 24 (`JDK-8337199`) and fail with `Command not recognized` on Java 21 LTS.

---

## 5. Methodological Normalization & Queueing Ledger

1. **Closed-Loop vs. Open-Loop Benchmarking:**
   - Closed-loop generators (k6 standard scenarios, wrk, ab) limit concurrency to active Virtual Users ($N$). When response time rises ($R \uparrow$), arrival rate drops ($X = N/R$).
   - Coordinated Omission occurs when generators fail to record virtual requests queued behind slow responses, depressing percentile latency metrics.
2. **Measurement Window Rigor:**
   - Raw aggregations over total test duration (e.g. 55 s) include ramp-up and ramp-down transients. Rigorous steady-state reporting must isolate the stable measurement window ($[T_{ramp}, T_{hold}]$).
3. **Statistical Integrity on JVM:**
   - Three-trial executions ($N=3$) represent *qualitative mechanism-isolation engineering trials*, confirming discrete runtime phenomena (carrier exhaustion, lock barging, JFR emissions). They must not be conflated with inferential parametric confidence intervals on non-stationary JIT runtimes.
