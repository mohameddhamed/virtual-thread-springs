# Java 21 Synchronization Matrix — 8 October 2026

## Protocol

This matrix isolates `POST /payments` and repeats each condition three times:

- Virtual Threads with a Java `synchronized` critical section;
- Virtual Threads with `ReentrantLock`;
- Virtual Threads with no lock, used only as a diagnostic upper-bound control;
- platform threads with the `synchronized` treatment.

Each run used 10 closed-loop k6 VUs, a 15-second ramp-up, 30-second hold,
10-second ramp-down, and a 500 ms blocking operation inside the payment
critical section. The Java 21 scheduler was constrained to one carrier for
mechanism isolation. This is a stress condition, not a production
configuration.

The repeated runs are grouped under
`run_set=java21-synchronization-20261008-repeated`. Each manifest records the
trial and condition identifiers, raw k6 output, JFR recording, telemetry, and
SHA-256 hashes.

## Results

| Condition | Runs | Mean requests | Mean median latency | Mean p95 latency |
|---|---:|---:|---:|---:|
| Virtual Threads + `synchronized` | 3 | 110.0 | 3923.86 ms | 7957.50 ms |
| Virtual Threads + `ReentrantLock` | 3 | 108.7 | 4941.99 ms | 4967.54 ms |
| Virtual Threads + no-lock diagnostic | 3 | 710.7 | 507.66 ms | 512.84 ms |
| Platform threads + `synchronized` | 3 | 110.0 | 3936.42 ms | 9002.48 ms |

All 12 runs completed with zero HTTP failures.

## JFR evidence

The three Java 21 `synchronized` recordings each contained 110
`jdk.VirtualThreadPinned` events. The three `ReentrantLock`, three no-lock,
and three platform-thread recordings contained zero such events.

This is consistent with the intended mechanism: in Java 21, the monitor-based
critical section pins a virtual thread to the sole carrier while the
500 ms operation executes. `ReentrantLock` avoids monitor pinning, but it does
not remove the application-level serialization: requests still contend for
one critical section. The no-lock condition is not a valid payment design; it
is included only to show the upper-bound behavior when serialization is
removed.

## Interpretation and limitations

The data does **not** establish that `synchronized` is faster than
`ReentrantLock`. Both serialized conditions completed approximately 109–110
requests, and their latency distributions differ under the deliberately
constrained scheduler. The defensible finding is that replacing
`synchronized` with `ReentrantLock` removed the observed Java 21 monitor-pinning
events, but did not remove the throughput limit caused by holding a lock across
500 ms of work.

The one-carrier setting is useful for mechanism isolation but is not
representative of a default production scheduler. The results should be
reported as a Java 21 controlled stress experiment and should not be
generalized to all lock workloads without testing additional carrier counts,
work durations, and endpoint mixes.
