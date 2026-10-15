# Research Artifact and Evidence Provenance Ledger

This ledger keeps unpublished project artifacts separate from the bibliography. A result is eligible for thesis claims only after the required identity and configuration fields are filled.

| Artifact class | Path/pattern | Required identity | Required interpretation fields | Status |
|---|---|---|---|---|
| Source | `src/**`, `pom.xml`, `src/main/resources/**` | Git commit; Java, Spring Boot, Tomcat, HikariCP, H2 versions | Endpoint contract; synchronization implementation; pool and timeout settings | Pending freeze |
| Workload | `k6/load-test.js` and endpoint-isolated scenarios | Git commit; k6 version; scenario name | Closed/open model; stages/rate; timeout; endpoint; dropped iterations | Mixed workload exists; isolation required |
| Orchestration | `run-benchmark.sh` | Git commit; shell; command line | JVM flags; JFR settings; startup/stop behavior; output paths | Needs manifest capture |
| Raw load output | `results/*.json` | SHA-256; timestamp; run ID; source commit | Mode; endpoint; VUs/rate; warm-up; valid hold interval; errors/timeouts | Historical files not fully mapped |
| JFR | `results/jfr/*.jfr` | SHA-256; JVM build; recording options | Event threshold; event count/duration; stack classification; extraction command | Historical files not fully mapped |
| Analysis | `results/*.md`, tables, scripts | Git commit; input artifact IDs | Formula; exclusions; aggregation level; uncertainty method | Narrative contains provisional values |

## Current evidence warning

The existing result summaries are pilot narratives, not yet a verified final dataset. In particular, the reported pinning counts, throughput percentages, and endpoint interpretations must be regenerated from mapped raw files. A latency value of roughly 53 seconds cannot be described as the expected consequence of a 500 ms critical section without checking the actual request/timeout distribution; service time, queueing time, and achieved throughput must be analysed separately.

## Current package status

The current research synthesis and Checkpoint 4 package use the validated
Java 21 synchronization matrix, endpoint-isolation controls, native/JNI
boundary runs, H2/PostgreSQL sensitivity runs, and scheduler probe. The
headline conclusions are qualified and no longer rely on the superseded
mixed-workload figures.

The provenance freeze is still incomplete for a final thesis submission:
historical raw files need a final source-revision/configuration mapping, and
the thesis tables and figures must be checked against that frozen mapping.
Until that is complete, unmapped artifacts remain retained raw material but
are not admitted as definitive evidence solely because they exist in
`results/`.

## Run manifest minimum schema

```text
run_id
timestamp_utc
git_commit
java_vendor_and_version
spring_boot_version
tomcat_version
hikaricp_version
h2_version
k6_version
os_and_kernel
cpu_model_and_logical_processors
memory
execution_mode
lock_variant
endpoint_or_mixed_workload
load_model
target_vus_or_arrival_rate
stage_or_rate_definition
warmup_rule
measurement_interval
timeout
connection_pool_size
tomcat_max_threads_or_executor
jvm_flags
jfr_configuration
result_json_sha256
jfr_sha256
validity_status
exclusion_reason
notes
```

## Claim admission rules

- A headline percentage requires two or more traceable raw conditions, the same metric definition, and a recorded formula.
- A pinning claim requires `jdk.VirtualThreadPinned` stack attribution to the application synchronization site; an event count without a stack is not sufficient.
- A refactoring claim requires endpoint correctness and mutual-exclusion tests on the same commit used for the benchmark.
- A historical single run is labelled exploratory, not a stable estimate.
- An unmapped JSON/JFR file remains retained as raw material but is not used for a definitive conclusion.
