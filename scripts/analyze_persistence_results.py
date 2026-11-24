#!/usr/bin/env python3
import json
import glob
import re
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Manifest timestamps for the 6 runs:
RUNS = [
    # Pool 1
    {"pool": 1, "trial": 1, "timestamp": "20261110-160949"},
    {"pool": 1, "trial": 2, "timestamp": "20261110-161109"},
    {"pool": 1, "trial": 3, "timestamp": "20261110-161227"},
    # Pool 10
    {"pool": 10, "trial": 1, "timestamp": "20261110-161344"},
    {"pool": 10, "trial": 2, "timestamp": "20261110-161451"},
    {"pool": 10, "trial": 3, "timestamp": "20261110-161559"},
]

def parse_iso8601(s):
    # e.g. 2026-11-10T15:10:00.123456+01:00 or Z
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)

def analyze_k6_json(json_path):
    durations_all = []
    durations_hold = []
    
    t0 = None
    timestamps = []
    initiation_times = []
    
    # First pass: find t0 (earliest request initiation)
    with open(json_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            if record.get("metric") == "orders_duration" and record.get("type") == "Point":
                val = float(record["data"]["value"])
                t_str = record["data"]["time"]
                t = parse_iso8601(t_str)
                timestamps.append(t)
                initiation_times.append(t - timedelta(milliseconds=val))
    
    if not timestamps:
        return {}
    
    t0 = min(initiation_times) if initiation_times else min(timestamps)
    t_max = max(timestamps)
    actual_span_s = (t_max - t0).total_seconds() if t_max else 55.0
    
    with open(json_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            if record.get("metric") == "orders_duration" and record.get("type") == "Point":
                val = float(record["data"]["value"])
                t_str = record["data"]["time"]
                t = parse_iso8601(t_str)
                rel_sec = (t - t0).total_seconds()
                
                durations_all.append(val)
                if 15.0 <= rel_sec <= 45.0:
                    durations_hold.append(val)
                    
    total_reqs = len(durations_all)
    hold_reqs = len(durations_hold)
    
    whole_tp = total_reqs / (actual_span_s if actual_span_s > 0 else 55.0)
    hold_tp = hold_reqs / 30.0
    
    return {
        "total_reqs": total_reqs,
        "hold_reqs": hold_reqs,
        "whole_tp": whole_tp,
        "hold_tp": hold_tp,
        "whole_p50": np.percentile(durations_all, 50) if durations_all else 0,
        "whole_p95": np.percentile(durations_all, 95) if durations_all else 0,
        "whole_p99": np.percentile(durations_all, 99) if durations_all else 0,
        "hold_p50": np.percentile(durations_hold, 50) if durations_hold else 0,
        "hold_p95": np.percentile(durations_hold, 95) if durations_hold else 0,
        "hold_p99": np.percentile(durations_hold, 99) if durations_hold else 0,
    }

def analyze_pool_telemetry(csv_path):
    active_vals = []
    pending_vals = []
    timeouts = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        headers = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 7: continue
            try:
                a = float(parts[1]) if parts[1] != "unknown" else 0.0
                p = float(parts[4]) if parts[4] != "unknown" else 0.0
                to = float(parts[6]) if parts[6] != "unknown" else 0.0
                active_vals.append(a)
                pending_vals.append(p)
                timeouts.append(to)
            except ValueError:
                continue
    return {
        "mean_active": np.mean(active_vals) if active_vals else 0,
        "max_active": np.max(active_vals) if active_vals else 0,
        "mean_pending": np.mean(pending_vals) if pending_vals else 0,
        "peak_pending": np.max(pending_vals) if pending_vals else 0,
        "total_timeouts": np.max(timeouts) if timeouts else 0,
    }

def main():
    results = []
    for run in RUNS:
        ts = run["timestamp"]
        k6_path = f"results/run-50vus-{ts}.json"
        pool_path = f"results/pool-telemetry-{ts}.csv"
        
        k6_res = analyze_k6_json(k6_path)
        pool_res = analyze_pool_telemetry(pool_path)
        
        entry = {**run, **k6_res, **pool_res}
        results.append(entry)
        
    print("=" * 105)
    print("DUAL-WINDOW LATENCY COMPARISON:")
    print("=" * 105)
    print(f"{'Condition':<15} | {'Trial':<6} | {'Whole p50':<11} | {'Hold p50':<11} | {'Delta (%)':<10} | {'Whole p95':<11} | {'Hold p95':<11}")
    print("=" * 105)
    for r in results:
        cond = f"pool-{r['pool']}"
        delta = (r['hold_p50'] - r['whole_p50']) / r['hold_p50'] * 100 if r['hold_p50'] else 0
        print(f"{cond:<15} | {r['trial']:<6} | {r['whole_p50']:<11.2f} | {r['hold_p50']:<11.2f} | {delta:<10.2f} | {r['whole_p95']:<11.2f} | {r['hold_p95']:<11.2f}")
    print("=" * 105)
    print()
    print("=" * 105)
    print("THROUGHPUT AND HIKARICP POOL TELEMETRY SUMMARY:")
    print("=" * 105)
    print(f"{'Condition':<15} | {'Trial':<6} | {'Whole TP':<9} | {'Hold TP':<9} | {'Hold p50':<9} | {'Hold p95':<9} | {'Act/Max':<7} | {'Peak Pend':<9} | {'Timeouts':<8}")
    print("=" * 105)
    for r in results:
        cond = f"pool-{r['pool']}"
        print(f"{cond:<15} | {r['trial']:<6} | {r['whole_tp']:<9.2f} | {r['hold_tp']:<9.2f} | {r['hold_p50']:<9.2f} | {r['hold_p95']:<9.2f} | {r['mean_active']:.1f}/{r['max_active']:.0f}   | {r['peak_pending']:<9.0f} | {r['total_timeouts']:<8.0f}")
    print("=" * 105)

if __name__ == "__main__":
    main()
