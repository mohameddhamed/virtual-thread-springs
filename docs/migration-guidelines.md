# Virtual Threads Migration Guidelines

A practical, step-by-step checklist for safely enabling Java 21 Virtual Threads in Spring Boot applications.

---

## Pre-Migration Checklist

Before flipping the `spring.threads.virtual.enabled` flag, complete all items below:

### 1. **Audit All Synchronized Blocks**

**Objective:** Replace intrinsic locks (OS monitor locks) with Virtual Thread-aware locks.

**Steps:**
1. Search your codebase for `synchronized` keyword:
   ```bash
   grep -r "synchronized" src/ --include="*.java"
   ```

2. For each match, determine if it protects a critical section:
   - **State mutation** (shared mutable fields): MUST replace with `ReentrantLock`
   - **Blocking calls** inside synchronized: MUST replace (this is a pinning culprit)
   - **Simple getter/setter**: Consider if the lock is even necessary

3. Replace with `java.util.concurrent.locks.ReentrantLock`:
   ```java
   // BEFORE
   private synchronized void criticalSection() {
       // protected code
   }

   // AFTER
   private final ReentrantLock lock = new ReentrantLock();
   
   private void criticalSection() {
       lock.lock();
       try {
           // protected code
       } finally {
           lock.unlock();
       }
   }
   ```

4. **Example from this repo:**
   - **File:** `src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java`
   - **Status:** ✅ Refactored in M7 (now uses `ReentrantLock`)

---

### 2. **Scan for ThreadLocal Usage**

**Objective:** Verify ThreadLocal is request-scoped and properly cleaned up.

**Steps:**
1. Search for ThreadLocal declarations:
   ```bash
   grep -r "ThreadLocal" src/ --include="*.java"
   ```

2. For each ThreadLocal, categorize it:
   - **Request-scoped context** (user ID, request ID, security context):
     - If using Spring Security: No action needed (Spring 6.1+ is VT-aware)
     - If custom context holder: Switch to Spring's `@Scope("request")` or scoped values (Java 21+)
   
   - **Application-scoped cache** (singleton pattern):
     - ⚠️ Dangerous with VTs (memory bloat)
     - Solution: Use `ConcurrentHashMap` or message-passing instead

   - **Test/framework internals**:
     - Verify cleanup is guaranteed (try-finally or @Before/@After)
     - Consider `try-with-resources` if possible

3. **Example from this repo:**
   - **File:** `src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java:28`
   - **Pattern:** `private static final ThreadLocal<String> REQUEST_CONTEXT = new ThreadLocal<>();`
   - **Status:** ⚠️ Acceptable because cleanup is guaranteed (`REQUEST_CONTEXT.remove()` in finally block)
   - **Recommendation:** For production, migrate to Spring Request Scope

---

### 3. **Check JDBC Connection Pool Configuration**

**Objective:** Ensure the connection pool can handle VT concurrency (orders of magnitude higher than platform threads).

**Steps:**
1. Locate your connection pool config:
   - Spring Boot default: HikariCP in `application.yml`
   - Check these properties:
     ```yaml
     spring:
       datasource:
         hikari:
           maximum-pool-size: 20      # Default too small for VTs
           minimum-idle: 5
           connection-timeout: 30000
           idle-timeout: 600000
           max-lifetime: 1800000
     ```

2. Verify HikariCP is being used (it's VT-aware):
   ```bash
   mvn dependency:tree | grep hikari  # Should show: com.zaxxer:HikariCP
   ```

3. **Tune the pool** based on your workload:
   - **Formula:** `pool_size = (avg_query_latency_ms / 1000) * max_concurrent_requests + buffer`
   - **Example:** 300ms queries × 100 concurrent VTs ÷ 1000 = 30 connections minimum
   - **Set:** `maximum-pool-size: 50-100` for typical VT workloads

   Recommended tuning:
   ```yaml
   spring:
     datasource:
       hikari:
         maximum-pool-size: 100       # Increased for VT concurrency
         minimum-idle: 20
         connection-timeout: 5000     # Fail fast if pool exhausted
   ```

4. **Example from this repo:**
   - **Current config:** H2 in-memory database (no pooling needed)
   - **When migrating to PostgreSQL:** Update connection pool sizes in `application.yml`

---

### 4. **Review Blocking I/O & Add Timeouts**

**Objective:** Prevent unbounded blocking from cascading into system overload.

**Steps:**
1. Identify all blocking I/O in your services:
   - Database queries
   - HTTP calls (RestTemplate, WebClient)
   - File I/O
   - Message queue operations

2. Add **query/request timeouts** to prevent cascading failures:
   ```yaml
   spring:
     datasource:
       hikari:
         connection-timeout: 5000     # Fail if no connection available
     jpa:
       properties:
         hibernate:
           jdbc:
             fetch_size: 50           # Batch fetch to reduce round-trips
   ```

3. For HTTP calls, use timeouts:
   ```java
   @Bean
   public RestTemplate restTemplate() {
       HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory();
       factory.setConnectTimeout(3000);   // Connection timeout
       factory.setReadTimeout(5000);      // Read timeout
       return new RestTemplate(factory);
   }
   ```

4. Add circuit breaker for external services (Spring Cloud Resilience4j):
   ```java
   @CircuitBreaker(name = "paymentService", fallbackMethod = "paymentFallback")
   public String callPaymentAPI() {
       // ...
   }
   ```

---

### 5. **Check for Native Code / JNI**

**Objective:** Identify code that cannot be unmounted (and cannot use Virtual Threads safely).

**Steps:**
1. Search for JNI usage:
   ```bash
   grep -r "System.loadLibrary\|System.load\|native " src/ --include="*.java"
   ```

2. If found, you have two options:
   - **Option A:** Isolate native calls to a separate thread pool (don't run on VT carrier threads):
     ```java
     private final ExecutorService nativeThreadPool = 
         Executors.newFixedThreadPool(4);  // Bounded pool for JNI work
     
     public void callNativeCode() {
         nativeThreadPool.submit(() -> {
             // native call here
         }).get();
     }
     ```
   
   - **Option B:** Migrate away from native code if possible

3. **Example from this repo:**
   - **Status:** ✅ No JNI usage detected

---

### 6. **Audit Frameworks & Dependencies**

**Objective:** Ensure your frameworks support Virtual Threads.

**Steps:**
1. Check framework versions in `pom.xml`:
   ```bash
   mvn dependency:tree | head -50
   ```

2. Verify support:
   - **Spring Boot 3.2+**: ✅ Full VT support
   - **Spring Framework 6.1+**: ✅ Full VT support
   - **Hibernate 6.2+**: ✅ Full VT support
   - **HikariCP 5.0+**: ✅ Full VT support
   - **Tomcat 10.1.11+**: ✅ Full VT support

3. **Example from this repo:**
   - Spring Boot 3.5.12 ✅
   - Spring Framework 6.x ✅
   - Hibernate included ✅

---

## Enabling Virtual Threads

Once all pre-migration checks pass:

### 1. Update `application.yml`

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

### 2. Verify with a Test Run

```bash
./mvnw spring-boot:run
```

Watch the logs for any pinning warnings (if JFR is enabled):
```bash
jdk.VirtualThreadPinned event triggered - investigate the stack trace
```

### 3. Run Load Tests

Use k6 or similar to verify throughput improvement:
```bash
./run-benchmark.sh
```

Compare results against baseline (platform threads).

---

## Post-Migration Monitoring

### JFR Pinning Detection

Enable Java Flight Recorder to detect pinning events:

```bash
# Start app with JFR
java -XX:StartFlightRecording=filename=recording.jfr,dumponexit=true -jar app.jar

# After benchmark, extract pinning events
jfr print --events jdk.VirtualThreadPinned recording.jfr
```

Look for:
- Stack traces showing `synchronized`, intrinsic locks, or OS calls
- High `jdk.VirtualThreadPinned` event counts
- Long pin durations

### Metrics to Monitor

- **Throughput (req/s):** Should improve 2-10x with VTs vs platform threads
- **Latency p99:** Should remain stable or improve
- **GC pause time:** May increase if ThreadLocal usage is high (more objects to collect)
- **Memory usage:** Monitor for unbounded thread creation (should be millions, but capped by heap)

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Performance not improved | Pinning events in JFR | Audit for synchronized blocks, enable JFR and check stack traces |
| OutOfMemoryError after enabling VTs | ThreadLocal bloat | Audit ThreadLocal usage, ensure cleanup |
| Connection pool exhausted | Too many concurrent DB queries | Increase `maximum-pool-size`, add query timeouts |
| Application hangs | Deadlock or unbounded blocking | Use JFR/debugger to inspect stack traces; add timeouts |

---

## Summary: Pre-Migration Checklist

- [ ] No `synchronized` blocks (except framework internals)
- [ ] All ThreadLocal is request-scoped and cleaned up
- [ ] JDBC connection pool tuned for VT concurrency
- [ ] Blocking I/O has timeouts
- [ ] No native code (or isolated in dedicated thread pool)
- [ ] Frameworks are VT-compatible versions
- [ ] Load tests confirm throughput improvement
- [ ] JFR monitoring enabled in production
- [ ] Alerting configured for pinning events

---

## References

- [Virtual Threads Best Practices - openjdk.org](https://loom.openjdk.org/)
- [Spring Boot Virtual Threads Guide](https://spring.io/blog/2023/09/09/all-together-now-spring-boot-3-2-graalvm-native-images-and-virtual-threads)
- [HikariCP Configuration](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)