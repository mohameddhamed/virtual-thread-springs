#!/usr/bin/env python3
"""Reproducibly extract verified thesis benchmark metrics into PGFPlots data tables.

Reads frozen metric recalculations, run metadata matrices, JVM CPU telemetry CSVs,
and HikariCP Stratum 8 pool/k6 traces to emit LaTeX/PGFPlots data tables without
hardcoded experimental coordinates.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

STRATUM8_RUNS = {
    1: ["20261110-160949", "20261110-161109", "20261110-161227"],
    10: ["20261110-161344", "20261110-161451", "20261110-161559"],
}


def parse_iso8601(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp string, converting trailing Z to UTC offset."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_stratum1_trials(recalc_csv: Path) -> dict[str, list[dict[str, float]]]:
    """Extract Stratum 1 Java 21 primary trials from metric-recalculations.csv."""
    grouped: dict[str, list[dict[str, float]]] = {
        "payments-synchronized": [],
        "payments-reentrant-lock": [],
        "platform-synchronized": [],
        "no-lock": [],
    }
    allowed_run_sets = {"java21-primary-repeat", "java21-primary-matrix"}
    with recalc_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["run_set"] not in allowed_run_sets:
                continue
            cond = row["condition_id"]
            if cond in grouped:
                grouped[cond].append(
                    {
                        "run_id": row["run_id"],
                        "steady_tp": float(row["steady_throughput"]),
                        "steady_p50": float(row["steady_p50"]),
                        "steady_p95": float(row["steady_p95"]),
                    }
                )
    return grouped


def compute_trial_cpu_percent(telemetry_csv: Path) -> float:
    """Compute trial CPU percent mean after dropping the first startup sample."""
    with telemetry_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 2:
        raise ValueError(f"Expected >= 2 CPU samples in {telemetry_csv}")
    vals = [float(r["cpu_percent"]) for r in rows[1:]]
    return sum(vals) / len(vals)


def load_stratum3_java21_trials(
    recalc_csv: Path,
    matrix_csv: Path,
    results_dir: Path,
) -> dict[str, list[dict[str, float]]]:
    """Extract Java 21 Stratum 3 trials pairing k6 hold throughput with JVM CPU."""
    java21_runs: set[str] = set()
    with matrix_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if (
                row["run_set"] == "native-boundary-20261008-repeated"
                and row["jdk_version"] == "21.0.8"
                and row["is_in_normalized_set"] == "True"
            ):
                java21_runs.add(row["run_id"])

    grouped: dict[str, list[dict[str, float]]] = {
        "blocking-jni": [],
        "pure-java-sleep": [],
        "native-short": [],
    }
    with recalc_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["run_id"] not in java21_runs:
                continue
            cond = row["condition_id"]
            if cond not in grouped:
                continue
            cpu_csv = results_dir / f"telemetry-{row['run_id']}.csv"
            grouped[cond].append(
                {
                    "run_id": row["run_id"],
                    "steady_tp": float(row["steady_throughput"]),
                    "steady_p50": float(row["steady_p50"]),
                    "cpu_pct": compute_trial_cpu_percent(cpu_csv),
                }
            )
    return grouped


def find_k6_t0(k6_json: Path, metric_name: str = "orders_duration") -> datetime:
    """Anchor k6 timeline to the earliest inferred request initiation timestamp."""
    initiations: list[datetime] = []
    with k6_json.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("metric") == metric_name and rec.get("type") == "Point":
                end_t = parse_iso8601(rec["data"]["time"])
                dur_ms = float(rec["data"]["value"])
                initiations.append(end_t - timedelta(milliseconds=dur_ms))
    if not initiations:
        raise ValueError(f"No {metric_name} Point records in {k6_json}")
    return min(initiations)


def load_stratum8_series(
    results_dir: Path,
    max_t_rel: float = 56.0,
) -> dict[int, list[dict[str, object]]]:
    """Load Stratum 8 Treatment B HikariCP telemetry aligned to each trial's k6 t0."""
    series_by_pool: dict[int, list[dict[str, object]]] = {1: [], 10: []}
    for pool_size, run_ids in STRATUM8_RUNS.items():
        for run_id in run_ids:
            t0 = find_k6_t0(results_dir / f"run-50vus-{run_id}.json")
            pool_csv = results_dir / f"pool-telemetry-{run_id}.csv"
            points: list[tuple[float, float, float]] = []
            with pool_csv.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    t_sample = parse_iso8601(row["timestamp"])
                    t_rel = (t_sample - t0).total_seconds()
                    if -0.5 <= t_rel <= max_t_rel:
                        points.append(
                            (
                                max(0.0, t_rel),
                                float(row["pending"]),
                                float(row["active"]),
                            )
                        )
            series_by_pool[pool_size].append(
                {
                    "run_id": run_id,
                    "points": points,
                    "peak_pending": max(p[1] for p in points),
                }
            )
    return series_by_pool


def percentile_linear(vals: list[float], pct: float) -> float:
    """Compute linear-interpolated percentile matching numpy.percentile default."""
    if not vals:
        raise ValueError("Cannot compute percentile of empty list")
    sorted_vals = sorted(vals)
    pos = (len(sorted_vals) - 1) * pct
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (pos - lo) * (sorted_vals[hi] - sorted_vals[lo])


def summarize_stratum8_k6(results_dir: Path) -> dict[int, dict[str, float]]:
    """Compute mean hold throughput and hold p50 for Stratum 8 K=1 and K=10."""
    summary: dict[int, dict[str, float]] = {}
    for pool_size, run_ids in STRATUM8_RUNS.items():
        hold_tps = []
        hold_p50s = []
        for run_id in run_ids:
            k6_path = results_dir / f"run-50vus-{run_id}.json"
            t0 = find_k6_t0(k6_path)
            hold_durs: list[float] = []
            with k6_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    if rec.get("metric") == "orders_duration" and rec.get("type") == "Point":
                        t = parse_iso8601(rec["data"]["time"])
                        rel = (t - t0).total_seconds()
                        if 15.0 <= rel <= 45.0:
                            hold_durs.append(float(rec["data"]["value"]))
            hold_tps.append(len(hold_durs) / 30.0)
            hold_p50s.append(percentile_linear(hold_durs, 0.50))
        summary[pool_size] = {
            "steady_tp": statistics.mean(hold_tps),
            "steady_p50": statistics.mean(hold_p50s),
        }
    return summary


def format_pgfplotstable(macro_name: str, header: list[str], rows: list[list[str]]) -> list[str]:
    """Render a PGFPlots inline table macro definition."""
    lines = [f"\\pgfplotstableread{{"]
    lines.append("  " + " ".join(header))
    for row in rows:
        lines.append("  " + " ".join(row))
    lines.append(f"}}{macro_name}")
    return lines


def generate_tex_data(repo_root: Path = REPO_ROOT) -> str:
    """Build complete LaTeX/PGFPlots data source from verified repository artifacts."""
    recalc_csv = repo_root / "docs" / "evidence-freeze" / "metric-recalculations.csv"
    matrix_csv = repo_root / "docs" / "evidence-freeze" / "run-family-matrix.csv"
    results_dir = repo_root / "results"

    s1 = load_stratum1_trials(recalc_csv)
    s3 = load_stratum3_java21_trials(recalc_csv, matrix_csv, results_dir)
    s8_series = load_stratum8_series(results_dir)
    s8_k6 = summarize_stratum8_k6(results_dir)

    lines: list[str] = [
        "% Auto-generated by scripts/generate_thesis_figure_data.py",
        "% Do not edit manually; re-run the generator against frozen artifacts.",
        "",
    ]

    # Panel A tables (Stratum 1: y=3 synchronized, y=2 reentrant-lock, y=1 platform-sync)
    y_map = [
        ("payments-synchronized", "3"),
        ("payments-reentrant-lock", "2"),
        ("platform-synchronized", "1"),
    ]
    panel_a_macro = {
        "payments-synchronized": "\\tblChSixPanelASync",
        "payments-reentrant-lock": "\\tblChSixPanelALock",
        "platform-synchronized": "\\tblChSixPanelAPlat",
    }
    for cond, y_val in y_map:
        trials = s1[cond]
        rows = [[f"{t['steady_p50']:.2f}", y_val] for t in trials]
        lines.extend(format_pgfplotstable(panel_a_macro[cond], ["p50", "y"], rows))
        lines.append("")

    # Scalar summary annotations for Panel A
    sync_sd = statistics.stdev(t["steady_p50"] for t in s1["payments-synchronized"])
    lock_sd = statistics.stdev(t["steady_p50"] for t in s1["payments-reentrant-lock"])
    plat_sd = statistics.stdev(t["steady_p50"] for t in s1["platform-synchronized"])
    sync_tp = statistics.mean(t["steady_tp"] for t in s1["payments-synchronized"])
    lock_tp = statistics.mean(t["steady_tp"] for t in s1["payments-reentrant-lock"])
    plat_tp = statistics.mean(t["steady_tp"] for t in s1["platform-synchronized"])
    nolock_tp = statistics.mean(t["steady_tp"] for t in s1["no-lock"])
    nolock_p50 = statistics.mean(t["steady_p50"] for t in s1["no-lock"])

    lines.extend(
        [
            f"\\newcommand{{\\ChSixSyncSd}}{{{sync_sd:.2f}}}",
            f"\\newcommand{{\\ChSixLockSd}}{{{lock_sd:.2f}}}",
            f"\\newcommand{{\\ChSixPlatSd}}{{{plat_sd:.2f}}}",
            f"\\newcommand{{\\ChSixSyncTp}}{{{sync_tp:.3f}}}",
            f"\\newcommand{{\\ChSixLockTp}}{{{lock_tp:.3f}}}",
            f"\\newcommand{{\\ChSixPlatTp}}{{{plat_tp:.3f}}}",
            f"\\newcommand{{\\ChSixNoLockTp}}{{{nolock_tp:.3f}}}",
            f"\\newcommand{{\\ChSixNoLockPFifty}}{{{nolock_p50:.2f}}}",
            "",
        ]
    )

    # Panel B tables (Stratum 3 Java 21)
    s3_macros = {
        "blocking-jni": "\\tblChSixPanelBBlocking",
        "pure-java-sleep": "\\tblChSixPanelBSleep",
        "native-short": "\\tblChSixPanelBShort",
    }
    for cond, macro in s3_macros.items():
        rows = [[f"{t['cpu_pct']:.3f}", f"{t['steady_tp']:.4f}"] for t in s3[cond]]
        lines.extend(format_pgfplotstable(macro, ["cpu", "tp"], rows))
        lines.append("")

    for cond, prefix in [
        ("blocking-jni", "Jni"),
        ("pure-java-sleep", "Sleep"),
        ("native-short", "Short"),
    ]:
        mean_cpu = statistics.mean(t["cpu_pct"] for t in s3[cond])
        mean_tp = statistics.mean(t["steady_tp"] for t in s3[cond])
        lines.append(f"\\newcommand{{\\ChSix{prefix}Cpu}}{{{mean_cpu:.2f}}}")
        lines.append(f"\\newcommand{{\\ChSix{prefix}Tp}}{{{mean_tp:.2f}}}")
    lines.append("")

    # Panel C tables (Stratum 8 Treatment B HikariCP pending trajectories)
    pool_labels = {1: "One", 10: "Ten"}
    trial_suffix = ["A", "B", "C"]
    for pool_size, pool_name in pool_labels.items():
        for idx, trial in enumerate(s8_series[pool_size]):
            macro = f"\\tblChSixPool{pool_name}Trial{trial_suffix[idx]}"
            rows = [
                [f"{t_rel:.2f}", f"{pending:.1f}", f"{active:.1f}"]
                for t_rel, pending, active in trial["points"]
            ]
            lines.extend(format_pgfplotstable(macro, ["t", "pending", "active"], rows))
            lines.append("")

        peak = max(t["peak_pending"] for t in s8_series[pool_size])
        lines.append(f"\\newcommand{{\\ChSixPool{pool_name}Tp}}{{{s8_k6[pool_size]['steady_tp']:.2f}}}")
        lines.append(f"\\newcommand{{\\ChSixPool{pool_name}Peak}}{{{int(round(peak))}}}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Write overleaf/figures/ch6-strata-data.tex from verified repository artifacts."""
    out_path = REPO_ROOT / "overleaf" / "figures" / "ch6-strata-data.tex"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = generate_tex_data(REPO_ROOT)
    out_path.write_text(content, encoding="utf-8")
    print(f"Wrote {out_path} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
