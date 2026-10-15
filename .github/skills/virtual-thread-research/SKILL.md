---
name: virtual-thread-research
description: Evidence-first research workflow for this Spring Boot MVC Virtual Threads project. Use when designing, implementing, running, interpreting, or documenting experiments involving Java 21 Virtual Threads, monitor pinning, synchronization, JNI/native boundaries, ThreadLocal/resource behavior, OS portability, energy use, or JDK-version comparisons.
---

# Virtual Thread Research Protocol

## Project context

This repository is a deliberately realistic Spring Boot MVC application used
to study the migration of an existing system to Java 21 Virtual Threads.
Some anti-patterns are intentional experimental treatments. Do not
automatically "clean up" the baseline: preserving the control condition is a
research requirement.

The primary research questions concern:

- the effect of legacy synchronization on throughput and monitor pinning;
- the architectural conditions that should be addressed before enabling
  Virtual Threads.

The project has also developed bounded secondary tracks:

- native/JNI and foreign-function boundaries;
- JDK 21 versus JDK 24+ behavior;
- synchronization alternatives and their semantics;
- finite resources, ThreadLocal lifecycle, and endpoint interference;
- CPU, operating-system, and energy-related external validity.

Do not force every new observation into the original questions. Label it as a
secondary track or candidate research question until the research plan is
updated.

## Non-negotiable evidence rules

1. **Preserve intentional controls.** Keep baseline anti-patterns in a
   traceable variant. Implement fixes in separate variants and change one
   causal factor at a time.
2. **Measure before interpreting or fixing.** Do not remove a synchronized
   block, change a pool size, or replace a data structure before the relevant
   baseline exists.
3. **Separate observations from explanations.** A slow run is not by itself
   proof of pinning, queueing, lock contention, database saturation, or
   energy cost.
4. **Use direct mechanism evidence where available.** For Java 21 monitor
   pinning, report `jdk.VirtualThreadPinned` events and stack evidence. For
   native/JNI results, a zero event count must remain explicit; behavioral
   carrier-occupation evidence must not be renamed "JFR-confirmed pinning."
5. **Record exact runtime identity.** Every result needs the JDK vendor/build,
   compiler target, Spring Boot version, Git revision, JVM flags, scheduler
   settings, workload, hardware, OS, and artifact hashes.
6. **Repeat process-level runs.** Report trial-level values and variation,
   not only the best run or an unqualified average. Keep raw k6, JFR, and
   telemetry artifacts linked through the manifest.
7. **Run correctness gates.** A faster condition is invalid if it changes
   response correctness, mutual exclusion, ordering, error behavior, or
   resource ownership.
8. **Do not import conclusions across JDK generations.** Java 21 monitor
   pinning and JDK 24+ monitor behavior are different conditions. Keep Java
   24/25 as boundary or external-validity evidence unless the research plan
   explicitly promotes them.
9. **Do not invent missing data.** If an artifact, event count, energy
   measurement, or OS result is unavailable, say so.
10. **Use precise claim classes:** measured, derived, conceptual, behavioral
    interpretation, or hypothetical projection.

## Current experimental families

### Java 21 synchronization

The primary matrix compares:

- Virtual Threads with `synchronized`;
- Virtual Threads with `ReentrantLock`;
- a no-lock diagnostic upper bound;
- platform threads with the synchronized treatment.

Interpret this matrix at two levels:

1. **Serialization:** a single critical section around 500 ms of work can
   limit throughput regardless of the lock primitive.
2. **Pinning mechanism:** in the Java 21 synchronized treatment, JFR events
   can distinguish monitor pinning from ordinary lock queueing.

Never summarize this as "`ReentrantLock` is faster" unless a controlled result
actually demonstrates that claim. It may remove monitor pinning while leaving
the serialized workload bottleneck unchanged.

### JNI/native boundary

Keep these conditions separate:

- pure Java `Thread.sleep`;
- long blocking JNI/native execution;
- short JNI/no-op transition control.

The short-call control tests transition overhead; it does not prove that all
JNI calls are cheap. Long native residency and monitor pinning are separate
mechanisms and must be reported separately.

### ThreadLocal, JDBC, and finite resources

Do not call ThreadLocal use "pinning" without mechanism evidence. Investigate
context correctness, lifecycle cleanup, allocation, heap growth, and
per-thread state separately.

Do not attribute `/orders` degradation to pinning without pool evidence.
Configure and record Hikari limits where possible, and measure active,
pending, acquisition latency, timeout, database, and endpoint metrics.
H2 and PostgreSQL are separate environments, not one pooled result table.

## Candidate extension tracks from research notes

These are research candidates, not automatic implementation instructions.
Before adding code, state the hypothesis, treatment, control, metric, and
decision rule.

### 1. Energy and green-computing track

Question candidate: does a migration change energy or power per completed
request, not merely elapsed time?

Minimum design:

- measure wall-clock energy/power with a named tool and documented sampling
  method;
- record CPU package/core power where the platform exposes it, otherwise
  label the measure as a proxy;
- report energy per successful request and total energy for a fixed workload;
- hold workload, warmup, hardware, OS power mode, background load, and run
  duration constant;
- repeat runs and include uncertainty;
- never compare Windows, macOS, and Linux as if their power counters were
  directly interchangeable.

This track should remain secondary until a reliable, platform-appropriate
measurement method exists. Do not infer green benefits from lower latency or
CPU percentage alone.

### 2. OS and hardware external-validity track

Candidate comparison: macOS, Windows, and Linux, with the same application
artifact and protocol.

Required controls:

- exact OS release and kernel/runtime details;
- CPU model, core count, SMT status, memory, power mode, and thermal state;
- JDK vendor/build and native-library compiler;
- identical workload and scheduler settings where meaningful;
- separate analysis of OS-specific observability and native behavior.

Do not claim a cross-OS effect from one machine per OS. Treat this as
external-validity evidence unless replication is adequate.

### 3. Synchronization semantics track

Compare semantics before performance:

- `synchronized`;
- `ReentrantLock` non-fair and fair;
- `lockInterruptibly`, timed `tryLock`, and ordinary `lock` only when the
  application contract requires the distinction;
- binary `Semaphore` as a permit/mutual-exclusion control;
- counting `Semaphore` for bounded resource access;
- atomic/lock-free state transitions using `AtomicInteger`,
  `AtomicReference`, `VarHandle`, or compare-and-set operations.

Important distinctions:

- `ReentrantLock` has ownership and reentrancy; a `Semaphore` has permits and
  no ownership, so a different thread can release a permit.
- Fairness affects acquisition ordering and can reduce throughput; fairness
  does not guarantee fair OS scheduling.
- `lockInterruptibly` changes cancellation semantics and is not an
  apples-to-apples replacement for `lock` unless interruption behavior is
  intentionally controlled.
- Atomics are not general replacements for locks. They fit state transitions
  that can be expressed without a multi-step invariant or blocking critical
  section.

Every alternative must pass the same correctness and mutual-exclusion tests.
Measure acquisition latency, service latency, throughput, tail latency,
failed/cancelled acquisitions, starvation indicators, CPU, and JFR evidence.
Do not add every primitive merely to increase the file count; add one only
when it answers a stated semantic or architectural question.

### 4. Context-switch and scheduler-cost track

The claim that an OS context switch costs "50 microseconds" is not a universal
constant. Treat it as an unverified hypothesis whose value depends on
hardware, OS, workload, measurement method, cache state, and scheduler.

If studied:

- define whether the measure is OS thread switching, virtual-thread
  mount/unmount, lock handoff, or scheduler park/unpark;
- use a purpose-built microbenchmark or JMH where appropriate;
- separate warmup from measurement;
- report distributions, not a single average;
- avoid translating a microbenchmark directly into application throughput;
- correlate with CPU counters or scheduler/JFR data only when the counters
  are available and documented.

The application benchmark remains the primary evidence; microbenchmarks are
mechanism support, not replacements for it.

### 5. Compile/runtime JDK-boundary track

Test these as distinct questions:

- compile targeting Java 21 and run on Java 21, 24, and 25;
- compile and run on a newer JDK;
- determine whether a supported compatibility flag or runtime option can
  reproduce pre-JDK-24 monitor behavior.

Never assume that a newer runtime has an official switch to restore old
monitor-pinning semantics. Verify the JDK documentation and release behavior.
If no supported switch exists, use separate runtime comparisons or an explicit
reproduction mechanism; do not present a modified JVM as ordinary Java 24/25.

Record compiler JDK, bytecode target, runtime JDK, JVM options, and source/JAR
hash separately. JDK 24's monitor changes mean that Java 21 synchronized
results cannot be treated as directly replicated by Java 24/25.

## Experimental protocol

For each new study:

1. State the research question or candidate hypothesis.
2. Define the unit of analysis and primary metric.
3. Define baseline, intervention, controls, and correctness invariants.
4. Freeze source revision, artifact hashes, runtime, JVM options, OS, and
   workload.
5. Warm up consistently and use a fixed measurement window.
6. Run at least three process-level repetitions for exploratory work; use
   more when the claim is central or variability is material.
7. Randomize condition order where practical and avoid concurrent application
   processes sharing a port or resource.
8. Capture k6, JFR, process/scheduler telemetry, resource metrics, and
   manifest metadata.
9. Analyze trial-level results before aggregate summaries.
10. Write observed result, supported interpretation, limitations, and
    unestablished claims separately.

Closed-loop VU workloads are useful for the existing mechanism-isolation
experiments. For queueing and saturation claims, consider an open arrival-rate
design so offered load is not reduced by slow responses. Do not silently
replace the established protocol; document any protocol change as a new
experiment family.

## Evidence and dashboard workflow

The evidence explorer is generated from repository artifacts:

```bash
python3 scripts/normalize_evidence.py
python3 scripts/validate_normalized_evidence.py
```

Never manually type new benchmark values into the dashboard. Preserve
trial-level records, source paths, hashes, JFR counts, and classification.
The UI may compute derived aggregates and show conceptual mechanism diagrams,
but conceptual diagrams must be labeled as such.

## Finding record

For each substantive finding, record:

- finding ID and experiment family;
- research question or secondary track;
- class: monitor-pinning, native-boundary, serialization,
  threadlocal-lifecycle, pool-bottleneck, synchronization-semantics,
  energy, OS-boundary, scheduler-cost, or other;
- exact source location and treatment;
- JDK/compiler/runtime identity;
- workload, scheduler, OS, and hardware;
- measured artifacts and hashes;
- trial count and spread;
- correctness result;
- direct evidence versus interpretation;
- fix or intervention and verification result;
- threats to validity;
- whether the implication is required, recommended, conditional, or unknown.

## Writing and decision language

Prefer:

- "In the tested Java 21 condition..."
- "The recordings reported..."
- "The result is consistent with..."
- "This separates X from Y under the stated controls."
- "This was not established..."

Avoid unsupported wording such as:

- "Virtual Threads are always faster."
- "`ReentrantLock` solves pinning."
- "Java 25 fixes native blocking."
- "JNI always pins."
- "Lower CPU means lower energy."
- "A single microbenchmark proves production behavior."

When a new note suggests an experiment, first decide whether it is:

1. necessary for an existing research question;
2. a useful secondary external-validity study;
3. a mechanism microbenchmark;
4. an attractive but currently low-information idea.

Only the first three should enter the experiment backlog, and each needs a
bounded protocol and stopping rule.

## Sources to verify before relying on advice

- JEP 444: https://openjdk.org/jeps/444
- JEP 491: https://openjdk.org/jeps/491
- Java 21 `ReentrantLock` API:
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html
- Java 21 `Semaphore` API:
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Semaphore.html
- Java 21 `AtomicInteger` API:
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/AtomicInteger.html
