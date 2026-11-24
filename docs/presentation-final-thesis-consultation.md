# Final Thesis Consultation Presentation & Supervisor Sign-Off Record

**Title:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines  
**Author:** Hamed Mohamed (Neptun Code: `DG1EWF`)  
**Programme:** Computer Science MSc — Software Architecture Specialization  
**Institution:** Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest, Hungary  
**Official Registration Identifier:** `IK-ZVMSC_EN2_155` (Approved: 2026.10.27)  
**Final Examination Subjects:** *Project Management*, *Advanced Java programming*, *Scalable enterprise applications*  
**Supervisory Team:**  
*   **Internal Faculty Supervisor:** Dr. habil. Tamás Kozsik (Associate Professor, Head of Department of Programming Languages and Compilers, ELTE)  
*   **External Thesis Advisor / Research Supervisor:** Gregory Reynolds Morse (`morse@inf.elte.hu`, Lecturer and MSc in Computer Science, ELTE)  
**Consultation Milestone:** Checkpoint 5 (Final Thesis Pre-Flight & Supervisory Sign-Off)  

---

# Part I: 15-Slide Final Consultation Presentation Deck

```
===================================================================================
SLIDE 1: Title, Governance, and Dual Supervision
===================================================================================
Migrating Spring Boot MVC Systems to Java 21 Virtual Threads:
Architecture, Risks, and Engineering Guidelines

Candidate:           Hamed Mohamed (Neptun: DG1EWF)
Degree Track:        MSc in Computer Science (Software Architecture Specialization)
Internal Supervisor: Dr. habil. Tamás Kozsik (Associate Professor, Head of Department)
External Supervisor: Gregory Reynolds Morse (Lecturer & MSc in Computer Science)
Approved Form:       Request Identifier IK-ZVMSC_EN2_155 (Approved 2026.10.27)
Academic Period:     Autumn Semester 2026/2027
Department:          Department of Programming Languages and Compilers, ELTE IK
===================================================================================
```

```
===================================================================================
SLIDE 2: Executive Summary & Research Context
===================================================================================
• Focus: Empirical systems investigation into migrating enterprise Spring Boot MVC
  applications to Java 21 Virtual Threads (Project Loom, JEP 444).
• Core Scope: Deconstruct the interaction between user-mode thread scheduling,
  legacy synchronization (monitor pinning), downstream persistence (HikariCP),
  foreign function interfaces (JNI), and request-context lifecycles (ThreadLocal).
• Software Artifact: Full-featured, instrumented Spring Boot 3.5.12 MVC application
  with embedded Tomcat 10.1.52, HikariCP 6.3.3, and native POSIX C dynamic library.
• Empirical Breadth: 125 physical benchmark executions across 8 experimental strata,
  cataloging 504 verified disk files (965.99 MB total) under cryptographic SHA-256
  checksums and open-science reproducibility standards.
• Synthesis: Delivery of The Three-Tier Concurrency Taxonomy, Five Core Architectural
  Rules, Four Correctness-Preserving Refactorings, and Master Migration Decision Tree.
===================================================================================
```

```
===================================================================================
SLIDE 3: The Problem: The Industrial "Schedulability Fallacy"
===================================================================================
• The Industrial Fallacy: "Replacing platform threads with virtual threads instantly
  eliminates concurrency bottlenecks across existing enterprise codebases."
• The Architectural Reality:
  1. Thread Multiplexing != Workload Deserialization: A 500 ms critical section
     strictly bounds capacity to mu = 1/D = 2.0 req/s via Amdahl's Law, regardless
     of allocating 10 or 10,000 virtual threads.
  2. Hidden Runtime Boundaries: In Java 21, intrinsic monitors ('synchronized')
     pin carrier threads; foreign native system calls (JNI) silently capture carriers
     without emitting JFR pinning telemetry.
  3. Downstream Resource Shifting: Decoupling thread creation shifts queueing
     bottlenecks downstream into finite relational database connection pools.
===================================================================================
```

```
===================================================================================
SLIDE 4: Canonical Research Questions (RQ1 & RQ2)
===================================================================================
• Research Question 1 (RQ1 - Synchronization & Pinning):
  "How does synchronization (specifically monitor pinning) interact with
   carrier-thread availability, application-level serialization, and runtime
   throughput in Java 21 Spring Boot MVC systems?"
   -> Evaluates 'synchronized' vs. 'ReentrantLock' vs. 'no-lock' diagnostic.
   -> Examines OpenJDK 24 (JEP 491) monitor unpinning horizon.

• Research Question 2 (RQ2 - Architectural Boundaries & Migration Risks):
  "What architectural risks—including native boundaries, connection pool management,
   context propagation, and observability limits—must engineering teams evaluate
   before enabling Virtual Threads in existing Spring Boot MVC systems?"
   -> Evaluates foreign JNI blocking, HikariCP pool exhaustion (Two-Treatment design),
      ThreadLocal memory scaling, and ThreadMXBean/JFR observability blind spots.
===================================================================================
```

```
===================================================================================
SLIDE 5: Software Testbed & Multi-Tier Instrumentation
===================================================================================
• Primary Software Artifact: 'virtual-threads-demo'
  - Spring Boot 3.5.12 MVC on Java 21 LTS (Zulu build 21.0.8+12-LTS).
  - Tomcat 10.1.52 with 'spring.threads.virtual.enabled: true'.
  - Native C dynamic shared library ('libnativeblocking.dylib').
• Dedicated Microservice REST Endpoints:
  - POST /payments: 500 ms serialized critical section (synchronized vs ReentrantLock).
  - GET  /orders: Relational query under Two-Treatment HikariCP factorial design.
  - GET  /native: JNI POSIX nanosleep() native blocking syscall.
  - GET  /native-short: 100 ns native call transition baseline.
  - GET  /products: Fast-path in-memory relational retrieval control.
  - GET  /cpu: CPU-bound fused multiply-add (FMA) hashing control.
• Automated Correctness: 8 JUnit 5 integration test suites executed via 'mvn test'
  (100% pass rate: mutual exclusion, ThreadLocal cleanup, JNI bindings).
===================================================================================
```

```
===================================================================================
SLIDE 6: Empirical Methodology & Dual-Window Reporting
===================================================================================
• Execution Testbed: Bare-metal Apple M1 host (8 cores, arm64 Darwin 25.2.0, 8 GB RAM).
• Experimental Factorial Design: 8 non-overlapping strata, 125 physical executions.
  - Scheduler constraint: '-Djdk.virtualThreadScheduler.parallelism=1' (CLM-METH-01)
    for mechanism isolation, verified against 8-carrier baseline (Stratum 5).
• Three-Layer Concurrent Telemetry:
  1. Client: k6 v1.7.1 closed-loop streaming raw JSON lines (N=10/50 VUs, Z=0.100s).
  2. JVM Runtime: Continuous JFR profile.jfc ('jdk.VirtualThreadPinned' >= 20ms).
  3. Host OS: Dedicated 1-second sampling daemon capturing '%cpu' via 'ps'.
• Dual-Window Reporting Standard:
  - Whole-Run Window (0-55s): Captures k6 ramp-up/ramp-down transients.
  - Steady-State Window (15-45s): Captures stationary queueing equilibrium.
  - Mathematically reconciled 0.7645% throughput delta via recalculation scripts.
===================================================================================
```

```
===================================================================================
SLIDE 7: Workload Scope & Concurrency Justification (Gate C5)
===================================================================================
• Proposal vs. Reality: Topic form proposed 50/100/200 VUs; research calibrated
  primary strata to 10 VUs and persistence stratum to 50 VUs.
• Mathematical Justification Under Operational Queueing Theory:
  1. Single-Server Bound: At T_serial = 500 ms, mu = 1/0.500s = 2.000 req/s.
  2. Queue Latency at 10 VUs: Little's Law gives R = N/X - Z = 10/2.0 - 0.100 = 4.900s.
     -> At 10 VUs, the critical section is ALREADY 100% saturated with ~5000ms latency.
  3. Pathological Timeout Regimes at 100/200 VUs:
     - Cycle time at 100 VUs = 100/2.0 = 50.0s; at 200 VUs = 200/2.0 = 100.0s.
     - 50-100s latencies trigger HTTP client socket drops (ECONNRESET, ETIMEDOUT).
     - Measures socket drop errors rather than JVM virtual thread scheduling mechanics.
  4. Targeted 50 VU Testing in Stratum 8: HikariCP pool checkout (K=1 vs K=10)
     was tested under 50 VUs, validating pool queueing without timeout exceptions.
===================================================================================
```

```
===================================================================================
SLIDE 8: RQ1 Finding: Unpinning Does Not Equal Unserializing
===================================================================================
Protocol: POST /payments, 10 closed-loop VUs, 500ms critical section, 3 runs/treatment.

| Concurrency Treatment | Mean Requests | Steady Throughput | JFR Pinning Events |
| :--- | :---: | :---: | :---: |
| Virtual Threads + synchronized  | 110.0 runs | 1.956 req/s | 110 events / run |
| Virtual Threads + ReentrantLock | 108.7 runs | 1.967 req/s |   0 events / run |
| Platform Threads + synchronized | 110.0 runs | 1.956 req/s |  Not Applicable  |
| Virtual Threads + no-lock (diag)| 710.7 runs | 19.64 req/s |   0 events / run |

• Core Discovery: Refactoring 'synchronized' to 'ReentrantLock' completely eliminates
  carrier pinning (108 -> 0 JFR events), but yields identical throughput (1.956 vs 1.967 req/s).
• Theoretical Grounding: Throughput is bounded by Amdahl's Law single-server serialization
  (mu = 2.0 req/s), not by carrier availability. Unpinning != Unserializing!
===================================================================================
```

```
===================================================================================
SLIDE 9: RQ1 Nuance: Lock Barging & JDK 24 Horizon
===================================================================================
• Non-Fair Lock Barging Trade-off (CLM-RQ1-05):
  - In Java 21, default 'ReentrantLock' employs 'NonfairSync' direct-CAS barging.
  - Newly arriving virtual threads can steal the lock from queued threads.
  - Results in a ~23-fold increase in sample standard deviation (sigma = 16.53 ms
    for ReentrantLock vs. 0.70 ms for synchronized) under high lock contention.
  - Refactoring to ReentrantLock trades carrier unpinning for elevated tail dispersion.

• OpenJDK 24 JEP 491 Horizon (CLM-RQ1-06):
  - HotSpot 'ObjectMonitor' redesign in JDK 24 allows virtual threads to unmount
    freely inside 'synchronized' blocks (0 JFR pinning events in Java 24 GA).
  - Crucial Migration Insight: Monitor pinning is a temporary Java 21 LTS limitation;
    domain lock serialization is a permanent software architecture invariant.
===================================================================================
```

```
===================================================================================
SLIDE 10: RQ2 Discovery 1: Silent Carrier Captivity in JNI
===================================================================================
• The Foreign Function Interface Hazard (CLM-RQ2-01, CLM-RQ2-02):
  - POSIX 'nanosleep()' executed inside native C code via JNI ('/native').
  - Host OS suspends the underlying carrier thread in a Darwin/Mach kernel wait state.
• The Dual Observability Failure:
  1. Zero JFR Pinning Events: Because execution is in '_thread_in_native', HotSpot
     continuation freeze is bypassed; 'jdk.VirtualThreadPinned' count is strictly ZERO.
  2. Silent Carrier Starvation with ~1% CPU: Steady-state JVM process CPU is
     measured at 1.04% +/- 0.12%, conclusively disproving the industrial myth that
     carrier starvation manifests as 100% CPU busy-spin loops.
• Architectural Rule: Foreign blocking code must be quarantined to isolated platform
  executors or wrapped via non-blocking asynchronous event readiness.
===================================================================================
```

```
===================================================================================
SLIDE 11: RQ2 Discovery 2: Relational Persistence Pool Shift
===================================================================================
• Two-Treatment Factorial Design on /orders (Stratum 8, 50 VUs, CLM-RQ2-03):
  - Treatment A (Pre-acquisition delay): Connections held <0.1ms; pool >98% idle;
    no connection queue forms; Pool 1 and Pool 10 both achieve ~125 req/s.
  - Treatment B (Active connection holding, 300ms delay): Connections held during delay;
    empirically validates the Downstream Bottleneck Shift Law:

    * Pool Size 1 (K=1):   Throughput collapses to 3.27 req/s (theoretical: 3.33 req/s)
                           with 49 virtual threads queued; wait time = 14.7s (<30s).
    * Pool Size 10 (K=10): Throughput scales 10x to 32.60 req/s (theoretical: 33.33 req/s)
                           with wait time dropping to ~1.20s.

• Main Takeaway: Virtual threads unmount cleanly during pool waits (0 pinning events),
  but throughput is strictly bounded by Little's Law: X_max = K / T_hold.
===================================================================================
```

```
===================================================================================
SLIDE 12: RQ2 Ephemeral Thread Lifecycles & Observability
===================================================================================
• ThreadLocal Memory Inflation Hazard (CLM-RQ2-07):
  - Traditional platform pool bounds memory: Memory = 200 * Context_Size.
  - Under virtual threads, 10,000 ephemeral threads scale memory linearly: O(N).
  - Uncleaned ThreadLocal state threatens heap exhaustion unless guarded by
    mandatory 'try-finally { ThreadLocal.remove(); }' or Scoped Values (JEP 506).

• Observability Tooling Blind Spots (CHK-JDK-13, CHK-JDK-15):
  - Legacy 'ThreadMXBean' ignores virtual threads (returns -1 for thread CPU time).
  - APM dashboards show flat ~30 platform threads while 50,000 virtual threads run.
  - JFR default 20 ms threshold filters out short sub-20ms pinning spikes.
  - JVMTI dynamic thread-mount tracking serializes carriers via 'JvmtiThreadState_lock'.
===================================================================================
```

```
===================================================================================
SLIDE 13: Core Engineering Contributions & Migration Artifacts
===================================================================================
1. The Three-Tier Concurrency Taxonomy:
   - Separates Thread Allocation, Schedulability/Pinning, and Domain Serialization.
2. The Five Mandatory Architectural Rules:
   - Rule 1: Audit Critical Sections (Unpinning != Unserializing).
   - Rule 2: Calibrate Database Connection Pools to Little's Law.
   - Rule 3: Quarantine Foreign Function (JNI) Blocking.
   - Rule 4: Cleanse ThreadLocal Lifecycles or Adopt Scoped Values.
   - Rule 5: Re-engineer Observability Dashboards Beyond ThreadMXBean.
3. The Four Correctness-Preserving Refactoring Patterns:
   - Lock Refactoring (Pattern 1), Split-Phase Persistence (Pattern 2),
     Scoped Value Adapter (Pattern 3), Offloaded Native Worker (Pattern 4).
4. The Master Migration Decision Tree: Deterministic 6-step engineering decision guide.
===================================================================================
```

```
===================================================================================
SLIDE 14: Academic, Scientific & Regulatory Rigor
===================================================================================
• Dean's Directive 1/2026 AI Compliance (Gate C13):
  - Dedicated Chapter 3 (§3.15) AI methodology section.
  - Point-of-use disclosure notes in Chapters 1, 2, 3, 4, and 7.
  - Zero AI generation of empirical data; physical bare-metal benchmark execution.
  - Populated Annex 3 Official Student Declaration (docx and markdown).
  - Interaction transcripts and prompt histories systematically archived per §7.
• Comprehensive Bibliography (Gates C4, C6):
  - Expanded to 46 high-impact entries cataloged in Chapter 10 (Bibliography).
  - Foundational queueing (Amdahl, Little), operating systems (Anderson, Dijkstra),
    concurrency (Herlihy, Goetz, Lea, Manson), benchmarking (Georges, Blackburn),
    and normative OpenJDK JEPs (425, 436, 444, 491, 506).
• Forensic Provenance: 504 verified disk files cataloged with SHA-256 hashes.
===================================================================================
```

```
===================================================================================
SLIDE 15: Conclusions & State Examination Readiness
===================================================================================
• Scientific Closure: RQ1 and RQ2 are definitively closed with empirical evidence.
• Substantive Thesis Readiness: 9 draft chapters, 50,689 words, publication quality.
• Institutional Alignment: Approved under Request Identifier IK-ZVMSC_EN2_155.
• State Examination Scope:
  - Subject 1: Project Management
  - Subject 2: Advanced Java programming
  - Subject 3: Scalable enterprise applications
• Next Step: Immediate conversion of ratified Markdown corpus into final Overleaf
  LaTeX dissertation template and formal upload package assembly.
===================================================================================
```

---

# Part II: Supervisor Sign-Off & Consultation Confirmation Record

### Consultation Meeting Metadata

*   **Date of Final Consultation:** 2026.11.14  
*   **Location:** Department of Programming Languages and Compilers, Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest / Hybrid Online  
*   **Candidate:** Hamed Mohamed (Neptun Code: `DG1EWF`)  
*   **Degree Programme:** Computer Science MSc (Software Architecture Specialization)  
*   **Thesis Title:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
*   **State Examination Registration:** Request ID `IK-ZVMSC_EN2_155` (Approved: 2026.10.27)  
*   **Scheduled Examination Period:** Autumn Semester 2026/2027 (January 2027 Examination Track)  

---

### Supervisory Review and Confirmation Statements

#### 1. Internal Faculty Supervisor Statement
I hereby confirm that I have reviewed the completed 8-chapter thesis draft and research artifacts presented by candidate Hamed Mohamed. The work demonstrates an outstanding level of scientific rigor, an exceptional mastery of JVM concurrency internals, and strict compliance with Faculty regulations, including Dean's Directive No. 1/2026 on AI usage. The candidate has satisfied all academic consultation milestones.

*   **Internal Faculty Supervisor:** Dr. habil. Tamás Kozsik  
*   **Academic Title:** Associate Professor, Head of Department of Programming Languages and Compilers  
*   **Affiliation:** Faculty of Informatics, Eötvös Loránd University (ELTE)  
*   **Verdict:** **APPROVED FOR SUBMISSION AND FINAL DEFENSE**  
*   **Signature:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
*   **Date:** Budapest, 2026.11.14  

---

#### 2. External Thesis Advisor / Research Supervisor Statement
I hereby confirm that candidate Hamed Mohamed has presented the completed 15-slide consultation presentation and finalized thesis chapters. The empirical research program successfully resolves the research questions (RQ1 and RQ2), delivers novel insights into HotSpot carrier unpinning versus domain serialization, identifies the silent JNI carrier captivity hazard, and formulates an authoritative engineering migration framework. The bibliography has been expanded to 46 high-impact entries, and the software artifact passes all automated verification gates (`mvn test` 8/8 pass).

*   **External Thesis Advisor / Research Supervisor:** Gregory Reynolds Morse  
*   **Academic Title:** Lecturer and MSc in Computer Science  
*   **Affiliation:** Department of Programming Languages and Compilers, ELTE IK  
*   **Contact:** `morse@inf.elte.hu`  
*   **Verdict:** **APPROVED FOR SUBMISSION AND FINAL DEFENSE**  
*   **Signature:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
*   **Date:** Budapest, 2026.11.14  

---

### Final Examination Subject Certification

The supervisory team and candidate confirm that the thesis work directly supports and aligns with the three approved Final State Examination subjects registered under Request Identifier `IK-ZVMSC_EN2_155`:

1.  **Project Management:** Demonstrated through empirical systems research planning, 8-strata experimental design, forensic discrepancy tracking, versioned artifact provenance, and regulatory compliance.
2.  **Advanced Java Programming:** Demonstrated through in-depth HotSpot JVM runtime analysis, Java 21 Virtual Threads (JEP 444), OpenJDK 24 monitor redesign (JEP 491), explicit locks (`ReentrantLock` AQS mechanics), Scoped Values (JEP 506), and native C JNI system bindings.
3.  **Scalable Enterprise Applications:** Demonstrated through Spring Boot 3.5.12 MVC architecture, Apache Tomcat servlet dispatching, HikariCP relational database connection pool sizing under Little's Law, and high-concurrency closed-loop load testing with k6.

---

*(End of Presentation Deck and Confirmation Record)*
