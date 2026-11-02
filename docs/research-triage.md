# Research Triage Register: Java 21 Virtual Threads & Spring Boot MVC Migration

**Document Identity:** Research Scout Triage, Methodological Audit & Fact-Check Reconciliation  
**Target Thesis:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
**Author Role:** Research Triage Analyst  
**Date:** 2 November 2026 (Updated with Fact-Check Reconciliation)  
**Target Skeleton:** `docs/thesis-draft-skeleton.md`  
**Source Document:** `docs/virtual-threads-research-scout-report.md`  
**Audited Fact-Check Reports:**  
- `docs/fact-check-jdk-runtime.md` (Domain A: Runtime Behavior & HotSpot Diagnostics)  
- `docs/fact-check-methodology-performance.md` (Domain B: Benchmarking Methodology & Queueing Theory)  
- `docs/fact-check-spring-ecosystem.md` (Domain C: Spring Boot, Database Access & Ecosystem)  
**Primary Runtime:** OpenJDK 21 LTS  
**Primary Artifact:** Spring Boot MVC Demonstration Application (`src/main/java/com/thesis/virtualthreadsdemo/`)

---

## 1. Executive Summary

This triage register audits, consolidates, and critically evaluates the findings, claims, and literature discoveries presented in the *Virtual Threads Research Scout Report* (`docs/virtual-threads-research-scout-report.md`), incorporating the independent findings from three technical fact-checking audits (`docs/fact-check-*.md`). The primary objective is to filter actionable, scientifically rigorous findings into the existing MSc thesis draft skeleton (`docs/thesis-draft-skeleton.md`) while strictly guarding against scope creep, unverified claims, and methodological errors.

The MSc thesis is an empirical engineering and systems study investigating the architectural risks, synchronization mechanics, and migration guidelines when moving Spring Boot MVC applications to Java 21 Virtual Threads. Its existing research questions focus on:
1. **RQ1:** How monitor pinning, critical-section serialization, and primitive refactorings (`synchronized` vs. `ReentrantLock` vs. platform threads) govern application throughput and carrier utilization.
2. **RQ2:** The broader architectural risks (finite resource waiting, `ThreadLocal` lifecycle, native/JNI boundaries, logging, database drivers) that must be audited before enabling Virtual Threads in Spring Boot MVC systems.

### Key Triage Takeaways (Post Fact-Check Reconciliation):

1. **Experimental Validity & JVM Mechanics (P0 — CHK-JDK-01):**  
   The scout report's claim that HotSpot's ForkJoinPool expands carrier parallelism to compensate for monitor pinning was **conclusively contradicted by JEP 444**. HotSpot never compensates for monitor pinning or native code. Carrier expansion is reserved exclusively for `ManagedBlocker` (file I/O, `Object.wait()`). The experimental configuration (`parallelism=1, maxPoolSize=1`) is an intentional, worst-case core-count isolation control—isomorphic to cgroup CPU truncation in 1-CPU Kubernetes containers (`resources.limits.cpu: 1000m`)—not a compensation bypass.

2. **Queueing Model & Capacity Ceiling (P0 — METH-01):**  
   The claim that the 2.0 req/s throughput floor on `/payments` is an "artificial generator self-throttling illusion" was **mathematically contradicted** via asymptotic queueing bounds ([Denning & Buzen 1978](https://doi.org/10.1145/356744.356747)). An exclusive 500 ms critical section imposes an absolute theoretical saturation ceiling of $\mu = 1 / D = 2.0\text{ req/s}$ across *both* open and closed systems. The closed-loop model ($N=10$, $R\approx 5000\text{ ms}$) caps queue length and forces arrival rate to match completion rate; it does not depress capacity.

3. **Normalization Pipeline Window Inconsistency (P0 — METH-05):**  
   While run manifests assert that the 15 s warm-up ramp is excluded from steady-state calculations, `scripts/normalize_evidence.py` aggregates all lines from $t=0$ to $t=55\text{s}$. Reported metrics reflect the entire 55-second run window ($108 / 55\text{s} \approx 1.96\text{ req/s}$), which must be clarified in the thesis methodology.

4. **Silent Carrier Monopolization & JFR Thresholds (P0 — CHK-JDK-02, CHK-JDK-03):**  
   Native C execution (`_thread_in_native` via JNI, Panama downcalls, POSIX `getaddrinfo` DNS) captures carrier threads completely while emitting **zero JFR `jdk.VirtualThreadPinned` events** because native execution never enters `VirtualThread.park()` / `freeze()`. Furthermore, default JFR configurations (`default.jfc`) suppress pinning events lasting $< 20\text{ ms}$. Zero recorded events does not prove carrier freedom.

5. **Exposing Section 12 Artifact & PR Hallucinations (FC-08 to FC-22):**  
   Over 60% of the specific GitHub issues, PR numbers, and commit hashes cited in Section 12 of the scout report were fabricated or misattributed (e.g., Commons Pool `POOL-415`, Spring Boot `#38841`, Spring Framework `#31215`, RestClient `#32001`, HttpClient `HTTPCLIENT-2311`, Agroal `AG-315`). Genuine tickets have been verified and substituted.

6. **Critical Version Boundary Adjustments (P1 — FC-02, FC-20):**  
   - **MySQL Connector/J 8.4 LTS still pins carriers** on socket reads; safe execution requires Connector/J $\ge 9.0.0$.
   - **Apache HttpClient 5.3.x still synchronizes** on connection pool leases; safe execution requires HttpClient $\ge 5.4.0+$.
   - **Apache Commons Pool 2 remains monitor-synchronized**; Loom PR #230 was never merged in 2.12.x.

---

## 2. Triage Methodology & Problem Taxonomy

### 2.1 Priority Classification Rules

- **P0 (Critical / Experimental Validity):**
  Discoveries that challenge, invalidate, or fundamentally clarify experimental results, measurement infrastructure, causal interpretation of data, or research question answers. *Action: Mandatory integration or factual correction in thesis.*
- **P1 (High / Architectural Risks & Guidelines):**
  Discoveries directly relevant to the architectural risks of migrating Spring Boot MVC systems to Java 21, including driver compatibility matrices, context propagation, connection pooling, and refactoring guidelines. *Action: Integrate into Chapter 6 (Analysis) and Chapter 7 (Migration Guidance).*
- **P2 (Medium / Background & Related Work):**
  Authoritative historical rationale, formal queueing/synchronization theory, and conceptual runtime comparisons that enrich Chapters 1, 2, and 3 without introducing new experimental obligations. *Action: Integrate into background, literature review, and discussion.*
- **P3 (Low / Peripheral / Excluded Scope):**
  Findings outside the primary scope of Java 21 Spring Boot MVC systems, requiring external hardware/privileges (energy measurement), or representing alternative programming models. *Action: Exclude from core empirical chapters; mention only in limitations/future work or omit entirely.*

### 2.2 Thesis Skeleton Impact Taxonomy

Every triaged cluster is mapped to one or more of six structural impact actions:
1. **Requires a factual correction:** Corrects an erroneous or conflated claim currently in the thesis draft or scout report notes.
2. **Requires a structural change:** Adds or reorganizes subsections within the existing draft skeleton.
3. **Adds supporting literature:** Provides authoritative academic, JEP, or primary-source citations.
4. **Requires additional experimental evidence:** Identifies an unverified empirical hypothesis that would require new benchmarking runs to substantiate.
5. **Belongs in limitations/future work:** Relevant insight that is deliberately bounded outside the current experimental package.
6. **Should be excluded:** Out of scope, speculative, or irrelevant to the thesis research questions.

---

## 3. Consolidated Findings Register

The register below consolidates all distinct findings from the research scout report into 25 mechanism and topic clusters. Status entries have been updated following reconciliation with the three independent fact-check reports.

| ID | Finding / mechanism | Scout report reference | Relevant evidence/source | Priority | Affected thesis section | Why it matters | Required next action | Reconciled Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CL-01** | **ForkJoinPool Carrier Compensation vs. Pinning Stalls**<br>HotSpot *never* compensates for monitor pinning; compensation is strictly for `ManagedBlocker` (file I/O, `Object.wait()`). `maxPoolSize=1` disables file compensation, while `parallelism=1` models 1-CPU container quotas. | Finding 9.1,<br>Finding 11.3,<br>Finding 2.1.2,<br>Finding 5.4.1 | JEP 444; JBS `JDK-8334304`; HotSpot `forkJoinPool.c`; Linux cgroup quota specs | **P0** | Section 2.2,<br>Section 2.3,<br>Section 3.9,<br>Section 3.14,<br>Section 5.3 | Corrects a major internal contradiction in early drafts. Confirms `parallelism=1` is an intentional core-count stress test matching 1-CPU Kubernetes containers, not a compensation bypass. | Factual correction in Section 2.3, 3.9, and 5.3. Explain carrier compensation scope accurately. | **Factual Correction Verified**<br>(CHK-JDK-01, METH-09) |
| **CL-02** | **JFR 20 ms Default Event Filtering Threshold**<br>The default JFR recording template (`default.jfc`) suppresses `jdk.VirtualThreadPinned` events lasting < 20 ms, masking high-frequency pinning in microservices. | Finding 11.2.A.4,<br>Finding 11.6.5,<br>Finding 12.3.3 | OpenJDK `default.jfc` source; JFR Event Settings Specification | **P0** | Section 2.9,<br>Section 3.10,<br>Section 3.14,<br>Section 5.15,<br>Section 7.5 | If benchmark runs used default JFR profiles without `threshold=0ms`, pinning events between 1–19 ms were silently omitted, creating false-negative zero-event results. | Audit `run-benchmark.sh` and manifests in `results/`. Document threshold as measurement threat in 3.14; mandate `threshold=0ms` in 7.5. | **Supported — Construct Threat**<br>(CHK-JDK-02, METH-12) |
| **CL-03** | **Closed-Loop Load Dynamics & Theoretical Capacity Ceiling**<br>An exclusive 500 ms critical section enforces an absolute saturation capacity ceiling of $\mu = 1/D = 2.0\text{ req/s}$ ([Denning & Buzen 1978](https://doi.org/10.1145/356744.356747)). Closed-loop load ($N=10$, $Z=0$) caps queue length and forces $R = N/\mu = 5.0\text{ s}$; it does not depress capacity. | Finding 5.1.1,<br>Finding 10.8,<br>Finding 11.6.5 | Denning & Buzen (1978); Lazowska et al. (1984); Schroeder et al. (NSDI 2006); Gil Tene (Coordinated Omission) | **P0** | Section 2.10,<br>Section 2.10.1,<br>Section 3.8,<br>Section 3.8.1,<br>Section 6.2,<br>Section 8.5 | Mathematical correction: 2 req/s is the server's saturation capacity ceiling, not an artificial generator illusion. Closed-loop load prevents unbounded queue explosion. | Formalize asymptotic bound ($X_{max}=1/D$) and Interactive Response Time Law ($X=N/R$) in 2.10.1 and 6.2. | **Contradiction Corrected**<br>(METH-01, METH-02) |
| **CL-04** | **Native Execution Carrier Occupation vs. Zero JFR Events**<br>Long native calls (JNI `nanosleep`, Panama downcalls, POSIX `getaddrinfo` DNS) capture carrier threads but emit zero `jdk.VirtualThreadPinned` events because `freeze()` is never called. | Finding 10.1,<br>Finding 11.2.A.1,<br>Finding 11.2.B.2,<br>Section 7.1,<br>Discovery 7 | HotSpot `continuationFreezeThaw.cpp`; JEP 418 (JDK-8263110); JEP 454; xerial issue #1136 | **P0** | Section 2.8,<br>Section 3.5,<br>Section 4.5,<br>Section 5.10,<br>Section 6.3,<br>Section 6.4,<br>Section 7.2 | Solves empirical anomaly of `/native` (108 requests, multi-second stalls, 0 JFR events across 27 runs). Proves zero JFR events does not imply carrier freedom. | Structural addition to Section 2.8 and 5.10 explaining HotSpot C++ event emission mechanics. Add DNS audit to Section 7.2. | **Supported — Mechanistic Attribution**<br>(CHK-JDK-03, METH-13) |
| **CL-05** | **Statistical Rigor & Process Replication Limitations**<br>A sample size of 3 process trials cannot support inferential confidence intervals or normality assumptions on the non-stationary JVM. | Finding 5.2.1 | Georges et al. (OOPSLA 2007); Kalibera & Jones (ISMM 2013) | **P0** | Section 3.12,<br>Section 3.13,<br>Section 3.14,<br>Section 5.1,<br>Section 8.5 | Prevents methodological rejection by thesis examiners. Justifies 3 trials as qualitative mechanism-isolation engineering units rather than population statistics. | Frame 3-trial dataset as mechanism-isolation trials in Section 3.12. Report dispersion (min/max/IQR) instead of confidence intervals. | **Supported — Methodological Framing**<br>(METH-04) |
| **CL-06** | **Hardware & Virtualization Confounders (macOS & Docker)**<br>Apple Silicon P/E-core QoS thread scheduling and Docker Desktop macOS VM network proxying (`vpnkit`) add 1.5–3.5 ms non-deterministic jitter and latency skew. | Finding 5.3.1,<br>Finding 5.3.2,<br>Finding 9.9 | Howard Oakley (eclecticlight.co 2023–2024); Docker Desktop macOS networking architecture | **P0** | Section 3.9,<br>Section 3.14,<br>Section 4.4,<br>Section 5.11,<br>Section 8.5 | Explains baseline latency differences between local H2 (~304 ms) and Dockerized PostgreSQL (~310 ms). Validates separating H2 and PostgreSQL tracks. | Document Apple Silicon core asymmetry and Docker VM proxying as threats to internal validity in 3.14 and 8.5. | **Supported — Validity Threat**<br>(METH-10, METH-11) |
| **CL-07** | **Mixed Synchronization Starvation Deadlocks**<br>Mixing `synchronized` and `ReentrantLock` in interdependent call paths creates circular carrier starvation deadlocks under carrier-constrained configurations. | Finding 2.1.1,<br>Finding 9.6,<br>Finding 11.3 | JBS `JDK-8305069`; Lorin Hochstein (TLA+ Model, Surfing Complexity 2024) | **P1** | Section 2.3,<br>Section 3.1,<br>Section 6.2,<br>Section 7.4 | Warns against partial or piecemeal lock refactoring: replacing some locks with `ReentrantLock` while leaving others intact can induce complete scheduler deadlocks. | Add architectural warning to Section 6.2 and 7.4. Cite Hochstein's TLA+ formal specification in Section 3.1 and 6.2. | **Partially Supported — Qualified**<br>(CHK-JDK-06) |
| **CL-08** | **Database Driver & Pool Pinning / Interruption Vulnerabilities**<br>Legacy drivers (`pgjdbc < 42.6.0`, `mysql < 9.0.0`) pin carriers on socket reads. Modern pools (HikariCP) unmount cleanly via `LockSupport.park()`. MySQL 8.4 LTS still pins. Commons Pool 2 PR #230 was never merged in 2.12.x. | Finding 3.1.1,<br>Finding 11.2.A.2,<br>Finding 3.3.1,<br>Finding 10.7,<br>Discoveries 5, 6, 9, 16 | pgjdbc PR #2629; MySQL Bug #109346; MariaDB CONJ-1367; HikariCP PR #2055; Oracle Sip #94; Commons Pool PR #230 | **P1** | Section 2.5,<br>Section 2.6,<br>Section 4.4,<br>Section 5.11,<br>Section 5.12,<br>Section 6.3,<br>Section 7.2,<br>Section 7.4 | Explains why database calls appear to pin carriers (driver-level synchronized blocks) vs pool capacity exhaustion (`SQLTransientConnectionException`). Proves layering semaphores is an anti-pattern. | Build driver/pool minimum version matrix in Section 7.2 (MySQL $\ge 9.0.0$, MariaDB $\ge 4.0.0$). Distinguish driver pinning from pool waiting in 2.6 and 5.11. | **Supported with Version Updates**<br>(FC-01, FC-02, FC-05, FC-08) |
| **CL-09** | **ORM & Serialization Bottlenecks (Jackson & Hibernate)**<br>Jackson `< 2.16` buffer recyclers allocate heavy `ThreadLocal` arrays driving heap bloat. Hibernate `6.2–6.4.0` sequence optimizers pin carriers during batch ID allocation. | Finding 9.2,<br>Discovery 8,<br>Section 7.3 | FasterXML Jackson Core #1089; Hibernate ORM Issue `HHH-17482` / Commit `7e14a8b` | **P1** | Section 2.5,<br>Section 2.7,<br>Section 4.1,<br>Section 4.3,<br>Section 6.3,<br>Section 7.2 | Identifies non-pinning memory bloat in Jackson JSON mapping and carrier pinning during entity pre-allocation. Resolves scout report contradiction regarding Hibernate pinning. | Add Jackson `JsonRecyclerPools.sharedLockFreePool()` and Hibernate $\ge 6.4.2$ to migration inventory in Section 7.2 and 6.3. | **Supported**<br>(FC-18, HHH-17482) |
| **CL-10** | **Spring Context Propagation & ThreadLocal Lifecycle**<br>`SecurityContextHolder`, `TransactionSynchronizationManager`, and MDC drop context across virtual thread dispatch. `MODE_INHERITABLETHREADLOCAL` causes severe heap churn under high concurrency. | Sections 4.1–4.4,<br>Finding 10.5,<br>Finding 11.3 | Spring Security #19259; Spring Framework `TransactionSynchronizationManager`; `io.micrometer:context-propagation`; JEP 444 | **P1** | Section 2.7,<br>Section 4.3,<br>Section 6.3,<br>Section 7.2,<br>Section 7.4 | Virtual threads do not propagate ThreadLocals across async dispatch, risking security context loss and transaction detachment. Tracing via `-Djdk.traceVirtualThreadLocals` incurs severe I/O overhead. | Document `TaskDecorator` and `ContextSnapshot` in Section 4.3 and 7.4. Warn against production use of trace flag in Section 7.5. | **Supported**<br>(FC-17, FC-26, CHK-JDK-12) |
| **CL-11** | **HTTP Client & Microservice Transport Contention**<br>Apache HttpClient 5 requires $\ge 5.4.0$ for `ReentrantLock` pool handoffs (5.3.x still pins). OkHttp virtual thread support landed in 5.0.0-alpha.12+. Spring RestClient ThreadLocal leak claim was unverified. | Discoveries 1, 10, 11, 12 | Apache HttpClient 5.4.0 Release Notes; OkHttp 5.0.0-alpha.12; Spring Framework #32001 audit | **P2**<br>*(Revised from P1)* | Section 2.7,<br>Section 3.6,<br>Section 6.3,<br>Section 7.2 | Outbound HTTP client concerns are peripheral to the thesis's inbound Spring MVC testbed. Safe HttpClient version is 5.4.0+, not 5.3.1. RestClient leak claim purged. | Update migration matrix in 7.2 with safe client versions (HttpClient $\ge 5.4.0$). Relegate outbound clients to general engineering context. | **Corrected & Re-prioritized (P2)**<br>(FC-15, FC-20, FC-21) |
| **CL-12** | **Unbounded Task Spawning & The "Threads are Cheap" Fallacy**<br>Spring 6.1 `SimpleAsyncTaskExecutor` rate-limiting was refactored in #32251 / #34727. Tomcat TCP connection handling remains bounded by OS platform socket limits. | Discovery 4,<br>Finding 3.2.1,<br>Warski Talk (6.1.1),<br>Section 12.3.1 | Spring Framework #32251, #34727; Apache Tomcat 10.1 documentation; Warski (Devoxx 2024/2025) | **P1** | Section 2.1,<br>Section 3.4,<br>Section 3.6,<br>Section 6.3,<br>Section 7.3,<br>Section 7.4 | Disproves the belief that virtual threads allow unlimited concurrent work. Explicit rate limiting (e.g. `Semaphore`) and OS backlog constraints are mandatory. | Document Tomcat platform socket limits in Section 3.4. Include concurrency limiting guidelines (`setConcurrencyLimit`) in Section 6.3 and 7.3. | **Supported with Ticket Updates**<br>(FC-11, FC-14) |
| **CL-13** | **Servlet Container Direct Memory Leaks & Platform Boundaries**<br>Undertow thread-local pooling of direct buffers is a recognized hazard under virtual threads. Netty default allocator already sets `useCacheForAllThreads=false`. | Discovery 3,<br>Finding 3.2.1,<br>Finding 11.2.B.3 | Undertow direct memory pooling; Netty Issue #13191 | **P2**<br>*(Revised from P1)* | Section 2.6,<br>Section 3.4,<br>Section 6.3,<br>Section 7.2 | The thesis artifact runs on Apache Tomcat; Undertow and Netty buffer pooling are alternative container considerations. Netty `false` is already default. | Retain as container selection guidance in 7.2; purge hallucinated PR #1612 citation. | **Qualified & Re-prioritized (P2)**<br>(FC-12, FC-19) |
| **CL-14** | **Observability Tooling Invalidation & Observer Effect**<br>`ThreadMXBean` silently omits virtual threads (-1 CPU time). JVMTI thread tracking causes global lock contention on `JvmtiThreadState_lock`. OpenTelemetry $\le 1.32$ pinned carriers via `WeakConcurrentHashMap`. | Finding 11.2.A.3,<br>Finding 11.2.A.5,<br>Finding 11.2.A.6,<br>Finding 2.2.1,<br>Finding 11.2.B.4,<br>Discovery 17,<br>Finding 3.5.2 | JBS `JDK-8303251`; OpenTelemetry PR #10747; async-profiler #779; JBS `JDK-8328083`; Eclipse Bugzilla 582190; Micrometer docs | **P1** | Section 2.9,<br>Section 3.10,<br>Section 4.6,<br>Section 6.3,<br>Section 7.5 | Standard APM dashboards flatline at ~30 threads during overload. Profilers attaching via JVMTI serialize carriers. JFR and Micrometer 1.12+ are the only zero-lock observability tools. | Detail observability failure modes in Section 2.9 and 7.5. Explain why external JVMTI profilers were excluded from benchmark harness in Section 4.6. | **Supported with Ticket Updates**<br>(CHK-JDK-13, CHK-JDK-15, FC-24, FC-25) |
| **CL-15** | **Logging Framework Carrier Pinning (Logback & Log4j2)**<br>Standard synchronous console and file appenders (`OutputStreamAppender`) synchronize stream writes, pinning carrier threads under high concurrent logging. | Finding 3.4.1 | Logback Issue #737; Log4j2 Issue `LOG4J2-3622` / PR #1532 | **P1** | Section 2.5,<br>Section 6.3,<br>Section 7.2,<br>Section 8.4 | Logging I/O inside synchronized blocks causes massive carrier thread starvation during error spikes or debug logging. | Mandate asynchronous appenders (`AsyncAppender`) or logback-classic $\ge 1.3.15$ in Pre-Migration Inventory (Section 7.2) and 6.3. | **Supported with Ticket Updates**<br>(CHK-JDK-24, FC-23) |
| **CL-16** | **Daemon Thread Immutability & Shutdown Evaporation**<br>Virtual threads are permanently daemon threads (`Thread.setDaemon(false)` throws `IllegalArgumentException`). On JVM shutdown, active virtual threads terminate immediately without completing transactions. | Finding 11.2.A.7 | OpenJDK JEP 444 specification | **P1** | Section 2.2,<br>Section 6.3,<br>Section 7.4 | In-flight HTTP requests and database transactions evaporate mid-flight during container restarts unless graceful shutdown is explicitly configured. | Add graceful shutdown configuration (`server.shutdown: graceful` with bounded await timeout) to Section 6.3 and 7.4. | **Supported**<br>(CHK-JDK-16, FC-27) |
| **CL-17** | **Packaging & ClassLoader Pinning (Fat JARs & `<clinit>`)**<br>Spring Boot `LaunchedClassLoader` zip entries pinned carriers under virtual threads (tracked under #51463, #50925). Static class initializers (`<clinit>`) permanently pin carriers across ALL JDKs (including JDK 24+). | Discovery 2,<br>Finding 10.3,<br>Parlog Talk (6.1.3) | Spring Boot Issues #51463, #50925; JEP 491 CSR `JDK-8338813`; OpenJDK `JDK-8369238` | **P1** | Section 2.4,<br>Section 3.8,<br>Section 5.1,<br>Section 6.3,<br>Section 6.4,<br>Section 7.4 | Explains why cold-start benchmarks on Docker fat JARs show carrier stalls absent in unpacked IDE runs. Confirms classloader pinning persists beyond JEP 491. | Recommend packaging Spring Boot as unpacked/exploded jars (`jar -xf`) in Docker containers. Document `<clinit>` in 2.4 and 6.4. | **Supported with Real Tickets**<br>(CHK-JDK-17, FC-13) |
| **CL-18** | **OS File I/O Kernel Asymmetry & Messaging Pinning**<br>Standard POSIX file I/O has no non-blocking readiness mechanism in Linux/macOS; file calls block carrier threads synchronously. Root cause of dotCMS migration reversion and ActiveMQ KahaDB log pinning. | Finding 9.3,<br>Finding 10.2,<br>Discovery 13 | OpenJDK HotSpot `FileChannelImpl.c`; dotCMS PR #36900; ActiveMQ PR #1162 | **P1** | Section 2.6,<br>Section 6.3,<br>Section 7.2,<br>Section 8.4 | Refutes the assumption that all Java I/O unmounts cleanly on Java 21. Real-world teams have reverted virtual threads due to disk-backed cache/persistence stalls. | Document socket vs file descriptor asymmetry in Section 2.6 and 6.3. Cite dotCMS rollback as real-world industrial evidence in Section 1.3 and 8.4. | **Supported**<br>(CHK-JDK-18, CHK-JDK-19) |
| **CL-19** | **JDK Evolution Timeline & Permanent Java 21 LTS Pinning Boundary**<br>JEP 491 (JDK 24) is strictly ineligible for backporting to Java 21 LTS (`jdk21u-dev`). `jcmd Thread.vthread_scheduler` exists only in JDK 24+. Scoped Values finalize in JDK 25 LTS. | Finding 2.1.4,<br>Finding 9.8,<br>Section 2.2 Table,<br>Finding 10.4,<br>Finding 11.3 | JEP 444; JEP 491; JEP 506; `jdk21u-dev` policies; JBS `JDK-8337199` | **P1** | Section 1.3,<br>Section 2.4,<br>Section 5.13,<br>Section 6.4,<br>Section 8.2 | Confirms the enduring thesis justification: Java 21 LTS will NEVER receive JEP 491. Enterprise Spring Boot systems on Java 21 permanently require the audit and refactoring guidelines developed here. | Formalize LTS non-backporting in Section 1.3 and 2.4. Remove `jcmd` scheduler commands from Java 21 checklists; keep JDK 24 in Section 5.13. | **Supported**<br>(CHK-JDK-09, CHK-JDK-10, CHK-JDK-11) |
| **CL-20** | **Concurrency Testing & CI Pinning Regression Verification**<br>`jcstress` tests hardware memory models, not M:N scheduling. Lincheck misses continuation yields. `loom-unit` (@ShouldNotPin) provides automated CI assertion of zero pinning in Maven builds. | Finding 9.5,<br>Finding 9.4,<br>Discovery 14,<br>Finding 5.6.1 | Clément Escoffier (`loom-unit`); CMU `Fray` (arXiv:2408.06579); Lincheck Issue #214; `jcstress` docs | **P1** | Section 3.10,<br>Section 4.7,<br>Section 6.1,<br>Section 7.5,<br>Section 8.7 | Solves the CI enforcement gap: migration guidelines need not rely solely on post-hoc k6/JFR runs. Unit tests can assert zero pinning in continuous integration. | Integrate `loom-unit` pattern into Section 4.7 and 7.5. Cite Fray, Lincheck, and jcstress as testing methodology context in Section 4.7 and 8.7. | **Supported** |
| **CL-21** | **Authoritative Synchronization Theory & Historical Context**<br>Single-node mutex serialization is governed by [Bernstein's Conditions (1966)](https://doi.org/10.1109/PGEC.1966.264565) and [Amdahl's Law (1967)](https://doi.org/10.1145/1465482.1465560), NOT the CALM Theorem. Brian Goetz (2004) documents `ReentrantLock` design history. | Finding 10.6,<br>Finding 10.9,<br>Finding 11.2.C.4,<br>Finding 2.1.3 | Bernstein (1966); Amdahl (1967); Brian Goetz (IBM developerWorks 2004); Dice & Kogan (PPoPP 2026); JBS `JDK-8316031` audit | **P2** | Section 2.1.1,<br>Section 2.5,<br>Section 3.6.1,<br>Section 4.2,<br>Section 5.4.1 | Theoretical correction: CALM applies to distributed systems; in-memory locks require Bernstein data-hazard framing. Explains why unmounting carriers does not speed up a serialized lock. | Replace CALM citation with Bernstein / Amdahl in 2.1.1 and 3.6.1. Add Goetz (2004) to 5.4.1. Correct `JDK-8316031` description. | **Contradiction Corrected (Theory)**<br>(METH-07, CHK-JDK-08, CHK-JDK-20) |
| **CL-22** | **Garbage Collection & Heap StackChunk Dynamics**<br>Virtual thread call stacks live on the Java heap as `StackChunk` arrays. High concurrency amplifies young-gen allocation rates; ZGC lowers p99 latency relative to G1GC under stack churn. | Finding 5.5.1,<br>Finding 10.10 | HotSpot `Continuation` source; Šimatović et al. (MIPRO 2025) | **P2** | Section 2.2,<br>Section 2.11,<br>Section 7.3,<br>Section 8.4 | Disproves the myth that virtual threads have zero memory footprint. Guides JVM heap sizing (`-Xmx`) and GC collector selection for high-concurrency deployments. | Add heap stack chunk allocation mechanics to Section 2.2. Add heap sizing and ZGC recommendations to Section 7.3 and 8.4. | **Supported**<br>(CHK-JDK-21) |
| **CL-23** | **Comparative Concurrency Runtime Models**<br>Java Loom's 100% cooperative M:N model contrasts with Go's kernel-signal preemption (`SIGURG`), BEAM's reduction counter, and .NET's abandonment of green threads in favor of Runtime Async (`async2`). | Finding 5.7,<br>Finding 9.7,<br>Finding 11.2.B.1,<br>Finding 11.2.C.1,<br>Finding 11.2.C.2,<br>Discovery 15 | Microsoft .NET Runtime Architecture Report (2023–2024); Go 1.14 Release Notes; Dragonwell Wisp Wiki; Kilim (ECOOP 2008); Kotlin PR #3870 | **P2** | Section 2.1.1,<br>Section 3.6.1,<br>Section 5.9,<br>Section 8.2 | Fulfills Copilot Notes #4 and #6. Explains why Java Loom is uniquely vulnerable to compute-heavy carrier starvation and why .NET abandoned green threads over native FFI pinning. | Add bounded comparative analysis to Section 2.1.1 and 3.6.1. Do NOT expand into benchmarking other languages. | **Supported — Conceptual Context** |
| **CL-24** | **Energy Benchmarking of Virtual Threads (Stocker & Wahler 2026)**<br>Empirical study measuring up to 18% energy reduction in Spring Petclinic on virtual threads via reduced OS context switching. | Finding 11.2.C.3 | Mirko Stocker & Michael Wahler (arXiv:2605.26609 / JSS 2026) | **P3** | Section 6.4,<br>Section 8.7 | Valuable green-computing data, but RAPL/package energy measurement requires bare-metal Linux hardware privileges outside the thesis's empirical scope. | Cite as external literature in Section 6.4 ("What the study did not establish") and Section 8.7 ("Future work"). Do not attempt replication. | **Excluded from Core Scope**<br>(Future Work Only) |
| **CL-25** | **Linux Kernel CFS Bandwidth Throttling Interacting with Carrier Parking**<br>Speculative suggestion from kernel mailing lists that carrier thread parking/waking induces CFS quota throttling bursts in Kubernetes containers. | Finding 11.2.D.1 | Linux Kernel Mailing List (LKML 2023) | **P3** | Section 3.14,<br>Section 8.5 | Theoretical conjecture without empirical replication on JVM virtual threads. Introducing it as a proven finding would weaken scientific rigor. | Exclude from core empirical claims and migration guidelines. Mention briefly as an unverified external validity limitation in Section 8.5. | **Unverifiable — Excluded**<br>(METH-14) |

---

## 4. Explicit List of Internal Contradictions within the Scout Report

A critical research triage requires identifying where the scout report contradicts itself or conflates distinct runtime mechanisms. The following five internal contradictions were uncovered:

### 1. Carrier Compensation vs. Monitor Pinning Stalls (Major Mechanical Error)
- **The Contradiction:**  
  In **Finding 9.1**, the scout report claimed:
  > *"By default, when a virtual thread blocks on a non-unmountable operation (such as `synchronized` pinning...), ForkJoinPool initiates carrier thread compensation, scaling up to 256. By setting `maxPoolSize=1`, this study disabled compensation, exposing the unmasked mechanism."*  
  However, in **Section 11.3 (Re-Audit)**, the scout report reversed itself, acknowledging:
  > *"Major Correction: JEP 444 explicitly states: 'The scheduler does not compensate for pinning by expanding its parallelism.' When a virtual thread is pinned by `synchronized` or JNI, HotSpot never initiates carrier compensation!"*
- **Resolution for Thesis:**  
  JEP 444 is authoritative: HotSpot **never** adds carrier threads when a virtual thread is pinned by an intrinsic monitor or native code. Carrier compensation is reserved exclusively for `ForkJoinPool.ManagedBlocker` calls (such as file I/O or explicit `CompletableFuture.get()`). Setting `-Djdk.virtualThreadScheduler.maxPoolSize=1` disabled compensation for file operations and managed blockers, but monitor pinning stalled carriers regardless of `maxPoolSize`. Setting `-Djdk.virtualThreadScheduler.parallelism=1` was the operative control that restricted the carrier pool to a single worker, isolating the serializing effect of monitor pinning. Sections 2.3, 3.9, and 5.3 must state this accurately.

### 2. Diagnostic Tool Availability on Primary Thesis Runtime (JDK Version Boundary)
- **The Contradiction:**  
  In **Finding 10.4**, the scout report presented `jcmd <pid> Thread.vthread_scheduler` and `Thread.vthread_pollers` as practical command-line tools for inspecting carrier pool utilization during Java 21 migration. In **Section 11.3**, it admitted under a warning label that these commands were introduced under `JDK-8337199` in **JDK 24**, and do not exist on the thesis's primary runtime (Java 21 LTS), where they produce `Command not recognized`.
- **Resolution for Thesis:**  
  The migration guidelines (Chapter 7) and observability protocols (Chapter 2 and 4) must strictly remove `jcmd Thread.vthread_scheduler` from Java 21 procedures. On Java 21 LTS, engineers must rely on JFR events, Micrometer 1.12+ metrics, or custom MXBeans.

### 3. Starvation vs. Deadlock Terminology (Overstated Liveness Claims)
- **The Contradiction:**  
  In **Finding 2.1.2**, the report claimed that according to `JDK-8334304`, whenever pinned threads exceed carrier count, the ForkJoinPool scheduler "deadlocks". In **Section 11.3**, the report qualified this, acknowledging that `JDK-8334304` models a circular deadlock *only when* pinned threads wait for tasks that must be executed on the exhausted carrier pool. If pinned threads wait on external socket responses (such as a database query), the result is **carrier starvation and throughput collapse**, not a circular deadlock.
- **Resolution for Thesis:**  
  The thesis must strictly maintain the vocabulary distinction defined in Section 1.2.1: carrier starvation (threads unable to acquire carriers due to monopolization) must not be casually labeled as deadlock (circular wait where no progress is possible).

### 4. Ecosystem Pinning Cleanliness Claims (Generalization vs. Specific Discoveries)
- **The Contradiction:**  
  In **Finding 3.5.1**, the scout report claimed that Spring Framework 6.1 conducted a comprehensive audit "ensuring zero framework-level pinning". Yet in **Section 12 (Discovery 2, 4, 10)**, the report documented that Spring Boot's own `LaunchedClassLoader` pinned carriers during nested fat JAR reading (#51463), `SimpleAsyncTaskExecutor` caused downstream resource collapse (#32251), and Jackson caused buffer memory bloat (#1089).
- **Resolution for Thesis:**  
  The thesis must qualify Section 1.1 and 4.1: while Spring Framework 6.1 refactored primary web request dispatchers (`ConcurrencyThrottleSupport`), the broader Spring Boot ecosystem (fat JAR classloader, client converters, third-party starter integrations) contained significant pinning and memory hazards that required subsequent maintenance updates.

### 5. Hibernate ORM Pinning Absence vs. ORM Sequence Optimizer Pinning
- **The Contradiction:**  
  In **Section 7 (Negative Query Register)**, the scout report stated under Hibernate ORM: *"No confirmed reports... no internal driver-level monitor pinning occurs in standard Session operations."* Yet in **Section 12 (Discovery 8)**, the report documented that Hibernate ORM 6.2.0–6.4.0 sequence optimizers (`PooledLoOptimizer` and `TableGenerator`) used `synchronized` blocks that pinned carrier threads during entity ID batch allocation (`HHH-17482`).
- **Resolution for Thesis:**  
  The negative register entry was too broad: while standard read queries using `Session.get()` do not pin, batch entity insertions using database sequence generators *did* pin carriers in Hibernate 6.2.0–6.4.0. Section 6.3 and 7.2 must include Hibernate ORM $\ge 6.4.2$ in the migration matrix.

---

## 5. Ten Highest-Priority Items Requiring Investigation (P0 Focus)

The following ten items represent the most critical discoveries from the scout report and fact-checking audits. Each has direct implications for experimental validity, causal attribution, or core architectural conclusions, and must be addressed prior to finalizing the thesis drafting:

### Item 1: ForkJoinPool Carrier Compensation vs. Monitor Pinning (CL-01)
- **Why It Matters:** Early project notes assumed that setting `maxPoolSize=1` was necessary to prevent ForkJoinPool from expanding carriers during monitor pinning. JEP 444 proves this assumption is mechanically false: HotSpot never expands carrier parallelism for monitor pinning.
- **Risk to Thesis:** Asserting in Section 3.9 or 5.3 that `maxPoolSize=1` "disabled pinning compensation" would be an embarrassing factual error regarding JVM internals.
- **Action Required:** Correct Section 2.3, 3.9, and 5.3. Explain that `parallelism=1` is an intentional core-count isolation control (mirroring 1-CPU container quotas), while `maxPoolSize=1` eliminates carrier expansion strictly for file I/O and managed blockers.

### Item 2: JFR 20 ms Default Event Filtering Threshold (CL-02)
- **Why It Matters:** `default.jfc` sets a 20 ms threshold on `jdk.VirtualThreadPinned`. Any critical section holding an intrinsic monitor for 1–19 ms emits zero JFR events under default settings.
- **Risk to Thesis:** If the thesis experimental harness executed k6 benchmarks without overriding this threshold, sub-20ms pinning events were silently discarded, threatening construct validity.
- **Action Required:** Inspect `run-benchmark.sh` and recording manifests in `results/`. Verify whether `-XX:StartFlightRecording` specified a custom `.jfc` with `threshold=0ms` or used `-Djdk.tracePinnedThreads=full`. Document this setting in Section 3.10 and Appendix E.

### Item 3: Closed-Loop Load Dynamics & Saturation Capacity Ceiling (CL-03)
- **Why It Matters:** An exclusive 500 ms critical section enforces an absolute theoretical capacity ceiling of $\mu = 1/D = 2.0\text{ req/s}$ ([Denning & Buzen 1978](https://doi.org/10.1145/356744.356747)). Under closed-loop testing ($N=10$), mean response time is forced to $R = N/\mu = 5000\text{ ms}$.
- **Risk to Thesis:** Asserting that 2 req/s is "not a server capacity limit" is mathematically erroneous and would be challenged by systems examiners.
- **Action Required:** Formalize the asymptotic saturation bound ($X_{max} = 1/D$) and Interactive Response Time Law ($X = N/R$) in Section 2.10.1 and 3.8.1. State clearly in Section 6.2 that under an open arrival model with $\lambda > 2\text{ req/s}$, queues would expand unboundedly *because* 2 req/s is the server's saturation capacity ceiling.

### Item 4: Native C Execution Mechanistic Attribution for Zero JFR Events (CL-04)
- **Why It Matters:** `/native` runs (500 ms `nanosleep`) exhibited multi-second carrier stalls across 108 requests, yet emitted exactly 0 `jdk.VirtualThreadPinned` events across 27 JFR recordings.
- **Risk to Thesis:** Without HotSpot C++ source attribution, an examiner could interpret zero JFR events as proof that `/native` did not block carriers or that the JFR recording was broken.
- **Action Required:** Integrate the HotSpot mechanism into Section 2.8 and 5.10: native execution (`_thread_in_native`) never invokes `VirtualThread.park()` or `Continuation::freeze()`. Because the unmount path is never executed, `is_pinned()` is never evaluated, and JFR emits zero events despite 100% carrier monopolization.

### Item 5: Database Driver Version Matrix as a Migration Prerequisite (CL-08)
- **Why It Matters:** `pgjdbc < 42.6.0` and `mysql-connector-j < 9.0.0` executed socket reads inside `synchronized` blocks. Running on Java 21 with MySQL 8.4 LTS driver still causes carrier pinning on every SQL query!
- **Risk to Thesis:** Recommending MySQL 8.4 LTS or failing to emphasize driver versions in migration guidance would leave enterprise applications vulnerable to catastrophic carrier stalls.
- **Action Required:** Build a dedicated Pre-Migration Driver & Pool Version Matrix in Section 7.2 (mandating `pgjdbc >= 42.6.0`, `mysql-connector-j >= 9.0.0`, `mariadb >= 4.0.0`). Contrast driver-level pinning with HikariCP pool waiting (which unmounts cleanly via `LockSupport.park()`) in Section 2.6 and 5.11.

### Item 6: Tooling Observer Effect & JMX Invalidation (CL-14)
- **Why It Matters:** `ThreadMXBean` silently excludes virtual threads (-1 CPU time). JVMTI thread callbacks trigger VM-global mutex contention on `JvmtiThreadState_lock`. OpenTelemetry $\le 1.32$ introduced synthetic carrier pinning via `WeakConcurrentHashMap`.
- **Risk to Thesis:** Operations teams relying on traditional APMs will be completely blind to virtual thread overload, while profilers will introduce synthetic bottlenecks.
- **Action Required:** Detail observability tooling invalidation in Section 2.9 and 7.5. Explain in Section 4.6 why external JVMTI profilers were excluded from the benchmark harness in favor of in-engine JFR.

### Item 7: `jcmd` Diagnostic Command JDK Version Incompatibility (CL-19)
- **Why It Matters:** The scout report initially recommended `jcmd Thread.vthread_scheduler` for Java 21 migrations. This command was added in JDK 24 (`JDK-8337199`) and fails on Java 21 LTS.
- **Risk to Thesis:** Recommending unsupported `jcmd` commands for Java 21 LTS would invalidate the operational integrity of the migration guidelines.
- **Action Required:** Remove all references to `Thread.vthread_scheduler` and `Thread.vthread_pollers` from Java 21 checklists in Chapter 7. Restrict them to the JDK boundary track (Section 5.13) as preview diagnostics.

### Item 8: Spring Context Propagation & ThreadLocal Lifecycle Hazards (CL-10)
- **Why It Matters:** Spring Security, Spring Transactions, and MDC rely on `ThreadLocal`. Virtual thread hops drop context unless explicitly wrapped via `TaskDecorator` or `ContextSnapshot`.
- **Risk to Thesis:** Overlooking context propagation would leave RQ2 without an answer for one of the most common production failure modes.
- **Action Required:** Integrate `TaskDecorator` and Micrometer Context Propagation guidelines into Section 4.3, 6.3, and 7.4. Warn against production use of `-Djdk.traceVirtualThreadLocals=true` due to extreme I/O overhead.

### Item 9: Mixed Synchronization Starvation Deadlocks (CL-07)
- **Why It Matters:** Replacing some `synchronized` blocks with `ReentrantLock` while leaving others intact in an interdependent call chain can induce a circular carrier starvation deadlock (`JDK-8305069`), formally verified by Hochstein's TLA+ model.
- **Risk to Thesis:** Migration guidelines could be criticized for naively recommending "just replace synchronized with ReentrantLock" without warning of mixed-synchronization deadlocks.
- **Action Required:** Add explicit warnings in Section 6.2 and 7.4. Emphasize that refactoring must cover the entire critical path atomically rather than piecemeal.

### Item 10: Hardware & Virtualization Confounders on Testbed (CL-06)
- **Why It Matters:** Apple Silicon P/E-core QoS thread scheduling and Docker Desktop macOS VM networking proxying (`vpnkit`) introduce multi-millisecond variance and baseline latency inflation.
- **Risk to Thesis:** Without documenting these threats, differences between H2 (~304 ms) and Dockerized PostgreSQL (~310 ms) could be misattributed to database engine characteristics.
- **Action Required:** Document Apple Silicon core heterogeneity and Docker VM proxying as threats to internal validity in Section 3.14 and 8.5. Emphasize why PostgreSQL and H2 were analyzed as separate tracks.

---

## 6. Scope Boundary Register: Findings That Must NOT Expand the Thesis Scope

To ensure the thesis remains focused, defensible, and achievable within MSc academic deadlines, the following discoveries from the scout report are triaged as **out of scope**. They must not be allowed to spawn new experimental tracks:

| Proposed Topic / Finding | Scout Report Ref | Reason for Exclusion from Thesis Scope | Bounded Disposition in Skeleton |
| :--- | :--- | :--- | :--- |
| **Energy & Power Benchmarking (RAPL)** | Finding 11.2.C.3<br>(Stocker & Wahler 2026) | Measuring CPU package energy requires bare-metal Linux servers, root access to `MSR_RAPL_POWER_UNIT`, and calibrated electrical probes. The thesis testbed is macOS/Docker. | Cite in Section 6.4 (*What the study did not establish*) and Section 8.7 (*Future work*) as an external empirical comparison. Do not benchmark. |
| **Comparative Runtime Benchmarking (.NET, Go, Rust, BEAM)** | Finding 5.7,<br>Finding 9.7,<br>Finding 11.2.B.1 | Implementing identical microservices in Go, C#, Rust, and Erlang would require a separate multi-language thesis and dilutes the focus on Java 21 Spring Boot MVC. | Restrict to conceptual background in Section 2.1.1 and 3.6.1 (fulfilling Copilot Note #4). No code or benchmarks. |
| **Downstream Vendor HotSpot Forks (Alibaba Wisp 2.0, Tencent Kona)** | Finding 11.2.C.1,<br>Finding 11.1.J | Historical coroutine modifications in proprietary/downstream OpenJDK 8/11 forks are historical trivia. Enterprise Spring MVC runs on mainline OpenJDK 21 LTS. | Retain as a brief historical footnote in Section 2.1.1. Exclude from experimental analysis. |
| **Messaging & Broker Storage Internals (ActiveMQ KahaDB, Kafka)** | Discovery 13<br>(ActiveMQ AMQ-9428) | The thesis artifact is an HTTP REST MVC application backed by relational databases (H2, PostgreSQL). JMS/Kafka introduces asynchronous messaging protocols outside the scope. | Mention briefly in Section 2.7/6.3 as evidence that file I/O pinning affects message brokers. Do not add messaging endpoints. |
| **Linux CFS Bandwidth Throttling Mechanics** | Finding 11.2.D.1 | Speculative kernel scheduling conjecture lacking reproducible empirical JVM evidence. Investigating kernel CFS periods is OS systems research, not software architecture. | Mention briefly in Section 8.5 as an unverified external validity limitation of containerized environments. |
| **Advanced Lock Algorithm Theory (Dave Dice Hapax Locks)** | Finding 11.2.C.4<br>(PPoPP 2026) | Value-based token locking algorithms are theoretical HotSpot research prototypes, not available in Java 21 LTS runtime libraries. | Cite in Section 2.5 as contemporary synchronization research. Do not attempt implementation. |
| **Alternative Embedded Database Rewrites (SQLite JNI)** | Discovery 7<br>(xerial sqlite-jdbc) | The thesis already contains H2 (pure Java in-memory) and PostgreSQL (Docker client-server). Adding SQLite provides redundant JNI evidence already covered by `/native`. | Use SQLite Issue #1136 as supporting literature for native carrier capture in Section 2.8 and 5.10. Do not implement SQLite endpoint. |
| **Comprehensive Formal Concurrency Testing (Lincheck, CMU Fray)** | Finding 9.4,<br>Discovery 14 | Lincheck cannot intercept M:N continuation yields, and Fray is an external research prototype. The thesis already possesses JUnit concurrency assertions and JFR CI gates. | Cite in Section 4.7 and 8.7 as the state of the art in testing literature. Rely on `loom-unit` for actionable CI guidance. |

---

## 7. Analysis of Methodological Problems & Problem Taxonomy

In accordance with Step 3 of the triage mandate, the following structural, evidentiary, and versioning problems across the scout report are explicitly documented:

### 7.1 Claims Broader than Cited Evidence (Overgeneralizations)

1. **"Throughput collapses to 2 req/s because Virtual Threads cannot handle serialization":**  
   *Problem:* The scout report documents the 2 req/s floor on `/payments`, but early project notes risked treating this as a universal server-side failure.  
   *Reality:* The 2.0 req/s ceiling is the mathematical saturation capacity ($\mu = 1/D = 1/0.5\text{s} = 2.0\text{ req/s}$) of an exclusive critical section. With 10 VUs in a closed loop, Little's Law / Interactive Response Time Law ($X = N/R$) forces average response time to $R = N/\mu = 5000\text{ ms}$. Under an open arrival process with $\lambda > 2\text{ req/s}$, arrival rate exceeds service rate, causing unbounded queue growth.
2. **"Replacing synchronized with ReentrantLock universally improves performance":**  
   *Problem:* The scout report emphasizes unmounting on `ReentrantLock`.  
   *Reality:* If a critical section protects a 500 ms operation and requests have no independent work, swapping to `ReentrantLock` unmounts carriers but leaves the 1-at-a-time serialization throughput ceiling completely unchanged (Copilot Note #5, Bernstein's Conditions, and Amdahl's Law). `ReentrantLock` only improves overall system throughput if carriers are constrained AND requests contain independent concurrent work or other endpoints need the carriers.
3. **"All database operations pin virtual threads":**  
   *Problem:* Some industry posts claim database access is broken on Virtual Threads.  
   *Reality:* As proven by HikariCP maintainers (Finding 3.3.1), connection pool waiting unmounts cleanly via `LockSupport.park()`. Pinning occurs *only* when using outdated database drivers (`pgjdbc < 42.6.0`, `mysql-connector-j < 9.0.0`) that wrap socket I/O in `synchronized` blocks.

### 7.2 Missing Primary-Source Evidence & Unverified Claims

1. **Linux CFS Bandwidth Throttling (Finding 11.2.D.1 / METH-14):**  
   *Status:* **Unverified.** Sourced strictly from Linux Kernel Mailing List discussions; lacks any published empirical benchmark demonstrating that carrier parking induces CFS throttling in containerized Java 21 runtimes. Must be labeled speculative and excluded from core claims.
2. **Apple Silicon Darwin QoS Carrier Demotion (Finding 5.3.1 / METH-10):**  
   *Status:* **Partially Verified.** Howard Oakley's reverse-engineering of Darwin kernel QoS scheduling is authoritative for macOS, but HotSpot's internal thread priority mapping to Darwin QoS classes during ForkJoinPool carrier worker creation has not been instrumented via `ktrace` on the thesis testbed. Must be treated as a plausible confounding hypothesis rather than an established fact.
3. **dotCMS Migration Reversion (Finding 10.2 / CHK-JDK-19):**  
   *Status:* **Verified Artifact, Unverified Benchmark Data.** GitHub PR #36900 verifies that dotCMS officially reverted virtual threads in their caching layer, citing file I/O lock contention, but their internal load-testing metrics were not published in the PR.

### 7.3 Version-Dependent Claims & Framework Compatibility Boundaries

The following matrix documents the exact software versions where behavior flips between catastrophic carrier pinning/leaks and safe virtual thread execution (updated with fact-check audit discoveries):

| Component / Layer | Vulnerable Version Range | Safe Version Range | Failure Mode on Vulnerable Versions |
| :--- | :--- | :--- | :--- |
| **PostgreSQL JDBC (`pgjdbc`)** | $< 42.6.0$ | $\ge 42.6.0$ | Carrier pinning during every SQL socket read (`QueryExecutorImpl.java`). |
| **MySQL Connector/J** | $\le 8.4\text{ LTS}$ | $\ge 9.0.0$ | Carrier pinning during socket reads (`NativeProtocol.java`). **8.4 LTS still pins!** |
| **MariaDB Connector/J** | $< 4.0.0$ | $\ge 4.0.0$ | SSL socket monitor pinning; JFR-verified zero pinning landed in 4.0.0 (`CONJ-1367`). |
| **Apache Commons Pool 2** | All 2.x releases | Unremediated | Evictor thread monitor pins borrowers; Loom PR #230 was **never merged**. |
| **Apache HttpClient 5** | $5.0.0 - 5.3.x$ | $\ge 5.4.0$ | Connection lease allocation synchronizes on `this.pool`, pinning carriers. Safe in 5.4.0+. |
| **Hibernate ORM** | $6.2.0 - 6.4.0$ | $\ge 6.4.2$ | Sequence optimizer pins carriers during batch ID pre-allocation (`HHH-17482`). |
| **Spring Boot Fat JAR** | All nested JARs | Unpacked / Exploded | `JarUrlClassLoader` pins carriers reading nested fat JAR zip entries (`#51463`, `#50925`). |
| **Spring Framework Core** | $6.1.0\text{ only}$ | $\ge 6.1.1$ | `SimpleAsyncTaskExecutor` rate-limiting refactored in `#32251` and `#34727`. |
| **Square OkHttp** | $4.x$ releases | $\ge 5.0.0\text{-alpha.12}$ | Dispatcher built on platform thread assumptions; virtual thread support in 5.x alpha. |
| **OpenTelemetry Java Agent** | $\le 1.32.0$ | $\ge 1.33.0$ | `WeakConcurrentHashMap` synchronization pins carriers during trace context attachment (`#9534`). |
| **Eclipse Memory Analyzer (MAT)** | $\le 1.14.0$ | $\ge 1.15.0$ | Fails to recognize heap continuation roots, misreporting virtual thread memory as leaked (`#582190`). |
| **OpenJDK `jcmd` Diagnostics** | JDK 21 – 23 | $\ge \text{JDK 24}$ | `jcmd Thread.vthread_scheduler` unsupported (`Command not recognized`) on Java 21 LTS. |
| **HotSpot Monitor Unmounting** | JDK 21 – 23 | $\ge \text{JDK 24 (JEP 491)}$ | `synchronized` methods/blocks pin carriers on Java 21; unmount cleanly on JDK 24+. |

### 7.4 Claims Requiring New Experiments to Establish (vs. Sourced Analysis)

1. **JFR Threshold Verification:**  
   *Question:* Did our historical recordings miss sub-20ms pinning?  
   *Requirement:* Does not require new benchmark runs if the recording manifests or `.jfc` profiles retained in `results/` confirm `threshold=0ms` was set. If default settings were used, running a quick 30-second verification probe with `-XX:FlightRecorderOptions=stackdepth=64` and `threshold=0ms` would definitively settle the question.
2. **Before-and-After Migration Validation (Copilot Note #3):**  
   *Question:* Does applying the migration guidelines measurably improve a legacy endpoint?  
   *Requirement:* The thesis skeleton explicitly reserves Section 1.6.1 for before-and-after validation. Comparing the existing legacy `synchronized` payment baseline with the refactored `ReentrantLock` payment baseline under identical load already establishes before-and-after validation for synchronization refactoring.
3. **Open-Loop Arrival Rate Testing (Copilot Note #7):**  
   *Question:* What happens to `/payments` under open arrival rates?  
   *Requirement:* The thesis skeleton (Section 3.8.1) explicitly marks this as a theoretical boundary: the causal model can be explained via queueing theory without running open-loop benchmarks, relegating open-loop k6 scripts to future work (Section 8.7).

---

## 8. Summary of Action Items for Thesis Drafting

Based on this triage register and the three fact-checking audits, the author should execute the following focused modifications across the thesis drafting process:

1. **Section 1.2 & 1.2.1 (Symptom-to-Mechanism Vocabulary):**  
   Add *Asymmetric Carrier Monopolization* and *Closed-Loop Queueing Feedback* to the vocabulary table. Distinguish carrier starvation from circular deadlocks.
2. **Section 2.3 & 3.9 (Carrier Compensation Correction):**  
   Correct the explanation of ForkJoinPool mechanics: state clearly that HotSpot never compensates for monitor pinning, and that `maxPoolSize=1` eliminated carrier expansion strictly for file I/O and managed blockers (CHK-JDK-01).
3. **Section 2.8 & 5.10 (Native Execution Attribution):**  
   Provide the HotSpot C++ source attribution (`_thread_in_native` never invokes `Continuation::freeze()`) explaining why 108 `/native` requests produced carrier starvation with exactly 0 JFR pinning events (CHK-JDK-03).
4. **Section 2.10.1 & 3.8.1 (Asymptotic Bounds & Queueing Dynamics):**  
   Integrate Denning & Buzen's asymptotic bound ($X_{max} = 1/D$) and the Interactive Response Time Law ($X = N/R$) to formalize why the 2 req/s throughput floor on `/payments` is an absolute saturation capacity ceiling, while closed-loop load prevents unbounded queue explosion (METH-01, METH-02).
5. **Section 3.8 & 3.10 (Data Pipeline Normalization Window):**  
   Reconcile the manifest description with `scripts/normalize_evidence.py`, clarifying that reported summary metrics represent the entire 55-second run window (METH-05).
6. **Section 2.1.1 & 3.6.1 (Theoretical Framing):**  
   Replace CALM Theorem references with Bernstein's Conditions (1966) and Amdahl's Law (1967) to explain why mutual exclusion on mutable state enforces serialization regardless of thread unmounting (METH-07).
7. **Section 3.12 & 3.13 (Statistical Framing):**  
   Cite Georges et al. (2007) and Kalibera & Jones (2013) to justify treating the 3 process trials as qualitative mechanism-isolation units rather than inferential sample statistics (METH-04).
8. **Section 3.14 & 8.5 (Threats to Validity):**  
   Document Apple Silicon P/E-core QoS scheduling and Docker Desktop macOS VM network proxying (`vpnkit`) as internal validity threats explaining baseline latency variations (METH-10, METH-11).
9. **Section 4.7 & 7.5 (Automated CI Verification):**  
   Integrate Clément Escoffier's `loom-unit` (`@ShouldNotPin`) as an actionable engineering guideline for continuous integration pipelines.
10. **Section 5.4.1 (Historical Context for ReentrantLock):**  
    Cite Brian Goetz (2004) to provide the authoritative historical rationale for explicit locks in Java 5.0 (fulfilling Copilot Note #9).
11. **Section 7.2 & 7.4 (Migration Matrix & Guidelines):**  
    Embed the corrected Pre-Migration Version Matrix (PostgreSQL $\ge 42.6.0$, MySQL $\ge 9.0.0$, MariaDB $\ge 4.0.0$, Apache HttpClient $\ge 5.4.0$, Jackson $\ge 2.16$, Hibernate $\ge 6.4.2$, Logback $\ge 1.3.15$) and graceful shutdown configuration rules.

---

## 9. Fact-Check Reconciliation

This section reconciles the original research triage register with the definitive findings of the three independent technical fact-checking audits (`docs/fact-check-jdk-runtime.md`, `docs/fact-check-methodology-performance.md`, and `docs/fact-check-spring-ecosystem.md`). It establishes the verified evidentiary baseline required for the upcoming experimental audit.

### 9.1 Summary of Consequential Changes to Original Triage

1. **Theoretical Inversion of the 2 req/s Throughput Floor (METH-01 vs. CL-03):**  
   The original triage accepted the scout report's assertion that 2.0 req/s was an artificial generator illusion rather than a server capacity ceiling. Fact-check Session B disproved this using asymptotic queueing theory ([Denning & Buzen 1978](https://doi.org/10.1145/356744.356747)). A 500 ms critical section enforces an absolute capacity bound of $\mu = 1 / 0.5\text{s} = 2.0\text{ req/s}$. What the closed-loop load model ($N=10$) alters is the arrival process (capping queue length to 10 and forcing $R \approx 5.0\text{ s}$), preventing unbounded queue growth.
2. **Measurement Window Discrepancy in Data Normalization (METH-05):**  
   Fact-check Session B audited [`scripts/normalize_evidence.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/normalize_evidence.py#L40-L69) and discovered that the script aggregates points across the entire 55-second run (ramp-up, hold, ramp-down) without stage filtering. The reported 108 requests represents $108 / 55\text{s} \approx 1.96\text{ req/s}$; over a 30s window it would imply $3.6\text{ req/s}$ (physically impossible for a 500ms lock). The thesis text must clarify this window.
3. **Purging the CALM Theorem Citation (METH-07 vs. CL-21):**  
   Fact-check Session B identified that applying the CALM Theorem ([Hellerstein & Alvaro 2020](https://doi.org/10.1145/3397885)) to single-process in-memory locks is a conceptual category mistake. CALM applies strictly to distributed program consistency across networks. In-memory locking is governed by [Bernstein's Conditions (1966)](https://doi.org/10.1109/PGEC.1966.264565) and [Amdahl's Law (1967)](https://doi.org/10.1145/1465482.1465560).
4. **Purging Hallucinated Artifacts from Section 12 (FC-08 to FC-22, CHK-JDK-08, CHK-JDK-15):**  
   Fact-check Sessions A and C exposed that over 60% of GitHub issues, PR numbers, and commit hashes cited in the scout report's archaeology workstream were fabricated or misattributed. These citations have been purged and replaced with genuine primary sources.
5. **Framework Version Threshold Corrections (FC-02, FC-20, FC-08):**  
   - MySQL Connector/J 8.4 LTS still pins carriers; safe version is strictly Connector/J $\ge 9.0.0$.
   - Apache HttpClient 5.3.x still pins on pool handoffs; safe version is strictly HttpClient $\ge 5.4.0+$.
   - Apache Commons Pool 2 Loom rewrite (PR #230) was never merged into 2.12.x; Commons Pool remains monitor-synchronized.

---

### 9.2 Master Mapping Register: Triage Clusters to Fact-Check Findings & Verdicts

The table below maps all 25 triage clusters to their corresponding fact-check finding IDs, established verdicts, reconciled priorities, and required experimental audit actions:

| Triage ID | Topic / Mechanism Cluster | Fact-Check Source & Finding ID | Fact-Check Verdict | Original Priority | Reconciled Priority | What Must Be Checked Against Actual Project / Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CL-01** | ForkJoinPool Carrier Compensation Scope | JDK: `CHK-JDK-01`<br>Meth: `METH-09` | **CONTRADICTED** (Compensation)<br>**SUPPORTED** (cgroups) | P0 | **P0** | Check `run-benchmark.sh` and manifests in `results/` for exact JVM scheduler flags (`-Djdk.virtualThreadScheduler.parallelism=1`, `maxPoolSize=1`). Confirm whether any file I/O or managed blocking occurred during test runs. |
| **CL-02** | JFR 20 ms Event Filtering Threshold | JDK: `CHK-JDK-02`<br>Meth: `METH-12` | **SUPPORTED** | P0 | **P0** | Inspect `run-benchmark.sh` and recording manifests to determine whether `-XX:StartFlightRecording` used `profile.jfc` (default 20ms threshold) or explicitly specified `threshold=0ms` / `-Djdk.tracePinnedThreads=full`. |
| **CL-03** | Closed-Loop Dynamics & Saturation Capacity | Meth: `METH-01`, `METH-02`<br>JDK: `CHK-JDK-20` | **CONTRADICTED** (Capacity claim)<br>**SUPPORTED** (Formula derivation) | P0 | **P0** | Audit raw k6 JSON metrics in `results/` for `/payments`. Verify whether service demand $S = 500\text{ ms}$ completely accounts for the observed 108 requests and response times. |
| **CL-04** | Native Execution Zero JFR Pinning Events | JDK: `CHK-JDK-03`, `CHK-JDK-04`<br>Meth: `METH-13`<br>Spring: `FC-04` | **SUPPORTED** | P0 | **P0** | Audit the 27 raw JFR recordings for `/native` to verify that `jdk.VirtualThreadPinned` event count is strictly zero, and check OS carrier CPU duration telemetry during `nanosleep`. |
| **CL-05** | Statistical Rigor & 3-Trial Process Units | Meth: `METH-04` | **SUPPORTED** | P0 | **P0** | Inspect `results/evidence-dashboard.json` and research iteration notes to verify that data is presented as dispersion (min/max/median) rather than inferential confidence intervals. |
| **CL-06** | Hardware & Virtualization Confounders | Meth: `METH-10`, `METH-11` | **PARTIALLY SUPPORTED** (QoS)<br>**SUPPORTED** (Docker vpnkit) | P0 | **P0** | Compare latency baseline differences between local in-memory H2 (~304 ms) and Dockerized PostgreSQL (~310 ms) across raw runs to verify if the ~6 ms delta matches Docker VM network proxying. |
| **CL-07** | Mixed Synchronization Starvation Deadlocks | JDK: `CHK-JDK-06` | **PARTIALLY SUPPORTED** (Qualified) | P1 | **P1** | Inspect `PaymentService.java` and repository code to confirm whether any critical paths mix `synchronized` with `ReentrantLock`. |
| **CL-08** | Database Drivers & Pool Pinning / Backpressure | Spring: `FC-01`, `FC-02`, `FC-05`, `FC-06`, `FC-08`<br>JDK: `CHK-JDK-23` | **SUPPORTED** (pgjdbc, HikariCP, Sip 94)<br>**CONTRADICTED** (Commons Pool fix) | P1 | **P1** | Inspect `pom.xml` for exact driver dependencies (`org.postgresql:postgresql`, `com.h2database:h2`). Verify HikariCP settings in `application.yml` (`maximum-pool-size: 10`). |
| **CL-09** | ORM & Serialization Bottlenecks (Jackson/Hibernate) | Spring: `FC-18`<br>Scout: `HHH-17482` | **SUPPORTED** | P1 | **P1** | Check `pom.xml` for Jackson and Hibernate versions resolved transitively by Spring Boot. Check whether `JsonRecyclerPools` is configured in any custom beans. |
| **CL-10** | Spring Context Propagation & ThreadLocal Lifecycle | Spring: `FC-17`, `FC-26`<br>JDK: `CHK-JDK-12` | **SUPPORTED** | P1 | **P1** | Audit application services for `ThreadLocal` usage or `@Async` subtask dispatching. Verify if `-Djdk.traceVirtualThreadLocals` was used in any test scripts. |
| **CL-11** | HTTP Client & Microservice Transport Contention | Spring: `FC-15`, `FC-20`, `FC-21`, `FC-22` | **CONTRADICTED** (RestClient leak, 5.3.1 safe version)<br>**SUPPORTED** (HttpClient 5.4.0+) | P1 | **P2** *(Revised)* | Inspect `pom.xml` to verify if any outbound HTTP clients (`httpclient5`, `okhttp`, `grpc`) are present in the project. (The thesis artifact is an inbound MVC service; these are peripheral). |
| **CL-12** | Unbounded Task Spawning & Tomcat Limits | Spring: `FC-11`, `FC-14` | **SUPPORTED** (Tomcat)<br>**PARTIALLY SUPPORTED** (SimpleAsync) | P1 | **P1** | Check `application.yml` for Tomcat thread and connection bounds (`server.tomcat.threads.max`, `accept-count`, `max-connections`). |
| **CL-13** | Servlet Container Memory & Platform Boundaries | Spring: `FC-12`, `FC-19` | **CONTRADICTED** (Undertow citation)<br>**QUALIFIED** (Netty default) | P1 | **P2** *(Revised)* | Confirm in `pom.xml` that the project uses standard `spring-boot-starter-web` (Tomcat) and does not import Undertow or Netty starters. |
| **CL-14** | Observability Tooling Invalidation & Observer Effect | JDK: `CHK-JDK-13`, `CHK-JDK-14`, `CHK-JDK-15`<br>Spring: `FC-24`, `FC-25` | **SUPPORTED** (ThreadMXBean, Micrometer)<br>**PARTIALLY SUPPORTED** (JVMTI) | P1 | **P1** | Check `pom.xml` for `micrometer-core` / `micrometer-java21`. Confirm that no JVMTI profiler agents were active during official benchmark runs. |
| **CL-15** | Logging Framework Carrier Pinning (Logback/Log4j2) | JDK: `CHK-JDK-24`<br>Spring: `FC-23` | **SUPPORTED** (Pinning hazard)<br>**PARTIALLY SUPPORTED** (Versions) | P1 | **P1** | Inspect `src/main/resources/application.yml` and `logback-spring.xml`. Verify logging levels (INFO vs DEBUG) and appender configuration (Console vs Async). |
| **CL-16** | Daemon Thread Immutability & Graceful Shutdown | JDK: `CHK-JDK-16`<br>Spring: `FC-27` | **SUPPORTED** | P1 | **P1** | Check `application.yml` to verify whether `server.shutdown: graceful` and `spring.lifecycle.timeout-per-shutdown-phase` are configured in the project. |
| **CL-17** | Packaging & ClassLoader Pinning (Fat JARs & `<clinit>`) | JDK: `CHK-JDK-17`<br>Spring: `FC-13` | **SUPPORTED** (`<clinit>`)<br>**SUPPORTED** (Real Fat JAR issues #51463) | P1 | **P1** | Inspect `Dockerfile` and `run-benchmark.sh`. Is the application executed as an executable fat JAR (`java -jar`) or an unpacked/exploded directory? |
| **CL-18** | OS File I/O Kernel Asymmetry & dotCMS Rollback | JDK: `CHK-JDK-18`, `CHK-JDK-19` | **SUPPORTED** | P1 | **P1** | Verify whether any endpoint in `virtualthreadsdemo` touches local disk storage. Confirm that H2 is configured in in-memory mode (`jdbc:h2:mem:...`). |
| **CL-19** | JDK Evolution Timeline & LTS Pinning Boundary | JDK: `CHK-JDK-09`, `CHK-JDK-10`, `CHK-JDK-11` | **SUPPORTED** | P1 | **P1** | Check Java compiler target in `pom.xml` and runtime version in Docker container (`openjdk:21`). Confirm `jcmd` scheduler commands are excluded from Java 21 scripts. |
| **CL-20** | Concurrency Testing & CI Pinning Regression Gates | Scout: 9.4, 9.5, 5.6.1, Disc 14 | **SUPPORTED** | P1 | **P1** | Inspect `src/test/` to see what unit/integration tests currently run in Maven CI. Check whether `loom-unit` or JFR assertions can be added to `./mvnw test`. |
| **CL-21** | Authoritative Synchronization Theory | Meth: `METH-07`<br>JDK: `CHK-JDK-08`, `CHK-JDK-20` | **CONTRADICTED** (CALM)<br>**SUPPORTED** (Bernstein, Amdahl, Goetz) | P2 | **P2** | Verify that Section 2.1.1, 3.6.1, and 5.4.1 in the draft skeleton cite Bernstein (1966), Amdahl (1967), and Goetz (2004) rather than the CALM Theorem. |
| **CL-22** | Garbage Collection & Heap StackChunk Dynamics | JDK: `CHK-JDK-21`<br>Scout: 10.10 | **SUPPORTED** | P2 | **P2** | Check JVM memory flags (`-Xmx`, `-Xms`, `-XX:+UseG1GC` vs `-XX:+UseZGC`) in `run-benchmark.sh` and Docker configurations. |
| **CL-23** | Comparative Concurrency Runtime Models | Scout: 5.7, 9.7, 11.2.B.1 | **SUPPORTED** (Conceptual) | P2 | **P2** | Purely conceptual background for Section 2.1.1 and 3.6.1. No project artifact check needed. |
| **CL-24** | Energy Benchmarking (Stocker & Wahler 2026) | Scout: 11.2.C.3 | **EXCLUDED** (Scope) | P3 | **P3** | Confirm that energy claims are strictly restricted to Section 6.4 and 8.7 (Future Work). No experimental audit needed. |
| **CL-25** | Linux Kernel CFS Bandwidth Quota Throttling | Meth: `METH-14` | **UNVERIFIABLE** (Speculative) | P3 | **P3** | Exclude from core claims. Mention only as an unverified external hypothesis in Section 8.5. |

---

### 9.3 Detailed Priority Revisions & Justifications

1. **Cluster CL-11 (HTTP Client & Microservice Transport Contention): Revised from P1 to P2**  
   - *Original Priority:* P1 (Architectural Risks RQ2).  
   - *Reconciled Priority:* **P2 (Useful Background / General Guidelines).**  
   - *Reason for Revision:* The thesis demonstration application (`src/main/java/com/thesis/virtualthreadsdemo/`) is an *inbound* Spring MVC REST service receiving HTTP traffic from k6 and querying relational databases. It does not make outbound HTTP/RPC calls to downstream microservices using Apache HttpClient 5, OkHttp, or gRPC. While the fact-check established important version boundaries for the broader ecosystem (e.g. HttpClient must be $\ge 5.4.0+$, and the RestClient ThreadLocal leak was unverified), these findings do not affect the thesis's primary experimental artifact or research questions. They belong in general migration guidelines (Chapter 7), not core architectural risks for this project.

2. **Cluster CL-13 (Servlet Container Direct Memory Leaks: Undertow & Netty): Revised from P1 to P2**  
   - *Original Priority:* P1 (Architectural Risks RQ2).  
   - *Reconciled Priority:* **P2 (Useful Background / Container Selection).**  
   - *Reason for Revision:* The thesis artifact relies strictly on Apache Tomcat (`spring-boot-starter-web`), which was fully verified as safe from direct memory leaks under its platform-bound `Acceptor` and `Poller` architecture. Undertow's buffer pooling hazard (PR #1612 was misattributed) and Netty's buffer allocator settings (where `useCacheForAllThreads=false` is already default) are alternative container concerns that do not threaten the project's empirical validity.

3. **Cluster CL-03 (Closed-Loop Load Dynamics & Saturation Capacity): Maintained at P0 (With Theoretical Inversion)**  
   - *Original Priority:* P0.  
   - *Reconciled Priority:* **P0 (Critical Experimental Validity & Causal Model).**  
   - *Reason for Retention:* Fact-check Session B contradicted the scout report's claim that 2 req/s was an artificial generator illusion, proving via queueing theory that it is the absolute theoretical saturation capacity ceiling ($\mu = 1/D = 2.0\text{ req/s}$) of the 500 ms critical section. Retaining P0 is mandatory because this mathematical formulation directly anchors the interpretation of RQ1 in Section 6.2 and fulfills Copilot Notes #5 and #7.

4. **Cluster CL-08 (Database Drivers & Connection Pools): Maintained at P1 (With Version Adjustments)**  
   - *Original Priority:* P1.  
   - *Reconciled Priority:* **P1 (Core Architectural Risks & Migration Guidelines).**  
   - *Reason for Retention:* While specific PR citations were corrected (e.g. Commons Pool PR #230 remains unmerged in 2.12.x), the core findings regarding driver socket pinning (PostgreSQL $\ge 42.6.0$, MySQL $\ge 9.0.0$) and HikariCP connection waiting (clean unmounting via `LockSupport.park()`) directly govern the thesis's database sensitivity experiments (`/orders`) and pre-migration inventory.

---

### 9.4 Critical Review of Fact-Check Reports (Addressing Overbroad Conclusions)

To avoid uncritically accepting the fact-check reports, the following three findings have been scrutinized and qualified:

1. **Qualification of METH-01 (Capacity Floor vs. Generator Feedback):**  
   While fact-check Finding METH-01 is mathematically correct that $\mu = 1 / D = 2.0\text{ req/s}$ is the saturation capacity ceiling of an exclusive 500 ms critical section, the thesis should **not** completely dismiss the closed-loop load dynamics. The closed-loop arrival process ($N=10$, zero think time) creates a negative feedback loop: when service time swells to 500 ms, mean response time becomes $R = N / \mu = 10 / 2 = 5.0\text{ s}$, which in turn forces the arrival rate to match the completion rate. Under open arrivals with offered load $\lambda = 10\text{ req/s}$, the completion rate would remain 2.0 req/s, but queue length and tail latency would expand unboundedly towards memory exhaustion. The thesis must explain both aspects: 2.0 req/s is the server capacity ceiling, and closed-loop load prevented queue explosion.
2. **Qualification of METH-10 (Apple Silicon Darwin QoS Scheduling):**  
   Fact-check Finding METH-10 correctly identifies Howard Oakley's research on Darwin kernel QoS thread scheduling as an authoritative explanation for thread performance on Apple Silicon. However, HotSpot's internal carrier thread creation has not been instrumented via macOS `ktrace` or `powermetrics` on the thesis hardware. While Darwin QoS core demotion is a highly plausible confounding mechanism explaining inter-trial latency spread, the thesis must present it as an *unverified internal validity threat*, not an experimentally established fact.
3. **Qualification of FC-08 (Commons Pool 2 Unmerged Status):**  
   Fact-check Finding FC-08 correctly proves that PR #230 was never merged in Commons Pool 2.12.x and that `POOL-415` was an unrelated ticket. However, because the thesis artifact uses HikariCP (and not Apache Commons DBCP2), Commons Pool 2's unmerged status is an ecosystem context finding that does not invalidate the thesis's primary database benchmark results.

---

### 9.5 Register of Unresolved and Hallucinated Claims

#### 9.5.1 Purged Hallucinated Tickets from Scout Report Section 12
The table below records the specific artifact identifiers from Section 12 that were proven fabricated or misattributed by the fact-checking audits, along with their verified disposition:

| Purged Ticket / Citation | Claimed Role in Scout Report | Actual Fact-Check Finding | Required Action |
| :--- | :--- | :--- | :--- |
| `JDK-8316031` | Refactoring `SSLFlowDelegate` to `ReentrantLock` | Titled *"SSLFlowDelegate should not log from synchronized block"*; moved logging out of lock. (CHK-JDK-08) | Purge claim of lock refactoring; cite genuine OpenJDK tickets (e.g. JEP 425 library audit). |
| `JDK-8308481` | HotSpot issue for `JvmtiThreadState_lock` contention | Minor JDI TestScaffold ticket. Real issue is in `async-profiler` #779. (CHK-JDK-15) | Replace citation with `async-profiler` Issue #779. |
| `xerial/sqlite-jdbc` PR `#1011` | JNI virtual thread statement compilation pinning | DataSource connection pool connection reuse fix. Real Loom discussion is in #1136. (FC-04) | Replace with Issue #1136; distinguish JNI carrier capture from JFR pinning. |
| `spring-projects/spring-boot` Issue `#38841` / PR `#38872` | Redesign of `LaunchedClassLoader` nested zip reading | RestTemplate Content-Length bug and routine Netty dependency bump. Real issues are #51463 and #50925. (FC-13) | Replace citations with Spring Boot **#51463** and **#50925**. |
| `spring-projects/spring-framework` Issue `#31215` / PR `#31221` | Adding virtual thread concurrency limits to SimpleAsync | `JdbcClient` positional parameter handling in SQL `IN` clauses. Real issues are #32251 and #34727. (FC-14) | Replace citations with Spring Framework **#32251** and **#34727**. |
| `spring-projects/spring-framework` Issue `#32001` | Fixing RestClient RequestCallback ThreadLocal buffer leak | WebClient URI query sanitization patch. No RestClient ThreadLocal leak exists. (FC-15) | **Purge claim completely** from thesis text. |
| `apache/httpcomponents-client` Issue `HTTPCLIENT-2311` / PR `#530` | Refactoring connection leasing to ReentrantLock in 5.3.1 | `HTTPCLIENT-2311` does not exist; PR #530 was Dependabot log4j update. Real fix landed in 5.4.0+. (FC-20) | Replace safe version recommendation with **HttpClient 5.4.0+**. |
| `square/okhttp` Issue `#7853` / PR `#7912` | Dispatcher concurrency bypass and ThreadLocal leaks | HTTP caching bug and JUnit bump. Official virtual thread refactoring landed in 5.0.0-alpha.12. (FC-21) | Replace citation with OkHttp 5.0.0-alpha.12 release notes. |
| `agroal/agroal` Commit `12f8a91` (`AG-315`) | Interruption causing IllegalMonitorStateException & connection leaks | Titled *"Disable collaborative connection creation on virtual threads"*. Interruption leak story was fabricated. (FC-09) | Correct narrative to collaborative connection creation contention. |
| `apache/commons-pool` JIRA `POOL-415` / PR `#251` | ReentrantLock rewrite in Commons Pool 2.12.1 | `POOL-415` is JdkProxySource exception unwrapping. Real Loom PR #230 was **never merged**. (FC-08) | State clearly that Commons Pool 2 remains monitor-synchronized. |
| Apache Log4j2 `LOG4J2-3642` | Ticket for virtual thread rolling file manager pinning | OSGi packaging ticket. Real tickets are `LOG4J2-3622` and GitHub Issue #1532. (FC-23) | Replace citation with **`LOG4J2-3622`** and **Issue #1532**. |

#### 9.5.2 Unresolved Claims Requiring Future Work or Relegation
1. **Linux CFS Bandwidth Quota Interactions with Carrier Parking (CL-25 / METH-14):** Sourced strictly from LKML mailing list discussions; no reproducible JVM empirical data exists. Relegated to Section 8.5/8.7.
2. **Apple Silicon Hardware Core Affinity Tracing (CL-06 / METH-10):** Darwin kernel QoS thread scheduling is authoritative, but carrier thread core mapping was not instrumented via `ktrace`. Retained as a qualified validity threat in Section 3.14.
3. **True Steady-State Metric Values Excluding Ramp-Up (METH-05):** Raw k6 data in `results/` was aggregated across the full 55 seconds. Determining the exact metrics strictly within $[15\text{s}, 45\text{s}]$ requires re-filtering in the upcoming experimental audit.

---

### 9.6 Tripartite Claim Classification

The table below groups all triaged findings into the required three operational categories:

#### Category A: Verified Against External Technical Sources
*These claims are backed by authoritative primary sources (JEPs, OpenJDK source code, release notes, peer-reviewed literature) and can be cited with confidence:*
1. **Carrier Compensation Scope (CHK-JDK-01):** HotSpot never compensates for monitor pinning or native code (JEP 444).
2. **JFR 20 ms Event Threshold (CHK-JDK-02, METH-12):** `default.jfc` suppresses pinning events lasting $< 20\text{ ms}$.
3. **Native Execution Zero JFR Pinning Events (CHK-JDK-03, METH-13):** Native code executes in `_thread_in_native` without calling `VirtualThread.park()`, emitting zero events.
4. **DNS Resolution Carrier Capture (CHK-JDK-04):** `InetAddress.getByName` calls POSIX `getaddrinfo(3)` via JNI, capturing carriers (JEP 418).
5. **Panama FFM Downcall Pinning (CHK-JDK-05):** Downcalls execute on platform frames, pinning carriers identically to JNI (JEP 454).
6. **LTS Runtime Boundaries (CHK-JDK-09, CHK-JDK-10):** JEP 491 eliminates monitor pinning in JDK 24, but is strictly ineligible for backporting to Java 21 LTS (`jdk21u-dev`).
7. **`jcmd` Command Availability (CHK-JDK-11):** `Thread.vthread_scheduler` was introduced in JDK 24 (`JDK-8337199`) and fails on Java 21 LTS.
8. **ThreadMXBean Virtual Thread Omission (CHK-JDK-13):** `ThreadMXBean` monitors platform threads only; returns -1 for virtual thread CPU time (CSR `JDK-8303251`).
9. **Daemon Thread Immutability (CHK-JDK-16, FC-27):** Virtual threads are permanently daemon threads; Spring Boot graceful shutdown is mandatory (JEP 444).
10. **Class Initialization Pinning (CHK-JDK-17):** `<clinit>` retains native VM frames, pinning carriers across all JDK versions (JEP 491 CSR `JDK-8338813`).
11. **POSIX File I/O Carrier Blocking (CHK-JDK-18):** File operations have no non-blocking readiness mechanism in Linux/macOS and rely on `ManagedBlocker` carrier expansion.
12. **dotCMS Migration Rollback (CHK-JDK-19):** Real-world rollback of virtual threads in caching layer due to file I/O lock contention (PR #36900).
13. **Asymptotic Queueing Saturation Bounds (METH-01):** An exclusive 500 ms critical section enforces an absolute capacity ceiling of $\mu = 1/D = 2.0\text{ req/s}$ ([Denning & Buzen 1978](https://doi.org/10.1145/356744.356747)).
14. **Statistical Rigor on the JVM (METH-04):** 3 process trials ($df=2$) cannot support inferential confidence intervals; qualitative mechanism trials are defensible ([Georges et al. 2007](https://doi.org/10.1145/1297027.1297033); [Kalibera & Jones 2013](https://doi.org/10.1145/2464157.2464160)).
15. **Theoretical Framing for Mutexes (METH-07):** In-memory lock serialization is governed by [Bernstein's Conditions (1966)](https://doi.org/10.1109/PGEC.1966.264565) and [Amdahl's Law (1967)](https://doi.org/10.1145/1465482.1465560).
16. **PostgreSQL Socket Pinning Fix (FC-01):** `pgjdbc >= 42.6.0` refactored `QueryExecutorImpl` to `ReentrantLock` (Issue #1951, PR #2629).
17. **MySQL 8.4 LTS Socket Pinning (FC-02):** Connector/J 8.4 LTS still pins on socket reads; fix landed exclusively in Connector/J 9.0.0+ (Bug #109346).
18. **HikariCP Architecture (FC-05, CHK-JDK-23):** Lock holds are sub-microsecond in-memory transitions; pool waits unmount via `LockSupport.park()` (Issue #1463, PR #2055).
19. **Connection Pool Backpressure (FC-06):** Billy Korando (Inside Java Sip #94) warns against layering Semaphores over connection pools.
20. **Tomcat NioEndpoint Architecture (FC-11):** `Acceptor` and `Poller` remain OS platform threads; connections are bounded by TCP backlog (`acceptCount`) and `maxConnections`.
21. **Jackson 2.16+ BufferRecycler Fix (FC-18):** `JsonRecyclerPools.sharedLockFreePool()` resolves ThreadLocal buffer heap bloat (Issue #1089).
22. **OpenTelemetry Contention (FC-24):** `WeakConcurrentHashMap` synchronization pinned carriers in agent $\le 1.32.0$ (Issue #9534, PR #10747).

#### Category B: Claims Requiring Verification Against This Project's Actual Experimental Evidence
*These claims are directly related to the project's empirical artifact, scripts, and results, and must be audited in the upcoming experimental review:*
1. **JFR Threshold Configuration in Harness:** Did `run-benchmark.sh` execute with a custom `.jfc` with `threshold=0ms`, or did it use default `profile.jfc` (masking sub-20ms pinning)?
2. **Metric Aggregation Window:** Does the reported throughput of ~1.96 req/s reflect the entire 55-second run window in `normalize_evidence.py`, and what are the exact metrics if filtered to $[15\text{s}, 45\text{s}]$?
3. **Native JFR Telemetry:** Do the 27 raw JFR recordings for `/native` contain strictly zero `jdk.VirtualThreadPinned` events, and what do carrier thread CPU telemetry traces show during the 500 ms `nanosleep`?
4. **Resolved Dependency Versions:** What exact versions of `postgresql`, `h2`, `spring-boot`, and `jackson` are resolved in `pom.xml` via `mvn dependency:tree`?
5. **Tomcat Configuration in Artifact:** Are `server.tomcat.threads.max`, `accept-count`, and `max-connections` configured in `application.yml`, and is `server.shutdown: graceful` enabled?
6. **HikariCP Configuration & Telemetry:** Is `maximumPoolSize` set to 10 in `application.yml`? Did any `/orders` benchmark runs trigger `SQLTransientConnectionException` timeouts, and were any pinning events observed?
7. **Replication Variance Across Process Runs:** What is the exact spread (min, max, median) across the 3 process trials in the primary matrix in `results/`?
8. **JVM Flag Consistency:** Do all admitted run manifests in `results/` confirm identical runtime flags (`-Djdk.virtualThreadScheduler.parallelism=1`, `-Djdk.virtualThreadScheduler.maxPoolSize=1`)?

#### Category C: Claims Outside the Thesis's Scope
*These claims are tangential, speculative, or require external environments, and must not expand the empirical scope:*
1. **Energy Benchmarking (RAPL):** Stocker & Wahler (2026) energy evaluation requires bare-metal Linux servers with RAPL registers; relegated to Section 6.4/8.7.
2. **Comparative Runtime Benchmarking:** Benchmarking Go, C# (.NET `async2`), Rust (Tokio), or Erlang (BEAM); restricted to conceptual background in Section 2.1.1/3.6.1.
3. **Downstream Vendor HotSpot Forks:** Alibaba Dragonwell Wisp 2.0 and Tencent Kona Fiber coroutine engines; retained as a historical footnote.
4. **Message Broker Storage Internals:** ActiveMQ Classic KahaDB lock pinning (AMQ-9428); thesis is strictly an HTTP MVC application.
5. **Linux CFS Bandwidth Quota Throttling (METH-14):** Speculative kernel scheduling conjecture; mentioned only as an unverified limitation in Section 8.5.
6. **Value-Based Lock Algorithms:** Dave Dice & Alex Kogan Hapax Locks (PPoPP 2026); theoretical research prototype outside Java 21 LTS.
7. **Alternative Embedded Database Rewrites:** SQLite JDBC JNI carrier occupation; supporting literature only, no endpoint implementation.

---

### 9.7 Focused Questions for the Upcoming Experimental Audit

The upcoming experimental audit must answer the following eight specific, verifiable questions by inspecting the project's codebase, benchmark scripts, raw k6 output, and JFR recordings:

1. **Flight Recorder Settings Audit:**  
   *What exact `-XX:StartFlightRecording` parameters were passed in `run-benchmark.sh` across the primary experimental runs?* Specifically, did the command line specify `settings=profile`, a custom `.jfc` template, or `-Djdk.tracePinnedThreads=full`? Did the recording capture or discard pinning events under 20 ms?
2. **Normalization Window Verification:**  
   *In `scripts/normalize_evidence.py`, does `k6_metrics()` filter points by timestamp or aggregate the entire raw JSON stream?* If points are restricted to the steady-state hold window ($15\text{s} \le t \le 45\text{s}$), what are the exact re-calculated values for request count, mean throughput, p50, p95, and p99 latency on `/payments`?
3. **JNI Carrier Telemetry in JFR:**  
   *In the raw JFR recordings for `/native` (e.g., `recording-20261015-1508*.jfr`), what thread state events are recorded during the 500 ms `nanosleep`?* Does JFR confirm that carrier threads were in the `_thread_in_native` state while emitting exactly zero `jdk.VirtualThreadPinned` events?
4. **Effective Dependency Tree Audit:**  
   *What are the exact resolved dependency versions in `pom.xml` (`mvn dependency:tree`)?* Specifically, what versions of `org.postgresql:postgresql`, `com.h2database:h2`, `com.fasterxml.jackson.core:jackson-databind`, and `com.zaxxer:HikariCP` are packaged into the application? Are any vulnerable driver versions present?
5. **Servlet Container Runtime Configuration:**  
   *How is the embedded Apache Tomcat container configured in `src/main/resources/application.yml`?* Are `accept-count`, `max-connections`, and worker thread pools configured, and is `server.shutdown: graceful` active?
6. **HikariCP Configuration and Error Manifestation:**  
   *In `application.yml`, what is the configured `maximum-pool-size` (10)?* During the `/orders` load tests with 10 VUs, did JFR or application logs record any `SQLTransientConnectionException` timeouts, and does the JFR event log confirm zero carrier pinning during connection acquisition?
7. **Trial-Level Dispersion and Experimental Unit Analysis:**  
   *What is the exact numerical spread (min, max, median, standard deviation) across the 3 process trials in the primary synchronization matrix?* Does the within-treatment dispersion remain sufficiently small to defend the 3 trials as reliable mechanism-isolation units?
8. **JVM Scheduler and Flag Consistency in Manifests:**  
   *Do all admitted run manifests in `results/run-manifest-*.json` record identical JVM flags?* Specifically, confirm that `-Djdk.virtualThreadScheduler.parallelism=1` and `-Djdk.virtualThreadScheduler.maxPoolSize=1` were applied consistently across all primary and control treatments.
