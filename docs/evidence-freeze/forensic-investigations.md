# Stage 1.2 Forensic Investigation Report: Physical Reality of Experimental Mechanisms

**Document Identity:** Forensic Engineering Audit of Experimental Mechanisms & Runtime Boundaries  
**Target Focus:** Prioritized Stage 1.2 Charter (Adjudication Section 8)  
**Author / Auditor:** Virtual Threads Research & Evidence Auditor  
**Date of Forensic Inspection:** 2 November 2026  
**Status:** Completed & Empirically Verified against Repository Code, Manifests, and Telemetry  

---

## 1. Executive Summary & Forensic Findings Matrix

Stage 1.2 was commissioned to establish the exact physical reality of what occurred during the October 2026 benchmarks. Every investigation was conducted by inspecting source code, compilation targets, shell orchestration scripts, telemetry CSV streams, and OpenJDK 21 HotSpot C++ architecture.

| Investigation | Priority | Target Subsystem | Root Cause / Physical Reality | Materiality to Thesis |
|---|:---:|---|---|---|
| **1. JNI Nanosleep, Carrier Occupation, Telemetry & JFR** | **P1** | `native_blocking.c`<br>`run-benchmark.sh`<br>`telemetry-*.csv`<br>HotSpot C++ | True `nanosleep()` syscall; steady-state CPU is **~1.0%**, NOT 100%. The claim of "100% CPU" was an author conflation of **carrier occupancy** with **active CPU utilization**. JFR reports 0 pinning events because `Continuation.yield()` is never called in native syscalls. | **CRITICAL (RQ1/RQ2):** Clarifies that native blocking silently starves carrier pools while appearing idle in both CPU telemetry and JFR pinning monitors. |
| **2. Spring Boot Datasource Configuration** | **P1** | `application.yml`<br>`docker-compose.yml` | In `application.yml`, lines 13–17, `datasource:` was indented under `demo:`. Spring Boot ignored it and fell back to default auto-configured in-memory H2 (`maxPoolSize=10`). `docker-compose.yml` correctly passed `SPRING_DATASOURCE_*`. | **HIGH (RQ2):** Local H2 runs used Spring Boot auto-configured defaults; custom pool properties under `demo:` were inert. |
| **3. OrderService Transaction & Checkout Boundaries** | **P1** | `OrderService.java`<br>`JdbcTemplate` | No `@Transactional` annotation. `simulateSlowQuery()` (`Thread.sleep(300)`) executed **before** `jdbcTemplate.queryForList(...)`. Connection was never checked out during sleep; actual query took $< 1\text{ ms}$. Pool was never saturated. | **CRITICAL (RQ2):** Explains why pool size 1 vs 10 showed identical latency. The experiment did not test database connection pool exhaustion during a slow query. |
| **4. Docker PostgreSQL Instrumentation & JFR Absence** | **P2** | `Dockerfile`<br>`docker-compose.yml` | `Dockerfile` entrypoint lacked JFR flags; `docker-compose.yml` lacked host volume mounts for JFR. Runs were executed outside `run-benchmark.sh` without manifests. Container `cpus: '0.5'` was declared but unverified by cgroup telemetry. | **MEDIUM (Methodology):** PostgreSQL runs lack JFR recordings; findings must remain strictly bounded to k6 throughput/latency. |

---

## 2. Investigation 1 (Priority P1) — JNI Nanosleep, Carrier Occupation, Telemetry, and JFR Omission

### 2.1 The Native C Implementation: True Kernel Sleep vs. Spin-Wait
Inspection of [`native/native_blocking.c#L1-L24`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/native/native_blocking.c#L1-L24) resolves any doubt regarding what the native code executed:

```c
JNIEXPORT void JNICALL
Java_com_thesis_virtualthreadsdemo_service_NativeBlockingService_nativeSleep(JNIEnv *env, jobject self, jlong sleep_millis) {
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
```

* **Observation:** The implementation invokes the POSIX `nanosleep()` system call. If interrupted by an OS signal (e.g., Darwin timer tick), it resumes sleeping for the remaining duration.
* **Conclusion:** It does **not** execute a CPU busy-wait loop. It does **not** perform arithmetic computation. It places the calling OS thread into the OS kernel's waiting/sleep state.

---

### 2.2 Telemetry Audit: Resolution of the "100% CPU" Discrepancy
In [`docs/experiment-audit-triage-reconciliation.md#L149`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/experiment-audit-triage-reconciliation.md#L149), the author stated:
> *"Process telemetry CSVs (`results/telemetry-*.csv`) recorded 100% CPU utilization on the carrier thread during `/native` execution."*

To determine the empirical truth, all companion telemetry CSV files for `/native` and `blocking-jni` executions were parsed.

#### How Telemetry Was Sampled:
In [`run-benchmark.sh#L145-L156`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/run-benchmark.sh#L145-L156):
```bash
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
* The metric `ps -p "$APP_PID" -o %cpu=` samples the **entire JVM process**, not an individual carrier thread or OS lightweight process (LWP).
* On Darwin / macOS (BSD), `%cpu` represents a decaying CPU utilization average over time.

#### Actual Telemetry Data Excerpt (`results/telemetry-20261008-143952.csv`):
```csv
timestamp,pid,threads,cpu_percent
2026-10-08T12:40:00Z,46195,39,89.7   <-- Startup / ramp-up burst
2026-10-08T12:40:01Z,46195,39,2.3    <-- Steady-state begins
2026-10-08T12:40:02Z,46195,39,0.9
2026-10-08T12:40:03Z,46195,39,1.4
2026-10-08T12:40:04Z,46195,39,2.1
...
2026-10-08T12:40:15Z,46195,39,0.4
2026-10-08T12:40:16Z,46195,39,0.4
...
2026-10-08T12:40:29Z,46195,39,0.3
```

#### Census Across All Repeated `blocking-jni` Executions:
| Run ID | Condition | Stage Samples | First Sample (Startup) | Steady-State Avg CPU (%) | Steady-State Max CPU (%) |
|---|---|:---:|:---:|:---:|:---:|
| `20261008-143952` | `blocking-jni` | 55 | 89.7% | **1.0%** | 5.1% |
| `20261008-144056` | `blocking-jni` | 55 | 59.4% | **1.0%** | 8.4% |
| `20261008-144201` | `blocking-jni` | 55 | 85.8% | **1.2%** | 6.1% |
| `20261008-144930` | `blocking-jni` | 56 | 56.4% | **0.9%** | 4.6% |
| `20261008-145035` | `blocking-jni` | 55 | 37.0% | **1.0%** | 4.2% |
| `20261008-145140` | `blocking-jni` | 55 | 32.8% | **1.0%** | 7.6% |
| `20261008-145909` | `blocking-jni` | 55 | 72.6% | **0.9%** | 4.1% |
| `20261008-150013` | `blocking-jni` | 54 | 37.9% | **1.2%** | 8.5% |
| `20261008-150118` | `blocking-jni` | 55 | 45.6% | **1.0%** | 5.5% |

#### Root Cause of the Contradiction:
1. **Physical Reality:** Steady-state CPU utilization during the 500 ms `nanosleep` benchmark is **~1.0%**. The host CPU was almost entirely idle.
2. **Origin of Error in Previous Report:** The previous author conflated **carrier thread occupancy** (the carrier thread was 100% occupied/blocked, unable to run other virtual threads) with **carrier CPU utilization** (active processor cycles). The author may also have imported text from the scout report's discussion of SQLite JDBC spin-loops (`NativeDB.c`, where `sqlite3_busy_timeout` does burn 100% CPU).

---

### 2.3 HotSpot Architectural Analysis: Why JNI Blocking Produces Zero `jdk.VirtualThreadPinned` Events

Across all 27 executions in `native-boundary-20261008-repeated`, JFR recorded exactly **0** `jdk.VirtualThreadPinned` events.

#### Mechanism in OpenJDK 21 HotSpot:
1. **The Role of `jdk.VirtualThreadPinned`:**
   In OpenJDK HotSpot (`src/hotspot/share/runtime/continuation.cpp` and `continuationFreeze.cpp`), the `jdk.VirtualThreadPinned` JFR event is emitted **exclusively when a virtual thread attempts to unmount/yield and the unmount operation fails**:
   ```cpp
   // Conceptual flow in HotSpot continuation freeze:
   if (!can_freeze(continuation)) {
       post_pinned_event(thread, reason); // reason: MONITOR or NATIVE
       return freeze_failed;
   }
   ```
2. **What Happens During a JNI Syscall:**
   - The Java thread executes the JNI native method transition via the generated JNI stub.
   - The OS carrier thread transitions from `_thread_in_Java` to `_thread_in_native`.
   - The C function `nativeSleep()` invokes `nanosleep(&remaining, &remaining)`.
   - The Darwin XNU kernel puts the OS carrier thread into an interruptible sleep wait-queue.
   - **Crucial Point:** At no point during `nanosleep()` does the code execute Java bytecode or invoke `VirtualThread.park()` / `Continuation.yield()`.
3. **The Architectural Blind Spot:**
   Because `Continuation.yield()` is **never invoked**, HotSpot's continuation freeze subsystem is never entered. Because it is never entered, `post_pinned_event` is never called.
   `jdk.VirtualThreadPinned` is an **unmount-failure event**, NOT an **OS carrier thread block or stall detector**.

#### Architectural Finding for Thesis (RQ1 & RQ2):
> **Finding 1.2-A:** Blocking inside JNI native methods (e.g., via blocking POSIX system calls, legacy C database drivers, or cryptographic libraries) causes complete carrier thread starvation under single-carrier configurations, yet is **completely invisible to standard JFR pinning observability**. CPU telemetry appears idle (~1%), and JFR reports 0 pinning events. This constitutes a severe silent failure mode for virtual thread adopters.

---

## 3. Investigation 2 (Priority P1) — Effective Spring Boot Datasource Configuration

### 3.1 Code Inspection of `src/main/resources/application.yml`
Inspection of lines 1–31 of `application.yml` reveals an indentation defect:

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

### 3.2 Spring Boot Configuration Binding Analysis
* In Spring Boot 3.x, `DataSourceAutoConfiguration` binds properties with the prefix `spring.datasource` (mapped to `org.springframework.boot.autoconfigure.jdbc.DataSourceProperties`).
* `SqlInitializationAutoConfiguration` binds `spring.sql.init.*`.
* `JpaBaseConfiguration` binds `spring.jpa.*`.
* Because lines 13–31 are indented under `demo:`, Spring Boot registered these properties as:
  - `demo.datasource.url`
  - `demo.datasource.driver-class-name`
  - `demo.h2.console.enabled`
  - `demo.jpa.hibernate.ddl-auto`
  - `demo.sql.init.mode`
* Grep across `src/` confirms that no `@ConfigurationProperties(prefix = "demo")` bean exists to capture `demo.datasource.*`.

### 3.3 What Actually Happened at Runtime?
1. Spring Boot detected `com.h2database:h2` on the classpath (`pom.xml#L44-L47`).
2. Finding no `spring.datasource.url` configured, Spring Boot's `EmbeddedDatabaseConnection` automatically initiated an auto-configured in-memory H2 database.
3. HikariCP was auto-configured with its built-in defaults:
   - `maximumPoolSize = 10`
   - `minimumIdle = 10`
   - `connectionTimeout = 30000 ms`
4. In `docker-compose.yml`, environment variables were correctly defined under the standard Spring Boot naming convention (`SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE`). Therefore, the PostgreSQL container runs correctly received the custom pool configurations.

#### Architectural Finding for Thesis (Chapter 4 & RQ2):
> **Finding 1.2-B:** In all local H2 benchmarks, Spring Boot operated on default auto-configured in-memory H2 settings with a default pool size of 10. Any attempt in local H2 benchmarks to modify pool sizes via `application.yml` under `demo:` was silently ignored. The thesis must document this autoconfiguration fallback.

---

## 4. Investigation 3 (Priority P1) — OrderService Transaction Boundaries & Connection Acquisition

### 4.1 Code Inspection of `OrderService.java`
Inspection of [`src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L36-L49`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L36-L49):

```java
    public List<Map<String, Object>> getOrders() {
        REQUEST_CONTEXT.set("user-request-" + Thread.currentThread().getName());

        try {
            // Simulate a slow database query (e.g. unindexed table scan)
            simulateSlowQuery();
            return jdbcTemplate.queryForList("SELECT * FROM orders");
        } finally {
            REQUEST_CONTEXT.remove();
        }
    }

    private void simulateSlowQuery() {
        try {
            Thread.sleep(300);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
```

### 4.2 Architectural Analysis of Connection Acquisition
1. **Absence of `@Transactional`:**
   Neither the class `OrderService` nor the method `getOrders()` is annotated with `@Transactional`.
2. **Spring `JdbcTemplate` Execution Lifecycle:**
   - In non-transactional execution, `JdbcTemplate.queryForList()` calls `execute(StatementCallback action)`.
   - `DataSourceUtils.getConnection(getDataSource())` checks out a connection from HikariCP **only when `queryForList()` is entered at line 43**.
   - The SQL statement (`SELECT * FROM orders`) executes against the 10-row seeded table (`schema.sql` / `data.sql`), completing in **$< 0.1\text{ ms}$**.
   - `DataSourceUtils.releaseConnection(con, getDataSource())` returns the connection to HikariCP in the `finally` block before `queryForList()` returns.
3. **The Timing Flaw:**
   - `simulateSlowQuery()` (`Thread.sleep(300)`) executed at **line 42**, *before* connection checkout.
   - During the 300 ms sleep, the virtual thread held **no database connection**. It simply parked its continuation.
   - The connection was held only for the fraction of a millisecond required to execute the in-memory `SELECT *`.

### 4.3 Mathematical Explanation of Why Pool 1 vs. Pool 10 Were Indistinguishable
* Under 50 closed-loop VUs, each request takes $\sim 300.5\text{ ms}$ (300 ms sleep + 0.5 ms network/app overhead).
* Total aggregate system throughput:
  $$X = \frac{50\text{ VUs}}{0.3005\text{ s}} \approx 166.4\text{ req/s}$$
* Since each request holds a connection for $T_{\text{hold}} \approx 0.0001\text{ s}$ (0.1 ms), the average number of busy connections in the pool is given by Little's Law:
  $$L_{\text{pool}} = X \times T_{\text{hold}} = 166.4 \times 0.0001 \approx \mathbf{0.0166\text{ connections}}$$
* **Conclusion:** The average demand on the connection pool was **less than 2% of a single connection**. Even with `maximumPoolSize = 1`, connection queueing never exceeded 0, and HikariCP never threw `SQLTransientConnectionException`.

#### Architectural Finding for Thesis (RQ2 & Chapter 6):
> **Finding 1.2-C:** The `/orders` benchmark did **not** evaluate database connection pool contention or exhaustion under virtual threads. Because the simulated 300 ms latency occurred prior to connection acquisition, connection checkout duration was sub-millisecond, leaving the pool over 98% idle even at pool size 1. Claims regarding virtual thread database resilience must be explicitly qualified: the experiment demonstrates virtual thread sleep unmounting, not connection pool saturation.

---

## 5. Investigation 4 (Priority P2) — Container PostgreSQL Trial Instrumentation & JFR Absence

### 5.1 Dockerfile and Compose Configuration
Inspection of [`Dockerfile#L14-L18`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/Dockerfile#L14-L18):
```dockerfile
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/virtual-threads-demo-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```
Inspection of [`docker-compose.yml#L1-L30`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docker-compose.yml#L1-L30):
* No JVM flight recorder arguments were supplied to the container entrypoint (e.g. no `-XX:StartFlightRecording=...` in `ENTRYPOINT` or `JAVA_TOOL_OPTIONS`).
* No volume mount existed to extract `.jfr` recordings from the container filesystem back to the host `results/jfr/` directory.
* The 6 Docker PostgreSQL benchmark runs (`docker-pg-orders-pool{1,10}-trial{1,2,3}.json`) were triggered via external k6 invocations directly against `localhost:8080`, bypassing `run-benchmark.sh`.

### 5.2 Container Resource Throttling Status
* `docker-compose.yml` specifies:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 1G
  ```
* However, no cgroup utilization files (`/sys/fs/cgroup/cpu.stat` or Docker stats CSVs) were collected during the executions.
* While the container limits were statically defined in Compose, CPU throttling cannot be empirically verified through runtime telemetry.

#### Architectural Finding for Thesis (Methodology & Chapter 5):
> **Finding 1.2-D:** The 6 Docker PostgreSQL trials (`Stratum 7`) lack companion JFR recordings and runtime container cgroup telemetry. While their k6 load-test outputs (`docker-pg-orders-pool*.json`) are cryptographically preserved, they cannot be used to substantiate claims regarding carrier unmounting or carrier starvation during database I/O.

---

## 6. Synthesis & Impact on Thesis Chapters

| Thesis Chapter | Specific Revision Mandated by Stage 1.2 Forensic Audit |
|---|---|
| **Chapter 3 (Methodology)** | Explicitly define the unmount-failure semantic of `jdk.VirtualThreadPinned`. State that JFR does not monitor OS thread blocking during JNI system calls. Detail the whole-run vs. hold-window metric reporting policy. |
| **Chapter 4 (Implementation)** | Disclose the `application.yml` indentation defect and explain Spring Boot's default autoconfiguration fallback for local H2. Acknowledge that Docker PostgreSQL runs were containerized without JFR hooks. |
| **Chapter 5 (Results)** | Present JNI throughput ($1.97\text{ req/s}$) alongside steady-state CPU telemetry (**~1.0%**), disproving the 100% CPU utilization assertion. Disclose that `/orders` pool 1 vs. 10 showed identical metrics due to pre-checkout sleep timing. |
| **Chapter 6 (RQ1 & RQ2 Analysis)** | **RQ1:** Unpinning via `ReentrantLock` solves monitor pinning, but does not solve lock serialization. JNI native blocking stalls carrier threads silently without emitting pinning events.<br>**RQ2:** Database pool sizing cannot be evaluated from `/orders` data due to the pre-checkout sleep; connection pool exhaustion risks must be supported by external literature and theoretical analysis rather than the `/orders` empirical dataset. |

---

*(End of Stage 1.2 Forensic Investigation Report)*
