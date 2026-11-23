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

from lib.presentation import page_heading
from lib.loaders import get_enriched_trials_df, load_telemetry_series
from lib.transformations import (
    PALETTE,
    apply_dark_scientific_layout,
    compute_descriptive_stats,
    format_latency_ms,
    hover_card,
    shade_workload_stages,
)

page_heading("04", "JNI Native Blocking Boundary")
st.markdown(
    "Investigation of carrier thread captivity during native C blocking calls (`nanosleep`). "
    "Demonstrates why JFR pinning events fail to detect OS-level carrier thread stalls."
)

# 1. Architectural Callout
st.markdown(
    """
    <div class="callout-box">
        <strong>Blocking JNI · Zero JFR pinning events with the carrier occupied</strong><br>
        During <code>nanosleep()</code>, the single carrier stays in <code>_thread_in_native</code>.
        Throughput averaged approximately <b>1.97 req/s</b>, latency reached approximately <b>4,960 ms</b>,
        and hold-window CPU across blocking JNI trials averaged <b>1.04%</b>.
        The native call bypasses <code>Continuation.yield()</code>, so the stall produces no
        <code>jdk.VirtualThreadPinned</code> event.
    </div>
    """,
    unsafe_allow_html=True,
)

trials_df = get_enriched_trials_df()
jni_df = trials_df[trials_df["stratum_id"] == 3].copy()

# 2. Time-Series Telemetry Visualization
st.subheader("Process CPU over the 55-second run")
st.markdown(
    "Process CPU sampled once per second with `ps -p $PID -o %cpu=`. The dashed line marks the selected trial’s hold-window mean."
)

blocking_trials = jni_df[jni_df["condition_id"] == "blocking-jni"]
run_options = blocking_trials["run_id"].tolist()

selected_run = st.selectbox(
    "Native-blocking trial",
    options=run_options,
    format_func=lambda rid: f"Run {rid} (JDK 21, Trial {blocking_trials[blocking_trials['run_id'] == rid]['trial_id'].iloc[0]})",
    index=0,
)

telemetry_df = load_telemetry_series(selected_run)

if telemetry_df is not None and not telemetry_df.empty:
    fig_telemetry = go.Figure()

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

    shade_workload_stages(fig_telemetry)

    # Compute hold window average CPU
    hold_cpu = telemetry_df[(telemetry_df["elapsed_s"] >= 15) & (telemetry_df["elapsed_s"] <= 45)]["cpu_percent"].mean()
    fig_telemetry.add_hline(
        y=hold_cpu,
        line_dash="dash",
        line_color=PALETTE["accent_amber"],
        annotation_text=f"Hold mean · {hold_cpu:.2f}%",
        annotation_position="top right", annotation_bgcolor=PALETTE["card_dark"],
        annotation_font_color=PALETTE["accent_amber"], line_width=1.5,
    )

    fig_telemetry = apply_dark_scientific_layout(fig_telemetry, title=f"Process CPU · {selected_run}", height=380)
    fig_telemetry.update_layout(xaxis_title="Elapsed Execution Time (seconds)", yaxis_title="Process CPU Utilization (%)")
    fig_telemetry.update_traces(hovertemplate=hover_card("Process CPU", "%{y:.2f}%", "Elapsed · %{x:.1f} s", PALETTE["accent_cyan"]))
    st.plotly_chart(fig_telemetry, width="stretch", theme=None)
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
    fig_tp = apply_dark_scientific_layout(fig_tp, title="Hold-window throughput", height=350, hover_value="%{y:,.4f} req/s")
    fig_tp.update_layout(yaxis_title="Throughput (req/s)")
    st.plotly_chart(fig_tp, width="stretch", theme=None)

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
    fig_p50 = apply_dark_scientific_layout(fig_p50, title="Hold-window median latency", height=350, hover_value="%{y:,.1f} ms")
    fig_p50.update_layout(yaxis_title="Latency (ms)")
    st.plotly_chart(fig_p50, width="stretch", theme=None)

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

with st.expander("Migration guidance · Native isolation"):
    st.markdown(
        """
        <div class="callout-box callout-guidance">
            <b>Engineering Migration Guidance:</b><br>
            The discovery of silent carrier starvation across foreign function boundaries establishes
            <b>Rule 2: The Native JNI Isolation Rule</b> (<span class="badge badge-primary">CLM-MIG-02</span>) and
            <b>Pattern 2: Platform Thread Offloading with AbortPolicy</b>. Foreign native calls that can block
            must never execute directly on virtual threads; they must be offloaded to dedicated bounded platform executors.<br>
            <i>Inspect the complete refactored executor configuration, CallerRunsPolicy trap analysis, and POSIX
            cancellation semantics in <a href="./migration_guidelines">Page 07 · Migration Guidelines</a>.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )
