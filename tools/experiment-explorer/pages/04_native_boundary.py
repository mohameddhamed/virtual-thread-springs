"""Page 4: JNI / Native Blocking Boundary Experiments."""
import sys
from pathlib import Path

# Ensure explorer root is in path
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.loaders import get_enriched_trials_df, load_telemetry_series
from lib.transformations import (
    PALETTE,
    apply_dark_scientific_layout,
    compute_descriptive_stats,
    format_latency_ms,
    format_throughput,
)

st.title("04 · JNI Native Blocking Boundary")
st.markdown(
    "Investigation of carrier thread captivity during native C blocking calls (`nanosleep`). "
    "Demonstrates why JFR pinning events fail to detect OS-level carrier thread stalls."
)

# 1. Architectural Callout
st.markdown(
    """
    <div class="callout-box">
        <b>The Silent Carrier Starvation Discovery:</b><br>
        When Java virtual threads execute native C methods that make blocking OS system calls (e.g. <code>nanosleep()</code>), 
        the carrier thread remains held captive in native state (<code>_thread_in_native</code>) for the full duration.<br>
        Under a single-carrier scheduler (<code>parallelism=1</code>), this completely starves the carrier pool, 
        bounding throughput to <b>&approx; 1.97 req/s</b> and inflating latency to <b>&approx; 4,960 ms</b>.<br>
        <b>The Critical Diagnostic Trap:</b> HotSpot's Flight Recorder emitted <b>strictly 0 <code>jdk.VirtualThreadPinned</code> events</b>, 
        while steady-state CPU utilization averaged only <b>1.04%</b>.<br>
        <i>Why?</i> Native code never calls <code>Continuation.yield()</code>; therefore HotSpot's continuation unmount 
        subsystem is completely bypassed.
    </div>
    """,
    unsafe_allow_html=True,
)

trials_df = get_enriched_trials_df()
jni_df = trials_df[trials_df["stratum_id"] == 3].copy()

# 2. Time-Series Telemetry Visualization
st.subheader("Time-Series Telemetry: Process CPU Utilization (55-Second Execution)")
st.markdown(
    "Companion host CPU telemetry sampled at 1-second intervals via `ps -p $PID -o %cpu=`. "
    "Select any native-blocking trial to inspect its CPU profile."
)

blocking_trials = jni_df[jni_df["condition_id"] == "blocking-jni"]
run_options = blocking_trials["run_id"].tolist()

selected_run = st.selectbox(
    "Select Native Blocking Trial for Telemetry Inspection:",
    options=run_options,
    format_func=lambda rid: f"Run {rid} (JDK 21, Trial {blocking_trials[blocking_trials['run_id'] == rid]['trial_id'].iloc[0]})",
    index=0,
)

telemetry_df = load_telemetry_series(selected_run)

if telemetry_df is not None and not telemetry_df.empty:
    fig_telemetry = go.Figure()

    # Shade the 3 staged profile regions
    # 0 - 15s Ramp-up
    fig_telemetry.add_vrect(
        x0=0, x1=15,
        fillcolor="rgba(88, 166, 255, 0.08)",
        layer="below", line_width=0,
        annotation_text="Ramp-Up (0-15s)",
        annotation_position="top left",
        annotation_font=dict(color=PALETTE["text_muted"], size=10),
    )
    # 15 - 45s Hold Window (Steady-State)
    fig_telemetry.add_vrect(
        x0=15, x1=45,
        fillcolor="rgba(57, 197, 187, 0.12)",
        layer="below", line_width=0,
        annotation_text="Steady Hold Window (15-45s)",
        annotation_position="top left",
        annotation_font=dict(color=PALETTE["accent_cyan"], size=10),
    )
    # 45 - 55s Ramp-Down
    fig_telemetry.add_vrect(
        x0=45, x1=55,
        fillcolor="rgba(139, 148, 158, 0.08)",
        layer="below", line_width=0,
        annotation_text="Ramp-Down (45-55s)",
        annotation_position="top left",
        annotation_font=dict(color=PALETTE["text_muted"], size=10),
    )

    # Plot CPU percentage series
    fig_telemetry.add_trace(
        go.Scatter(
            x=telemetry_df["elapsed_s"],
            y=telemetry_df["cpu_percent"],
            mode="lines+markers",
            name="JVM Process CPU %",
            line=dict(color=PALETTE["accent_cyan"], width=2.5),
            marker=dict(size=4),
        )
    )

    # Compute hold window average CPU
    hold_cpu = telemetry_df[(telemetry_df["elapsed_s"] >= 15) & (telemetry_df["elapsed_s"] <= 45)]["cpu_percent"].mean()
    fig_telemetry.add_hline(
        y=hold_cpu,
        line_dash="dash",
        line_color=PALETTE["accent_amber"],
        annotation_text=f"Steady-State Mean CPU: {hold_cpu:.2f}%",
        annotation_position="bottom right",
    )

    fig_telemetry = apply_dark_scientific_layout(fig_telemetry, title=f"CPU Utilization Profile: Run {selected_run}", height=380)
    fig_telemetry.update_layout(xaxis_title="Elapsed Execution Time (seconds)", yaxis_title="Process CPU Utilization (%)")
    st.plotly_chart(fig_telemetry, width="stretch")
else:
    st.info(f"No telemetry series found on disk for run {selected_run}.")

st.markdown("---")

# 3. Native JNI Comparison Matrix (blocking-jni vs native-short vs pure-java-sleep)
st.subheader("Comparison Across Native Boundary Conditions")

comp_col1, comp_col2 = st.columns([1, 1])

# Aggregate conditions in Stratum 3
conditions = ["blocking-jni", "pure-java-sleep", "native-short"]
agg_tp = jni_df.groupby("condition_id")["steady_throughput"].mean().reindex(conditions)
agg_p50 = jni_df.groupby("condition_id")["steady_p50"].mean().reindex(conditions)

with comp_col1:
    fig_tp = go.Figure()
    fig_tp.add_trace(
        go.Bar(
            x=["Blocking JNI (500ms)", "Pure Java Sleep (500ms)", "Short JNI (1ms)"],
            y=agg_tp.values,
            marker_color=[PALETTE["accent_red"], PALETTE["accent_blue"], PALETTE["accent_cyan"]],
            text=[f"{v:.2f} req/s" for v in agg_tp.values],
            textposition="auto",
        )
    )
    fig_tp = apply_dark_scientific_layout(fig_tp, title="Steady-State Throughput (req/s)", height=350)
    fig_tp.update_layout(yaxis_title="Throughput (req/s)")
    st.plotly_chart(fig_tp, width="stretch")

with comp_col2:
    fig_p50 = go.Figure()
    fig_p50.add_trace(
        go.Bar(
            x=["Blocking JNI (500ms)", "Pure Java Sleep (500ms)", "Short JNI (1ms)"],
            y=agg_p50.values,
            marker_color=[PALETTE["accent_red"], PALETTE["accent_blue"], PALETTE["accent_cyan"]],
            text=[f"{v:.1f} ms" for v in agg_p50.values],
            textposition="auto",
        )
    )
    fig_p50 = apply_dark_scientific_layout(fig_p50, title="Median Steady-State Latency (p50 ms)", height=350)
    fig_p50.update_layout(yaxis_title="Latency (ms)")
    st.plotly_chart(fig_p50, width="stretch")

st.markdown("---")

# 4. Multi-Condition Summary Ledger (Dual-Window Reporting Preserved)
st.subheader("Multi-Condition Empirical Ledger (Stratum 3 · 27 Runs)")
st.markdown(
    "Preserving both the **Full Run [0, 55s]** and **Steady-State Hold [15, 45s]** windows. "
    "In ramping workloads like `pure-java-sleep`, hold throughput (16.5 req/s) is ~27% higher than whole-run throughput (12.98 req/s)."
)

table_rows = []
for c in conditions:
    sub = jni_df[jni_df["condition_id"] == c]
    tp_stats = compute_descriptive_stats(sub["steady_throughput"])
    full_tp_stats = compute_descriptive_stats(sub["full_throughput"])
    p50_stats = compute_descriptive_stats(sub["steady_p50"])
    full_p50_stats = compute_descriptive_stats(sub["full_p50"])
    p95_stats = compute_descriptive_stats(sub["steady_p95"])
    jfr_events = int(sub["jfr_pinning_count"].iloc[0]) if not sub.empty else 0

    table_rows.append({
        "Condition": c,
        "Trials (N)": tp_stats["count"],
        "Full TP [0,55s] (req/s)": f"{full_tp_stats['mean']:.4f} ± {full_tp_stats['std']:.4f}",
        "Hold TP [15,45s] (req/s)": f"{tp_stats['mean']:.4f} ± {tp_stats['std']:.4f}",
        "Full p50 (ms)": f"{full_p50_stats['mean']:.1f} ± {full_p50_stats['std']:.1f}",
        "Hold p50 (ms)": f"{p50_stats['mean']:.1f} ± {p50_stats['std']:.1f}",
        "Hold p95 (ms)": f"{p95_stats['mean']:.1f} ± {p95_stats['std']:.1f}",
        "JFR Pinning Events": jfr_events,
        "Steady-State CPU %": "1.04% ± 0.12%" if c == "blocking-jni" else "N/A",
    })

st.dataframe(pd.DataFrame(table_rows), hide_index=True, width="stretch")
