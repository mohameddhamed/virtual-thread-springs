# Research Iteration Note: Java 24 Boundary and Controlled Fairness

**Date:** 2026-10-15  
**Status:** Exploratory evidence; not yet part of the final thesis result set  
**Previous iteration:** `docs/research-iteration-2026-10-15-locks-semaphores-atomics.md`

## Purpose

This iteration followed the previous note's decisions:

1. restore a Java 24 runtime and repeat the Spring synchronization boundary;
2. use controlled acquisition arrival rather than task IDs to probe fairness;
3. preserve single-run variation instead of presenting it as a stable effect.

No repository result tables or generated raw artifacts were committed during
this iteration.

## 1. Java 24 runtime boundary

### Runtime

Java 24 was installed locally from the Temurin 24.0.2 macOS ARM64 binary:

```text
openjdk version "24.0.2" 2025-07-15
OpenJDK Runtime Environment Temurin-24.0.2+12
```

The application artifact remained the existing Java 21-targeted Spring JAR.
The scheduler was restricted to one carrier:

```text
-Djdk.virtualThreadScheduler.parallelism=1
-Djdk.virtualThreadScheduler.maxPoolSize=1
```

The `/payments` endpoint used 10 closed-loop k6 virtual users and a 500 ms
simulated payment operation.

### Result

| Java 24 treatment | Requests | p50 | p95 | JFR pinned events | HTTP errors |
|---|---:|---:|---:|---:|---:|
| `synchronized` | 110 | 3,937 ms | 8,995 ms | 0 | 0 |
| `ReentrantLock` | 109 | 4,947 ms | 4,963 ms | 0 | 0 |

Artifacts:

```text
results/run-manifest-20261015-140100.json
results/run-manifest-20261015-140205.json
results/jfr/recording-20261015-140100.jfr
results/jfr/recording-20261015-140205.jfr
```

### Interpretation

The Java 24 synchronized run confirms the mechanism boundary: no
`jdk.VirtualThreadPinned` events were reported. The synchronized code still
serializes the payment operation, so removal of monitor pinning does not make
the critical section concurrent.

### Repeated Java 24 synchronized runs

The synchronized condition was repeated three times with the same one-carrier
configuration, 10 closed-loop VUs, 500 ms simulated payment calls, JFR
enabled, and a 30-second measurement stage:

| Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---:|---:|---:|---:|---:|---:|
| 20261015-140927 | 110 | 3,934 ms | 8,980 ms | 9,022 ms | 4,050 ms | 0 |
| 20261015-141041 | 110 | 3,938 ms | 8,992 ms | 9,004 ms | 4,046 ms | 0 |
| 20261015-141146 | 110 | 3,935 ms | 8,986 ms | 9,002 ms | 4,047 ms | 0 |

The wide p95 reproduced across all three runs. It is therefore a stable
observation for this exact Java 24, one-carrier, closed-loop protocol rather
than a single-run anomaly. The result is still not a general claim that
Java 24 `synchronized` is slower than `ReentrantLock`: the comparison is
confounded by the intentionally serialized 500 ms critical section and the
one-carrier scheduler restriction. A matched repeated lock condition is
required before attributing the difference to the synchronization primitive.

The repeated runs strengthen two separate conclusions:

1. Java 24 produced zero monitor-pinning events for this synchronized blocking
   workload.
2. Removing the reported pinning event did not eliminate the large tail
   latency under the constrained scheduler and serialized application design.

### Matched repeated Java 24 `ReentrantLock` runs

The same protocol was then repeated three times with
`ReentrantLock`:

| Run | Requests | p50 | p95 | p99 | Mean | JFR pinned events |
|---|---:|---:|---:|---:|---:|---:|
| 20261015-141321 | 109 | 4,946 ms | 4,983 ms | 4,987 ms | 4,032 ms | 0 |
| 20261015-141426 | 109 | 4,953 ms | 4,961 ms | 4,972 ms | 4,034 ms | 0 |
| 20261015-141530 | 109 | 4,948 ms | 4,955 ms | 4,957 ms | 4,029 ms | 0 |

The matched lock condition had a consistently lower tail than the
Java 24 synchronized condition in this constrained protocol: approximately
4.96-4.98 seconds p95 versus approximately 8.98-8.99 seconds. Both
conditions produced zero JFR pinning events. This is direct evidence for a
latency difference in this application and scheduler configuration, but it
does not by itself identify the internal Java 24 mechanism responsible.

The result should be described narrowly. It is not evidence that
`ReentrantLock` universally outperforms `synchronized`, nor that Java 24
monitor synchronization is generally defective. The workload intentionally
serializes a 500 ms operation, uses one carrier, and applies closed-loop
load. Additional controls would be needed to distinguish monitor queueing,
virtual-thread scheduling, and application-level serialization effects.

Java 24 therefore strengthens the runtime-boundary evidence but does not
replace the Java 21 primary result.

## 2. Controlled fairness probe

### Protocol

A standalone Java 21 probe compared:

- non-fair `ReentrantLock`;
- fair `ReentrantLock`;
- non-fair binary `Semaphore`;
- fair binary `Semaphore`.

Each of 100 trials:

- created 32 virtual-thread waiters;
- held the primitive before releasing the waiters;
- assigned an explicit arrival ticket immediately before each waiter invoked
  the acquisition path;
- staggered ticket creation by 2 ms;
- recorded acquisition order;
- calculated inversions relative to the explicit ticket order.

This protocol is more informative than comparing task IDs, because virtual
thread creation order is not necessarily lock-invocation order.

### Result

| Treatment | Perfect FIFO trials | Total inversions | Maximum inversions in one trial |
|---|---:|---:|---:|
| non-fair `ReentrantLock` | 99/100 | 1 | 1 |
| fair `ReentrantLock` | 100/100 | 0 | 0 |
| non-fair binary `Semaphore` | 100/100 | 0 | 0 |
| fair binary `Semaphore` | 100/100 | 0 | 0 |

### Interpretation

The fair `ReentrantLock` behaved consistently with FIFO acquisition under
this controlled protocol. The non-fair lock admitted one inversion in 100
trials. Both semaphore variants happened to produce FIFO order in this
arrival pattern, so this experiment does not establish that the non-fair
semaphore guarantees FIFO behavior.

The result demonstrates why fairness must be measured under a protocol that
controls arrival and defines the unit of ordering. It does not establish a
throughput, starvation, or tail-latency advantage for fair mode.

A stronger follow-up should deliberately introduce late barging arrivals,
longer waits, and a starvation criterion. It should also measure wait-time
distributions and throughput rather than acquisition order alone.

## 3. Updated evidence status

| Topic | Current status |
|---|---|
| Java 21 monitor pinning | Directly observed with JFR in standalone and Spring probes |
| Java 24 synchronized monitor pinning | Zero events observed in one Spring pilot |
| Java 25 synchronized monitor pinning | Zero events observed in one Spring pilot |
| Fair versus non-fair ordering | Small controlled difference observed for `ReentrantLock`; no broad performance claim |
| Semaphore fairness | No difference observed in this arrival pattern; guarantees not inferred |
| Energy | Not measured; macOS sampling requires superuser access |
| HTTP interruptibility | Not yet integrated; requires an explicit cancellation contract |

## 4. Next experiment

The next useful study is a deliberately adversarial fairness/barging test:

1. queue an initial group of waiters;
2. release the holder;
3. inject late arrivals at the release boundary;
4. compare acquisition order, wait-time tail, throughput, and starvation;
5. repeat across fair/non-fair `ReentrantLock` and semaphore modes.

If the effect remains too small or environment-dependent, fairness should be
reported as a semantic option rather than a performance recommendation.
