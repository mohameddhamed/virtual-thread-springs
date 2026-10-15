# Research Iteration Note: Adversarial Fairness and Barging

**Date:** 2026-10-15  
**Status:** Exploratory standalone evidence  
**Related note:** `docs/research-iteration-2026-10-15-jdk24-fairness.md`

## Purpose

The previous fairness probe mostly observed FIFO behavior because tasks were
created in a simple sequence. This iteration introduced a deliberate
late-arrival test:

1. hold the primitive;
2. start an initial group of 32 virtual-thread waiters;
3. release the initial group into the acquisition path together;
4. wait briefly so they can reach the queue;
5. release the holder;
6. inject 32 late arrivals;
7. measure whether an initial waiter is acquired after a late waiter.

The experiment was run for 100 trials per treatment on Java 21 with four
virtual-thread scheduler carriers. Each critical-section hold lasted 1 ms.

## Result

The primary metric is **initial-after-late inversions**: an initial waiter
that acquired after at least one late waiter. The initial group was released
through a common start gate and given 50 ms to enter the acquisition path
before the holder was released.

| Treatment | Initial-after-late inversions | Trials with an inversion |
|---|---:|---:|
| non-fair `ReentrantLock` | 96 | 3/100 |
| fair `ReentrantLock` | 0 | 0/100 |
| non-fair binary `Semaphore` | 0 | 0/100 |
| fair binary `Semaphore` | 0 | 0/100 |

The earlier version of the probe incorrectly treated any late task acquired
before an initial ticket as proof of barging. That was too strong because a
task can be submitted before it has reached the primitive's internal wait
queue. The tightened probe reports only the ordering inversion after the
initial acquisition group has been released through a common gate.

## Interpretation

The controlled result is consistent with the documented distinction:

- fair `ReentrantLock` preserved the order of the initial waiters under this
  protocol;
- non-fair `ReentrantLock` permitted occasional barging/reordering;
- both semaphore variants happened not to show an inversion in this
  workload.

The semaphore result does **not** establish that a non-fair semaphore is FIFO.
It only says that no inversion was observed in 100 trials with this arrival
pattern, carrier count, and 1 ms hold time.

The experiment also does not establish a throughput or starvation advantage.
Fairness is a semantic acquisition-order property; its performance cost and
starvation behavior require separate metrics and a longer workload.

## Limitations

- This was a standalone primitive probe, not the Spring `/payments` endpoint.
- The 50 ms queueing window is a test control, not a production arrival model.
- Virtual-thread scheduling and the macOS runtime can affect queue arrival.
- The primitive was held for only 1 ms; longer critical sections may expose
  different tail behavior.
- No energy or CPU comparison was collected for this probe.

## Decision

The evidence is sufficient to keep fairness as a semantic extension, but not
to recommend fair mode on throughput grounds. The next useful fairness study
should use the real application or a longer synthetic workload and report:

- acquisition wait-time distributions;
- p95/p99 request latency;
- throughput;
- late-arrival inversions;
- starvation or maximum-wait indicators;
- correctness and cancellation behavior.
