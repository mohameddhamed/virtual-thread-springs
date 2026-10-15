# Thesis Outline: Virtual Threads & Spring Boot Migration

**Title:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines

---

## 1. Introduction

This thesis investigates the practical challenges of adopting Java 21 Virtual
Threads (Project Loom) in existing Spring Boot MVC applications. The study
does not assume that every blocking or legacy pattern causes pinning; it
separates monitor pinning, application serialization, finite-resource
contention, and native-boundary carrier occupation.

**Research Questions:**
- RQ1: How do legacy synchronization mechanisms impact Virtual Thread performance due to thread pinning?
- RQ2: What architectural anti-patterns must be refactored before enabling Virtual Threads to prevent degradation?

**Contributions:**
- A mechanism-focused catalog of migration risks, with measured and unestablished
  claims clearly separated
- Correctness-preserving synchronization alternatives and their semantic trade-offs
- A practical migration checklist tied to JFR, endpoint isolation, resource
  auditing, and explicit limitations

---

## 2. Background: Virtual Threads & Thread Pinning

### 2.1 Project Loom and Virtual Threads

Virtual Threads are lightweight threads managed by the JVM, not the OS. A single Carrier Thread (OS thread) can schedule millions of Virtual Threads, switching between them when blocking operations occur.

**Key benefits:**
- Millions of concurrent threads with minimal memory overhead (~100 bytes per VT vs. 1-2 MB per OS thread)
- Automatic blocking point handling (no explicit async/await)
- Seamless Spring Boot integration (drop-in replacement for platform threads)

**Limitation:** Performance gains depend on the blocking operation and the
runtime boundary. In Java 21, the tested intrinsic-monitor treatment produced
pinning evidence; ordinary Java blocking can unmount, while long native
execution requires separate investigation.

### 2.2 Thread Pinning Definition

**Thread pinning** occurs when a Virtual Thread cannot safely unmount from its Carrier Thread during a blocking operation. The Carrier Thread remains blocked, preventing other Virtual Threads from executing.

**Mechanisms studied:**
1. **Intrinsic locks (`synchronized`)** in the Java 21 primary treatment
2. **Long native/JNI execution** as a separate carrier-occupation boundary
3. **Ordinary blocking and JDBC** as controls that must not be labelled pinning
   without direct mechanism evidence

**Impact:**
- Throughput collapses to levels worse than platform threads
- Latency becomes highly variable
- System can enter cascading failure under load

### 2.3 Detection: Java Flight Recorder (JFR)

The JVM emits `jdk.VirtualThreadPinned` events whenever pinning occurs. JFR can capture these events with stack traces, identifying root causes.

---

## 3. Related Work

### 3.1 Virtual Threads in the Wild

- **Spring Framework 6.1+** (2023): Added VT support; Spring Boot 3.2+ enables by default (experimental)
- **Quarkus** (2022): Early VT support; showcased 10x throughput gains on I/O-bound workloads
- **Helidon** (2021): VT-first design; influenced Java standard library decisions

### 3.2 Thread Pinning Literature

- **Loom Design Documents** (OpenJDK): Detailed pinning mechanics and limitations
- **DaCapo & Renaissance Benchmarks**: VT performance evaluation on real workloads
- **Industry Reports**: Adoption challenges (synchronized blocks in legacy code, ThreadLocal patterns)

### 3.3 Gap Addressed by This Work

Most research focuses on *new* systems designed for VTs. **This thesis focuses on legacy systems** with existing anti-patterns, which is the dominant industry scenario.

---

## 4. Methodology: Demo Application Design

### 4.1 System Architecture

A deliberately realistic Spring Boot MVC application simulating a payment processing system:

**Three endpoints:**
1. **GET /orders**: Slow JDBC query (300ms) with ThreadLocal context
2. **POST /payments**: External API call (500ms) with synchronization
3. **GET /products**: Fast query with no anti-patterns (control group)

### 4.2 Intentional Treatments and Risks

| Endpoint | Anti-pattern | Severity | Cause |
|----------|---|---|---|
| /orders | ThreadLocal + blocking JDBC-shaped work | Context/resource risk | Lifecycle and finite-resource audit |
| /orders | Hikari pool size sensitivity | Secondary treatment | Resource contention, not assumed pinning |
| /payments | `synchronized` around blocking work | Primary mechanism treatment | Java 21 monitor pinning |
| /native | Long JNI/native call | Boundary risk | Carrier occupation assessed separately |

### 4.3 Experimental Setup

**Variables:**
- **Thread mode:** Platform Threads (baseline) vs. Naive Virtual Threads vs. Refactored Virtual Threads
- **Load:** 50, 100, 200 concurrent users (virtual users in k6)
- **Duration:** 60 seconds per test

**Metrics:**
- Throughput (requests/sec)
- Latency (p50, p95, p99, max)
- Error rate
- JFR pinning events

**Platform:** macOS on Apple Silicon, 8 logical CPUs; Java 21.0.8 Zulu for the
primary study. H2 and Dockerized PostgreSQL are analysed as separate
environments.

---

## 5. Results & Analysis

The current result tables and interpretations are maintained in
`docs/research-synthesis.md`. Earlier mixed-workload pilot tables in this file
were superseded because their raw-artifact mapping was incomplete.

### 5.1 Baseline: Platform Threads

The earlier mixed-workload platform table is not retained as a final result
because its artifact-to-configuration mapping was incomplete. The retained
platform control is the matched Java 21 `/payments` condition shown in the
primary matrix below. Platform-thread runs are interpreted as a control for
that isolated protocol, not as a universal Tomcat capacity estimate.

### 5.2 Java 21 primary synchronization matrix

| Condition | Mean requests | Mean p50 | Mean p95 | Pinning evidence |
|---|---:|---:|---:|---:|
| Virtual Threads + `synchronized` | 110.0 | 3,923.86 ms | 7,957.50 ms | 110/run |
| Virtual Threads + `ReentrantLock` | 108.7 | 4,941.99 ms | 4,967.54 ms | 0/run |
| Virtual Threads + no-lock diagnostic | 710.7 | 507.66 ms | 512.84 ms | 0/run |
| Platform threads + `synchronized` | 110.0 | 3,936.42 ms | 9,002.48 ms | N/A |

All runs had zero HTTP failures. The lock replacement removed the observed
monitor-pinning evidence but did not remove serialization.

---

## 6. Anti-Patterns & Pinning Analysis

See `docs/anti-patterns.md` for detailed catalog:

1. **synchronized block in PaymentService** (CRITICAL)
   - Cause: intrinsic monitor around blocking work
   - Impact: direct `jdk.VirtualThreadPinned` evidence in the tested Java 21
     condition
   - Fix: Replace or redesign only after preserving the synchronization
     contract

2. **ThreadLocal in OrderService** (MEDIUM)
   - Cause: request-context lifecycle and allocation risk
   - Impact: no leak, GC, or pinning effect was measured in this study
   - Fix: guarantee cleanup; consider request scope or explicit context passing

3. **Unbounded JDBC blocking** (MEDIUM)
   - Cause: finite database capacity can become a queueing bottleneck
   - Impact: no material pool-size effect was exposed in the tested H2 and
     PostgreSQL closed-loop sensitivity runs
   - Fix: measure active/pending connections and tune for the real workload

---

## 7. Migration Guidelines

See `docs/migration-guidelines.md` for practical checklist:

**Pre-Migration Steps:**
1. Audit synchronized blocks → replace with ReentrantLock
2. Scan ThreadLocal → verify request-scoped, ensure cleanup
3. Check JDBC pool config → tune for VT concurrency
4. Add I/O timeouts → prevent cascading failures
5. Verify VT-compatible framework versions

**Post-Migration Monitoring:**
- Enable JFR for pinning event detection
- Monitor throughput, latency, GC pauses, memory

---

## 8. Discussion

### 8.1 Implications for Industry

- Virtual Threads are **not** a "drop-in replacement"; legacy code must be audited
- **Most benefit** comes from I/O-bound systems with many concurrent connections
- **Thread pinning** is the primary barrier; tools (JFR) make diagnosis feasible
- **Framework support** is critical; Spring 6.1+ and modern ORM versions ease migration

### 8.2 Limitations of This Study

- Single application design; other workload patterns may show different results
- No production-scale testing (millions of VTs under real load)
- JFR analysis on dev machine; production monitoring setup requires additional tooling
- DB performance not optimized (query plan analysis beyond scope)

### 8.3 Future Work

- Performance comparison with async/reactive (WebFlux) patterns
- JFR tooling to automate anti-pattern detection
- Case studies of production migration (when available)
- Native image (GraalVM) compatibility with Virtual Threads
- Interaction with Project Leyden (sealed classes, pre-initialization) for startup time

---

## 9. Conclusion

The current evidence supports a narrower and more defensible conclusion:

1. In the tested Java 21 condition, `synchronized` around blocking work
   produced direct Virtual Thread monitor-pinning evidence.
2. `ReentrantLock` removed that monitor-pinning evidence but did not remove the
   serialized payment bottleneck.
3. ThreadLocal, JDBC pool size, native execution, and newer JDK behavior must
   be analysed as separate mechanisms rather than folded into one pinning
   claim.
4. A safe migration procedure therefore begins with mechanism evidence,
   semantic correctness, resource-capacity checks, and repeatable comparison.

The complete current result map is `docs/research-synthesis.md`.

---

## References

- [JEP 444: Virtual Threads (Preview)](https://openjdk.org/jeps/444)
- [Virtual Threads Best Practices](https://loom.openjdk.org/)
- [Spring Framework 6.1 Virtual Threads](https://spring.io/blog/2023/09/09/all-together-now-spring-boot-3-2-graalvm-native-images-and-virtual-threads)
- [HikariCP Connection Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- [Structured Concurrency in Java (JEP 453)](https://openjdk.org/jeps/453)