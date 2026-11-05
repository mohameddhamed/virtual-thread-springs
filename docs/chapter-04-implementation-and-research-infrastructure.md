# Chapter 4: Implementation and Research Infrastructure

## 4.1 Application Architecture and Core Endpoints

To investigate the runtime interactions between Java 21 Virtual Threads, monitor pinning, mutual exclusion serialization, and database persistence, a custom enterprise-grade Model-View-Controller (MVC) benchmark application was constructed. The application is implemented in Java 21 utilizing the Spring Boot 3.5.12 framework, running on top of an embedded Apache Tomcat 10.1.52 servlet container, and built via Apache Maven 3.9.

### 4.1.1 Package Structure and Architectural Decomposition

The application source tree is organized under the root package `com.thesis.virtualthreadsdemo`, following a clean separation of concerns across four primary architectural layers:

```
src/main/java/com/thesis/virtualthreadsdemo/
├── VirtualThreadsDemoApplication.java        // Application entrypoint & Spring Boot bootstrap
├── controller/                               // REST API routing and HTTP request mapping
│   ├── PaymentController.java                // /payments endpoint (synchronization treatments)
│   ├── OrderController.java                  // /orders endpoint (JDBC persistence & ThreadLocal)
│   ├── ProductController.java                // /products endpoint (in-memory fast-path baseline)
│   ├── NativeController.java                 // /native endpoint (JNI blocking POSIX nanosleep)
│   ├── NativeShortController.java            // /native-short endpoint (JNI no-op transition control)
│   ├── CpuController.java                    // /cpu endpoint (cryptographic compute benchmark)
│   └── HelloController.java                  // Diagnostic sanity check endpoint
├── service/                                  // Business logic, concurrency control, and native bridging
│   ├── PaymentService.java                   // Mutex implementations (synchronized vs ReentrantLock)
│   ├── OrderService.java                     // Transactional logic, slow query simulation, ThreadLocal
│   ├── ProductService.java                   // In-memory catalog lookup
│   ├── NativeBlockingService.java            // JNI wrapper and libnativeblocking binding
│   └── CpuService.java                       // Cryptographic SHA-256 compute payload
└── repository/                               // Spring JDBC persistence abstraction
    ├── OrderRepository.java                  // Relational order querying
    └── ProductRepository.java                // Relational product catalog querying
```

### 4.1.2 Spring Boot 3 Virtual Thread Wiring and Tomcat Configuration

The integration of Virtual Threads within Spring Boot 3 relies on Spring Framework 6's native support for JEP 444. When the configuration flag:

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

is evaluated during the auto-configuration phase of `ServletWebServerFactoryConfiguration`, Spring Boot registers a `TomcatProtocolHandlerCustomizer` bean that modifies Apache Tomcat's underlying `StandardThreadExecutor`. Instead of allocating requests to a fixed-size platform thread pool (Tomcat's traditional default of 200 OS threads bounded by an internal queue), Tomcat instantiates an unbounded virtual thread-per-task executor:

```java
// Conceptual wiring executed inside Spring Boot 3 autoconfiguration
@Bean
public TomcatProtocolHandlerCustomizer<?> protocolHandlerVirtualThreadCustomizer() {
    return protocolHandler -> {
        protocolHandler.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
    };
}
```

Under this configuration, every accepted TCP connection and incoming HTTP request is immediately dispatched to an ephemeral virtual thread. When an application thread performs blocking operations (such as socket I/O, `Thread.sleep()`, or lock acquisition via `java.util.concurrent`), the virtual thread yields its underlying carrier thread back to the JVM's ForkJoinPool scheduler. When platform thread mode is selected (`spring.threads.virtual.enabled: false`), Tomcat falls back to its default bounded OS thread pool.

---

## 4.2 Payment Synchronization Implementations

The primary synchronization treatments evaluated in Research Question 1 are implemented within [`PaymentService.java`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java). The service models an atomic transactional payment operation where requests must be strictly serialized through mutual exclusion to prevent double-spending or ledger inconsistencies.

```java
@Service
public class PaymentService {

    private final String lockMode;
    private final ReentrantLock lock = new ReentrantLock();
    private final ReentrantLock fairLock = new ReentrantLock(true);
    private final Semaphore semaphore = new Semaphore(1);
    private final Semaphore fairSemaphore = new Semaphore(1, true);
    private final Object monitor = new Object();

    public PaymentService(@Value("${demo.payment.lock-mode:reentrant-lock}") String lockMode) {
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

### 4.2.1 The Synchronized Treatment (`synchronized`)
When `demo.payment.lock-mode` is configured to `synchronized`, mutual exclusion is enforced by entering a Java monitor synchronized on an internal heap object (`private final Object monitor = new Object()`).
*   **HotSpot Pinning Mechanism:** In Java 21, the HotSpot execution engine couples object monitors to the executing physical OS thread. When the virtual thread executes `simulatePaymentCall()` and calls `Thread.sleep(500)`, the virtual thread attempts to unmount by calling `Continuation.yield()`. HotSpot's continuation freeze subsystem (`continuationFreeze.cpp`) checks whether the thread holds any active monitor frames on its stack. Because the monitor frame is present, the freeze operation fails (`can_freeze() == false`).
*   **Resulting Runtime State:** The virtual thread remains pinned to its underlying carrier thread for the entire 500 ms sleep duration. Under the single-carrier mechanism isolation constraint (`parallelism=1`), the single carrier thread is completely blocked, preventing any other virtual thread in the JVM from being scheduled.

### 4.2.2 The ReentrantLock Treatment (`reentrant-lock`)
When configured to `reentrant-lock`, mutual exclusion is governed by an explicit `java.util.concurrent.locks.ReentrantLock`.
*   **Unpinning Mechanism:** `ReentrantLock` is implemented in pure Java via `AbstractQueuedSynchronizer` (AQS). Waiting threads are queued within an in-memory linked node structure and parked via `LockSupport.park()`.
*   **Continuation Yielding:** `LockSupport.park()` delegates directly to `VirtualThread.park()`, which invokes `Continuation.yield()`. Because no Java monitor frame exists on the stack, HotSpot successfully freezes the virtual thread's stack frames to the Java heap and unmounts the virtual thread, returning the carrier thread to the ForkJoinPool scheduler.
*   **Non-Fair Barging:** By default, `ReentrantLock` instantiates a `NonfairSync`. Newly arriving virtual threads can barge ahead of queued threads if the lock happens to become available at the instant of acquisition. This non-fair acquisition path produces greater latency variance under contention than intrinsic monitors, explaining the wider latency dispersion documented in `CLM-RQ1-05`.

### 4.2.3 Diagnostic Control: The No-Lock Branch (`none`)
The `none` branch invokes `simulatePaymentCall()` without acquiring any lock. This condition intentionally violates mutual exclusion invariants, simulating an architectural scenario where concurrent payment transactions execute without synchronization. It serves solely as an empirical baseline to quantify the performance ceiling of unconstrained concurrent thread scheduling under identical synthetic delays.

---

## 4.3 Native Interface (JNI) and Foreign Function Implementation

To evaluate the impact of foreign library execution and non-yielding operating system calls on virtual thread schedulers (RQ2), a custom native shared library was developed in C and bound via the Java Native Interface (JNI).

### 4.3.1 C Implementation: `libnativeblocking.dylib`

The native source file [`native/native_blocking.c`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/native/native_blocking.c) defines two exported entry points:

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
        /* Resume the bounded sleep if a signal interrupts it. */
    }
}

JNIEXPORT void JNICALL
Java_com_thesis_virtualthreadsdemo_service_NativeBlockingService_nativeNoop(
        JNIEnv *env, jobject self) {
    (void) env;
    (void) self;
}
```

The C library is compiled during the Maven build lifecycle via a custom shell step generating the native binary (`target/native/libnativeblocking.dylib` on macOS / arm64).

### 4.3.2 The Service Binding: `NativeBlockingService.java`

The Java service encapsulates library loading and native method declaration:

```java
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
}
```

### 4.3.3 JNI Transition Mechanics and HotSpot Carrier Captivity

The invocation of `nativeSleep(500)` triggers an important low-level transition within the HotSpot runtime:

```
[Virtual Thread (Java)]
         │
         │ Executes nativeSleep(500)
         ▼
[HotSpot JNI Stub] ──> Transitions thread state: _thread_in_Java ──> _thread_in_native
         │
         │ Direct C call (Foreign Machine Code)
         ▼
[POSIX nanosleep()] ──> Kernel Traversal: sys_nanosleep()
         │
         │ Darwin XNU kernel suspends OS carrier thread (wait queue)
         │ * Carrier thread is completely idle in kernel *
         │ * VirtualThread continuation is NEVER unmounted *
         ▼
[HotSpot Scheduler (ForkJoinPool)]
         │
         └─► Scheduler is completely blind to carrier sleep state!
             No Continuation.yield() invoked; zero JFR pinning events emitted.
```

1.  **Thread State Transition:** The generated JNI transition stub switches the carrier thread's internal state from `_thread_in_Java` to `_thread_in_native`.
2.  **Kernel Wait-Queue Suspension:** The C function executes the POSIX `nanosleep()` system call. The Darwin XNU kernel places the physical OS carrier thread into an interruptible sleep wait-queue. The thread yields its CPU core to the operating system scheduler and consumes virtually zero CPU cycles (measured at $\approx 1.0\%$, resolving `DISC-02` / `CLM-RQ2-02`).
3.  **Suppression of Continuation Unmounting:** Because the carrier thread is executing machine code outside the JVM's bytecode interpreter loop, it never encounters a bytecode safe-point and never executes `Continuation.yield()`. The virtual thread continuation is never detached from the carrier.
4.  **JFR Observability Omission:** JFR's `jdk.VirtualThreadPinned` event is designed exclusively as an **unmount-failure event**; it is posted only when `Continuation.yield()` fails. Because `Continuation.yield()` is never called during foreign function execution, JFR records exactly **0** pinning events across all 27 native trials (`CLM-RQ2-01`, `DISC-03`). Under `parallelism=1`, this produces complete carrier starvation that is completely invisible to standard JFR pinning monitoring.

---

## 4.4 Database and Persistence Layer

Relational persistence is implemented using Spring's `JdbcTemplate` backed by a HikariCP connection pool. The application was designed to support dual database backends: an embedded in-memory H2 database for local isolated testing, and a containerized PostgreSQL 15 database orchestrated via Docker Compose.

### 4.4.1 Relational Schema and In-Memory Data

The database schema (`src/main/resources/schema.sql`) defines two tables:

```sql
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

The database is populated at startup via `data.sql` with 10 seed rows per table.

### 4.4.2 The Physical Anatomy of the `/orders` Pre-Acquisition Delay Flaw (`CLM-RQ2-03`)

The `/orders` endpoint was intended to assess HikariCP connection pool saturation and virtual thread unmounting under constrained pool sizing (pool size 1 vs. 10). Inspection of [`OrderService.java#L36-L59`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L36-L59) revealed a critical construct flaw in the execution lifecycle:

```java
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
            // CONSTRUCT FLAW: Sleep executes BEFORE connection checkout!
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

#### Lifecycle and Timing Analysis:
1.  **Absence of `@Transactional`:** Neither `OrderService` nor `getOrders()` is annotated with Spring's `@Transactional`.
2.  **Deferred Connection Acquisition:** In standard non-transactional Spring JDBC, `JdbcTemplate.queryForList()` obtains a database connection lazily via `DataSourceUtils.getConnection(getDataSource())` when the query is executed at line 43.
3.  **Uncoupled Delay:** `simulateSlowQuery()` (`Thread.sleep(300)`) executes at line 42, **prior to connection acquisition**. During this 300 ms delay, the virtual thread holds zero database connections; it simply unmounts from its carrier thread.
4.  **Sub-Millisecond Query Hold Time:** When `queryForList("SELECT * FROM orders")` finally executes at line 43, it checks out a connection, executes a fast query over the 10-row in-memory table ($< 0.1\text{ ms}$), and immediately releases the connection back to HikariCP in the `finally` block of `JdbcTemplate.execute()`.
5.  **Pool Utilization Consequence:** As derived via Little's Law in Chapter 3 (`CLM-RQ2-03`), 50 concurrent VUs sleeping for 300 ms generate $\approx 166.4\text{ req/s}$. With a connection hold time of $T_{\text{hold}} \approx 0.0001\text{ s}$, average pool occupancy is:
    $$L_{\text{pool}} = 166.4 \times 0.0001 \approx \mathbf{0.0166\text{ connections}}$$
    The HikariCP pool was over 98% idle throughout the test. Even under `maximumPoolSize = 1`, no queue formed, explaining why pool size 1 and pool size 10 produced identical latency profiles.

### 4.4.3 The YAML Indentation Defect and Autoconfiguration Fallback (`CLM-RQ2-04`)

A secondary configuration defect was identified in [`src/main/resources/application.yml`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/resources/application.yml):

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

  # CONFIGURATION DEFECT: Indented under demo: instead of spring:
  datasource:
    url: jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1
    driver-class-name: org.h2.Driver
    username: sa
    password:

  h2:
    console:
      enabled: true
```

*   **Property Binding Evaluation:** Spring Boot's `DataSourceAutoConfiguration` binds properties matching the prefix `spring.datasource.*`. Because lines 13–22 were indented two spaces under `demo:`, Spring Boot registered them as `demo.datasource.*`.
*   **Classpath Fallback:** Finding no `spring.datasource.url` defined, Spring Boot's `EmbeddedDatabaseConnection` automatically initiated an auto-configured in-memory H2 database.
*   **Effective Pool Parameters:** The embedded database was instantiated with HikariCP's default properties: **`maximumPoolSize = 10`**, `minimumIdle = 10`, and `connectionTimeout = 30000 ms`. Custom pool adjustments attempted in local H2 runs via `application.yml` were completely inert.

### 4.4.4 Docker Compose PostgreSQL 15 Deployment

In contrast to the local H2 setup, the containerized PostgreSQL environment was orchestrated via [`docker-compose.yml`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docker-compose.yml):

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
```

In this environment, environment variables used the standard `SPRING_DATASOURCE_*` naming scheme, successfully binding to Spring Boot's datasource properties and allowing parameterization of `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE` (tested at pool sizes 1 and 10).

---

## 4.5 Request Context and ThreadLocal Lifecycle

The application explicitly models request-scoped context propagation in [`OrderService.java`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java) to evaluate the memory and hygiene implications of ThreadLocal storage under virtualized concurrency (RQ2):

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

In traditional Spring MVC deployments, a bounded thread pool (e.g., Tomcat's 200 OS threads) serves requests. Each thread retains a `ThreadLocalMap`. Even if an application fails to invoke `ThreadLocal.remove()`, the maximum number of thread-local map instances is strictly bounded by the maximum pool size:

$$\text{Max Memory}_{\text{platform}} = 200 \times M_{\text{context}}$$

Where $M_{\text{context}}$ is the byte size of the context payload.

Under Virtual Threads, thread creation is unbounded ($10^4$ to $10^6$ concurrent threads). When a virtual thread allocates a ThreadLocal variable:
1.  A dedicated `ThreadLocalMap` is allocated on the Java heap for that specific virtual thread continuation.
2.  If the virtual thread is long-lived or blocked in a queue, its ThreadLocal map cannot be garbage collected.
3.  Under $N = 100,000$ concurrent requests, heap memory consumption scales to:
    $$\text{Memory}_{\text{virtual}} = 100,000 \times M_{\text{context}}$$
4.  If $M_{\text{context}} = 50\text{ KB}$ (typical of enterprise security tokens and tenant attributes), total heap overhead reaches **$5.0\text{ GB}$**, precipitating `OutOfMemoryError: Java heap space`.

While `OrderService` implements defensive cleanup via `REQUEST_CONTEXT.remove()`, the code artifact establishes the theoretical foundation for Chapter 7's migration guidelines regarding JEP 446 Scoped Values.

---

## 4.6 Benchmarking and Automation Infrastructure

All experimental trials were orchestrated via an automated bash pipeline encapsulated in [`run-benchmark.sh`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/run-benchmark.sh), ensuring identical execution environments and strict lifecycle control.

```
+-----------------------------------------------------------------------------------+
|                           run-benchmark.sh Orchestration                          |
+-----------------------------------------------------------------------------------+
  │
  ├─► 1. Pre-flight initialization: creates results/ and results/jfr/
  │
  ├─► 2. JVM Launch:
  │      java $JFR_OPTS $JAVA_EXTRA_OPTS -jar target/app.jar
  │      -Djdk.virtualThreadScheduler.parallelism=1
  │      -Djdk.virtualThreadScheduler.maxPoolSize=1
  │      -XX:StartFlightRecording=settings=profile,dumponexit=true
  │
  ├─► 3. Health Probe: polls http://localhost:8080/products until 200 OK
  │
  ├─► 4. Background Telemetry Daemon: starts ps -p $APP_PID sampling loop (1s interval)
  │
  ├─► 5. Workload Execution:
  │      k6 run --out json=results/run-10vus-<timestamp>.json k6/isolated-load-test.js
  │
  ├─► 6. Teardown: sends SIGINT/SIGTERM to JVM; waits for JFR dump on exit
  │
  ├─► 7. Cryptographic Hashing: computes SHA-256 for k6 JSON, JFR binary, telemetry
  │
  └─► 8. Manifest Generation: compiles metadata into run-manifest-<timestamp>.json
```

### 4.6.1 Workload Generation via k6

Client-side HTTP traffic was generated via [k6](https://k6.io/) executing [`k6/isolated-load-test.js`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/k6/isolated-load-test.js). The harness executes three distinct stages:
*   `15s` ramp-up to target concurrency (10 VUs in primary matrix; 50 VUs in pool sensitivity).
*   `30s` hold stage at constant concurrency.
*   `10s` ramp-down to 0 VUs.

Every completed request emits a JSON line recording microsecond-level timing metrics (`http_req_duration`, `http_req_connecting`, `http_req_tls_handshaking`), HTTP response codes, and expected response validations.

### 4.6.2 The Process Telemetry Daemon

Resource consumption was recorded by a background bash loop started immediately following the application health check:

```bash
TELEMETRY_FILE="$RESULTS_DIR/telemetry-$TIMESTAMP.csv"
echo "timestamp,pid,threads,cpu_percent" > "$TELEMETRY_FILE"
capture_telemetry() {
  while kill -0 "$APP_PID" 2>/dev/null; do
    now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    threads=$(ps -M "$APP_PID" 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
    cpu=$(ps -p "$APP_PID" -o %cpu= 2>/dev/null | tr -d ' ')
    printf '%s,%s,%s,%s\n' "$now" "$APP_PID" "${threads:-unknown}" "${cpu:-unknown}" >> "$TELEMETRY_FILE"
    sleep 1
  done
}
```

This telemetry stream provided the empirical evidence that disproved the 100% CPU utilization assertion during native JNI blocking (`DISC-02` / `CLM-RQ2-02`).

### 4.6.3 Execution Manifest Structure

At the conclusion of each benchmark run, `run-benchmark.sh` generates a cryptographically sealed JSON manifest (`results/run-manifest-<timestamp>.json`):

```json
{
  "run_id": "20261015-142646",
  "timestamp_utc": "2026-10-15T12:26:46Z",
  "git_commit": "1ccb617b6beecb250e534d758d4f0eb1ea67e2d2",
  "java_vendor_and_version": "OpenJDK 21.0.8",
  "execution_mode": "virtual",
  "lock_variant": "synchronized",
  "endpoint_or_workload": "payments",
  "scheduler_parallelism": 1,
  "scheduler_max_pool_size": 1,
  "result_files": [
    {
      "vus": 10,
      "path": "results/run-10vus-20261015-142646.json",
      "sha256": "81fcae13ef83bfa1398846c4f09d5c312fb27ba1ca1a43a0e9803875323ad8d7"
    }
  ],
  "jfr_file": "results/jfr/recording-20261015-142646.jfr",
  "jfr_sha256": "4c47864ff843a91a921d7b00366eb5da23fcb5be4900742f518e38d338a08272",
  "telemetry_file": "results/telemetry-20261015-142646.csv",
  "telemetry_sha256": "038eb9f493540bf5ea828943714bfa1e6fbe5ffb52c0eb4cb4be5617aee2fc18"
}
```

---

## 4.7 Verification, Recalculation, and Provenance Tooling

To ensure that the experimental dataset is fully reproducible and traceable backwards from thesis claims to raw bytes, three standalone, zero-dependency Python tools were developed.

### 4.7.1 The Master Artifact Inventory Generator (`scripts/generate_artifact_inventory.py`)
This script crawls the `results/` directory, computing SHA-256 digests, recording byte sizes, extracting run metadata, and mapping each file to its admission status. It generated the definitive master ledger [`docs/evidence-freeze/artifact-inventory.csv`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/artifact-inventory.csv) (504 physical disk files) and resolved the historical glob double-counting defect (`DISC-04`).

### 4.7.2 The Configuration Matrix Auditor (`scripts/generate_run_family_matrix.py`)
This script parses all 113 execution manifests and unmanifested Docker runs, extracting scheduler flags, JVM versions, and database parameters into [`docs/evidence-freeze/run-family-matrix.csv`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-matrix.csv) (120 matrix rows representing 119 actual executions and 1 template).

### 4.7.3 The Independent Metric Recalculator (`scripts/recalculate_metrics.py`)
This tool streams through the raw k6 JSON lines (parsing over 150,000 JSON records), recalculating full-run ($t \in [0, 55\text{s}]$) versus steady-state ($t \in [15, 45\text{s}]$) throughput, failure rates, and exact percentile latencies ($p50, p95, p99$). It resolved the throughput normalization error (`DISC-01` / `CLM-METH-02`), confirming the exact throughput delta of **0.765%** and $p50$ latency delta of **0.184%**, and produced [`docs/evidence-freeze/metric-recalculations.csv`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/metric-recalculations.csv).

---

*(End of Chapter 4 Draft Text)*
