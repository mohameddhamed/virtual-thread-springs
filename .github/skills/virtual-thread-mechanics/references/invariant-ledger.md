# Invariant Ledger: Mathematical Laws, Ecosystem Matrix, & HotSpot Traps

**Target Runtime:** OpenJDK 21 LTS (Azul Zulu 21 / HotSpot)  
**Classification:** Definitive Verification Ledger for Java 21 Virtual Threads

---

## 1. Mathematical Laws of Concurrency & Capacity

### 1.1 Amdahl's Law Throughput Ceiling
For any service or endpoint where a portion of the request processing requires exclusive access to mutable state for duration $D_{critical}$:
$$X_{max} \le \frac{1}{D_{critical}}$$
- **Invariant:** No threading model—virtual threads, platform threads, or reactive coroutines—can exceed this throughput ceiling.
- **Empirical Proof:** An endpoint with $D_{critical} = 500\text{ ms}$ has a theoretical saturation capacity of exactly $\mu = 1 / 0.5 = 2.0\text{ req/s}$. Switching from `synchronized` to `ReentrantLock` eliminates carrier pinning, freeing the carrier thread for independent tasks, but leaves the endpoint throughput strictly capped at 2.0 req/s.

### 1.2 Interactive Response Time Law (derived from Little's Law)
In a closed queueing network with concurrency population $N$ and think time $Z$:
$$R = \frac{N}{X} - Z \quad \iff \quad X = \frac{N}{R + Z}$$
When think time $Z = 0$ (tight client loop):
$$X = \frac{N}{R}$$
- **Invariant:** When $N$ clients access a serialized resource with service demand $S$, response time scales as $R \approx N \times S$. Achieved throughput $X = N / (N \times S) = 1 / S$.
- **Closed-Loop Feedback:** Closed-loop client models (k6 virtual users, wrk, ab) self-throttle arrivals based on response time, capping queue depth to $N$ and preventing memory exhaustion.

### 1.3 Bernstein's Conditions for Local Concurrency
Two concurrent instructions $S_1$ and $S_2$ with input memory locations $I_i$ and output memory locations $O_i$ can execute concurrently without synchronization if and only if:
$$I_1 \cap O_2 = \emptyset \quad \land \quad O_1 \cap I_2 = \emptyset \quad \land \quad O_1 \cap O_2 = \emptyset$$
- **Category Rigor:** Local in-memory lock contention is governed strictly by Bernstein's Conditions and Amdahl's Law. (The CALM Theorem applies exclusively to distributed networks computing monotonic distributed logic without consensus rounds; applying CALM to local mutexes is a category fallacy).

---

## 2. Verified Ecosystem Compatibility Matrix

| Technology / Component | Verified Boundary | Invariant & Failure Mode | Source / Verification |
|---|---|---|---|
| **PostgreSQL (`pgjdbc`)** | **$\ge$ 42.6.0** | Socket reads in `QueryExecutorImpl` synchronized on monitors prior to 42.6.0, pinning carriers on every query. | Issue [#1951](https://github.com/pgjdbc/pgjdbc/issues/1951), PR [#2629](https://github.com/pgjdbc/pgjdbc/pull/2629). Refactored to `ReentrantLock`. |
| **MySQL Connector/J** | **$\ge$ 9.0.0** | `NativeProtocol` / `MysqlIO` socket reads synchronized on monitors. **WARNING:** 8.4 LTS still pins carriers! | Bug [#109346](https://bugs.mysql.com/bug.php?id=109346), Bug [#110512](https://bugs.mysql.com/bug.php?id=110512). Merged exclusively into 9.0.0+. |
| **MariaDB Connector/J** | **$\ge$ 4.0.0** | Driver internal synchronization and SSL pinned carriers. | JIRA [CONJ-1367](https://mariadb.atlassian.net/browse/CONJ-1367) verified zero pinning via JFR tests in 4.0.0. |
| **SQLite JDBC** | **HAZARDOUS** | Native C downcalls via JNI (`_thread_in_native`) capture carrier threads with **0 JFR events**. | JNI boundary architecture; Issue [#1136](https://github.com/xerial/sqlite-jdbc/issues/1136). |
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

## 3. HotSpot Runtime Diagnostic Traps & Invariants

1. **Carrier Compensation Fallacy (JEP 444):**
   - The scheduler does NOT expand carrier threads to compensate for `synchronized` or JNI pinning.
   - HotSpot carrier expansion is strictly reserved for `ForkJoinPool.ManagedBlocker` calls (POSIX file I/O).
   - Under container cgroup quotas ($\le 1.0\text{ CPU}$), `parallelism=1`. A single monitor pin completely freezes carrier scheduling for all virtual threads.

2. **JFR 20 ms Pinning Event Suppression:**
   - Default JFR profiles (`default.jfc`, `profile.jfc`) suppress `jdk.VirtualThreadPinned` events lasting $< 20\text{ ms}$.
   - High-frequency microsecond or sub-20ms pinning will show 0 events in production profiling.
   - Mandatory audit setting: custom `.jfc` with `threshold=0ms` or `-Djdk.tracePinnedThreads=full`.

3. **Silent Carrier Capture via Native Boundaries:**
   - In native C execution (`_thread_in_native`: JNI downcalls, Panama downcalls, POSIX `getaddrinfo` DNS lookups), `VirtualThread.park()` is never invoked.
   - Carrier threads are captured for multi-second durations with **0 JFR events emitted**.

4. **`-Djdk.traceVirtualThreadLocals` Operational Hazard:**
   - Passing `-Djdk.traceVirtualThreadLocals=true` prints a full Java stack trace to `System.err` on every `ThreadLocal.set()`.
   - In production or multi-threaded staging load tests, this causes catastrophic I/O lockups and CPU exhaustion. Restrict strictly to single-threaded unit tests.

5. **`ThreadMXBean` Invisibility (CSR JDK-8303251):**
   - In Java 21, `ThreadMXBean.getAllThreadIds()` and `getThreadCpuTime()` return platform threads only.
   - Traditional APM dashboards reporting thread count flatline at $\sim 30\text{ threads}$ during surges of 100,000+ virtual threads.

6. **Virtual Thread Daemon Immutability:**
   - Virtual threads are permanently daemon threads; `setDaemon(false)` throws `IllegalArgumentException`.
   - Without Spring Boot `server.shutdown=graceful` and a defined timeout phase, JVM shutdown instantly destroys in-flight virtual threads without executing `finally` blocks or rolling back transactions.

7. **JDK 21 LTS vs JDK 24 (JEP 491) Immutability:**
   - JEP 491 eliminates carrier pinning for `synchronized` in JDK 24 GA.
   - Upstream OpenJDK `jdk21u-dev` rules strictly forbid backporting JEP 491 to Java 21 LTS. Java 21 LTS systems permanently require `ReentrantLock` audits.
   - Diagnostic commands `jcmd <pid> Thread.vthread_scheduler` and `Thread.vthread_pollers` were introduced in JDK 24 (`JDK-8337199`) and fail on Java 21 LTS with `Command not recognized`.
