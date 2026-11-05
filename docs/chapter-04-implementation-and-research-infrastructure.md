# Chapter 4: Implementation and Research Infrastructure

## 4.1 Application Architecture and Core Endpoints

To investigate the runtime interactions between Java 21 Virtual Threads, monitor pinning, mutual exclusion serialization, database persistence, and foreign function boundaries, a dedicated, instrumented enterprise benchmark application was engineered. The system models an enterprise Model-View-Controller (MVC) microservice architecture implemented in Java 21 LTS utilizing the Spring Boot 3.5.12 framework, deployed on top of an embedded Apache Tomcat 10.1.52 servlet container, and compiled via Apache Maven 3.9.

### 4.1.1 Package Structure and Architectural Decomposition

The application source tree is organized under the root package `com.thesis.virtualthreadsdemo` in [`src/main/java/com/thesis/virtualthreadsdemo/`](../src/main/java/com/thesis/virtualthreadsdemo/), adhering to a strict separation of concerns across four primary architectural layers: HTTP controllers, service implementations, data persistence abstractions, and low-level native shared libraries.

```
virtual-thread-springs/
├── pom.xml                                   // Maven BOM, dependencies & JNI compilation lifecycle
├── docker-compose.yml                        // Containerized PostgreSQL 15 & resource limits
├── Dockerfile                                // Multi-stage build definition for containerized trials
├── native/
│   └── native_blocking.c                     // C source: POSIX nanosleep() and nativeNoop()
├── src/main/
│   ├── java/com/thesis/virtualthreadsdemo/
│   │   ├── VirtualThreadsDemoApplication.java// Spring Boot bootstrap entry point
│   │   ├── controller/                       // HTTP REST routing and request mapping
│   │   │   ├── PaymentController.java        // POST /payments (synchronization treatments)
│   │   │   ├── OrderController.java          // GET /orders (JDBC persistence & ThreadLocal)
│   │   │   ├── ProductController.java        // GET /products (fast-path JDBC baseline)
│   │   │   ├── NativeController.java         // GET /native (JNI blocking POSIX nanosleep)
│   │   │   ├── NativeShortController.java    // GET /native-short (JNI transit baseline)
│   │   │   ├── CpuController.java            // GET /cpu (CPU-bound FMA compute benchmark)
│   │   │   └── HelloController.java          // GET /hello (zero-allocation health probe)
│   │   ├── service/                          // Business logic, concurrency, and native wrappers
│   │   │   ├── PaymentService.java           // Mutex treatments (synchronized vs. ReentrantLock)
│   │   │   ├── OrderService.java             // Relational retrieval, sleep delay, ThreadLocal
│   │   │   ├── ProductService.java           // Fast-path relational catalog retrieval
│   │   │   ├── NativeBlockingService.java    // JNI wrapper loading libnativeblocking
│   │   │   └── CpuService.java               // Fused multiply-add floating-point benchmark
│   │   └── repository/                       // Persistence abstractions
│   │       ├── OrderRepository.java          // Order data access contract
│   │       └── ProductRepository.java        // Product catalog data access contract
│   └── resources/
│       ├── application.yml                   // Application configuration and runtime properties
│       ├── schema.sql                        // DDL: orders and products relational schema
│       └── data.sql                          // DML: Seed datasets for relational tables
├── k6/
│   ├── isolated-load-test.js                 // Parameterized closed-loop k6 workload harness
│   └── load-test.js                          // Mixed-workload scenario definition
├── run-benchmark.sh                          // Process lifecycle orchestrator & telemetry harness
└── scripts/
    ├── run-java21-synchronization-matrix.sh  // Primary RQ1 matrix runner (12 executions)
    ├── run-native-boundary-matrix.sh         // RQ2 native matrix runner (27 executions across JDKs)
    ├── generate_artifact_inventory.py        // Master artifact ledger generator (504 files)
    ├── generate_run_family_matrix.py         // Run family matrix auditor (120 rows)
    ├── recalculate_metrics.py                // Dual-window metric recalculation engine
    ├── normalize_evidence.py                 // Evidence consolidation and JSON normalization
    └── validate_normalized_evidence.py       // Structural and schema validation harness
```

### Table 4.1: Empirical Endpoint Catalog and Experimental Roles

| Endpoint Path | HTTP Method | Service Implementation | Primary Concurrency Mechanism | Experimental Classification | Addressed Question |
| :--- | :---: | :--- | :--- | :--- | :---: |
| `/payments` | `POST` | [`PaymentService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java) | Configurable mutex (`synchronized`, `ReentrantLock`, `Semaphore`) + 500 ms delay | Primary Mutex Treatment | **RQ1** |
| `/orders` | `GET` | [`OrderService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java) | `ThreadLocal` context + 300 ms delay + `JdbcTemplate.queryForList()` | Persistence & Context Treatment | **RQ2** |
| `/products` | `GET` | [`ProductService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/ProductService.java) | Unconstrained fast-path `JdbcTemplate.queryForList()` (no delay) | Fast-Path Persistence Baseline | **RQ1, RQ2** |
| `/native` | `GET` | [`NativeBlockingService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/NativeBlockingService.java) | JNI binding to C `nanosleep(500ms)` system call | Foreign Syscall Treatment | **RQ2** |
| `/native-short`| `GET` | [`NativeBlockingService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/NativeBlockingService.java) | JNI binding to C `nativeNoop()` (sub-microsecond return) | Native Transit Baseline | **RQ2** |
| `/cpu` | `GET` | [`CpuService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/CpuService.java) | $5 \times 10^6$ iterations of `Math.fma` and `Math.sqrt` | Compute-Bound Negative Control | **RQ1, RQ2** |
| `/hello` | `GET` | [`HelloController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/HelloController.java) | Static string allocation (`"Virtual Threads are working"`) | Zero-I/O Harness Health Probe | **Diagnostics** |

### 4.1.2 Framework Bill of Materials (BOM) and Runtime Versions

To eliminate version ambiguity and ensure strict experimental reproducibility across repeated trial runs, all runtime dependencies were statically pinned via Maven and audited. The resolved component inventory comprises:
*   **Java Runtime Environment:** OpenJDK 64-Bit Server VM (OpenJDK 21.0.8 as recorded in the benchmark manifests; the manifests do not provide a reliable vendor identity), compiling to target bytecode version 21. Comparative boundary trials were executed against OpenJDK 24 (`24.0.2+12`) and early-access OpenJDK 25.
*   **Application Framework:** Spring Boot version **`3.5.12`** (derived from `spring-boot-starter-parent:3.5.12`), pulling Spring Framework core version **`6.2.x`**.
*   **Web Container:** Embedded **Apache Tomcat 10.1.52** (`org.apache.tomcat.embed:tomcat-embed-core:10.1.52`), incorporating virtual thread lifecycle fixes.
*   **Connection Pool:** **HikariCP 6.3.3** (`com.zaxxer:HikariCP:6.3.3`), providing JDBC connection management.
*   **In-Memory Database:** **H2 Database 2.3.232** (`com.h2database:h2:2.3.232`), utilized in local exploratory executions.
*   **Container Database & Driver:** **PostgreSQL 15-alpine** container engine backed by **PostgreSQL JDBC Driver 42.7.10** (`org.postgresql:postgresql:42.7.10`). This driver version strictly exceeds the `pgjdbc >= 42.6.0` threshold, ensuring internal socket monitor refactoring is active ([`CLM-RQ2-06`](../docs/evidence-freeze/claim-evidence-ledger.md#L226-L237)).
*   **Load Generation Harness:** **k6 v1.7.1** in the admitted manifests (darwin/arm64), driving closed-loop HTTP virtual users.

### 4.1.3 Spring Boot 3 Virtual Thread Wiring and Tomcat Configuration

Integration of Java 21 Virtual Threads within the servlet container relies upon Spring Boot 3's auto-configuration infrastructure. When the declarative configuration property:

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

is evaluated during the initialization phase of `org.springframework.boot.autoconfigure.web.embedded.TomcatWebServerFactoryCustomizer`, Spring Boot registers a `TomcatProtocolHandlerCustomizer` bean that modifies Apache Tomcat's underlying `StandardThreadExecutor`:

```java
// Conceptual autoconfiguration executed inside Spring Boot 3
@Bean
public TomcatProtocolHandlerCustomizer<?> protocolHandlerVirtualThreadCustomizer() {
    return protocolHandler -> {
        protocolHandler.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
    };
}
```

```
+-----------------------------------------------------------------------------------+
|               SPRING BOOT 3 TOMCAT VIRTUAL THREAD REQUEST DISPATCH                |
+-----------------------------------------------------------------------------------+
  Client HTTP Connection
            │
            ▼
  Tomcat NioEndpoint Acceptor (Platform Thread)
            │
            ▼
  NioEndpoint Poller multiplexes non-blocking socket via OS readiness (kqueue/epoll)
            │
            ▼ Socket Readable
  TomcatProtocolHandlerCustomizer Executor:
  Executors.newVirtualThreadPerTaskExecutor()
            │
            ├─► Allocates Ephemeral VirtualThread (Heap Continuation < 1 KB)
            │
            ▼
  VirtualThread.start() ──> Scheduled onto Carrier ForkJoinPool (Worker OS Thread)
            │
            ▼
  Spring DispatcherServlet ──> Controller ──> Service Invocation
```

Under this configuration:
1.  **Request Dispatching:** Tomcat's non-blocking `NioEndpoint` acceptor and poller threads accept incoming TCP connections using OS-level event multiplexing (`kqueue` on macOS Darwin; `epoll` on Linux).
2.  **Thread Allocation:** Upon socket readability, request parsing and servlet execution are handed off to an ephemeral Virtual Thread produced by `Thread.ofVirtual().factory()`. The legacy bounded thread pool (Tomcat's traditional default of `maxThreads = 200` platform threads bounded by an internal task queue) is completely bypassed.
3.  **Carrier Scheduling:** The newly allocated virtual thread is submitted to HotSpot's dedicated private virtual-thread scheduler (`java.lang.VirtualThread.DEFAULT_SCHEDULER`), distinct from `ForkJoinPool.commonPool()`.
4.  **Platform Mode Fallback:** When `spring.threads.virtual.enabled` is set to `false`, Tomcat retains its traditional `StandardThreadExecutor`, allocating requests from a bounded pool of 200 physical OS threads.

---

## 4.2 Payment Synchronization Implementations

The primary synchronization treatments evaluated in Research Question 1 are implemented within [`PaymentService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java#L32-L107). The service models an atomic financial transaction where state mutations must be strictly serialized via mutual exclusion to prevent double-spending or ledger inconsistencies:

```java
package com.thesis.virtualthreadsdemo.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;
import java.util.concurrent.Semaphore;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class PaymentService {

    private final String lockMode;
    private final ReentrantLock lock = new ReentrantLock();
    private final ReentrantLock fairLock = new ReentrantLock(true);
    private final Semaphore semaphore = new Semaphore(1);
    private final Semaphore fairSemaphore = new Semaphore(1, true);
    private final Object monitor = new Object();

    public PaymentService(@Value("${demo.payment.lock-mode:reentrant-lock}") String lockMode) {
        if (!lockMode.equals("synchronized")
                && !lockMode.equals("reentrant-lock")
                && !lockMode.equals("fair-reentrant-lock")
                && !lockMode.equals("semaphore")
                && !lockMode.equals("fair-semaphore")
                && !lockMode.equals("none")) {
            throw new IllegalArgumentException(
                    "demo.payment.lock-mode must be synchronized, reentrant-lock, fair-reentrant-lock, "
                            + "semaphore, fair-semaphore, or none");
        }
        this.lockMode = lockMode;
    }

    public String processPayment(String orderId) {
        switch (lockMode) {
            case "synchronized" -> {
                synchronized (monitor) {
                    simulatePaymentCall();
                }
            }
            case "reentrant-lock" -> {
                lock.lock();
                try {
                    simulatePaymentCall();
                } finally {
                    lock.unlock();
                }
            }
            case "fair-reentrant-lock" -> {
                fairLock.lock();
                try {
                    simulatePaymentCall();
                } finally {
                    fairLock.unlock();
                }
            }
            case "semaphore" -> {
                semaphore.acquireUninterruptibly();
                try {
                    simulatePaymentCall();
                } finally {
                    semaphore.release();
                }
            }
            case "fair-semaphore" -> {
                fairSemaphore.acquireUninterruptibly();
                try {
                    simulatePaymentCall();
                } finally {
                    fairSemaphore.release();
                }
            }
            case "none" -> simulatePaymentCall();
        }

        return "Payment processed for order: " + orderId;
    }

    private void simulatePaymentCall() {
        try {
            Thread.sleep(500); // 500 ms serialized critical section
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

### 4.2.1 The Intrinsic Monitor Treatment (`synchronized`)

When `demo.payment.lock-mode` is configured to `synchronized`, mutual exclusion is enforced by entering a Java monitor synchronized on an internal heap object (`private final Object monitor = new Object()`).

#### HotSpot Continuation Freeze Subsystem Mechanics:
1.  **Monitorenter Execution:** When a virtual thread executes bytecode instruction `monitorenter`, HotSpot associates the target `ObjectMonitor` with the thread.
2.  **Unmount Attempt on Blocking:** Inside `simulatePaymentCall()`, the thread calls `Thread.sleep(500)`. In Java 21, `Thread.sleep()` delegates to `VirtualThread.sleepNanos()`, which invokes `VirtualThread.park()` and ultimately calls HotSpot C++ runtime method `Continuation.yield()`.
3.  **The `can_freeze()` HotSpot Predicate:** HotSpot's continuation freeze subsystem ([`continuationFreeze.cpp`](https://github.com/openjdk/jdk/blob/jdk-21%2B35/src/hotspot/share/runtime/continuationFreeze.cpp)) evaluates whether the virtual thread's call frames can be frozen to heap `StackChunk` memory:
    ```cpp
    // Conceptual OpenJDK HotSpot continuationFreeze.cpp predicate
    bool ContinuationFreeze::can_freeze() {
        if (_target->held_monitor_count() > 0) {
            return false; // Intrinsic ObjectMonitor held on stack frame -> FREEZE REJECTED
        }
        return true;
    }
    ```
4.  **Pinning Invocation:** Because the virtual thread holds `monitor`, `can_freeze()` returns `false`. The unmount operation is rejected.
5.  **Carrier Captivity:** Unable to yield, the virtual thread invokes `VirtualThread.parkOnCarrierThread()`. The underlying operating system carrier thread is forced into physical kernel sleep for the full 500 ms duration.
6.  **JFR Pinning Event Generation:** HotSpot posts the `jdk.VirtualThreadPinned` event to the active Java Flight Recorder session, logging the pin duration and full Java stack trace.
7.  **Carrier Starvation Under Single-Carrier Isolation:** Under the single-carrier mechanism isolation constraint (`parallelism=1`), this lone carrier thread is immobilized. Although 9 other virtual users in k6 are waiting to execute, the JVM cannot schedule any task, establishing the empirical foundation of [`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L55) and [`CLM-RQ1-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L57-L70).

> [!IMPORTANT]
> **The Carrier Compensation Fallacy (`CLM-RQ1-07`):** Early literature hypothesized that HotSpot's `ForkJoinPool` dynamically compensates for monitor pinning by spawning additional carrier threads up to `maxPoolSize = 256`. As established by [JEP 444](https://openjdk.org/jeps/444) and verified during research triage ([`fact-check-jdk-runtime.md#L17-L21`](../docs/fact-check-jdk-runtime.md#L17-L21)), **HotSpot never expands carrier parallelism for monitor pinning or native code**. Carrier expansion is reserved exclusively for `ForkJoinPool.ManagedBlocker` calls (file I/O and specific `Object.wait()` calls). Constraining `maxPoolSize=1` strictly eliminated carrier expansion for file operations, ensuring unambiguous single-carrier isolation.

### 4.2.2 The ReentrantLock Treatment (`reentrant-lock`)

When configured to `reentrant-lock`, mutual exclusion is governed by an explicit `java.util.concurrent.locks.ReentrantLock`.

#### Unpinning and Stack Thawing Mechanics:
1.  **Pure Java AQS Architecture:** `ReentrantLock` relies upon `AbstractQueuedSynchronizer` (AQS). Lock state is maintained as an atomic integer, and contending threads are enqueued within an in-memory doubly-linked queue of `Node` objects.
2.  **Clean Continuation Yielding:** Contending virtual threads park via `LockSupport.park()`, which calls `VirtualThread.park()` and `Continuation.yield()`. Because no Java `ObjectMonitor` is held on the stack, `can_freeze()` in `continuationFreeze.cpp` returns `true`.
3.  **Heap Freezing:** HotSpot copies the virtual thread's interpreted and compiled activation frames into a `jdk.internal.vm.StackChunk` object allocated on the Java heap.
4.  **Carrier Release:** The carrier thread unbinds from the virtual thread continuation and immediately returns to the `ForkJoinPool` work-stealing scheduler, free to execute other runnable tasks.
5.  **Resumption via `continuationThaw.cpp`:** When the lock holder releases the lock via `unlock()`, it calls `LockSupport.unpark()`. The scheduler places the waiting virtual thread into a carrier run-queue. Upon dispatch, HotSpot's `continuationThaw.cpp` copies the stack frames from the heap chunk back to the physical carrier stack, restoring execution seamlessly ([`CLM-RQ1-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L72-L84)).

#### The Non-Fair Direct-CAS Barging Signature (`CLM-RQ1-05`):
By default, `ReentrantLock` instantiates a `NonfairSync`. In `NonfairSync.initialTryLock()`, an arriving virtual thread immediately attempts to flip the state word via `compareAndSetState(0, 1)`:

```java
// OpenJDK java.util.concurrent.locks.ReentrantLock.NonfairSync
final boolean initialTryLock() {
    Thread current = Thread.currentThread();
    if (compareAndSetState(0, 1)) { // Direct barging attempt!
        setExclusiveOwnerThread(current);
        return true;
    }
    // ... enqueues only after CAS failure
}
```

If the lock is released at the precise microsecond of request arrival, the newly arriving virtual thread barges ahead of threads that have been parked in the AQS queue for seconds. This barging dynamic introduces high tail-latency dispersion under contention:
*   Intrinsic monitor (`synchronized`) latency standard deviation: $s \le \mathbf{7.4\text{ ms}}$.
*   `ReentrantLock` latency standard deviation: $s \approx \mathbf{16.0\text{--}30.0\text{ ms}}$ (a **$23\times$ expansion** in variance, documented in [`CLM-RQ1-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L101-L112)).

### 4.2.3 Fair Lock and Semaphore Treatments

To evaluate whether the tail latency dispersion observed in `ReentrantLock` could be mitigated, two additional synchronization modes were implemented:
1.  **Fair ReentrantLock (`fair-reentrant-lock`):** Instantiates `new ReentrantLock(true)`. The `FairSync` implementation enforces strict FIFO ordering by invoking `hasQueuedPredecessors()` prior to any CAS acquisition attempt, eliminating barging at the cost of slight CAS throughput overhead.
2.  **Counting Semaphores (`semaphore` and `fair-semaphore`):** Instantiates `Semaphore(1)` and `Semaphore(1, true)`. These treatments evaluate whether counting semaphore AQS state transitions exhibit identical continuation unmounting and barging characteristics as mutual exclusion locks.

### 4.2.4 Diagnostic Control: The No-Lock Branch (`none`)

The `none` branch directly invokes `simulatePaymentCall()` without acquiring any lock. This condition intentionally violates mutual exclusion invariants, simulating an architectural scenario where concurrent payment transactions execute without synchronization. It serves solely as an empirical baseline to quantify the performance ceiling of unconstrained concurrent thread scheduling under identical synthetic delays.

---

## 4.3 Native Interface (JNI) and Foreign Function Implementation

To evaluate the impact of foreign library execution and non-yielding operating system calls on virtual thread schedulers (RQ2), a custom native shared library was developed in C and bound via the Java Native Interface (JNI).

### 4.3.1 C Implementation: `libnativeblocking`

The native source file [`native/native_blocking.c`](../native/native_blocking.c) defines two exported entry points:

```c
#include <jni.h>
#include <errno.h>
#include <time.h>

JNIEXPORT void JNICALL
Java_com_thesis_virtualthreadsdemo_service_NativeBlockingService_nativeSleep(
        JNIEnv *env, jobject self, jlong sleep_millis) {
    (void) env;
    (void) self;

    struct timespec remaining = {
        .tv_sec = (time_t) (sleep_millis / 1000),
        .tv_nsec = (long) ((sleep_millis % 1000) * 1000000L)
    };

    while (nanosleep(&remaining, &remaining) == -1 && errno == EINTR) {
        /* Resume the bounded sleep if a POSIX signal interrupts it. */
    }
}

JNIEXPORT void JNICALL
Java_com_thesis_virtualthreadsdemo_service_NativeBlockingService_nativeNoop(
        JNIEnv *env, jobject self) {
    (void) env;
    (void) self;
}
```

The C library is compiled during the Maven build lifecycle via `exec-maven-plugin` in [`pom.xml#L62-L83`](../pom.xml#L62-L83), producing a shared library (`target/native/libnativeblocking.dylib` on macOS / arm64; `target/native/libnativeblocking.so` on Linux / amd64).

### 4.3.2 The Service Binding: `NativeBlockingService.java`

The Java service encapsulates library loading, configuration properties, and native method declarations:

```java
package com.thesis.virtualthreadsdemo.service;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@ConditionalOnProperty(prefix = "demo.native", name = "enabled", havingValue = "true")
public class NativeBlockingService {

    public static final long DEFAULT_SLEEP_MILLIS = 500L;

    static {
        System.loadLibrary("nativeblocking");
    }

    private final long sleepMillis;

    public NativeBlockingService(
            @Value("${demo.native.sleep-millis:" + DEFAULT_SLEEP_MILLIS + "}") long sleepMillis) {
        if (sleepMillis < 1) {
            throw new IllegalArgumentException("demo.native.sleep-millis must be at least 1");
        }
        this.sleepMillis = sleepMillis;
    }

    private native void nativeSleep(long sleepMillis);
    private native void nativeNoop();

    public String block() {
        nativeSleep(sleepMillis);
        return "Native blocking sleep completed";
    }

    public String noOp() {
        nativeNoop();
        return "Native no-op completed";
    }

    public long sleepMillis() {
        return sleepMillis;
    }
}
```

### 4.3.3 JNI Transition Mechanics and HotSpot Carrier Captivity

The invocation of `nativeSleep(500)` triggers a low-level thread transition within the HotSpot runtime:

```
[Virtual Thread (Java)]
         │
         │ Executes nativeSleep(500)
         ▼
[HotSpot JNI Assembly Stub]
         │ Transitions thread state: _thread_in_Java ──► _thread_in_native
         │ Saves Java register state; aligns stack to C calling convention
         ▼
[Foreign C Function: Java_..._nativeSleep]
         │ Executes POSIX system call: nanosleep(&ts, &ts)
         ▼
[Kernel Space: sys_nanosleep()]
         │ Darwin XNU / Linux kernel places OS carrier thread into wait queue
         │ Thread state = Darwin/Mach wait state; `TASK_INTERRUPTIBLE` is Linux-specific terminology
         │ * Carrier thread yields CPU core to OS scheduler *
         │ * Steady-state CPU consumption drops to ~1.0% *
         │ * VirtualThread continuation is NEVER unmounted! *
         ▼
[HotSpot ForkJoinPool Scheduler]
         │ Scheduler receives NO notification of kernel wait!
         │ Bytecode execution is suspended; safe-points are unreachable.
         │ No Continuation.yield() invoked; zero JFR pinning events emitted.
```

#### Detailed Execution Phases:
1.  **Thread State Transition:** The HotSpot-generated JNI transition stub updates the carrier thread's internal state machine from `_thread_in_Java` to `_thread_in_native`.
2.  **Kernel Wait-Queue Suspension:** The C function executes the POSIX `nanosleep()` system call. The host operating system kernel (Darwin XNU or Linux) places the physical OS carrier thread into an interruptible sleep wait-queue. The thread yields its CPU core to the operating system scheduler.
3.  **Zero Active CPU Consumption (`CLM-RQ2-02`, `DISC-02`):** Process telemetry sampled at 1-second intervals via `ps -p $APP_PID -o %cpu=` recorded **$1.04\% \pm 0.12\%$** across the recorded Java 21 blocking-JNI trials; this refutes busy-spinning for this path but does not generalize to all native calls. This directly refuted the pre-experimental assumption that native blocking manifests as a 100% CPU busy-spin loop ([`discrepancy-register.md#L63-L80`](../docs/evidence-freeze/discrepancy-register.md#L63-L80)).
4.  **Suppression of Continuation Unmounting:** Because the carrier thread is executing machine code outside the JVM's bytecode interpreter loop, it never encounters a bytecode safe-point and never executes `Continuation.yield()`. The virtual thread continuation remains rigidly bound to the carrier.
5.  **JFR Observability Omission (`CLM-RQ2-01`, `DISC-03`):** JFR's `jdk.VirtualThreadPinned` event is architecturally implemented as an **unmount-failure diagnostic**; it is posted exclusively inside `java.lang.VirtualThread.parkOnCarrierThread()` when `Continuation.yield()` returns false. Because `Continuation.yield()` is never called during native syscall execution, JFR recorded exactly **0 pinning events** across all 27 native experimental trials ([`forensic-investigations.md#L40-L120`](../docs/evidence-freeze/forensic-investigations.md#L40-L120)). Under `parallelism=1`, this produces complete carrier starvation that is completely undetectable by standard JFR pinning alerts.

### 4.3.4 Native No-Op Control (`/native-short`)

To ensure that the throughput collapse observed under `/native` was caused by kernel sleep rather than the overhead of crossing the JNI boundary itself, [`NativeShortController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/NativeShortController.java) exposes `/native-short`, which invokes `nativeNoop()`. The native function immediately returns without invoking system calls. This endpoint showed no measurable scheduler stall in the recorded workload; it did not measure a universal nanosecond-level JNI transition cost.

---

## 4.4 Database and Persistence Layer

Relational persistence is implemented using Spring's `JdbcTemplate` backed by a HikariCP connection pool. The application supports dual database environments: an embedded in-memory H2 database for local testing and a containerized PostgreSQL 15 database orchestrated via Docker Compose.

### 4.4.1 Relational Schema and Seed Data

The database schema ([`src/main/resources/schema.sql`](../src/main/resources/schema.sql)) defines two relational tables:

```sql
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;

CREATE TABLE orders (
    id         BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    customer   VARCHAR(100) NOT NULL,
    item       VARCHAR(100) NOT NULL,
    amount     DECIMAL(10, 2) NOT NULL,
    status     VARCHAR(20) NOT NULL
);

CREATE TABLE products (
    id         BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    price      DECIMAL(10, 2) NOT NULL,
    stock      INT NOT NULL
);
```

At startup, the database is seeded by [`src/main/resources/data.sql`](../src/main/resources/data.sql) with 5 initial records in `orders` (representing pending and shipped customer orders) and 8 records in `products` (representing catalog inventory).

### 4.4.2 The Physical Anatomy of the `/orders` Pre-Acquisition Delay Flaw (`CLM-RQ2-03`)

The `/orders` endpoint was designed to evaluate HikariCP connection pool exhaustion and carrier unmounting under constrained connection pool limits (`maximumPoolSize = 1` vs. `10`). Source code inspection of [`OrderService.java#L36-L59`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L36-L59) revealed a critical construct flaw in the service execution lifecycle:

```java
package com.thesis.virtualthreadsdemo.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;

@Service
public class OrderService {

    private static final ThreadLocal<String> REQUEST_CONTEXT = new ThreadLocal<>();
    private final JdbcTemplate jdbcTemplate;

    public OrderService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<Map<String, Object>> getOrders() {
        REQUEST_CONTEXT.set("user-request-" + Thread.currentThread().getName());

        try {
            // CONSTRUCT FLAW: 300 ms sleep executes BEFORE connection checkout!
            simulateSlowQuery();
            return jdbcTemplate.queryForList("SELECT * FROM orders");
        } finally {
            REQUEST_CONTEXT.remove();
        }
    }

    private void simulateSlowQuery() {
        try {
            Thread.sleep(300); // 300 ms simulated slow query delay
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

#### Detailed Execution Sequence and Pool Utilization Derivation:
1.  **Absence of Transactional Context:** Neither `OrderService` nor `getOrders()` is annotated with Spring's `@Transactional`.
2.  **Deferred Connection Acquisition:** In standard non-transactional Spring JDBC, `JdbcTemplate.queryForList()` obtains a database connection lazily via `DataSourceUtils.getConnection()` inside `execute()` at line 43.
3.  **Uncoupled Delay:** `simulateSlowQuery()` (`Thread.sleep(300)`) executes at line 42, **strictly prior to connection checkout**. During this 300 ms duration, the virtual thread holds zero database connections; it simply unmounts from its carrier thread and waits in heap memory.
4.  **Sub-Millisecond Query Hold Time:** When `queryForList("SELECT * FROM orders")` finally executes at line 43, it checks out a connection from HikariCP, executes a fast query over the 5-row table in $< 0.1\text{ ms}$, and immediately releases the connection back to the pool in the `finally` block of `JdbcTemplate.execute()`.
5.  **Pool Utilization Consequence (Little's Law):** Under 50 concurrent virtual users with 300 ms sleep and 100 ms k6 think time ($R \approx 300.5\text{ ms}$, think time $Z = 100\text{ ms}$), total throughput is:
    $$X = \frac{N}{R + Z} = \frac{50}{0.3005 + 0.100} \approx 124.8\text{ req/s}$$
    With a connection hold time of $T_{\text{hold}} \approx 0.0001\text{ s}$ ($0.1\text{ ms}$), average pool occupancy $L_{\text{pool}}$ is:
    $$L_{\text{pool}} = X \times T_{\text{hold}} = 124.8 \times 0.0001 \approx \mathbf{0.0125\text{ connections}}$$
    Even during the 50-VU load test with `maximumPoolSize = 1`, the HikariCP pool was over **98.7% idle**. No connection wait queue ever formed, explaining why pool size 1 and pool size 10 produced identical latency profiles ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L193), [`DISC-07`](../docs/evidence-freeze/discrepancy-register.md#L150-L166)).

### 4.4.3 The YAML Indentation Defect and Autoconfiguration Fallback (`CLM-RQ2-04`)

A secondary configuration defect was identified during static inspection of [`src/main/resources/application.yml`](../src/main/resources/application.yml#L13-L31):

```yaml
spring:
  threads:
    virtual:
      enabled: true

demo:
  native:
    enabled: false
    sleep-millis: 500
  payment:
    lock-mode: reentrant-lock

  # CONFIGURATION DEFECT: Indented under demo: instead of root spring:
  datasource:
    url: jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1
    driver-class-name: org.h2.Driver
    username: sa
    password:

  h2:
    console:
      enabled: true

  jpa:
    hibernate:
      ddl-auto: none
    show-sql: false
    open-in-view: false

  sql:
    init:
      mode: always
```

*   **Property Binding Evaluation:** Spring Boot's `DataSourceAutoConfiguration` binds properties matching the prefix `spring.datasource.*`. Because lines 13–31 were indented under `demo:`, Spring Boot bound them as `demo.datasource.*`, `demo.jpa.*`, and `demo.sql.*`.
*   **Classpath Fallback:** Finding no `spring.datasource.url` defined, Spring Boot's `EmbeddedDatabaseConnection` automatically initiated an auto-configured in-memory H2 database based on `com.h2database:h2` on the classpath.
*   **Default Pool Parameters:** The fallback H2 database was initialized with HikariCP 6.3.3 default properties: **`maximumPoolSize = 10`**, `minimumIdle = 10`, and `connectionTimeout = 30000 ms`. Custom pool adjustments attempted in local H2 runs via `application.yml` were completely inert ([`CLM-RQ2-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L195-L208), [`DISC-06`](../docs/evidence-freeze/discrepancy-register.md#L133-L149)).

### 4.4.4 Docker Compose PostgreSQL 15 Deployment and JFR Omission

In contrast to the local H2 setup, the containerized PostgreSQL environment was orchestrated via [`docker-compose.yml`](../docker-compose.yml):

```yaml
version: '3.8'
services:
  demo-app:
    build: .
    container_name: vt-springs-app
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/thesis_db
      SPRING_DATASOURCE_USERNAME: postgres
      SPRING_DATASOURCE_PASSWORD: thesis
      SPRING_JPA_HIBERNATE_DDL_AUTO: none
      SPRING_SQL_INIT_MODE: always
      SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE: "${HIKARI_MAXIMUM_POOL_SIZE:-10}"
      SPRING_THREADS_VIRTUAL_ENABLED: "true"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G

  postgres:
    image: postgres:15-alpine
    container_name: vt-springs-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: thesis
      POSTGRES_DB: thesis_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

In this environment:
1.  **Valid Environment Binding:** Environment variables used the canonical `SPRING_DATASOURCE_*` prefix, successfully overriding defaults and allowing parameterization of `HIKARI_MAXIMUM_POOL_SIZE` (tested at pool sizes 1 and 10).
2.  **Driver Pinning Immunity (`CLM-RQ2-06`):** The application resolved PostgreSQL JDBC driver `42.7.10`. In pgjdbc version `42.6.0`, internal driver monitors wrapping network socket streams were refactored to `ReentrantLock` (PR #2670), ensuring database network reads do not pin carrier threads.
3.  **JFR Instrumentation Omission (`CLM-RQ2-05`, `DISC-08`):** Audit of [`Dockerfile#L14-L18`](../Dockerfile#L14-L18) confirmed that the container image entry point executes `java -jar app.jar` without `-XX:StartFlightRecording`. Consequently, while k6 measured stable HTTP latencies ($p50 \approx 303.5\text{ ms}$), no JFR data exists for containerized runs; all claims of measured carrier unmounting on PostgreSQL are declared **Not Established** ([`CLM-RQ2-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L210-L224)).

---

## 4.5 Request Context and ThreadLocal Lifecycle

The application explicitly models request-scoped context propagation in [`OrderService.java#L28-L47`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L28-L47) to evaluate the memory and hygiene implications of ThreadLocal storage under virtualized concurrency (RQ2):

```java
public class OrderService {

    // ANTI-PATTERN: Static ThreadLocal capturing per-request user context
    private static final ThreadLocal<String> REQUEST_CONTEXT = new ThreadLocal<>();

    public List<Map<String, Object>> getOrders() {
        // Simulates context population (e.g., Spring Security SecurityContextHolder)
        REQUEST_CONTEXT.set("user-request-" + Thread.currentThread().getName());

        try {
            simulateSlowQuery();
            return jdbcTemplate.queryForList("SELECT * FROM orders");
        } finally {
            // Mandatory defensive cleanup
            REQUEST_CONTEXT.remove();
        }
    }
}
```

### 4.5.1 Architectural Memory Analysis: Platform vs. Virtual Threads (`CLM-RQ2-07`)

In traditional Spring MVC deployments, a bounded thread pool (Tomcat's default 200 platform threads) serves incoming requests. Each platform thread retains an internal `ThreadLocalMap`. Even if an application fails to invoke `ThreadLocal.remove()`, the maximum number of thread-local map instances is strictly bounded by the maximum pool size:

$$\text{Max Memory}_{\text{platform}} = N_{\text{threads}} \times M_{\text{context}} = 200 \times M_{\text{context}}$$

Where $M_{\text{context}}$ is the byte size of the context payload.

Under Virtual Threads, thread creation is unbounded ($10^4$ to $10^6$ concurrent threads). When a virtual thread allocates a ThreadLocal variable:
1.  A dedicated `ThreadLocalMap` is allocated on the Java garbage-collected heap for that specific virtual thread continuation.
2.  If the virtual thread remains reachable while it is long-lived, queued in a downstream executor, or blocked on an external socket, its `ThreadLocalMap` remains reachable as well.
3.  Under $N = 100,000$ concurrent requests, heap memory consumption scales linearly:
    $$\text{Memory}_{\text{virtual}} = 100,000 \times M_{\text{context}}$$
4.  If $M_{\text{context}} = 50\text{ KB}$ (typical of enterprise security credentials, JWT tokens, tenant metadata, and distributed tracing contexts), total heap overhead reaches:
    $$\text{Memory}_{\text{virtual}} = 100,000 \times 50\text{ KB} = \mathbf{5.0\text{ GB}}$$

This is an arithmetic projection under explicit assumptions, not a measured heap result.
    This projection identifies potential heap pressure; an `OutOfMemoryError` outcome was not measured ([`CLM-RQ2-07`](../docs/evidence-freeze/claim-evidence-ledger.md#L239-L250)).

While `OrderService` implements defensive cleanup via `REQUEST_CONTEXT.remove()`, the code artifact establishes the theoretical foundation for Chapter 7's migration guidelines regarding JEP 446 / JEP 481 Scoped Values (`ScopedValue`).

---

## 4.6 Benchmarking and Automation Infrastructure

All experimental trials were orchestrated via an automated bash pipeline encapsulated in [`run-benchmark.sh`](../run-benchmark.sh), ensuring identical execution environments, reproducible parameters, and cryptographic provenance.

```
+-----------------------------------------------------------------------------------+
|                        run-benchmark.sh ORCHESTRATION PIPELINE                    |
+-----------------------------------------------------------------------------------+
  │
  ├─► 1. Pre-flight Setup: Initializes results/ and results/jfr/
  │
  ├─► 2. JVM Launch:
  │      java $JFR_OPTS $JAVA_EXTRA_OPTS -jar target/virtual-threads-demo-*.jar
  │      -Djdk.virtualThreadScheduler.parallelism=1
  │      -Djdk.virtualThreadScheduler.maxPoolSize=1
  │      -XX:StartFlightRecording=settings=profile,dumponexit=true
  │      -Djdk.tracePinnedThreads=full
  │
  ├─► 3. Health Probe: Polls http://localhost:8080/products until 200 OK
  │
  ├─► 4. Background Telemetry Daemon: Starts companion ps sampling loop (1s interval)
  │
  ├─► 5. Workload Execution:
  │      k6 run --out json=results/run-10vus-<timestamp>.json k6/isolated-load-test.js
  │
  ├─► 6. Teardown: Sends SIGTERM to JVM; waits for clean JFR dump on process exit
  │
  ├─► 7. SHA-256 checksums: Computes digests for k6 JSON, JFR binary, and telemetry CSV
  │
  └─► 8. Manifest Generation: Compiles metadata into results/run-manifest-<timestamp>.json
```

### 4.6.1 Master Orchestrator: `run-benchmark.sh`

The harness script [`run-benchmark.sh`](../run-benchmark.sh) accepts command-line arguments to parameterize trials:
*   `--vus <count>`: Overrides target virtual user concurrency (defaults to 50, 100, 200).
*   `--endpoint <name>`: Selects workload endpoint (`payments`, `orders`, `products`, `cpu`, `native`, `native-short`).
*   `--lock-mode <mode>`: Sets mutex implementation (`synchronized`, `reentrant-lock`, `fair-reentrant-lock`, `semaphore`, `fair-semaphore`, `none`).
*   `--platform`: Sets `spring.threads.virtual.enabled=false`, activating Tomcat's bounded platform thread pool.
*   `--no-jfr`: Omits Java Flight Recorder overhead for diagnostic speed runs.

### 4.6.2 Automated Matrix Runners

To execute repeated experimental matrices across varied JVM runtimes without manual intervention, dedicated matrix runner scripts were developed:
*   [`scripts/run-java21-synchronization-matrix.sh`](../scripts/run-java21-synchronization-matrix.sh): Executes 12 randomized trials across four conditions (`synchronized`, `reentrant-lock`, `no-lock-diagnostic`, `platform-synchronized`) under 10 VUs and single-carrier isolation.
*   [`scripts/run-native-boundary-matrix.sh`](../scripts/run-native-boundary-matrix.sh): Executes 27 repeated trials across three runtimes (Java 21 LTS, Java 24, and Java 25) across three conditions (`pure-java-sleep`, `blocking-jni`, `native-short`) under `SCHEDULER_OPTS="-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1"`.

### 4.6.3 Workload Generation via k6

Client-side HTTP traffic was generated via [k6](https://k6.io/) executing [`k6/isolated-load-test.js`](../k6/isolated-load-test.js). The load test executes three distinct stages:
*   `15s` ramp-up to target concurrency (10 VUs in primary matrix; 50 VUs in pool sensitivity).
*   `30s` steady-state hold stage at constant concurrency.
*   `10s` ramp-down to 0 VUs.

Every completed request emits a JSON line recording microsecond-level timing metrics (`http_req_duration`, `http_req_connecting`, `http_req_waiting`), HTTP response codes, and validation status. Virtual users incorporate a 100 ms think time (`sleep(0.1)` at line 47) between successive requests.

### 4.6.4 The Process Telemetry Daemon

Operating system resource consumption was recorded by a background bash sampling loop started immediately following application startup verification:

```bash
TELEMETRY_FILE="$RESULTS_DIR/telemetry-$TIMESTAMP.csv"
echo "timestamp,pid,threads,cpu_percent" > "$TELEMETRY_FILE"
capture_telemetry() {
  while kill -0 "$APP_PID" 2>/dev/null; do
    now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    threads=$(ps -M "$APP_PID" 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
    if [ "$threads" = "0" ] && [ -r "/proc/$APP_PID/status" ]; then
      threads=$(awk '/^Threads:/ {print $2}' "/proc/$APP_PID/status")
    fi
    cpu=$(ps -p "$APP_PID" -o %cpu= 2>/dev/null | tr -d ' ')
    printf '%s,%s,%s,%s\n' "$now" "$APP_PID" "${threads:-unknown}" "${cpu:-unknown}" >> "$TELEMETRY_FILE"
    sleep 1
  done
}
```

This telemetry stream provided the empirical evidence that disproved the 100% CPU utilization assertion during native JNI blocking ([`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L177), [`DISC-02`](../docs/evidence-freeze/discrepancy-register.md#L63-L80)).

### 4.6.5 Cryptographic Execution Manifest Structure

At the conclusion of each benchmark run, `run-benchmark.sh` generates a cryptographically sealed JSON manifest (`results/run-manifest-<timestamp>.json`):

```json
{
  "run_id": "20261015-142646",
  "trial_id": "1",
  "condition_id": "payments",
  "run_set": "java21-primary-20261015",
  "timestamp_utc": "2026-10-15T12:26:46Z",
  "git_commit": "1ccb617b6beecb250e534d758d4f0eb1ea67e2d2",
  "application_jar_sha256": "4b5c7e12...",
  "java_command": "java",
  "java_vendor_and_version": "OpenJDK 21.0.8",
  "spring_boot_version": "3.5.12",
  "k6_version": "k6 v1.7.1",
  "os": "Darwin 25.2.0 Darwin Kernel Version 25.2.0",
  "cpu": "Apple M1",
  "logical_processors": "8",
  "memory": "16 GB",
  "execution_mode": "virtual",
  "virtual_threads_enabled": true,
  "lock_variant": "synchronized",
  "endpoint_or_workload": "payments",
  "load_model": "closed",
  "target_vus": "10",
  "stage_definition": "15s ramp-up, 30s hold, 10s ramp-down",
  "measurement_interval": "30s hold stage",
  "jvm_flags": "-XX:StartFlightRecording=... -Djdk.tracePinnedThreads=full",
  "java_extra_options": "-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1",
  "native_library": "target/native/libnativeblocking.dylib",
  "native_library_sha256": "a3f89e21...",
  "telemetry_file": "results/telemetry-20261015-142646.csv",
  "telemetry_sha256": "038eb9f493540bf5ea828943714bfa1e6fbe5ffb52c0eb4cb4be5617aee2fc18",
  "result_files": [
    {
      "vus": 10,
      "path": "results/run-10vus-20261015-142646.json",
      "sha256": "81fcae13ef83bfa1398846c4f09d5c312fb27ba1ca1a43a0e9803875323ad8d7"
    }
  ],
  "jfr_file": "results/jfr/recording-20261015-142646.jfr",
  "jfr_sha256": "4c47864ff843a91a921d7b00366eb5da23fcb5be4900742f518e38d338a08272",
  "validity_status": "exploratory",
  "k6_exit_status": 0
}
```

---

## 4.7 Verification, Recalculation, and Provenance Tooling

To ensure that the experimental dataset is fully reproducible and traceable backwards from thesis claims to raw disk bytes, three standalone, zero-dependency Python tools were developed.

### 4.7.1 The Master Artifact Inventory Generator (`scripts/generate_artifact_inventory.py`)

This tool ([`scripts/generate_artifact_inventory.py`](../scripts/generate_artifact_inventory.py)) crawls the `results/` directory, computing SHA-256 digests, recording byte sizes, extracting run metadata, and mapping each file to its admission status. It generated the definitive master ledger [`docs/evidence-freeze/artifact-inventory.csv`](../docs/evidence-freeze/artifact-inventory.csv) (**504 physical disk files**) and resolved the historical glob double-counting defect ([`DISC-04`](../docs/evidence-freeze/discrepancy-register.md#L99-L115)).

### 4.7.2 The Configuration Matrix Auditor (`scripts/generate_run_family_matrix.py`)

This script ([`scripts/generate_run_family_matrix.py`](../scripts/generate_run_family_matrix.py)) parses all 113 execution manifests and unmanifested Docker runs, extracting scheduler flags, JVM versions, and database parameters into [`docs/evidence-freeze/run-family-matrix.csv`](../docs/evidence-freeze/run-family-matrix.csv) (**120 matrix rows** representing 119 physical executions and 1 template).

### 4.7.3 The Independent Metric Recalculator (`scripts/recalculate_metrics.py`)

This engine ([`scripts/recalculate_metrics.py`](../scripts/recalculate_metrics.py)) streams through raw k6 JSON lines (parsing over 150,000 JSON records), recalculating full-run ($t \in [0, 55\text{s}]$) versus steady-state ($t \in [15, 45\text{s}]$) throughput, failure rates, and exact percentile latencies ($p50, p95, p99$). It resolved the throughput normalization error ([`DISC-01`](../docs/evidence-freeze/discrepancy-register.md#L42-L61), [`CLM-METH-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L271-L284)), confirming the exact throughput delta of **0.765%** and $p50$ latency delta of **0.184%**, and produced [`docs/evidence-freeze/metric-recalculations.csv`](../docs/evidence-freeze/metric-recalculations.csv).

### 4.7.4 Evidence Normalization Pipeline

To provide a consolidated data source for visualization dashboards and automated audit reporting, [`scripts/normalize_evidence.py`](../scripts/normalize_evidence.py) aggregates parsed run manifests, recalculated metrics, and JFR event counts into a single JSON schema ([`normalized-evidence.json`](../src/main/resources/static/data/normalized-evidence.json)). The schema is verified for consistency by [`scripts/validate_normalized_evidence.py`](../scripts/validate_normalized_evidence.py).

---

## 4.8 Methodological Summary and Threats to Validity

To preserve publication-grade scientific integrity, all implementation components, experimental treatments, and known construct defects are summarized in Table 4.2 alongside their forensic mitigations.

### Table 4.2: Implementation Component Evaluation and Forensic Mitigations

| Architectural Component | Target Mechanism | RQ Addressed | Identified Defect / Threat | Applied Forensic Qualification | Primary Claim Reference |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **`PaymentService` (`synchronized`)** | HotSpot monitor pinning under single-carrier stress | **RQ1** | Misconception that HotSpot expands carrier pool to compensate for pinning | ForkJoinPool pinning compensation disproven via JEP 444 source audit; `parallelism=1` confirmed effective. | [`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L55)<br>[`CLM-RQ1-07`](../docs/evidence-freeze/claim-evidence-ledger.md#L129-L140) |
| **`PaymentService` (`reentrant-lock`)** | AQS continuation yielding & non-fair barging | **RQ1** | Latency standard deviation inflation ($23\times$) misattributed to lock overhead | Identified as AQS `NonfairSync` direct-CAS barging; verified via fair lock baseline. | [`CLM-RQ1-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L72-L84)<br>[`CLM-RQ1-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L101-L112) |
| **`NativeBlockingService` (`/native`)** | Foreign C POSIX `nanosleep()` syscall | **RQ2** | 0 JFR events interpreted as healthy execution; CPU assumed 100% | Proved JFR suppresses native events; process telemetry proved carrier is suspended in kernel at 1.0% CPU. | [`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L162)<br>[`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L177) |
| **`OrderService` (`/orders`)** | HikariCP pool exhaustion under concurrency | **RQ2** | Pre-acquisition sleep defect: `simulateSlowQuery()` executes *before* connection checkout | Little's Law proved pool was >98% idle ($L_{\text{pool}} \approx 0.0125$); qualified as construct defect. | [`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L193)<br>[`DISC-07`](../docs/evidence-freeze/discrepancy-register.md#L150-L166) |
| **`application.yml` (H2 Configuration)** | Local database connection pool sizing | **RQ2** | Indentation defect under `demo:` caused fallback to default pool size 10 | Static configuration audit confirmed fallback; qualified local pool variation as inert. | [`CLM-RQ2-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L195-L208)<br>[`DISC-06`](../docs/evidence-freeze/discrepancy-register.md#L133-L149) |
| **`docker-compose.yml` (PostgreSQL)** | Containerized database concurrency | **RQ2** | Docker runtime omitted JFR instrumentation (`-XX:StartFlightRecording`) | k6 latency admitted as exploratory; all JFR carrier unmounting claims declared Not Established. | [`CLM-RQ2-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L210-L224)<br>[`DISC-08`](../docs/evidence-freeze/discrepancy-register.md#L167-L182) |
| **`OrderService` (`ThreadLocal`)** | Request context propagation memory scaling | **RQ2** | Closed-loop 10/50 VUs insufficient to trigger heap `OutOfMemoryError` | Evaluated analytically ($O(N)$ heap scaling); foundational motivation for JEP 446 Scoped Values. | [`CLM-RQ2-07`](../docs/evidence-freeze/claim-evidence-ledger.md#L239-L250) |
| **`run-benchmark.sh` (Harness)** | Automated execution and telemetry | **Methodology** | Throughput calculation normalized against 55s rather than 30s steady window | Recalculated via `recalculate_metrics.py`; confirmed exact steady-state throughput delta of 0.765%. | [`CLM-METH-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L271-L284)<br>[`DISC-01`](../docs/evidence-freeze/discrepancy-register.md#L42-L61) |
