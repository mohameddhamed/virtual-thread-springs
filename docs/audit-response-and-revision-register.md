# Audit Response and Revision Register

## Accepted corrections

| Audit point | Decision | Implemented response |
|---|---|---|
| JEP 491 and Java-version boundary | Accept | Scope primary conclusions to Java 21 LTS; discuss JDK 24+ monitor-pinning change explicitly |
| Missing recent closest work | Accept | Added a critical comparison covering JEP 491, database, framework, Spring, reactive, and steady-state studies |
| Incomplete citations and point-of-use traceability | Accept | Rebuilt the review with stable identifiers where verified; flagged entries requiring proceedings/version verification |
| Local artifacts mixed with literature | Accept | Created a separate artifact/provenance ledger |
| RQ2 too broad | Accept | Bound RQ2 to synchronization, ThreadLocal context correctness, and JDBC finite-resource contention |
| Missing protocol details | Accept | Added required run-manifest fields, load-model disclosure, JFR extraction, warm-up, exclusion, and endpoint-isolation requirements |
| Three-run bootstrap precision | Accept | Three runs are exploratory only; final repetition count must be pilot-justified |
| Correctness equivalence | Accept | Require endpoint and mutual-exclusion tests before interpreting lock-refactoring results |
| Schedule and minimum viable scope | Accept in substance | Optional PostgreSQL/pool extensions are explicitly deferrable; the checkpoint artifact should use dated entries once the exam track is confirmed |
| Generic AI paragraph | Accept | Final submission must contain a factual tool-use disclosure and retained interaction log, not policy prose alone |

## Proportionality decisions

| Audit point | Decision | Reason |
|---|---|---|
| Full 2×2 platform/Virtual Thread × lock matrix | Valuable extension, not a prerequisite | The approved topic and existing artifact already define the three-condition Java 21 comparison. The missing fourth cell improves factor separation, so it is planned if resources permit; otherwise the limitation is stated rather than pretending the design is factorial |
| JDK 25 boundary run | Valuable extension, not required for the primary thesis | A Java 21 LTS study remains coherent if all practical guidance is version-bounded and JEP 491 is discussed. A boundary run is preferred but must not displace reproducible Java 21 measurements |
| Three-to-five-page limit versus thesis-oriented plan | Resolve by maintaining two artifacts | Keep a compact checkpoint plan and a fuller methodology document. The latter may become the thesis chapter; the former satisfies the formal product |
| Formal “insufficient” gate despite supervisor check-off | Diagnostic, not rejection | The audit identifies evidence and packaging defects. The supervisor’s check-off remains a separate administrative fact; this register addresses the scientific improvement work |

## Unresolved before final submission

1. Freeze the exact runtime and dependency versions from the retained runs.
2. Map each retained k6/JFR file to a commit and manifest.
3. Re-extract pinning counts and stack traces rather than copying narrative counts.
4. Replace or qualify any result that cannot be reproduced from traceable artifacts.
5. Confirm the applicable ELTE consultation calendar and complete the factual AI declaration.

## Research expansion decision — 8 October 2026

The three endpoint paths are retained because they represent distinct roles:
payment synchronization treatment, data/context/resource treatment, and clean
control. Expansion will target causal separation rather than file count:
endpoint-isolated workloads, explicit synchronized/`ReentrantLock`/no-lock
payment variants, Hikari pool telemetry, and a CPU-bound control are
high-value additions. A dedicated ThreadLocal lifecycle experiment is
conditional on retaining a lifecycle claim; native/JNI and additional similar
slow endpoints are out of scope.

JDK 24/25 will be treated as a version-boundary arm, not mixed into the Java
21 primary result. JEP 491 removes nearly all monitor-related Virtual Thread
pinning beginning in JDK 24, so Java 21 synchronized-pinning findings remain
valid but explicitly version-bounded. `jdk.tracePinnedThreads` is not a
cross-JDK measurement instrument, and raw `jdk.VirtualThreadPinned` counts
must not be compared without accounting for changed event semantics.
