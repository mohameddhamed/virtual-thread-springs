"""Page 2: Synchronization Experiments (Flagship Matrix)."""
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

from lib.loaders import get_enriched_trials_df
from lib.transformations import (
    PALETTE,
    aggregate_by_condition,
    apply_dark_scientific_layout,
    compute_descriptive_stats,
    format_latency_ms,
    format_throughput,
)

st.title("02 · Synchronization Matrix")
st.markdown(
    "Evaluation of monitor pinning, carrier starvation, and lock serialization in Java 21 Spring Boot MVC. "
    "Investigates whether replacing `synchronized` with `ReentrantLock` resolves the application bottleneck."
)

# 1. Stratification and Filter Controls
st.sidebar.header("Synchronization Filters")
carrier_filter = st.sidebar.radio(
    "Carrier Scheduler Environment:",
    options=[
        "Stratum 1 · Single-Carrier Mechanism Isolation (parallelism=1, maxPoolSize=1)",
        "Stratum 5 · Historical 8-Carrier Default Baseline (parallelism=8, maxPoolSize=256)",
    ],
    index=0,
)

is_stratum_1 = "Stratum 1" in carrier_filter
target_stratum_id = 1 if is_stratum_1 else 5

trials_df = get_enriched_trials_df()
sync_df = trials_df[trials_df["stratum_id"] == target_stratum_id].copy()

if sync_df.empty:
    st.warning("No trials matched the selected carrier filter.")
    st.stop()

# 2. Key Thesis Finding Callout
if is_stratum_1:
    st.markdown(
        """
        <div class="callout-box">
            <b>Core Thesis Finding: Decoupling of Carrier Unpinning from Application Serialization</b><br>
            Under single-carrier stress (<code>parallelism=1</code>), refactoring from <code>synchronized</code> 
            to <code>ReentrantLock</code> completely eliminated all <b>108–110 JFR pinning events</b> (dropping to strictly <b>0</b>), 
            allowing virtual threads to unmount during blocking.<br>
            However, <b>steady-state throughput remained virtually unchanged</b> (<b>1.967 req/s</b> vs. <b>1.956 req/s</b>, &Delta; = 0.56%; 
            whole-run throughput was 1.964 req/s for both), and median latency remained &approx; 4,982 ms.<br>
            <b>Scientific Takeaway:</b> The bottleneck was application-level serialization (the 500 ms mutual exclusion critical section governed by Amdahl's Law), 
            not carrier thread pinning.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="callout-box">
            <b>Stratum 5 Historical Baseline (8-Carrier Default Pool):</b><br>
            On an unconstrained 8-carrier scheduler, <code>synchronized</code> pins 1 carrier thread, leaving 7 carrier threads 
            available for other virtual threads. Latencies and throughput reflect multi-core scheduling headroom.<br>
            <i>Methodological Rule:</i> Historical 8-carrier measurements must remain strictly segregated from 1-carrier mechanism isolation.
        </div>
        """,
        unsafe_allow_html=True,
    )

# 3. Two-Panel Flagship Comparison (Steady-State Throughput vs JFR Pinning)
st.subheader("Flagship Comparison: Steady-State Throughput vs. JFR Pinning Events")

# Diagnostic ceiling toggle
include_nolock = st.checkbox(
    "Include diagnostic ceiling (no-lock · 16.5 req/s)",
    value=False,
    help="Toggle display of no-lock. Disabled by default so mutual-exclusion treatments (1.96-1.97 req/s) can be clearly inspected without axis compression.",
)

treatment_order = ["synchronized", "reentrant-lock", "platform-synchronized"]
if include_nolock:
    treatment_order.append("no-lock")

filtered_treatments = [t for t in treatment_order if t in sync_df["condition_id"].unique()]

plot_rows = []
for t in filtered_treatments:
    t_df = sync_df[sync_df["condition_id"] == t]
    for _, row in t_df.iterrows():
        plot_rows.append({
            "condition_id": t,
            "condition_label": row["condition_label"],
            "steady_throughput": row["steady_throughput"],
            "jfr_pinning_count": row["jfr_pinning_count"],
            "run_id": row["run_id"],
            "trial_id": row["trial_id"],
            "is_diagnostic": t == "no-lock",
        })
plot_df = pd.DataFrame(plot_rows)

panel_col1, panel_col2 = st.columns([1, 1])

with panel_col1:
    fig_tp = go.Figure()

    agg_df = plot_df.groupby("condition_id")["steady_throughput"].mean().reindex(filtered_treatments)
    colors = [
        PALETTE["condition_sync"] if t == "synchronized"
        else PALETTE["condition_lock"] if t == "reentrant-lock"
        else PALETTE["condition_platform"] if t == "platform-synchronized"
        else PALETTE["condition_nolock"]
        for t in filtered_treatments
    ]

    fig_tp.add_trace(
        go.Bar(
            x=filtered_treatments,
            y=agg_df.values,
            marker_color=colors,
            opacity=0.65,
            name="Mean Steady-State Throughput",
            hoverinfo="skip",
        )
    )

    # Individual trial scatter overlay
    for t in filtered_treatments:
        sub = plot_df[plot_df["condition_id"] == t]
        fig_tp.add_trace(
            go.Scatter(
                x=[t] * len(sub),
                y=sub["steady_throughput"],
                mode="markers",
                marker=dict(size=10, color="#ffffff", line=dict(width=1.5, color="#000000")),
                name=f"{t} trials",
                text=[f"Run: {r['run_id']}<br>Trial: {r['trial_id']}<br>TP: {r['steady_throughput']:.4f} req/s" for _, r in sub.iterrows()],
                hoverinfo="text",
                showlegend=False,
            )
        )

    if include_nolock:
        fig_tp.add_hline(
            y=16.67,
            line_dash="dash",
            line_color=PALETTE["accent_purple"],
            annotation_text="Theoretical Closed-Loop Ceiling: 16.67 req/s",
            annotation_position="top right",
        )

    fig_tp = apply_dark_scientific_layout(fig_tp, title="Steady-State Throughput (15s–45s Hold Window)", height=380)
    fig_tp.update_layout(yaxis_title="Throughput (req/s)", xaxis_title="Treatment Condition")
    if not include_nolock:
        fig_tp.update_layout(yaxis=dict(range=[0, 2.5]))
    st.plotly_chart(fig_tp, width="stretch")

with panel_col2:
    fig_jfr = go.Figure()

    agg_jfr = plot_df.groupby("condition_id")["jfr_pinning_count"].mean().reindex(filtered_treatments)

    fig_jfr.add_trace(
        go.Bar(
            x=filtered_treatments,
            y=agg_jfr.values,
            marker_color=colors,
            opacity=0.65,
            name="Mean JFR Pinning Events",
            hoverinfo="skip",
        )
    )

    # Overlay trial dots
    for t in filtered_treatments:
        sub = plot_df[plot_df["condition_id"] == t]
        fig_jfr.add_trace(
            go.Scatter(
                x=[t] * len(sub),
                y=sub["jfr_pinning_count"],
                mode="markers",
                marker=dict(size=10, color="#ffffff", line=dict(width=1.5, color="#000000")),
                name=f"{t} trials",
                text=[f"Run: {r['run_id']}<br>Trial: {r['trial_id']}<br>Pinning Events: {int(r['jfr_pinning_count'])}" for _, r in sub.iterrows()],
                hoverinfo="text",
                showlegend=False,
            )
        )

    fig_jfr = apply_dark_scientific_layout(fig_jfr, title="JFR jdk.VirtualThreadPinned Events (>= 20ms)", height=380)
    fig_jfr.update_layout(yaxis_title="Pinning Event Count", xaxis_title="Treatment Condition")
    st.plotly_chart(fig_jfr, width="stretch")

# Diagnostic warning for no-lock
if include_nolock:
    st.markdown(
        """
        <div class="callout-warning">
            <b>Methodological Invariant Caveat: <code>no-lock</code> is Strictly Diagnostic</b><br>
            The <code>no-lock</code> treatment achieves steady throughput of &approx; 16.5 req/s 
            (closely matching the theoretical closed-loop ceiling $X = N / (S + Z) = 10 / (0.500 + 0.100) = 16.67\\text{ req/s}$) 
            because it completely bypasses mutual exclusion. It violates transactional safety and payment state consistency. 
            It is plotted solely as a theoretical unconstrained hardware ceiling, not an operational design candidate.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# 4. Latency Percentiles Comparison
st.subheader("Latency Percentiles Across Treatments")

lat_col1, lat_col2 = st.columns([1, 1])

with lat_col1:
    agg_lat = sync_df[sync_df["condition_id"] != "no-lock"].groupby("condition_id").agg(
        p50=("steady_p50", "mean"),
        p95=("steady_p95", "mean"),
        p99=("steady_p99", "mean"),
    ).reset_index()

    fig_lat = go.Figure()
    fig_lat.add_trace(go.Bar(x=agg_lat["condition_id"], y=agg_lat["p50"], name="p50 (Median)", marker_color=PALETTE["accent_blue"]))
    fig_lat.add_trace(go.Bar(x=agg_lat["condition_id"], y=agg_lat["p95"], name="p95", marker_color=PALETTE["accent_amber"]))
    fig_lat.add_trace(go.Bar(x=agg_lat["condition_id"], y=agg_lat["p99"], name="p99", marker_color=PALETTE["accent_red"]))

    fig_lat = apply_dark_scientific_layout(fig_lat, title="Steady-State Latency Percentiles (p50 / p95 / p99)", height=350)
    fig_lat.update_layout(barmode="group", yaxis_title="Latency (ms)", xaxis_title="Treatment")
    st.plotly_chart(fig_lat, width="stretch")

with lat_col2:
    st.markdown(
        """
        ### Latency Dispersion & Non-Fair Barging Signature
        While median latency (p50) is indistinguishable between `synchronized` and `ReentrantLock` 
        (within 0.31%), **within-treatment dispersion** reveals an architectural difference:
        
        * **`synchronized` (JVM Object Monitor):** Exhibits tight, deterministic queue order 
          (spread &le; 7.4 ms, &sigma; &le; 3.6 ms).
        * **`ReentrantLock` (`NonfairSync`):** Exhibits wider latency dispersion 
          (spread &approx; 16–30 ms, &sigma; &approx; 13–18 ms) due to barging in Java's 
          `AbstractQueuedSynchronizer` (AQS), where newly arriving threads acquire the lock 
          before parked threads wake up.
        """
    )
    disp_rows = []
    for cond in ["synchronized", "reentrant-lock"]:
        c_sub = sync_df[sync_df["condition_id"] == cond]
        if not c_sub.empty:
            p50_stats = compute_descriptive_stats(c_sub["steady_p50"])
            p95_stats = compute_descriptive_stats(c_sub["steady_p95"])
            disp_rows.append({
                "Treatment": cond,
                "Trials (N)": p50_stats["count"],
                "p50 Mean (ms)": p50_stats["mean"],
                "p50 Spread (ms)": p50_stats["spread"],
                "p50 Std Dev (ms)": p50_stats["std"],
                "p95 Mean (ms)": p95_stats["mean"],
                "p95 Spread (ms)": p95_stats["spread"],
                "p95 Std Dev (ms)": p95_stats["std"],
            })
    st.dataframe(pd.DataFrame(disp_rows), hide_index=True, width="stretch")

st.markdown("---")

# 5. Dual-Window Reporting Ledger
st.subheader("Dual-Window Measurement Ledger (Whole-Run vs. Hold-Window)")
st.markdown(
    "Preserving both the **Full Run [0, 55s]** and **Steady-State Hold [15, 45s]** windows. "
    "The hold window is a selected constant-concurrency sampling interval, not proof of statistical equilibrium."
)

table_cols = [
    "run_id", "trial_id", "condition_id",
    "full_throughput", "steady_throughput", "throughput_delta_pct",
    "full_p50", "steady_p50", "p50_delta_pct",
    "steady_p95", "jfr_pinning_count",
]
display_df = sync_df[table_cols].copy()
display_df = display_df.rename(
    columns={
        "run_id": "Run ID",
        "trial_id": "Trial",
        "condition_id": "Condition",
        "full_throughput": "Full TP (req/s)",
        "steady_throughput": "Hold TP (req/s)",
        "throughput_delta_pct": "TP Δ (%)",
        "full_p50": "Full p50 (ms)",
        "steady_p50": "Hold p50 (ms)",
        "p50_delta_pct": "p50 Δ (%)",
        "steady_p95": "Hold p95 (ms)",
        "jfr_pinning_count": "JFR Pins",
    }
)
st.dataframe(display_df, hide_index=True, width="stretch")
