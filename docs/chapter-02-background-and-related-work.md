# Chapter 2: Background and Related Work

## 2.1 The Evolution of Concurrency in the Java Virtual Machine

### 2.1.1 Early Concurrency: From Green Threads to 1:1 Operating System Threads

The architecture of concurrency in the Java Virtual Machine (JVM) has undergone continuous evolution since the platform's inception in 1995. In Java 1.0 and 1.1, the Java runtime implemented what were historically known as **green threads**. Green threads were user-mode execution threads managed entirely inside the JVM runtime without operating system (OS) kernel awareness:
*   **$M:1$ Thread Mapping:** A green thread implementation mapped many user-level Java threads ($M$) onto a single underlying operating system kernel thread ($1$).
*   **Cooperative and Simulated Scheduling:** The JVM runtime scheduled green threads cooperatively or through user-space timers. Because the host operating system managed only one thread, the runtime could not exploit symmetric multiprocessing (SMP) or multi-core architectures; only one Java thread could execute instructions at any given instant.
*   **Blocking I/O Vulnerability:** The fatal flaw of the early green threads model was input/output handling. If a single green thread executed a synchronous, blocking OS system call (such as a blocking socket read or disk write), the underlying operating system platform thread suspended. Consequently, the entire JVM process—including all other green threads waiting to run—was completely halted.

To overcome these severe scalability and multi-core scheduling limitations, Java 1.2 (released in 1998) fundamentally abandoned green threads in favor of **native threads**. Under the native threading model, the JVM established an **architectural 1:1 mapping** between each `java.lang.Thread` instance and a physical operating system platform thread (such as a POSIX `pthread` on Linux, Solaris, and macOS, or a Win32 thread on Windows).

By delegating thread scheduling, CPU affinity, and hardware preemption directly to the operating system kernel, the 1:1 platform thread architecture allowed Java applications to achieve genuine hardware parallelism across multi-socket and multi-core server processors. However, this 1:1 coupling bound Java's scalability ceiling directly to the physical costs of operating system kernel threads:
1.  **Fixed Virtual Memory Stack Allocation:** The operating system kernel requires each platform thread to maintain a dedicated, contiguous virtual memory stack allocated outside the garbage-collected Java heap. HotSpot commonly configures a stack reservation such as 1,024 KB (`-Xss1m`) per platform thread. A high-concurrency server hosting 2,000 platform threads may reserve substantial virtual address space, but committed memory depends on stack use and platform/runtime behavior.
2.  **Kernel Scheduling and Mode Transitions:** Thread preemption, synchronization, and rescheduling require kernel context transitions (`ring 3` user mode to `ring 0` kernel mode). These transitions can incur scheduling and cache-locality costs; their magnitude depends on the operating system, hardware, workload, and switching pattern.

### 2.1.2 The Synchronous Thread-per-Request Paradigm and Its Ceiling

For the subsequent two decades, the **thread-per-request** programming model became the foundational architecture of enterprise Java systems. Standardized by the Java Servlet API and embodied in containers such as Apache Tomcat, Eclipse Jetty, and Spring Framework Model-View-Controller (MVC), this model assigns each incoming HTTP network connection to a dedicated platform worker thread.

The architectural ergonomics of the thread-per-request model are clear:
*   **Procedural Call Stacks:** Application logic executes sequentially down a single, predictable call stack. Control flow conforms directly to standard procedural constructs (`if`, `for`, `try-catch`), eliminating the cognitive friction of asynchronous callbacks.
*   **Implicit Context Propagation:** Transactional boundaries, security authentication tokens, and distributed tracing metadata ([`ThreadLocal`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L28)) can be stored in per-thread memory and accessed transparently across deep layered architectures without explicit method argument threading.
*   **Deterministic Diagnostics:** If an exception occurs, the resulting stack trace captures a chronological snapshot of the entire request lifecycle from HTTP controller down to database persistence.

However, because platform threads are scarce and memory-intensive, enterprise servlet containers must strictly constrain concurrency using **bounded thread pools** (e.g., Apache Tomcat's default `maxThreads = 200`). This constraint imposes a strict architectural limit: **concurrency is bounded to thread pool capacity**.

In modern microservice architectures, enterprise services spend the vast majority of their lifecycle waiting on external network dependencies—such as relational database queries via JDBC, REST calls to downstream services, or external payment gateways. Under high concurrency, worker threads rapidly block on network sockets. The container thread pool exhausts, incoming requests queue up in container backlogs, client response times escalate exponentially, and the application may queue requests, increase latency, or trigger timeouts under saturation.

```
+-----------------------------------------------------------------------------------+
|               TRADITIONAL PLATFORM THREAD CONCURRENCY (1:1 MAPPING)               |
+-----------------------------------------------------------------------------------+
  HTTP Ingestion        Tomcat Worker Pool (maxThreads=200)       OS Kernel Threads
  [Req 1]  ───────>    [Platform Thread 1 (1 MB Stack)]  ──1:1──>  [Kernel Thread A]
  [Req 2]  ───────>    [Platform Thread 2 (1 MB Stack)]  ──1:1──>  [Kernel Thread B]
  [Req ...] ───────>    [Platform Thread ...]             ──1:1──>  [Kernel Thread ...]
  [Req 201] ───────>    [WAITING IN TOMCAT QUEUE]         ───────>  *THREAD EXHAUSTION*
+-----------------------------------------------------------------------------------+
```

### 2.1.3 The Asynchronous and Reactive Divergence

To break free from the platform thread bottleneck, the software engineering industry explored asynchronous and reactive architectures during the 2010s. Frameworks such as Node.js, Netty, Vert.x, Spring WebFlux, and Project Reactor decoupled connection concurrency from thread count by adopting an **event-loop architecture**.

Under the reactive model, a tiny, fixed pool of worker threads (typically matching the physical CPU core count) handles thousands of concurrent network connections using non-blocking operating system readiness multiplexers (such as Linux `epoll` or macOS `kqueue`). When a request initiates an I/O operation, the thread does not block; instead, it registers an asynchronous callback with the event loop and is immediately freed to process other incoming network events.

While reactive programming dramatically increased concurrent connection capacity and eliminated thread stack memory waste, it introduced steep architectural, cognitive, and operational penalties:
1.  **Function "Coloring" and Monadic Composition:** Asynchronous programming enforces what literature describes as "function coloring": asynchronous operations cannot be invoked transparently from synchronous code. Developers must rewrite imperative business logic into functional, monadic streams (`Mono`, `Flux`, `CompletableFuture`). Control flow primitives (`for`, `try-catch`) are replaced by complex functional operators (`flatMap`, `switchIfEmpty`, `onErrorResume`).
2.  **Loss of Context Propagation and Thread-Local State:** Because a single HTTP request hops across different event-loop worker threads at each asynchronous stage, standard thread-local storage (`ThreadLocal`) ceases to function reliably. Propagating security contexts or tracing identifiers requires framework-specific context abstractions (e.g., Reactor `Subscriber` Context), which do not interoperate seamlessly with third-party libraries.
3.  **Fragmented Stack Traces and Obscured Debuggability:** When an exception occurs in a reactive pipeline, the captured stack trace typically reflects only the internal machinery of the event-loop scheduler rather than the causal sequence of business operations, creating profound diagnostic challenges in production environments.
4.  **Relational Database Impedance Mismatch:** Enterprise persistence relies overwhelmingly on standard relational databases accessed via the Java Database Connectivity (JDBC) API and connection pools such as HikariCP. JDBC drivers are inherently synchronous and blocking. Integrating blocking JDBC operations into a reactive pipeline requires offloading database calls to dedicated platform thread pools (e.g., `Schedulers.boundedElastic()`), which fundamentally re-introduces thread management complexity and memory overhead.

### 2.1.4 Cross-Language Concurrency Models: Design Rationale and Contrasts

The tension between synchronous imperative programming and scalable concurrency is not unique to Java. Different programming language ecosystems have adopted contrasting concurrency paradigms, each reflecting distinct runtime design tradeoffs:

### Table 2.1: Architectural Concurrency Model Comparison Across Language Runtimes

| Runtime / Language | Concurrency Abstraction | Thread Mapping | Stack Management | Scheduling Mechanism | Preemption Model | Blocking I/O Handling |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **Java Platform Threads** | `java.lang.Thread` | $1:1$ (OS) | Heavyweight (1 MB fixed virtual stack) | OS Kernel Scheduler | Preemptive (OS timer interrupt) | OS kernel suspends platform thread |
| **Go (Golang)** | Goroutine (`go fn()`) | $M:N$ | Resizable (starts at 2 KB, grows on heap) | User-space runtime scheduler | Semi-preemptive (compiler-inserted checks at function prologues) | Integrated network poller (`netpoller`) yields goroutine |
| **Erlang / Elixir (BEAM)**| Actor Process (`spawn`) | $M:N$ | Tiny (starts at ~300 words heap memory) | BEAM Virtual Machine Scheduler | Fully preemptive (reduction-counter per process) | Asynchronous non-blocking message passing |
| **C# / TypeScript / Node** | `async / await` Task | Promise / Task | Stackless continuations compiled to state machines | Event Loop / Task ThreadPool | Cooperative (yields explicitly on `await`) | Non-blocking OS readiness multiplexing |
| **Java 21 Virtual Threads** | `java.lang.Thread` (Loom) | $M:N$ | Resizable heap `StackChunk` frames | JVM HotSpot `ForkJoinPool` | Semi-cooperative (yields on blocking Java APIs) | JVM runtime unmounts virtual thread to heap |

Unlike Go, which built its $M:N$ scheduler into the language runtime from its initial design, or C#, which introduced explicit `async/await` syntax, Java faced a strict evolutionary constraint: **backward compatibility with 25 years of existing enterprise code**.

Rewriting the Java language with `async/await` would have fractured the ecosystem into mutually incompatible synchronous and asynchronous libraries. Instead, the OpenJDK design team chose **Project Loom**: re-engineering the Java Virtual Machine runtime so that standard, synchronous, imperative Java code could achieve $M:N$ user-mode concurrency without modifying language syntax or discarding the fundamental `java.lang.Thread` API contract.

---

## 2.2 Project Loom and Java 21 Virtual Threads Architecture

### 2.2.1 Core Architectural Components: Continuations, Carriers, and Schedulers

**Project Loom**, delivered as a production feature in **Java 21 LTS** via **JEP 444**, introduces Virtual Threads as lightweight, user-mode implementations of `java.lang.Thread`. The architecture consists of three fundamental components:

```
+-----------------------------------------------------------------------------------+
|               PROJECT LOOM THREE-TIER RUNTIME ARCHITECTURE                        |
+-----------------------------------------------------------------------------------+
  TIER 1: USER-SPACE ABSTRACTION
  [VirtualThread 1]   [VirtualThread 2]   [VirtualThread 3]   ...   [VirtualThread M]
  (Tiny heap object <1 KB, extends java.lang.Thread, encapsulates a Continuation)
                                     │
                                     ▼ Mounts via Scheduler
  TIER 2: SCHEDULING INFRASTRUCTURE
  ForkJoinPool instance (java.lang.VirtualThread.DEFAULT_SCHEDULER)
  Work-stealing FIFO/LIFO queues, parallelism = Runtime.availableProcessors()
                                     │
                                     ▼ Executes on
  TIER 3: OPERATING SYSTEM EXECUTION
  [Carrier Thread 1]  [Carrier Thread 2]  ...  [Carrier Thread N] (OS Platform Threads)
  [CPU Core 0]        [CPU Core 1]        ...  [CPU Core N-1]
+-----------------------------------------------------------------------------------+
```

1.  **The User-Mode Virtual Thread (`java.lang.VirtualThread`):** A virtual thread is an instance of `java.lang.Thread` whose execution state is managed directly by HotSpot runtime bytecode rather than the OS kernel. It encapsulates a `jdk.internal.vm.Continuation` object representing its suspendable call stack.
2.  **Carrier Threads:** A carrier thread is a standard OS platform thread that provides CPU execution cycles for a virtual thread. The virtual thread is temporarily **mounted** onto a carrier thread to execute instructions. From the perspective of Java code executing within the virtual thread, the identity of the carrier thread is invisible; calling `Thread.currentThread()` returns the virtual thread instance itself.
3.  **The Dedicated ForkJoinPool Scheduler:** Virtual threads are scheduled onto carrier threads by a dedicated, private `ForkJoinPool` instance encapsulated within `java.lang.VirtualThread.DEFAULT_SCHEDULER`.
    *   This scheduler is completely separate from `ForkJoinPool.commonPool()`, which is used by parallel streams and `CompletableFuture`.
    *   The scheduler's default parallelism equals the number of available logical processor cores (`Runtime.getRuntime().availableProcessors()`).
    *   Carrier worker threads are assigned internal HotSpot names following the convention `ForkJoinPool-1-worker-*`.

### 2.2.2 The Mounting and Unmounting Lifecycle

The defining capability of a virtual thread is its ability to **unmount** from its carrier thread when encountering cooperative blocking operations, and **remount** when ready to resume:

```
+-----------------------------------------------------------------------------------+
|                     VIRTUAL THREAD MOUNTING AND UNMOUNTING CYCLE                  |
+-----------------------------------------------------------------------------------+
       [CREATED] ──> newVirtualThreadPerTaskExecutor()
           │
           ▼
       [RUNNABLE] (Enqueued in ForkJoinPool work queue)
           │
           ▼ Mounts onto OS Carrier Thread (ForkJoinPool-1-worker-X)
       [RUNNING]  ─── Bytecode executes on CPU core
           │
           ├── Encounters Blocking API (e.g. Socket.read(), LockSupport.park())
           │
           ▼
  HotSpot Continuation.yield()
  ├── Stack frames frozen from CPU execution stack into heap StackChunk objects
  ├── Virtual thread unmounts from carrier thread
  └── Carrier thread is IMMEDIATELY RETURNED to ForkJoinPool for other tasks!
           │
           ▼
       [PARKED] (Suspended on heap; consumes ~0 active CPU cycles)
           │
           ├── Asynchronous notification (Network readiness poller / Timer fires)
           │
           ▼
       [RUNNABLE] (Re-enqueued in ForkJoinPool queue)
           │
           ▼ Remounts onto ANY available Carrier Thread (may differ from worker-X!)
       [RUNNING]  ─── Stack frames thawed from heap; execution resumes seamlessly
+-----------------------------------------------------------------------------------+
```

1.  **Mounting:** The `ForkJoinPool` scheduler assigns a runnable virtual thread to an idle carrier worker thread. HotSpot copies or points the execution frame to the carrier's native execution stack.
2.  **Execution:** The virtual thread executes normal Java bytecode instructions directly on physical CPU hardware.
3.  **Continuation Yield:** When the virtual thread invokes a non-native blocking operation within the standard Java Class Library (such as `SocketInputStream.read()`, `Thread.sleep()`, or `LockSupport.park()`), the underlying implementation calls `Continuation.yield()`.
4.  **Freezing Frames to Heap:** HotSpot's continuation subsystem freezes the virtual thread's active execution stack frames from the carrier thread's physical stack, packing them into `StackChunk` objects allocated directly on the garbage-collected Java heap.
5.  **Unmounting:** The virtual thread transitions to the `PARKED` state. The carrier thread is released immediately back to the `ForkJoinPool` work-stealing queue, free to execute other runnable virtual threads.
6.  **Poller Notification and Thawing:** When the blocking condition resolves (e.g., the OS kernel notifies the JVM's background network poller thread via `epoll`/`kqueue` that data is ready on the socket), the runtime unparks the continuation. The virtual thread is placed back into the `ForkJoinPool` queue, mounts onto an available carrier thread (which need not be the same carrier thread that originally hosted it), thaws its stack frames from the heap, and resumes execution seamlessly.

### 2.2.3 Memory Footprint and Stack Chunk Management

In contrast to platform threads, which allocate a static 1 MB stack off-heap, virtual threads manage stack memory dynamically within the Java heap:
*   **Initial Overhead:** A newly created virtual thread requires less than 1 KB of heap memory.
*   **Lazy Stack Growth:** Call stacks are allocated as small `StackChunk` objects (represented internally by `instanceStackChunkKlass` in HotSpot C++). The stack grows and shrinks dynamically in small segments as method invocation depth increases and decreases.
*   **Garbage Collection Dynamics:** Because continuation stack chunks live on the Java heap, rapid creation, blocking, and destruction of millions of short-lived virtual threads increases young-generation heap allocation rates. Applications operating under high concurrency require properly sized JVM heap headroom (`-Xmx`) and modern generational garbage collectors (such as G1GC or Generational ZGC) to handle ephemeral stack churn without inducing stop-the-world GC pauses (`CHK-JDK-21`).

---

## 2.3 The Mechanics of Monitor Pinning in Java 21

### 2.3.1 HotSpot ObjectMonitor Architecture and the Freeze Subsystem

While Virtual Threads unmount cleanly during standard Java library blocking, Java 21 LTS contains an architectural constraint known as **monitor pinning**.

In the Java programming language, every object can act as an intrinsic mutual exclusion monitor via the `synchronized` keyword (method-level or block-level). In the OpenJDK HotSpot C++ runtime, intrinsic monitors are implemented via the `ObjectMonitor` subsystem:
1.  When a thread executes the bytecode instruction `monitorenter`, it attempts to acquire the `ObjectMonitor` associated with the target object's header mark-word.
2.  In Java 21, the HotSpot continuation subsystem (`src/hotspot/share/runtime/continuationFreeze.cpp`) contains a foundational predicate: `can_freeze()`.
3.  Before freezing a virtual thread's stack frames to the heap during a blocking operation (`Thread.sleep()`, socket read, or lock wait), HotSpot evaluates whether the thread holds any active `ObjectMonitor` locks on its stack frames.
4.  If the virtual thread holds an intrinsic monitor, **`can_freeze()` returns `false`**:

```cpp
// HotSpot continuationFreeze.cpp (Java 21 representation)
bool ContinuationFreeze::can_freeze() {
    if (_target->held_monitor_count() > 0) {
        // Virtual thread holds an intrinsic ObjectMonitor!
        return false; // FREEZE REJECTED -> PINNING OCCURS
    }
    return true;
}
```

The underlying technical reason for this restriction in Java 21 stems from HotSpot's historical C++ architecture. When an intrinsic monitor is acquired, the C++ runtime stores direct native memory pointers to the `ObjectMonitor` structures on the physical OS execution stack. In Java 21, the continuation engine lacked the capability to safely evacuate, relocate, and update these internal C++ memory addresses on the heap. Consequently, HotSpot prohibits continuation freezing while an intrinsic monitor is held.

```
+-----------------------------------------------------------------------------------+
|               HOTSPOT CONTINUATION FREEZE FAILURE (MONITOR PINNING)               |
+-----------------------------------------------------------------------------------+
  Virtual Thread (Inside synchronized block)
  Calls: Thread.sleep(500)
    │
    ▼
  HotSpot Runtime: Continuation.yield()
    │
    ▼
  continuationFreeze.cpp: can_freeze()
    ├── Checks held_monitor_count()
    └── FOUND: ObjectMonitor acquired on stack frame!
    │
    ▼
  FREEZE REFUSED (can_freeze() == false)
    │
    ▼
  VIRTUAL THREAD CANNOT UNMOUNT!
  ├── Stack frames remain physically locked to OS Carrier Thread
  ├── Carrier Thread enters kernel sleep (nanosleep)
  └── CARRIER IS STOLEN FROM THE SCHEDULER (PINNED)
+-----------------------------------------------------------------------------------+
```

### 2.3.2 Operational Consequences: Carrier Pool Starvation

When a virtual thread executes a blocking operation inside a `synchronized` block on Java 21, it **pins** its underlying OS carrier thread:
*   The virtual thread cannot detach from its carrier.
*   The carrier thread is forced to remain physically attached to the virtual thread, blocking in the operating system kernel for the duration of the delay.
*   While pinned, the carrier thread cannot return to the `ForkJoinPool` scheduler to execute other virtual threads.

If an application possesses a limited number of carrier threads (e.g., in single-carrier stress benchmarks or 1-vCPU containerized cloud environments), a single pinned virtual thread starves the entire carrier pool. All other virtual threads waiting in the `ForkJoinPool` queue stall, causing overall system throughput to collapse and response times to inflate dramatically.

### 2.3.3 Discarding the Carrier Dynamic Compensation Myth (`CLM-RQ1-07`)

Early literature and industrial research notes (including early scout reports) frequently asserted that HotSpot's `ForkJoinPool` dynamically spawns additional carrier threads to compensate for monitor pinning, and that setting `-Djdk.virtualThreadScheduler.maxPoolSize=1` was required to disable this automatic expansion.

This assertion is a **demonstrated factual misconception** regarding JVM internals:
*   [JEP 444](https://openjdk.org/jeps/444) explicitly specifies: *"The scheduler does not compensate for pinning by expanding its parallelism."*
*   Inspection of OpenJDK HotSpot source code confirms that carrier compensation is implemented exclusively for operations wrapped in `ForkJoinPool.ManagedBlocker` (primarily POSIX file I/O operations via `FileChannelImpl` and certain `Object.wait()` calls).
*   HotSpot **never** expands carrier thread parallelism to compensate for intrinsic monitor pinning or native JNI execution (`CHK-JDK-01`). The single-carrier stalls observed under `parallelism=1` occur purely due to carrier exhaustion without compensation; `maxPoolSize=1` merely constrains file I/O expansion.

---

## 2.4 The JDK Runtime Boundary: Java 21 LTS vs. Java 24/25

### 2.4.1 JEP 491 (JDK 24): Synchronize Virtual Threads without Pinning

To eliminate the monitor pinning bottleneck, the OpenJDK team undertook a comprehensive multi-year redesign of HotSpot's object monitor subsystem, finalized in **Java 24 GA** (March 2025) under **JEP 491** (*Synchronize Virtual Threads without Pinning*).

JEP 491 rearchitected `ObjectMonitor` locking so that acquiring, holding, or waiting on an intrinsic monitor no longer pins the virtual thread to its carrier:
1.  HotSpot's monitor acquisition and release paths were rewritten to integrate directly with the continuation subsystem.
2.  When a virtual thread encounters monitor contention or blocks (e.g., `Thread.sleep()`) inside a `synchronized` block on Java 24, HotSpot evacuates the continuation frames to the heap and unmounts the virtual thread, freeing the carrier thread for other work.
3.  In this research, empirical validation on JDK 24.0.2 (`Stratum 2`, Table 5.5) confirmed that under the exact identical workload that produced 110 pinning events on Java 21, Java 24 recorded **exactly 0 `jdk.VirtualThreadPinned` events** (`CLM-RQ1-06`).

### 2.4.2 Ineligibility of JEP 491 for Java 21 LTS Backporting

A critical architectural reality for enterprise software engineering is that **JEP 491 will never be backported to Java 21 LTS**:
*   OpenJDK `jdk21u-dev` maintenance and stability policies strictly forbid backporting large-scale, invasive architectural modifications that alter core object monitor assembly stubs across all CPU hardware architectures.
*   Because Java 21 is a Long-Term Support (LTS) release scheduled for enterprise production support through at least 2028–2030, thousands of enterprise organizations will remain deployed on Java 21 LTS for years.
*   Consequently, enterprise systems deployed on Java 21 LTS permanently require the codebase auditing, dependency verification, and mutex refactoring guidelines established in this dissertation.

### 2.4.3 Residual Pinning Vectors Post-JEP 491

Software architects must recognize that even on Java 24 and later runtimes, JEP 491 did **not** eliminate all forms of carrier pinning (`CHK-JDK-09`):
1.  **Class Initialization Locks (`<clinit>`):** Class loading and static class initialization hold internal JVM class loader monitors. Blocking inside a static initializer continues to pin the carrier thread across all JDK versions (Java 21 through Java 25+) (`CHK-JDK-17`).
2.  **Native Stack Frames:** If a virtual thread invokes a C function via JNI or Foreign Function & Memory (FFM) APIs, native machine stack frames are pushed onto the carrier stack. The presence of native frames permanently prevents continuation freezing, pinning the carrier thread regardless of JDK version.

### 2.4.4 The Evolutionary Path to Java 25 LTS (JEP 506 Scoped Values)

In addition to monitor unpinning, the Java platform has evolved its context propagation model:
*   **Scoped Values (JEP 446 / 481 / 506):** Designed as a lightweight, immutable alternative to `ThreadLocal`.
*   *Version Evolution:* Previewed in Java 21 (JEP 446), refined across Java 22–24, and finalized as a **permanent standard feature in Java 25 LTS via JEP 506**.
*   *Engineering Guidance:* For Java 21 LTS production systems, standard `ThreadLocal` storage with deterministic `try-finally { context.remove(); }` cleanup remains the mandatory production baseline, while Scoped Values serve as an evolutionary target for post-Java 21 architectures.

---

## 2.5 Synchronization Primitives and Concurrency Contracts

### 2.5.1 Intrinsic Monitors vs. Explicit Locks (`java.util.concurrent.locks.ReentrantLock`)

When migrating away from monitor pinning on Java 21, the primary refactoring pattern is replacing intrinsic `synchronized` blocks with explicit locks from the `java.util.concurrent.locks` package, predominantly `ReentrantLock`.

While both primitives provide mutual exclusion and reentrancy, they represent fundamentally distinct architectural implementations:

### Table 2.2: Concurrency Primitive Contract and Mechanical Comparison

| Architectural Property | Intrinsic Monitor (`synchronized`) | Explicit Lock (`ReentrantLock`) |
| :--- | :--- | :--- |
| **Implementation Layer** | JVM HotSpot C++ (`ObjectMonitor`) bytecode | Java Class Library (`AbstractQueuedSynchronizer` [AQS]) |
| **Java 21 Virtual Thread Behavior** | **Pins Carrier Thread** if blocking occurs inside | **Unmounts Cleanly** to heap via `LockSupport.park()` |
| **Java 24+ Virtual Thread Behavior** | Unmounts cleanly (JEP 491) | Unmounts cleanly |
| **Lock Acquisition Fairness** | Strictly non-fair (OS-dependent thread scheduling) | Configurable: Non-fair (default) or Fair |
| **Interruptibility** | Uninterruptible (thread blocks indefinitely) | Configurable: `lock()` vs. `lockInterruptibly()` |
| **Timed Acquisition** | Unsupported | Supported (`tryLock(timeout, unit)`) |
| **Scope Encapsulation** | Strict lexical block scoping (compiler-enforced) | Explicit method calls (requires mandatory `finally` block) |

### 2.5.2 Lock Acquisition Policies and the AQS Non-Fair Barging Signature

A subtle but profound finding of this research concerns the latency distribution differences between `synchronized` and `ReentrantLock`.

In standard enterprise usage, `ReentrantLock` is instantiated via its default parameterless constructor:

```java
private final Lock lock = new ReentrantLock(); // Defaults to NonfairSync
```

In the OpenJDK implementation, `ReentrantLock` delegates internal queue management to `AbstractQueuedSynchronizer` (AQS). The default `NonfairSync` implementation incorporates an aggressive optimization: **direct compare-and-swap (CAS) barging**.

```
+-----------------------------------------------------------------------------------+
|               AQS NON-FAIR DIRECT-CAS BARGING MECHANICS                           |
+-----------------------------------------------------------------------------------+
  Thread A (Currently holds lock, finishing work)
  AQS Wait Queue:  [Head] <── [VirtualThread B (Waiting)] <── [VirtualThread C]
                                        ▲
  Newly Arriving VirtualThread D        │
  Bypasses Queue! Directly executes:    │ (VirtualThread B has been waiting 4.8s,
  compareAndSetState(0, 1)              │  waking up from carrier unpark)
  ├── SUCCESS!                          │
  └── Thread D BARGES ahead of B! ──────┴─> Thread B must re-park and wait again!
+-----------------------------------------------------------------------------------+
```

When a thread attempts to acquire an unlocked `NonfairSync` lock, it immediately executes `compareAndSetState(0, 1)`. If the lock was released fractions of a microsecond prior, the newly arriving thread **barges** ahead of all threads currently waiting in the AQS FIFO queue.

Because waiting virtual threads must be unparked by the scheduler, re-enqueued, and remounted onto a carrier thread, a barging thread already executing on a hot carrier core possesses an overwhelming scheduling advantage. This phenomenon introduces substantial tail-latency jitter, directly explaining the **$\approx 23\times$ wider latency dispersion** observed in `ReentrantLock` compared to `synchronized` (`CLM-RQ1-05`).

---

## 2.6 Persistence Layer Concurrency: Blocking I/O, JDBC, and Connection Pools

### 2.6.1 Socket I/O vs. Regular File I/O Asymmetry in OS Kernels

A widespread misconception regarding Project Loom is that *all* Java blocking I/O unmounts virtual threads. In reality, the runtime behavior depends entirely on whether the underlying operating system kernel supports non-blocking readiness notification for the specific file descriptor:

1.  **Network Socket I/O (Unmounts Cleanly):** Modern operating systems provide asynchronous readiness multiplexers for network sockets (`epoll` on Linux, `kqueue` on macOS, I/O Completion Ports on Windows). HotSpot integrates a background network poller thread that monitors socket readiness. When a virtual thread executes a socket read or write that cannot proceed immediately, it unmounts cleanly to the heap.
2.  **Regular File Descriptor I/O (Blocks Carrier Threads):** In standard POSIX operating systems (Linux and macOS), regular disk file descriptors are fundamentally incompatible with `epoll` and `kqueue`; the OS kernel always reports regular files as immediately "ready," even though actual read/write operations block waiting on physical NVMe/SATA disk controller I/O. True asynchronous file I/O requires newer kernel interfaces (such as Linux `io_uring`), which are not integrated into Java 21 Virtual Threads.

Consequently, when a virtual thread performs regular file I/O via `java.io` or `java.nio.channels.FileChannelImpl`, **it physically blocks the carrier thread**. HotSpot mitigates this carrier blockage using `ForkJoinPool.ManagedBlocker`, dynamically expanding carrier thread count up to `maxPoolSize` (`CHK-JDK-18`). If an application executes intensive synchronous file logging or disk cache operations under virtual threads, carrier thread proliferation can exhaust operating system thread limits, as demonstrated in real-world rollbacks such as dotCMS PR #36900 (`CHK-JDK-19`).

### 2.6.2 Relational Database Persistence and HikariCP Architecture

In enterprise Spring Boot MVC systems, relational data persistence relies upon the Java Database Connectivity (JDBC) API. Because JDBC connections are stateful, single-threaded socket connections, concurrent requests cannot share a single physical connection; they must borrow connections from a managed connection pool, typically **HikariCP**.

HikariCP implements an exceptionally fast, lock-free connection pool architecture centered around a specialized data structure: the `ConcurrentBag`. The lifecycle of a connection checkout proceeds as follows:
1.  **Thread-Local Fast Path:** HikariCP attempts to retrieve a previously used connection cached in thread-local storage.
2.  **Shared Bag Scan:** If no cached connection exists, HikariCP scans a shared `CopyOnWriteArrayList` of available connections.
3.  **Handoff Queue Waiting:** If all connections in the pool are currently checked out, the requesting thread enters a synchronous handoff queue implemented via `SynchronousQueue` or `LockSupport.parkNanos()`.

Because HikariCP's connection wait mechanics delegate directly to `LockSupport.parkNanos()`, **waiting for a database connection in HikariCP unmounts virtual threads cleanly without pinning carrier threads** (`CHK-JDK-23`).

However, this clean unmounting exposes the **Connection Pool Sizing Fallacy** (`CLM-MIG-03`). While a JVM may support many virtual threads subject to heap and workload limits, the physical database server (e.g., PostgreSQL or Oracle) is strictly bounded by hardware capacity (CPU cores, RAM buffer pools, disk IOPS, and transaction row locks). If an engineering team expands the HikariCP pool to thousands of connections to match virtual-thread concurrency, the database engine may encounter increased memory, scheduling, and query-contention costs; the magnitude is workload- and database-dependent.

### 2.6.3 Database Driver Pinning Vulnerabilities

Even when application code avoids `synchronized`, legacy database drivers historically contained internal intrinsic monitor locks wrapping network socket write streams.

A prominent example is the PostgreSQL JDBC driver (`pgjdbc`). Prior to version **42.6.0**, the driver synchronized on an internal stream monitor during query transmission:
*   In `pgjdbc < 42.6.0`, when a query was sent across the network socket, the driver held an intrinsic Java monitor while blocking on network I/O, **pinning the carrier thread on Java 21**.
*   In pgjdbc version **42.6.0** (evaluated in this study via version 42.7.10), PostgreSQL maintainers refactored these internal socket synchronization blocks to explicit locks, eliminating driver-level carrier pinning (`CLM-RQ2-06`).

Auditing third-party driver dependencies is therefore an essential prerequisite for virtual thread migration.

---

## 2.7 ThreadLocal Semantics, Request Context, and Memory Retention

### 2.7.1 The Role of ThreadLocal in Enterprise Spring Frameworks

Enterprise Spring applications make extensive use of `ThreadLocal` storage for implicit per-request context management:
*   `SecurityContextHolder`: Stores the authenticated user identity and security credentials.
*   `RequestContextHolder`: Exposes HTTP request attributes to arbitrary service beans.
*   `TransactionSynchronizationManager`: Tracks active JDBC transactions and connection bindings.

### 2.7.2 The Memory Scaling Hazard Under Ephemeral Concurrency (`CLM-RQ2-07`)

In traditional platform thread deployments, `ThreadLocal` usage was implicitly constrained by the bounded size of the web container's thread pool:
$$\text{Memory}_{\text{ThreadLocal}} \le N_{\text{platform\_pool}} \times \text{Size}_{\text{context}} = 200 \times \text{Size}_{\text{context}}$$

Because platform worker threads are reused, context footprint was bounded by the active pool only under the stated payload and cleanup assumptions.

Under Virtual Threads, this operational assumption collapses:
*   Virtual threads are ephemeral: a new virtual thread is created for every incoming HTTP request and discarded upon request completion.
*   If an application or library attaches large object graphs to a virtual thread's `ThreadLocal` map without invoking `ThreadLocal.remove()` in a mandatory `finally` block, the memory remains referenced until garbage collection cleans up the dead virtual thread.
*   If 100,000 virtual threads execute concurrently, total memory overhead scales linearly as $O(N)$:
$$\text{Memory}_{\text{ThreadLocal}} = N_{\text{concurrent\_virtual\_threads}} \times \text{Size}_{\text{context}}$$
This parameterized projection identifies a possible heap risk, not an observed outcome. Actual retention depends on payload size, reachability, request lifetime, garbage collection, and cleanup discipline; heap exhaustion was not measured here.

---

## 2.8 The Foreign Function Interface Boundary: JNI and Project Panama

### 2.8.1 Java Native Interface (JNI) Execution Mechanics

Many enterprise Java backends rely upon native compiled code (C/C++) via the **Java Native Interface (JNI)** or the modern **Foreign Function & Memory (FFM) API (Project Panama / JEP 454)**. Native bindings are ubiquitous in cryptographic accelerators, high-performance compression libraries, embedded databases (e.g., SQLite), hardware security modules, and legacy C system integrations.

When a Java thread invokes a native C function via JNI:
1.  HotSpot transitions the thread state from `_thread_in_Java` to `_thread_in_native`.
2.  Execution leaves the managed JVM bytecode environment and enters compiled native machine code executing directly on the physical processor.

### 2.8.2 Carrier Captivity During Native System Calls (`CLM-RQ2-01`, `CLM-RQ2-02`)

The interaction between Virtual Threads and native code exposes a critical architectural vulnerability: **silent carrier thread captivity**.

```
+-----------------------------------------------------------------------------------+
|               SILENT CARRIER CAPTIVITY IN FOREIGN CODE (JNI)                      |
+-----------------------------------------------------------------------------------+
  Virtual Thread invokes native method: NativeService.blockingOperation()
    │
    ▼
  Thread enters: _thread_in_native state
  Executes compiled C function in libnativeblocking.dylib
    │
    ▼
  C code invokes blocking POSIX syscall: nanosleep(&req, NULL)
    ├── Darwin / Linux kernel suspends OS Platform Thread (Carrier)
    ├── Thread enters a Darwin/Mach wait state (Linux-specific terminology such as `TASK_INTERRUPTIBLE` does not apply to this host)
    │
    ▼
  CARRIER THREAD IS HELD CAPTIVE IN THE OS KERNEL!
  ├── Native code NEVER calls HotSpot Continuation.yield()
  ├── Continuation freeze subsystem is COMPLETELY BYPASSED
  ├── JFR jdk.VirtualThreadPinned event is NEVER GENERATED (Count = 0!)
  └── Carrier consumes ~0 active CPU cycles (Steady-State %CPU ~ 1.0%)
+-----------------------------------------------------------------------------------+
```

When native C code executes a blocking system call (such as POSIX `nanosleep()`, synchronous file `read()`, or socket `connect()`):
1.  The operating system kernel suspends the underlying physical platform thread.
2.  Because the thread is executing outside the managed JVM environment, **it never invokes `Continuation.yield()`**.
3.  The continuation freeze engine is bypassed entirely; the virtual thread cannot unmount.
4.  The underlying OS carrier thread is captured and held captive for the entire duration of the native call.
5.  **The Observability Failure:** Because `java.lang.VirtualThread.parkOnCarrierThread()` is never called, HotSpot never triggers `postPinnedEvent`. Consequently, **Java Flight Recorder emits exactly zero `jdk.VirtualThreadPinned` events** (`CLM-RQ2-01`).
6.  **The CPU Utilization Reality:** Because the carrier thread is suspended in the operating-system wait state, it consumes little active processor time in this tested path. Process telemetry confirms that steady-state JVM CPU utilization during native blocking is **approximately 1.0%**, conclusively disproving the industrial myth that carrier blocking manifests as 100% CPU spinning (`CLM-RQ2-02`).

---

## 2.9 Observability, Telemetry, and Diagnostics

### 2.9.1 Java Flight Recorder (JFR) Instrumentation and the 20 ms Threshold (`CLM-METH-04`)

Java Flight Recorder (JFR) is the primary low-overhead diagnostic engine built into the OpenJDK HotSpot JVM. To monitor virtual thread scheduling, OpenJDK introduced the event:

```xml
<event name="jdk.VirtualThreadPinned">
  <setting name="enabled">true</setting>
  <setting name="threshold">20 ms</setting>
  <setting name="stackTrace">true</setting>
</event>
```

A critical diagnostic limitation governed by `CLM-METH-04` is the **20 ms duration threshold**:
*   HotSpot's built-in `default.jfc` and `profile.jfc` templates enforce a default minimum event threshold of **20 ms**.
*   If a virtual thread pins its carrier thread inside a `synchronized` block for 5 ms, 10 ms, or 19 ms, **JFR silently discards the event**.
*   Consequently, observing zero `jdk.VirtualThreadPinned` events in a flight recording **does not prove the absence of carrier pinning**; it proves only that no individual pinning duration exceeded the 20 ms threshold.

### 2.9.2 Breakdown of Legacy APM Tools and ThreadMXBean (`CHK-JDK-13`)

Enterprise Application Performance Monitoring (APM) agents (e.g., Prometheus JMX Exporters, Datadog, New Relic) historically monitored JVM concurrency by polling `java.lang.management.ThreadMXBean`.

In Java 21 LTS, `ThreadMXBean` intentionally excludes virtual threads (`CHK-JDK-13`):
*   `ThreadMXBean.getAllThreadIds()` and `getThreadCount()` monitor **platform threads only**.
*   `ThreadMXBean.getThreadCpuTime(id)` returns `-1` for virtual thread identifiers.
*   As a result, legacy monitoring dashboards display a flat line of ~30 platform threads even when an application is processing 50,000 concurrent virtual thread requests. Operations teams relying on legacy thread metrics are completely blind to virtual thread surges.

### 2.9.3 JVMTI Observer Effect and Carrier Serialization (`CHK-JDK-15`)

When developers attach external profilers that track virtual thread mount/unmount events via the JVM Tool Interface (JVMTI), HotSpot executes internal state transitions guarded by the global VM lock `JvmtiThreadState_lock`.

Under high concurrency, contention for `JvmtiThreadState_lock` serializes carrier worker threads across the entire JVM (documented in `async-profiler` Issue #779). This observer effect introduces severe performance distortion, justifying this dissertation's methodological decision to rely strictly on non-invasive in-process JFR recording and host OS telemetry rather than external JVMTI profilers.

---

## 2.10 Performance Measurement Foundations and The Causal Saturation Model

### 2.10.1 Fundamental Concurrency Laws: Amdahl, Little, and Kendall

To evaluate virtual thread performance scientifically, empirical observations must be interpreted through classical queueing theory and concurrency conservation laws:

#### 1. Amdahl's Law (1967)
Amdahl's Law defines the maximum theoretical speedup $S(N)$ achievable by allocating $N$ parallel processing units to a task:

$$S(N) = \frac{1}{(1 - P) + \frac{P}{N}}$$

Where $P$ represents the parallelizable fraction of the workload and $(1 - P)$ represents the strictly serial fraction. If an operation spends 99.9% of its duration inside a mutual exclusion lock, $(1 - P) = 0.999$. Even if $N \to \infty$, the maximum theoretical speedup is strictly capped:

$$\lim_{N \to \infty} S(N) = \frac{1}{1 - P} = \frac{1}{0.999} \approx 1.001$$

#### 2. Little's Law (1961) (`CLM-METH-05`)
In any stationary queueing system, the average number of requests in the system ($L$) equals the long-term average effective arrival rate ($\lambda$) multiplied by the average time a request spends in the system ($W$):

$$L = \lambda W \quad \iff \quad N = X \times (R + Z)$$

For this workload, the configured client think time is $Z = 0.100\text{ s}$. Therefore, in a closed-loop benchmarking regime where $N$ Virtual Users issue requests and wait between iterations:

$$R = \frac{N}{X} - Z$$

When response time $R$ inflates due to queueing behind a serialized bottleneck, throughput $X$ must decrease proportionally.

#### 3. Kendall's Single-Server Service Ceiling
A critical section guarded by a mutual exclusion lock acts as a single-server queue ($M/M/1$ or $G/G/1$) with a deterministic service duration $D = T_{\text{critical}}$. The absolute maximum service rate ($\mu$) of this bottleneck is:

$$\mu = \frac{1}{D} = \frac{1}{T_{\text{critical}}}$$

No concurrency architecture can exceed this physical ceiling.

### 2.10.2 The Request Decomposition Model

To resolve Copilot Note #5 and establish what benchmark harnesses can and cannot measure, this dissertation establishes the **Request Decomposition Model**:

$$T_{\text{request}} = T_{\text{queue}} + T_{\text{critical}} + T_{\text{independent}} + T_{\text{overhead}}$$

Where:
*   $T_{\text{queue}}$: Time spent waiting to acquire access to a serialized resource or carrier thread.
*   $T_{\text{critical}}$: Time spent holding the mutual exclusion lock or serialized domain resource.
*   $T_{\text{independent}}$: Time spent performing parallelizable, independent work (e.g., JSON serialization, hashing, independent remote calls).
*   $T_{\text{overhead}}$: Framework routing, socket reading, and JVM scheduler dispatch latency.

```
+-----------------------------------------------------------------------------------+
|               REQUEST DECOMPOSITION AND CAUSAL SATURATION MODEL                   |
+-----------------------------------------------------------------------------------+
  CASE A: DOMINANT CRITICAL SECTION (The /payments Benchmark Protocol)
  [=== T_queue (4500 ms) ===][===== T_critical (500 ms) =====][ T_indep (0.5 ms) ]
  ├── T_critical represents 99.9% of non-queue execution time.
  ├── Capacity is strictly bound by: mu = 1 / T_critical = 1 / 0.5s = 2.0 req/s.
  └── Eliminating carrier pinning via ReentrantLock frees carriers, but CANNOT
      increase throughput because T_critical admits only ONE request at a time!

  CASE B: SHORT CRITICAL SECTION WITH DOMINANT INDEPENDENT WORK
  [ T_q ][ T_crit (2 ms) ][============= T_independent (498 ms) =============]
  ├── T_critical is minimal; requests spend 99% of time in independent I/O.
  ├── Eliminating carrier pinning allows thousands of virtual threads to execute
  │   T_independent concurrently across carrier cores without starvation.
  └── Throughput scales dramatically from 2 req/s to hundreds of req/s!
+-----------------------------------------------------------------------------------+
```

*   **Analysis of Case A (The `/payments` Study):** When $T_{\text{critical}} \gg T_{\text{independent}}$ (as in `/payments`, where $T_{\text{critical}} = 500\text{ ms}$ and $T_{\text{independent}} \le 0.5\text{ ms}$), the system is completely serialized at the application domain level. Refactoring from `synchronized` to `ReentrantLock` eliminates monitor pinning, but throughput remains pegged at $\approx 1.96\text{ req/s}$ (`CLM-RQ1-04`).
*   **Analysis of Case B (Independent Work):** When $T_{\text{independent}} \gg T_{\text{critical}}$, carrier unpinning allows thousands of virtual threads to execute their independent work concurrently. In this scenario, eliminating pinning restores carrier availability, delivering massive throughput expansion.

This formal distinction prevents false generalities: **unpinning eliminates carrier starvation; it does not eliminate domain serialization**.

### 2.10.3 Workload Models: Open-Loop vs. Closed-Loop Load Realism

As demonstrated by Schroeder, Wierman, and Harchol-Balter (2006), the choice of workload generator fundamentally dictates system queueing behavior:
*   **Closed-Loop Workloads (k6 Virtual Users):** Virtual users wait for the previous response before issuing the next request. Under closed-loop models, when a server slows down, the client arrival rate automatically self-throttles. Throughput plateaus, and queue lengths remain bounded by $N_{\text{VU}}$.
*   **Open-Loop Workloads (Poisson Arrival):** Requests arrive according to an independent stochastic process irrespective of server response time. If arrival rate exceeds service capacity ($\lambda > \mu$), queue lengths escalate toward infinity and the system collapses into catastrophic packet drops.

The empirical benchmarks in this research operate strictly in a **closed-loop regime**, modeling synchronous microservice RPC clients and batch processors.

---

## 2.11 Critical Review of Related Empirical Studies

To situate this dissertation within the broader scientific literature, this section critically analyzes the closest empirical studies evaluating Project Loom, reactive programming, and JVM concurrency:

### Table 2.3: Comparative Synthesis of Closest Empirical Literature

| Study / Citation | Evaluated System & Runtime | Primary Contribution | Critical Methodological Limitation Relative to This Thesis |
| :--- | :--- | :--- | :--- |
| **Pressler (JEP 444, 2023)** | OpenJDK Core Runtime (Java 21 LTS) | Normative specification of Virtual Threads, carrier scheduling, and pinning definitions. | Platform architectural specification; does not quantify end-to-end Spring MVC application lock/resource interactions. |
| **Pressler (JEP 491, 2024)** | OpenJDK Core Runtime (Java 24 GA) | Normative specification of `ObjectMonitor` redesign eliminating monitor pinning. | JDK enhancement proposal; establishes version boundary, but provides no empirical data for enterprise Spring applications. |
| **Beronić et al. (2021)** | Early Loom Prototype (pre-JDK 17) | Early exploratory analysis of structured concurrency and virtual thread scalability. | Evaluated pre-standard Loom prototypes; does not evaluate Java 21 LTS, Spring Boot MVC, or JFR pinning telemetry. |
| **Navarro et al. (2023)** | Quarkus Framework (Java 19 / 20) | Evaluated virtual threads under container resource constraints; showed reactive Quarkus outperformed VT near saturation. | Focuses on Quarkus reactive core; does not isolate Java `synchronized` monitors, JDBC pools, or JNI boundaries in Spring MVC. |
| **Lašić et al. (2024)** | Database Server Workloads (Java 21) | Assessed virtual thread throughput in database-driven server workloads. | Demonstrates that database pools bound scalability, but does not isolate application-level monitor pinning or JNI carrier capture. |
| **Likus & Krużel (2025)** | Spring REST Endpoints (Java 21) | Compared I/O-bound vs. CPU-bound REST performance under Virtual Threads. | Closest framework context; does not evaluate `synchronized` vs. `ReentrantLock` refactoring, JFR stack attribution, or JNI stalls. |
| **Charlak et al. (2026)** | Comparative Web-Server Study | Demonstrated reactive architectures retain memory efficiency advantages near server saturation. | Focuses on reactive vs. virtual thread paradigms; does not evaluate migration refactoring patterns for legacy Spring MVC systems. |
| **Traini et al. (2022)** | 586 JMH Benchmarks from 30 Systems | Formulated rigorous methodology for JVM steady-state warm-up, repetition, and variance discipline. | Methodological literature justifying experimental rigor; does not evaluate Virtual Threads or concurrency mechanics. |
| **dotCMS Core (PR #36900, 2024)** | dotCMS Enterprise CMS (Java 21) | Real-world industrial rollback: reverted async cache commits on virtual threads due to disk I/O and lock pinning. | Industry post-mortem confirming practical migration failure modes, but lacks controlled academic benchmark isolation. |

---

## 2.12 Related-Work Synthesis and The Research Gap

### 2.12.1 Literature Synthesis

The existing literature establishes several foundational realities:
1.  **Concurrency Capacity:** Virtual Threads dramatically reduce the memory cost of concurrent tasks compared to platform threads for purely non-blocking or cooperative I/O workloads (JEP 444, Beronić et al.).
2.  **Downstream Bottlenecks:** When workloads interact with external relational databases, database connection pools quickly supersede thread scheduling as the primary throughput constraint (Lašić et al., Navarro et al.).
3.  **Reactive Efficiency Near Saturation:** In CPU-bound or saturated network conditions, optimized reactive event loops retain slight memory and resource efficiency advantages over virtual threads (Charlak et al., Navarro et al.).
4.  **Real-World Friction Points:** Industrial teams have experienced unexpected rollbacks when enabling virtual threads on workloads involving synchronous disk I/O and legacy locking (dotCMS PR #36900).

### 2.12.2 The Identified Research Gap

Despite these contributions, the literature exhibits a critical **research gap**:
> *Prior empirical studies have failed to provide a controlled, reproducible, end-to-end Spring Boot MVC investigation that jointly isolates:*
> 1.  *A Java 21 `synchronized` monitor-pinning treatment alongside an identical `ReentrantLock` refactored treatment under an unbroken business endpoint contract;*
> 2.  *Controlled platform thread and diagnostic baseline comparisons on the identical hardware artifact;*
> 3.  *Continuous, low-overhead Java Flight Recorder (JFR) stack attribution verifying the exact duration and method origin of `jdk.VirtualThreadPinned` events;*
> 4.  *A clear empirical decoupling of carrier thread unmounting from application-level mutual exclusion serialization; and*
> 5.  *An empirical deconstruction of silent carrier captivity across foreign function (JNI) boundaries, distinguishing OS kernel wait-states from active CPU utilization.*

This dissertation is specifically designed to fill this research gap. By establishing a rigorous empirical testbed, enforcing strict cryptographic provenance, and applying classical queueing theory, this study provides software engineering researchers and practitioners with an authoritative, mechanism-grounded foundation for migrating enterprise Spring Boot MVC systems to Java 21 Virtual Threads.

---

*(End of Chapter 2 Draft Text)*
