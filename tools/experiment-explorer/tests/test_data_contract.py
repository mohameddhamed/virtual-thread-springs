"""Test suite for Data Contract integrity, schemas, strata, and inventory reconciliation."""
from __future__ import annotations

import sys
from pathlib import Path

# Add explorer root
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pytest
from lib.loaders import (
    assign_stratum,
    get_enriched_trials,
    load_artifact_inventory_df,
    load_metric_recalculations_df,
    load_normalized_evidence_raw,
    load_run_family_matrix_df,
)
from lib.schemas import STRATA


def test_strata_definitions():
    """Verify that all 8 canonical strata are defined with valid properties."""
    assert len(STRATA) == 8
    for sid in range(1, 9):
        assert sid in STRATA
        sdef = STRATA[sid]
        assert sdef.stratum_id == sid
        assert len(sdef.name) > 0
        assert len(sdef.code) > 0
        assert sdef.admission_status in {"primary", "supporting", "historical", "diagnostic", "excluded", "ablation", "exploratory"}
        assert sdef.target_count > 0


def test_admitted_trial_population():
    """Verify that normalized-evidence.json contains exactly 76 records."""
    norm_data = load_normalized_evidence_raw()
    records = norm_data.get("records", [])
    assert len(records) == 76, f"Expected 76 trial records, got {len(records)}"

    # 75 records have manifests, 1 is the standalone CPU control
    manifest_records = [r for r in records if r.get("provenance", {}).get("manifest")]
    assert len(manifest_records) == 75, f"Expected 75 manifest-backed records, got {len(manifest_records)}"

    cpu_control = [r for r in records if r.get("run_id") == "cpu-control-20261008"]
    assert len(cpu_control) == 1, "Expected standalone cpu-control-20261008 record"


def test_artifact_inventory_discrepancy_reconciliation():
    """Verify the 504 vs 543 inventory reconciliation math."""
    inv_df = load_artifact_inventory_df()
    assert len(inv_df) == 543, f"Expected 543 total artifacts on disk, got {len(inv_df)}"

    type_counts = inv_df["artifact_type"].value_counts().to_dict()
    assert type_counts.get("manifest_json") == 121
    assert type_counts.get("k6_json") == 157
    assert type_counts.get("jfr_binary") == 140
    assert type_counts.get("telemetry_csv") == 120
    assert type_counts.get("markdown_report") == 5

    # Check sum
    total_files = sum(type_counts.values())
    assert total_files == 543

    # Check candidate statuses
    status_counts = inv_df["candidate_status"].value_counts().to_dict()
    assert status_counts.get("admitted_normalized") == 226
    assert status_counts.get("historical_baseline") == 239
    assert status_counts.get("diagnostic") == 12
    assert status_counts.get("exploratory_uninstrumented") == 9
    assert status_counts.get("unmapped") == 57

    # Admitted files: exactly 75 manifests + 76 k6 JSONs + 75 JFRs = 226
    admitted_df = inv_df[inv_df["in_normalized_dataset"] == True]
    assert len(admitted_df) == 226

    adm_types = admitted_df["artifact_type"].value_counts().to_dict()
    assert adm_types.get("manifest_json") == 75
    assert adm_types.get("k6_json") == 76
    assert adm_types.get("jfr_binary") == 75


def test_stratum_assignment():
    """Verify that executions are mapped to the correct strata."""
    assert assign_stratum("java21-primary-matrix", "synchronized", "1-carrier").stratum_id == 1
    assert assign_stratum("java21-primary-repeat", "reentrant-lock", "1-carrier").stratum_id == 1
    assert assign_stratum("java24-sync-repeat", "synchronized", "1-carrier").stratum_id == 2
    assert assign_stratum("native-boundary-20261008-repeated", "blocking-jni", "1-carrier").stratum_id == 3
    assert assign_stratum("java21-endpoint-isolation", "orders-virtual", "1-carrier").stratum_id == 4
    assert assign_stratum("java21-cpu-control", "cpu-virtual", "1-carrier").stratum_id == 4
    assert assign_stratum("java21-synchronization-20261008-repeated", "synchronized", "8-carrier/default").stratum_id == 5
    assert assign_stratum("java21-orders-persistence-contention", "orders-held-pool-1", "1-carrier").stratum_id == 8
    assert assign_stratum("java21-h2-pool-sensitivity", "orders", "mixed").stratum_id == 7
    assert assign_stratum("docker-pg-orders", "orders-docker-pg-pool-1", "1-carrier").stratum_id == 7


def test_complete_execution_census_distribution():
    """Verify that all 126 manifest-backed runs are correctly partitioned across the 8 strata."""
    from lib.loaders import load_all_runs_df

    df = load_all_runs_df()
    assert len(df) == 126, f"Expected 126 total execution runs, got {len(df)}"

    # Strata distribution per Adjudication Charter Section 6 and Claim-Evidence Ledger
    strata_counts = df["stratum_id"].value_counts().to_dict()
    assert strata_counts.get(1) == 12, f"Stratum 1 expected 12, got {strata_counts.get(1)}"
    assert strata_counts.get(2) == 10, f"Stratum 2 expected 10, got {strata_counts.get(2)}"
    assert strata_counts.get(3) == 27, f"Stratum 3 expected 27, got {strata_counts.get(3)}"
    assert strata_counts.get(4) == 18, f"Stratum 4 expected 18, got {strata_counts.get(4)}"
    assert strata_counts.get(5) == 12, f"Stratum 5 expected 12, got {strata_counts.get(5)}"
    assert strata_counts.get(6) == 27, f"Stratum 6 expected 27, got {strata_counts.get(6)}"
    assert strata_counts.get(7) == 13, f"Stratum 7 expected 13, got {strata_counts.get(7)}"
    assert strata_counts.get(8) == 6, f"Stratum 8 expected 6, got {strata_counts.get(8)}"

    # Total physical executions = 125 (+ 1 template manifest = 126)
    physical_total = sum(strata_counts.get(sid, 0) for sid in range(1, 9))
    assert physical_total == 125

    # JDK distribution
    jdk_counts = df["jdk_major_label"].value_counts().to_dict()
    assert jdk_counts.get("Java 21") == 89
    assert jdk_counts.get("Java 24") == 21
    assert jdk_counts.get("Java 25 (Exploratory)") == 15
    assert jdk_counts.get("Other / Template") == 1
