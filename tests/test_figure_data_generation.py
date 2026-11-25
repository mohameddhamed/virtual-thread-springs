#!/usr/bin/env python3
"""Unit and reproducibility tests for thesis PGFPlots data generation."""
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_thesis_figure_data import (
    compute_trial_cpu_percent,
    generate_tex_data,
    load_stratum1_trials,
    load_stratum3_java21_trials,
    load_stratum8_series,
    summarize_stratum8_k6,
)


def test_compute_trial_cpu_percent_drops_first_sample(tmp_path: Path):
    csv_file = tmp_path / "telemetry-test.csv"
    csv_file.write_text(
        "timestamp,pid,threads,cpu_percent\n"
        "2026-10-08T12:00:00Z,1,10,95.0\n"
        "2026-10-08T12:00:01Z,1,10,1.0\n"
        "2026-10-08T12:00:02Z,1,10,2.0\n",
        encoding="utf-8",
    )
    assert compute_trial_cpu_percent(csv_file) == 1.5


def test_stratum1_and_stratum3_verified_aggregates():
    recalc_csv = REPO_ROOT / "docs" / "evidence-freeze" / "metric-recalculations.csv"
    matrix_csv = REPO_ROOT / "docs" / "evidence-freeze" / "run-family-matrix.csv"
    results_dir = REPO_ROOT / "results"

    s1 = load_stratum1_trials(recalc_csv)
    assert len(s1["payments-synchronized"]) == 3
    assert len(s1["payments-reentrant-lock"]) == 3
    assert len(s1["platform-synchronized"]) == 3
    assert len(s1["no-lock"]) == 3

    s3 = load_stratum3_java21_trials(recalc_csv, matrix_csv, results_dir)
    assert len(s3["blocking-jni"]) == 3
    assert len(s3["pure-java-sleep"]) == 3
    assert len(s3["native-short"]) == 3

    jni_cpu = sum(t["cpu_pct"] for t in s3["blocking-jni"]) / 3.0
    sleep_cpu = sum(t["cpu_pct"] for t in s3["pure-java-sleep"]) / 3.0
    short_cpu = sum(t["cpu_pct"] for t in s3["native-short"]) / 3.0
    assert round(jni_cpu, 2) == 1.06
    assert round(sleep_cpu, 2) == 3.95
    assert round(short_cpu, 2) == 7.42


def test_stratum8_verified_series_and_summary():
    results_dir = REPO_ROOT / "results"
    series = load_stratum8_series(results_dir)
    assert len(series[1]) == 3
    assert len(series[10]) == 3
    assert max(t["peak_pending"] for t in series[1]) == 49.0
    assert max(t["peak_pending"] for t in series[10]) == 40.0

    summary = summarize_stratum8_k6(results_dir)
    assert round(summary[1]["steady_tp"], 2) == 3.27
    assert round(summary[10]["steady_tp"], 2) == 32.60


def test_generated_tex_file_is_up_to_date():
    tex_path = REPO_ROOT / "overleaf" / "figures" / "ch6-strata-data.tex"
    expected = generate_tex_data(REPO_ROOT)
    assert tex_path.exists(), "Run scripts/generate_thesis_figure_data.py first"
    assert tex_path.read_text(encoding="utf-8") == expected
