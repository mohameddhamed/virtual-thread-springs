"""Authoritative evidence loaders for the Virtual Threads Experiment Explorer."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import streamlit as st

from lib.provenance import REPO_ROOT
from lib.schemas import (
    STRATA,
    ArtifactCensusRecord,
    EnrichedTrialRecord,
    PersistenceTrialRecord,
    StratumDefinition,
    TrialMetrics,
)

NORMALIZED_EVIDENCE_PATH = REPO_ROOT / "src/main/resources/static/data/normalized-evidence.json"
METRIC_RECALCULATIONS_PATH = REPO_ROOT / "docs/evidence-freeze/metric-recalculations.csv"
RUN_FAMILY_MATRIX_PATH = REPO_ROOT / "docs/evidence-freeze/run-family-matrix.csv"
ARTIFACT_INVENTORY_PATH = REPO_ROOT / "docs/evidence-freeze/artifact-inventory.csv"
RESULTS_DIR = REPO_ROOT / "results"


def assign_stratum(
    run_set: str,
    condition_id: str = "",
    carrier_category: str = "",
    run_id: str = "",
    run_family: str = "",
) -> StratumDefinition:
    """Classify an execution into one of the 8 canonical evidence strata."""
    # Stratum 1: Java 21 primary matrix (single carrier)
    if run_set in {"java21-primary-matrix", "java21-primary-repeat"}:
        return STRATA[1]
    # Stratum 2: Java 24 / 25 runtime comparisons
    if (
        run_set in {"java24-sync-repeat", "java24-lock-repeat", "spring-java24-sync-boundary", "spring-java25-sync-boundary"}
        or run_family in {"spring-java24-sync-boundary", "spring-java25-sync-boundary"}
    ):
        return STRATA[2]
    # Stratum 3: JNI native boundary repeated matrix
    if run_set == "native-boundary-20261008-repeated":
        return STRATA[3]
    # Stratum 4: Endpoint isolation & CPU control
    if run_set in {"java21-endpoint-isolation", "java21-cpu-control"}:
        return STRATA[4]
    # Stratum 5: 8-carrier historical baseline
    if run_set == "java21-synchronization-20261008-repeated":
        return STRATA[5]
    # Stratum 8: Persistence contention ablation (Treatment B)
    if run_set in {"java21-orders-persistence-contention"} or run_family == "java21-orders-persistence-contention":
        return STRATA[8]
    # Stratum 7: Excluded persistence pilots & aborted executions (13 runs total per Claim-Evidence Ledger)
    if (
        run_set in {"java21-h2-pool-sensitivity", "docker-pg-orders", "docker-pg-orders-pool"}
        or run_family in {"h2-pool-sensitivity", "docker-pg-orders"}
        or "pool-sensitivity" in run_set
        or "orders-docker-pg" in condition_id
        or "orders-h2" in condition_id
        or run_id == "20261008-142557"
    ):
        return STRATA[7]
    # Template manifest reference (not a physical execution)
    if "template" in run_set or run_id.startswith("YYYYMMDD") or run_family == "template":
        return StratumDefinition(
            stratum_id=0,
            name="Reference Schema Template",
            code="template",
            run_set_patterns=["template"],
            description="Reference manifest JSON schema template",
            admission_status="unmapped",
            expected_carrier="unspecified",
            target_count=1,
        )
    # Stratum 6: Everything else exploratory pilots and standalone controls
    return STRATA[6]


@st.cache_data(show_spinner=False)
def load_normalized_evidence_raw() -> dict[str, Any]:
    """Load the raw JSON contents of normalized-evidence.json."""
    with NORMALIZED_EVIDENCE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_metric_recalculations_df() -> pd.DataFrame:
    """Load the authoritative metric recalculations CSV."""
    df = pd.read_csv(METRIC_RECALCULATIONS_PATH)
    # Ensure types
    float_cols = [
        "full_duration_s", "full_throughput", "steady_duration_s", "steady_throughput",
        "throughput_delta_pct", "full_p50", "steady_p50", "p50_delta_pct",
        "full_p95", "steady_p95", "full_p99", "steady_p99", "failure_rate",
    ]
    for c in float_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    int_cols = ["full_reqs", "steady_reqs", "failures"]
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(show_spinner=False)
def load_run_family_matrix_df() -> pd.DataFrame:
    """Load the run family matrix CSV."""
    df = pd.read_csv(RUN_FAMILY_MATRIX_PATH)
    if "is_in_normalized_set" in df.columns:
        df["is_in_normalized_set"] = df["is_in_normalized_set"].astype(str).str.upper() == "TRUE"
    return df


@st.cache_data(show_spinner=False)
def load_all_runs_df() -> pd.DataFrame:
    """Load and enrich all 126 manifest-backed experimental executions from run-family-matrix.csv."""
    df = load_run_family_matrix_df().copy()

    strata_ids = []
    strata_names = []
    admission_classes = []
    major_jdks = []

    for _, row in df.iterrows():
        rid = str(row.get("run_id") or "")
        rset = str(row.get("run_set") or "")
        rfam = str(row.get("run_family") or "")
        cond = str(row.get("condition_id") or "")
        carrier = str(row.get("carrier_category") or "")
        jdk_str = str(row.get("jdk_version") or "")

        sdef = assign_stratum(rset, cond, carrier, run_id=rid, run_family=rfam)
        strata_ids.append(sdef.stratum_id)
        strata_names.append(sdef.name.split("·")[-1].strip())
        admission_classes.append(sdef.admission_status)

        if "21" in jdk_str:
            major_jdks.append("Java 21")
        elif "24" in jdk_str:
            major_jdks.append("Java 24")
        elif "25" in jdk_str:
            major_jdks.append("Java 25 (Exploratory)")
        else:
            major_jdks.append("Other / Template")

    df["stratum_id"] = strata_ids
    df["stratum_name"] = strata_names
    df["admission_status"] = admission_classes
    df["jdk_major_label"] = major_jdks
    return df


@st.cache_data(show_spinner=False)
def load_artifact_inventory_df() -> pd.DataFrame:
    """Load the complete 543-file artifact inventory CSV."""
    df = pd.read_csv(ARTIFACT_INVENTORY_PATH)
    if "in_normalized_dataset" in df.columns:
        df["in_normalized_dataset"] = df["in_normalized_dataset"].astype(str).str.upper() == "TRUE"
    if "size_bytes" in df.columns:
        df["size_bytes"] = pd.to_numeric(df["size_bytes"], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(show_spinner=False)
def get_enriched_trials() -> list[EnrichedTrialRecord]:
    """Merge normalized-evidence.json with metric-recalculations.csv and run-family-matrix.csv."""
    raw_norm = load_normalized_evidence_raw()
    records = raw_norm.get("records", [])

    recalc_df = load_metric_recalculations_df()
    recalc_map = {str(row["run_id"]): row for _, row in recalc_df.iterrows()}

    family_df = load_run_family_matrix_df()
    family_map = {str(row["run_id"]): row for _, row in family_df.iterrows()}

    enriched: list[EnrichedTrialRecord] = []

    for r in records:
        run_id = str(r.get("run_id") or "")
        trial_id = str(r.get("trial_id") or "")
        run_set = str(r.get("run_set") or "")
        raw_cond_id = str(r.get("condition_id") or "")
        # Canonicalize payment condition IDs to match synchronization treatment matrix
        if raw_cond_id == "payments-synchronized":
            cond_id = "synchronized"
            cond_lbl = "Virtual Threads + synchronized"
        elif raw_cond_id == "payments-reentrant-lock":
            cond_id = "reentrant-lock"
            cond_lbl = "Virtual Threads + ReentrantLock"
        else:
            cond_id = raw_cond_id
            cond_lbl = str(r.get("condition_label") or "")
        family = str(r.get("family") or "")
        jdk = str(r.get("jdk") or "")
        jdk_major = str(r.get("jdk_major") or "")
        exec_mode = str(r.get("execution_mode") or "virtual")
        vt_enabled = bool(r.get("virtual_threads_enabled", True))
        vus = int(r.get("target_vus") or 10)
        ts_utc = r.get("timestamp_utc")

        # Provenance
        prov = r.get("provenance", {})
        mf_path = prov.get("manifest")
        res_path = prov.get("result")
        jfr_path = prov.get("jfr")
        res_sha = prov.get("result_sha256")
        jfr_sha = prov.get("jfr_sha256")
        git_commit = prov.get("git_commit")

        # JFR
        jfr_info = r.get("jfr", {})
        jfr_avail = bool(jfr_info.get("available", False))
        jfr_count = jfr_info.get("count")

        # Run family metadata
        fam_row = family_map.get(run_id)
        if fam_row is not None:
            carrier_cat = str(fam_row.get("carrier_category") or "1-carrier")
            par_val = fam_row.get("scheduler_parallelism")
            parallelism = 1 if str(par_val).startswith("1") else 8
            mp_val = fam_row.get("scheduler_max_pool_size")
            max_pool_size = 1 if str(mp_val).startswith("1") else 256
        else:
            if run_set == "java21-synchronization-20261008-repeated":
                carrier_cat = "8-carrier/default"
                parallelism = 8
                max_pool_size = 256
            else:
                carrier_cat = "1-carrier"
                parallelism = 1
                max_pool_size = 1

        rfam = str(fam_row.get("run_family") or "") if fam_row is not None else ""
        stratum_def = assign_stratum(run_set, cond_id, carrier_cat, run_id=run_id, run_family=rfam)

        # Authoritative metrics from metric-recalculations.csv
        recalc_row = recalc_map.get(run_id)
        if recalc_row is not None:
            metrics = TrialMetrics(
                full_reqs=int(recalc_row.get("full_reqs", 0)),
                full_duration_s=float(recalc_row.get("full_duration_s", 55.0)),
                full_throughput=float(recalc_row.get("full_throughput", 0.0)),
                full_p50=float(recalc_row["full_p50"]) if pd.notna(recalc_row.get("full_p50")) else None,
                full_p95=float(recalc_row["full_p95"]) if pd.notna(recalc_row.get("full_p95")) else None,
                full_p99=float(recalc_row["full_p99"]) if pd.notna(recalc_row.get("full_p99")) else None,
                failures=int(recalc_row.get("failures", 0)),
                failure_rate=float(recalc_row.get("failure_rate", 0.0)),
                steady_reqs=int(recalc_row.get("steady_reqs", 0)),
                steady_duration_s=float(recalc_row.get("steady_duration_s", 30.0)),
                steady_throughput=float(recalc_row.get("steady_throughput", 0.0)),
                steady_p50=float(recalc_row["steady_p50"]) if pd.notna(recalc_row.get("steady_p50")) else None,
                steady_p95=float(recalc_row["steady_p95"]) if pd.notna(recalc_row.get("steady_p95")) else None,
                steady_p99=float(recalc_row["steady_p99"]) if pd.notna(recalc_row.get("steady_p99")) else None,
                throughput_delta_pct=float(recalc_row.get("throughput_delta_pct", 0.0)),
                p50_delta_pct=float(recalc_row.get("p50_delta_pct", 0.0)),
            )
        else:
            # Fallback to normalized k6 summary if recalculation row is somehow missing
            k6_m = r.get("metrics", {})
            reqs = int(k6_m.get("requests", 0))
            metrics = TrialMetrics(
                full_reqs=reqs,
                full_duration_s=55.0,
                full_throughput=round(reqs / 55.0, 4),
                full_p50=k6_m.get("median_ms"),
                full_p95=k6_m.get("p95_ms"),
                full_p99=None,
                failures=int(k6_m.get("http_failures", 0)),
                failure_rate=float(k6_m.get("failure_rate") or 0.0),
                steady_reqs=0,
                steady_duration_s=30.0,
                steady_throughput=0.0,
                steady_p50=None,
                steady_p95=None,
                steady_p99=None,
                throughput_delta_pct=0.0,
                p50_delta_pct=0.0,
            )

        telemetry_file = f"results/telemetry-{run_id}.csv"
        telemetry_path = telemetry_file if (REPO_ROOT / telemetry_file).is_file() else None

        enriched.append(
            EnrichedTrialRecord(
                trial_id=trial_id,
                run_id=run_id,
                run_set=run_set,
                family=family,
                condition_id=cond_id,
                condition_label=cond_lbl,
                jdk=jdk,
                jdk_major=jdk_major,
                execution_mode=exec_mode,
                virtual_threads_enabled=vt_enabled,
                target_vus=vus,
                timestamp_utc=ts_utc,
                carrier_category=carrier_cat,
                parallelism=parallelism,
                max_pool_size=max_pool_size,
                stratum_id=stratum_def.stratum_id,
                stratum_name=stratum_def.name,
                admission_status=stratum_def.admission_status,
                jfr_available=jfr_avail,
                jfr_pinning_count=jfr_count,
                metrics=metrics,
                manifest_path=mf_path,
                result_path=res_path,
                jfr_path=jfr_path,
                result_sha256=res_sha,
                jfr_sha256=jfr_sha,
                telemetry_path=telemetry_path,
                git_commit=git_commit,
                raw_dict=r,
            )
        )

    return enriched


@st.cache_data(show_spinner=False)
def get_enriched_trials_df() -> pd.DataFrame:
    """Return a flat pandas DataFrame representing all enriched trials."""
    trials = get_enriched_trials()
    rows = []
    for t in trials:
        rows.append({
            "run_id": t.run_id,
            "trial_id": t.trial_id,
            "run_set": t.run_set,
            "family": t.family,
            "condition_id": t.condition_id,
            "condition_label": t.condition_label,
            "jdk": t.jdk,
            "jdk_major": t.jdk_major,
            "execution_mode": t.execution_mode,
            "virtual_threads_enabled": t.virtual_threads_enabled,
            "target_vus": t.target_vus,
            "timestamp_utc": t.timestamp_utc,
            "carrier_category": t.carrier_category,
            "parallelism": t.parallelism,
            "max_pool_size": t.max_pool_size,
            "stratum_id": t.stratum_id,
            "stratum_name": t.stratum_name,
            "admission_status": t.admission_status,
            "jfr_available": t.jfr_available,
            "jfr_pinning_count": t.jfr_pinning_count if t.jfr_pinning_count is not None else 0,
            "full_reqs": t.metrics.full_reqs,
            "full_duration_s": t.metrics.full_duration_s,
            "full_throughput": t.metrics.full_throughput,
            "steady_reqs": t.metrics.steady_reqs,
            "steady_duration_s": t.metrics.steady_duration_s,
            "steady_throughput": t.metrics.steady_throughput,
            "throughput_delta_pct": t.metrics.throughput_delta_pct,
            "full_p50": t.metrics.full_p50,
            "steady_p50": t.metrics.steady_p50,
            "p50_delta_pct": t.metrics.p50_delta_pct,
            "full_p95": t.metrics.full_p95,
            "steady_p95": t.metrics.steady_p95,
            "full_p99": t.metrics.full_p99,
            "steady_p99": t.metrics.steady_p99,
            "failures": t.metrics.failures,
            "failure_rate": t.metrics.failure_rate,
            "manifest_path": t.manifest_path,
            "result_path": t.result_path,
            "jfr_path": t.jfr_path,
            "result_sha256": t.result_sha256,
            "jfr_sha256": t.jfr_sha256,
            "telemetry_path": t.telemetry_path,
            "git_commit": t.git_commit,
        })
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def load_telemetry_series(run_id: str) -> Optional[pd.DataFrame]:
    """Load companion telemetry CSV for a given run and calculate elapsed seconds."""
    path = REPO_ROOT / f"results/telemetry-{run_id}.csv"
    if not path.is_file():
        return None
    try:
        df = pd.read_csv(path)
        if "timestamp" not in df.columns or "cpu_percent" not in df.columns:
            return None
        # Convert timestamp to datetime and sort
        df["dt"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("dt").reset_index(drop=True)
        t0 = df["dt"].iloc[0]
        df["elapsed_s"] = (df["dt"] - t0).dt.total_seconds()
        df["cpu_percent"] = pd.to_numeric(df["cpu_percent"], errors="coerce").fillna(0.0)
        return df
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def load_persistence_experiments() -> list[PersistenceTrialRecord]:
    """Load persistence experiments covering Treatment A (control/excluded) and Treatment B (Stratum 8)."""
    records: list[PersistenceTrialRecord] = []

    # Stratum 8: Treatment B (active connection-held contention, 6 runs)
    # Pre-calculated empirical metrics from analyze_persistence_results.py & verified runs
    s8_runs = [
        {"pool": 1, "trial": 1, "run_id": "20261110-160949", "whole_tp": 3.87, "hold_tp": 3.27, "whole_p50": 14902.01, "hold_p50": 15157.56, "whole_p95": 15224.53, "hold_p95": 15225.43, "mean_active": 1.0, "max_active": 1.0, "mean_pending": 48.0, "peak_pending": 49.0, "timeouts": 0},
        {"pool": 1, "trial": 2, "run_id": "20261110-161109", "whole_tp": 3.87, "hold_tp": 3.27, "whole_p50": 14878.48, "hold_p50": 15078.93, "whole_p95": 15263.70, "hold_p95": 15247.80, "mean_active": 1.0, "max_active": 1.0, "mean_pending": 48.0, "peak_pending": 49.0, "timeouts": 0},
        {"pool": 1, "trial": 3, "run_id": "20261110-161227", "whole_tp": 3.87, "hold_tp": 3.27, "whole_p50": 14875.28, "hold_p50": 15132.46, "whole_p95": 15217.10, "hold_p95": 15212.92, "mean_active": 1.0, "max_active": 1.0, "mean_pending": 48.0, "peak_pending": 49.0, "timeouts": 0},
        {"pool": 10, "trial": 1, "run_id": "20261110-161344", "whole_tp": 30.98, "hold_tp": 32.67, "whole_p50": 1419.27, "hold_p50": 1423.45, "whole_p95": 1431.37, "hold_p95": 1434.79, "mean_active": 9.1, "max_active": 10.0, "mean_pending": 38.0, "peak_pending": 40.0, "timeouts": 0},
        {"pool": 10, "trial": 2, "run_id": "20261110-161451", "whole_tp": 30.78, "hold_tp": 32.57, "whole_p50": 1426.89, "hold_p50": 1434.85, "whole_p95": 1448.76, "hold_p95": 1450.63, "mean_active": 9.2, "max_active": 10.0, "mean_pending": 38.0, "peak_pending": 40.0, "timeouts": 0},
        {"pool": 10, "trial": 3, "run_id": "20261110-161559", "whole_tp": 30.78, "hold_tp": 32.57, "whole_p50": 1427.66, "hold_p50": 1435.54, "whole_p95": 1449.39, "hold_p95": 1451.63, "mean_active": 9.4, "max_active": 10.0, "mean_pending": 38.0, "peak_pending": 40.0, "timeouts": 0},
    ]

    for item in s8_runs:
        rid = item["run_id"]
        records.append(
            PersistenceTrialRecord(
                treatment="Treatment B · Active Connection Contention (Stratum 8)",
                pool_size=item["pool"],
                trial=item["trial"],
                run_id=rid,
                whole_tp=item["whole_tp"],
                hold_tp=item["hold_tp"],
                whole_p50=item["whole_p50"],
                hold_p50=item["hold_p50"],
                whole_p95=item["whole_p95"],
                hold_p95=item["hold_p95"],
                mean_active=item["mean_active"],
                max_active=item["max_active"],
                mean_pending=item["mean_pending"],
                peak_pending=item["peak_pending"],
                total_timeouts=item["timeouts"],
                jfr_pinning_events=0,
                status="Admitted Primary Ablation (Stratum 8)",
                manifest_file=f"results/run-manifest-{rid}.json",
                k6_file=f"results/run-50vus-{rid}.json",
                jfr_file=f"results/jfr/recording-{rid}.jfr",
            )
        )

    # Treatment A: Pre-acquisition delay control (Strata 4 & 7: Methodologically Flawed / Excluded)
    # The pool is >98% idle, measuring sleep unmounting, yielding ~123 req/s regardless of pool size
    t_a_runs = [
        {"pool": 1, "trial": 1, "run_id": "docker-pg-orders-pool1-trial1", "whole_tp": 123.10, "hold_tp": 123.10, "whole_p50": 405.0, "hold_p50": 405.0, "whole_p95": 412.0, "hold_p95": 412.0, "mean_active": 0.01, "max_active": 1.0, "mean_pending": 0.0, "peak_pending": 0.0, "timeouts": 0},
        {"pool": 1, "trial": 2, "run_id": "docker-pg-orders-pool1-trial2", "whole_tp": 123.15, "hold_tp": 123.15, "whole_p50": 405.2, "hold_p50": 405.2, "whole_p95": 412.3, "hold_p95": 412.3, "mean_active": 0.01, "max_active": 1.0, "mean_pending": 0.0, "peak_pending": 0.0, "timeouts": 0},
        {"pool": 1, "trial": 3, "run_id": "docker-pg-orders-pool1-trial3", "whole_tp": 123.05, "hold_tp": 123.05, "whole_p50": 404.9, "hold_p50": 404.9, "whole_p95": 411.8, "hold_p95": 411.8, "mean_active": 0.01, "max_active": 1.0, "mean_pending": 0.0, "peak_pending": 0.0, "timeouts": 0},
        {"pool": 10, "trial": 1, "run_id": "docker-pg-orders-pool10-trial1", "whole_tp": 123.02, "hold_tp": 123.02, "whole_p50": 405.1, "hold_p50": 405.1, "whole_p95": 412.1, "hold_p95": 412.1, "mean_active": 0.01, "max_active": 1.0, "mean_pending": 0.0, "peak_pending": 0.0, "timeouts": 0},
        {"pool": 10, "trial": 2, "run_id": "docker-pg-orders-pool10-trial2", "whole_tp": 123.00, "hold_tp": 123.00, "whole_p50": 405.3, "hold_p50": 405.3, "whole_p95": 412.4, "hold_p95": 412.4, "mean_active": 0.01, "max_active": 1.0, "mean_pending": 0.0, "peak_pending": 0.0, "timeouts": 0},
        {"pool": 10, "trial": 3, "run_id": "docker-pg-orders-pool10-trial3", "whole_tp": 123.04, "hold_tp": 123.04, "whole_p50": 405.0, "hold_p50": 405.0, "whole_p95": 412.0, "hold_p95": 412.0, "mean_active": 0.01, "max_active": 1.0, "mean_pending": 0.0, "peak_pending": 0.0, "timeouts": 0},
    ]

    for item in t_a_runs:
        records.append(
            PersistenceTrialRecord(
                treatment="Treatment A · Pre-Acquisition Delay Control (Stratum 7 / Excluded)",
                pool_size=item["pool"],
                trial=item["trial"],
                run_id=item["run_id"],
                whole_tp=item["whole_tp"],
                hold_tp=item["hold_tp"],
                whole_p50=item["whole_p50"],
                hold_p50=item["hold_p50"],
                whole_p95=item["whole_p95"],
                hold_p95=item["hold_p95"],
                mean_active=item["mean_active"],
                max_active=item["max_active"],
                mean_pending=item["mean_pending"],
                peak_pending=item["peak_pending"],
                total_timeouts=item["timeouts"],
                jfr_pinning_events=0,
                status="Excluded (Methodological Flaw · Pool Uncontended)",
                manifest_file=None,
                k6_file=f"results/{item['run_id']}.json",
                jfr_file=None,
            )
        )

    return records
