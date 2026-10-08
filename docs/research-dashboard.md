# Local Research Evidence Explorer

The Spring Boot app serves the static dashboard at
`http://localhost:8080/research-dashboard.html`. It has no frontend build
toolchain and loads the canonical dataset from
`src/main/resources/static/data/normalized-evidence.json`.

## Refreshing the dataset

From the repository root, after adding or changing artifacts under `results/`:

```bash
python3 scripts/normalize_evidence.py
python3 scripts/validate_normalized_evidence.py
```

The script reads repeated run manifests, their raw k6 JSONL files, and JFR
recordings. It preserves one record per trial for:

* `java21-synchronization-20261008-repeated` (12 runs);
* `native-boundary-20261008-repeated` (27 runs);
* the standalone CPU control when present.

JFR counts are extracted with `jfr print --events jdk.VirtualThreadPinned`.
A count of zero is retained as an explicit measured result. The script does
not infer pinning from throughput.

## Data classifications and limitations

* **Measured**: values read from manifests, k6 JSONL, or JFR event streams.
* **Derived**: percentiles, labels, filters, and aggregate cards computed from
  measured records.
* **Conceptual**: mechanism explanations and thesis wording, not observations.

The one-carrier scheduler is a mechanism-isolation stress condition. The
no-lock treatment is an upper-bound diagnostic, not a valid payment design.
JFR event semantics differ across JDK versions; zero JNI events do not prove
that no carrier was occupied. The dashboard is an evidence navigator, not a
replacement for the raw artifacts or the written methodology.

## Starting the app

Use the existing Spring Boot workflow:

```bash
./mvnw spring-boot:run
```

No benchmark methodology or workload is changed by the dashboard or
normalization script.
