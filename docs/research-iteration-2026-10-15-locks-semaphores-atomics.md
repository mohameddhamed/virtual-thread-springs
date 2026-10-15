# Research Iteration Note: Locks, Semaphores, Atomics, and JDK Boundaries

**Date:** 2026-10-15  
**Status:** Exploratory evidence; not yet part of the final thesis result set  
**Environment:** macOS Darwin 25.2.0, Apple arm64, MacBookPro17,1, 8 logical
CPUs, 8 GB memory  
**Primary runtime:** Azul Zulu Java 21.0.8  
**Boundary runtime:** Oracle OpenJDK 25  
**Application:** Spring Boot 3.5.12

## Purpose

This iteration explored the research notes concerning:

- `synchronized` versus `ReentrantLock`;
- fair and non-fair lock behavior;
- binary semaphores;
- interruptible and timed lock acquisition;
- valid use of atomic state transitions;
- compilation/runtime JDK boundaries;
- feasibility of physical energy measurement.

The experiments were deliberately separated into mechanism probes and the real
Spring application. The results below are observations from this iteration,
not universal claims about all Java applications.

## 1. Standalone Java 21/25 monitor probe

### Condition

The same Java 21-targeted class file was run with:

```text
-Djdk.virtualThreadScheduler.parallelism=1
-Djdk.virtualThreadScheduler.maxPoolSize=1
```

Thirty-two virtual threads each entered a synchronized region and called
`Thread.sleep(100)`. The comparison used Java 21.0.8 and Java 25.

### Result

| Runtime | Treatment | Completion time | `jdk.VirtualThreadPinned` |
|---|---|---:|---:|
| Java 21.0.8 | `synchronized` | 3,330 ms | 32 |
| Java 21.0.8 | `ReentrantLock` | 109 ms | 0 |
| Java 25 | `synchronized` | 108 ms | 0 |

The Java 21 synchronized recording contained stack traces through
`VirtualThread.parkOnCarrierThread`, `VirtualThread.sleepNanos`,
`Thread.sleep`, and the application lambda.

### Interpretation

Under one carrier, Java 21 intrinsic monitor pinning serialized the sleeping
virtual threads. `ReentrantLock` allowed the virtual threads to park without
occupying the only carrier. Java 25 removed the synchronized-monitor pinning
effect for the same Java 21-targeted bytecode.

This is a mechanism probe, not an application benchmark.

## 2. Spring application lock/semaphore pilot

### Condition

The existing Spring application was run with:

```text
-Djdk.virtualThreadScheduler.parallelism=1
-Djdk.virtualThreadScheduler.maxPoolSize=1
```

The `/payments` endpoint used 10 closed-loop k6 virtual users. Each payment
holds the selected treatment around a 500 ms simulated blocking call.

The pilot was run once per treatment after rebuilding the application
artifact. An earlier launch attempt used a stale JAR and was discarded because
the new modes were not present in the artifact.

### Result

| Java 21 treatment | Requests | p50 | p95 | JFR pinned events | HTTP errors |
|---|---:|---:|---:|---:|---:|
| `synchronized` | 109 | 4,948 ms | 4,967 ms | 109 | 0 |
| non-fair `ReentrantLock` | 109 | 4,946–4,950 ms | 4,958–4,967 ms | 0 | 0 |
| fair `ReentrantLock` | 109 | 4,946 ms | 4,973 ms | 0 | 0 |
| non-fair binary `Semaphore` | 109 | 4,946 ms | 4,980 ms | 0 | 0 |
| fair binary `Semaphore` | 109 | 4,949 ms | 4,958 ms | 0 | 0 |

Representative artifacts are under:

```text
results/run-manifest-20261015-132847.json
results/run-manifest-20261015-132952.json
results/run-manifest-20261015-133056.json
results/run-manifest-20261015-133201.json
results/run-manifest-20261015-133305.json
results/jfr/recording-20261015-132847.jfr
results/jfr/recording-20261015-132952.jfr
results/jfr/recording-20261015-133056.jfr
results/jfr/recording-20261015-133201.jfr
results/jfr/recording-20261015-133305.jfr
```

### Interpretation

All five treatments preserved the serialized application behavior. Replacing
the monitor removed Java 21 monitor-pinning events but did not improve this
one-carrier payment throughput because the application still permits only one
500 ms payment at a time.

This result must not be written as “`ReentrantLock` is faster” or “a semaphore
solves the bottleneck.” The supported distinction is:

1. primitive choice changes the carrier-pinning mechanism;
2. the critical-section design still determines application serialization.

## 3. Java 25 Spring boundary

The same Java 21-targeted Spring artifact was run on Java 25 with one virtual
carrier and 10 payment VUs.

| Java 25 treatment | Requests | p50 | p95 | JFR pinned events | HTTP errors |
|---|---:|---:|---:|---:|---:|
| `synchronized` | 109 | 4,953 ms | 4,963 ms | 0 | 0 |
| `ReentrantLock` | 109 | 4,937 ms | 4,959 ms | 0 | 0 |

The application result reproduces the standalone boundary: Java 25
`synchronized` still serializes the endpoint, but does not show the Java 21
monitor-pinning event.

Java 24 was not available at the expected local path during this iteration.

## 4. Fairness and contention probe

A standalone contention probe used 64 virtual threads, a 2 ms critical
section, and four carriers. It compared non-fair/fair `ReentrantLock` and
non-fair/fair binary `Semaphore`.

The observed acquisition orders were close under the tested arrival pattern.
Fairness differences were not large enough in this probe to support a
throughput or starvation conclusion. This is not evidence that the
implementations have identical fairness guarantees; it shows that task IDs
and scheduler arrival order are poor substitutes for measuring the primitive's
waiting policy.

The probe also showed that synchronized acquisition order is not a fair FIFO
order. A stronger fairness experiment needs controlled arrival tickets,
longer contention, wait-time distributions, and an explicit starvation
criterion.

## 5. Interruptibility and timed acquisition

### Standalone cancellation condition

A holder retained a `ReentrantLock` for 500 ms. Twenty virtual-thread waiters
started, and half were cancelled after 100 ms.

| Acquisition method | Waiters entering | Cancelled waiters entering |
|---|---:|---:|
| `lock()` | 20 | 10 |
| `lockInterruptibly()` | 10 | 0 |
| `tryLock(250 ms)` | 0 | 0 |

The result was reproduced on Java 21 and Java 25.

### Interpretation

Interruptibility is a semantic contract, not merely a performance setting.
`lock()` allowed cancelled waiters to enter after the lock became available.
`lockInterruptibly()` prevented cancelled waiters from entering. Timed
acquisition bounded waiting and returned failure before the holder released
the lock.

The Spring `/payments` endpoint currently has no realistic request
cancellation contract, so these modes have not yet been added to the
application. A valid application experiment requires defining HTTP timeout,
interruption propagation, response behavior, and cleanup first.

## 6. Ownership probe

A thread holding each primitive attempted to release it from another virtual
thread:

```text
ReentrantLock wrong-thread release = IllegalMonitorStateException
Semaphore wrong-thread release     = accepted
```

This confirms that a binary semaphore is not an ownership-preserving,
reentrant replacement for `ReentrantLock`. The distinction is important for
payment/resource protocols and must be part of any semaphore correctness gate.

## 7. Atomic reservation state machine

### Condition

A purpose-built bounded reservation probe compared:

- synchronized counter update;
- `ReentrantLock` counter update;
- `AtomicInteger` compare-and-set update.

There were 1,000 virtual-thread requests, capacity 8, and 2 ms simulated
resource use. Waiting requests parked briefly before retrying.

### Result

All treatments completed all 1,000 reservations and maintained:

```text
maximum active reservations = 8
```

Approximate throughput was 2,500–3,000 successful reservations per second in
the short local probe. CAS retries appeared under four-carrier contention and
were zero or negligible with one carrier.

### Interpretation

CAS can implement a finite state transition when the invariant is represented
by one atomic value and retries are side-effect-free. This does not justify
replacing the payment lock: a 500 ms external call, multiple related fields,
failure compensation, and ownership semantics are a different problem.

An atomic experiment should use a dedicated reservation/idempotency state
machine rather than alter `/payments` into an invalid pseudo-lock-free design.

## 8. Energy feasibility

macOS `powermetrics` is installed and supports process-energy and CPU-power
samplers, but invoking it for sampling requires superuser access in the
current environment:

```text
powermetrics must be invoked as the superuser
```

The tool also warns that estimated power values are not suitable for
comparison between devices. Therefore this iteration produced no energy
measurements and makes no energy claim.

The current evidence supports only this feasibility conclusion:

- same-machine energy comparison may be possible with privileged sampling;
- CPU percentage is not an energy measurement;
- cross-OS energy comparison would require separately validated,
  platform-appropriate instruments.

## 9. Code and artifact state

The local `PaymentService` experiment currently adds:

- fair `ReentrantLock`;
- non-fair binary `Semaphore`;
- fair binary `Semaphore`.

All existing application correctness tests passed for:

```text
synchronized
reentrant-lock
fair-reentrant-lock
semaphore
fair-semaphore
```

The source change, this note, and generated benchmark artifacts are not yet
committed or pushed. Raw benchmark files remain local and are subject to the
repository's existing ignore policy.

## 10. Decisions for the next iteration

1. Do not add `lockInterruptibly` to `/payments` until HTTP cancellation
   semantics are designed and tested.
2. Keep fair/non-fair lock and semaphore results as exploratory until a
   controlled fairness protocol measures wait ordering and starvation.
3. Keep the atomic work as a separate reservation/state-transition study.
4. Attempt the Java 24 boundary only after locating or reinstalling the JDK 24
   runtime.
5. Treat energy as a feasibility study, not a result, unless privileged
   measurements can be obtained and repeated.
6. Before further experiments, decide whether to preserve the new semaphore
   treatments in the application or keep them in a separate experimental
   branch/variant.
