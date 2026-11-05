# Experimental Identity Matrix

This matrix records the identity facts used to correct Chapters 1–7. Values are
derived from the benchmark manifests, the load-test script, and the application
source; they are not claims that every historical run used one homogeneous
configuration.

| Dimension | Authoritative value or boundary |
|---|---|
| Primary Java 21 runtime | OpenJDK `21.0.8` as recorded in manifests; vendor is not reliably recorded |
| Boundary runtimes | `24.0.2` and `25-ea` in the relevant exploratory/repeated families |
| Load generator | k6 `v1.7.1` in the admitted manifests |
| Host | Apple M1, Darwin `25.2.0`, 8 logical processors, 8 GB |
| Primary scheduler control | `-Djdk.virtualThreadScheduler.parallelism=1` and `maxPoolSize=1` |
| Historical scheduler control | Default 8-carrier population; not interchangeable with the primary 1-carrier population |
| Workload | Closed-loop staged profile: 15 s ramp-up, 30 s hold, 10 s ramp-down |
| Inter-request delay | `sleep(0.1)`, therefore `Z = 0.100 s` |
| `/cpu` implementation | 5,000,000 iterations of `Math.fma` and `Math.sqrt` |
| `/products` implementation | `JdbcTemplate.queryForList("SELECT * FROM products")`; not an in-memory static fast path |
| `/orders` construct | 300 ms sleep occurs before JDBC connection checkout; pool saturation was not established |
| Evidence scope | 368 result/JFR checksum comparisons and 92 telemetry comparisons matched recorded hashes |

Run-family differences in JDK, carrier count, database, pool configuration, and
Git revision remain stratification variables. They must be reported with the
corresponding family rather than collapsed into one universal environment.
