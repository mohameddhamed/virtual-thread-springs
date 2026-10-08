# Experimental Indicator and JDK-Boundary Research

**Date:** 8 October 2026
**Project:** Spring Boot MVC and Java 21 Virtual Threads

## 1. Are the three current paths sufficient?

Yes, as experimental roles; no, as complete causal evidence by themselves.

| Path | Retain as | What it can show now | Limitation |
|---|---|---|---|
| `/payments` | Primary synchronization treatment | Blocking work under a serialized payment critical section; candidate Java 21 pinning path | The current checkout contains only `ReentrantLock`; the synchronized treatment must be restored as a fixed, traceable variant |
| `/orders` | Blocking data/resource treatment | JDBC-like blocking, request-context lifecycle, and possible finite-pool contention | The current `ThreadLocal` is cleaned up in `finally`; no leak is demonstrated, and pool waits are not yet measured |
| `/products` | Clean control and interference observer | Fast work without intentionally introduced anti-patterns; possible cross-endpoint interference | Mixed-workload degradation alone cannot prove carrier starvation or pinning causality |

The endpoint design is therefore sound, but the study needs stronger **contrasts** rather than more similar endpoints.

## 2. Recommended additions

### A. Endpoint-isolated workloads — recommended

Add separate k6 workloads for `/orders`, `/payments`, and `/products`, while retaining the current mixed script as a secondary whole-system workload. This separates endpoint-specific behavior from request-order and cross-endpoint interference.

### B. Explicit payment variants — essential

Maintain fixed source/JAR variants for:

1. `synchronized` around the 500 ms blocking section;
2. `ReentrantLock` around the same section;
3. no lock around the sleep as a concurrency upper-bound control.

The no-lock variant is not a valid payment implementation; it is a diagnostic control that separates ordinary serialized queueing from the monitor-pinning mechanism. Existing correctness tests must remain attached to the synchronized and lock variants.

### C. JDBC-pool telemetry and sensitivity — recommended

Set the Hikari pool size explicitly and record pool active, pending, acquisition-time, and timeout metrics. A small sensitivity comparison such as pool sizes 2, 8, and 32 can determine whether `/orders` behavior is dominated by Virtual Thread scheduling or finite database capacity.

### D. CPU-bound control — recommended

Add one deterministic CPU-only path with no JDBC, sleep, lock, or `ThreadLocal`. Its purpose is to show that Virtual Threads are not expected to accelerate CPU-bound work and to prevent the thesis from becoming a generic “Virtual Threads are faster/slower” claim.

### E. ThreadLocal lifecycle/correctness — conditional

Only add a dedicated ThreadLocal experiment if RQ2 retains a lifecycle claim. The current implementation removes the value reliably, so the source alone does not demonstrate a leak. A useful experiment would compare context correctness under concurrent requests and, separately, a deliberately retained-value treatment with explicit heap/lifecycle measurements. The latter must be clearly labelled synthetic.

### F. Endpoint executor isolation — optional architectural extension

A bounded executor dedicated to `/payments` could test whether isolating a problematic endpoint protects `/products` and `/orders`. This is a genuinely architectural result, but it introduces a second intervention and should remain optional.

## 3. Experiments not recommended now

- Native/JNI control: useful in a broader migration survey, but high effort and outside the approved Java 21 Spring MVC scope.
- More similar slow endpoints: low information gain.
- Automatically adding every lock type: `StampedLock` and related primitives are not general replacements for the existing semantics.
- PostgreSQL and H2 mixed into one result table: retain PostgreSQL as a separate sensitivity/replication condition.

## 4. Java 21 versus Java 24/25

JEP 444 documented two Java 21 Virtual Thread pinning situations:

1. blocking in a `synchronized` method or statement;
2. execution in native or foreign-function code.

JEP 491, delivered in JDK 24, changed monitor handling so that Virtual Threads can generally unmount while acquiring, holding, or reacquiring Java monitors. Therefore:

- Java 21 synchronized-pinning findings remain valid as Java 21 findings;
- Java 24/25 should not be expected to reproduce ordinary monitor pinning;
- Java 24/25 do not make `ReentrantLock` universally superior;
- `ReentrantLock` remains appropriate when fairness, timed or interruptible acquisition, conditions, or other lock-specific features are needed;
- blocking while holding any lock should still be avoided where the application design permits it;
- `jdk.tracePinnedThreads` is meaningful for the Java 21 diagnostic story but is removed or ineffective for the old monitor-pinning purpose from JDK 24 onward;
- `jdk.VirtualThreadPinned` remains useful on newer JDKs for residual native/JVM pinning, but raw event counts are not directly comparable across the version boundary.

## 5. How to include newer JDKs

Do not replace the Java 21 primary study. Add a bounded external-validity condition:

| Runtime | Purpose |
|---|---|
| Java 21 | Primary causal study of monitor-related Virtual Thread pinning |
| Java 24 | Boundary condition after JEP 491 |
| Java 25 | Optional confirmation that the JDK 24 behavior persists |

The cleanest comparison is to compile the application once to Java 21 bytecode, then run the same SHA-256-identified JAR on each runtime. Record the runtime vendor/version separately from the compiler JDK. Keep source treatment, application configuration, database state, workload, hardware, and resource limits fixed.

Minimum boundary matrix:

- Java 21: platform legacy treatment, Virtual Thread synchronized treatment, Virtual Thread `ReentrantLock` treatment;
- Java 24: Virtual Thread synchronized and `ReentrantLock` treatments;
- Java 25: the same two treatments if time permits.

The newer-JDK arm should answer a separate question:

> To what extent do the Java 21 pinning and synchronization findings remain observable when the same Spring MVC artifact runs on Java 24 and Java 25?

Java 24/25 data can qualify external validity and support runtime-aware migration guidance. It cannot retroactively invalidate the Java 21 result or make pinning-event counts directly comparable without interpreting the changed JFR semantics.

## 6. Final recommendation

Proceed in this order:

1. Restore and version the Java 21 synchronized payment treatment.
2. Add isolated endpoint workloads.
3. Add explicit Hikari configuration and pool telemetry.
4. Add the no-lock payment control and retain correctness tests.
5. Add a CPU-bound control if implementation effort remains reasonable.
6. Re-run Java 21 with repeated traceable process-level measurements.
7. Add Java 24 as a boundary run only after the Java 21 protocol is stable.
8. Add Java 25 only if it answers a clearly stated version-persistence question.

This creates new information about **pinning versus queueing, endpoint interference, finite-resource saturation, CPU-bound behavior, and runtime evolution** without padding the project with arbitrary files.

## Sources

- OpenJDK, [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
- Pressler, [JEP 491: Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491)
- Oracle, [Java 21 Virtual Threads](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html)
- Oracle, [Java 25 Virtual Threads](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html)
- Spring Boot, [3.5 system requirements](https://docs.spring.io/spring-boot/3.5/system-requirements.html)
- Spring Boot, [Virtual Thread support](https://docs.spring.io/spring-boot/3.5/reference/features/spring-application.html#features.spring-application.virtual-threads)
