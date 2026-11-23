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

from lib.presentation import page_heading
from lib.loaders import get_enriched_trials_df
from lib.transformations import (
    PALETTE,
    apply_dark_scientific_layout,
    compute_descriptive_stats,
    hover_card,
)

page_heading("02", "Synchronization Matrix")
st.markdown(
    "Evaluation of monitor pinning, carrier starvation, and lock serialization in Java 21 Spring Boot MVC. "
    "Investigates whether replacing `synchronized` with `ReentrantLock` resolves the application bottleneck."
)

# 1. Stratification and Filter Controls
st.sidebar.header("Synchronization Filters")
carrier_filter = st.sidebar.radio(
    "Carrier Scheduler Environment:",
    options=[
        "Stratum 1 · Single-carrier isolation",
        "Stratum 5 · Historical 8-carrier baseline",
    ],
    index=0,
)

is_stratum_1 = "Stratum 1" in carrier_filter
target_stratum_id = 1 if is_stratum_1 else 5
st.sidebar.caption("parallelism=1 · maxPoolSize=1" if is_stratum_1 else "parallelism=8 · maxPoolSize=256")

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
            <strong>Single carrier · Pinning fell from 108–110 events to zero</strong><br>
            With <code>synchronized</code> and <code>ReentrantLock</code>, hold-window throughput averaged
            <b>1.967</b> and <b>1.956 req/s</b>, respectively (Δ = 0.56%). Both averaged <b>1.964 req/s</b>
            over the full run. Median latency stayed near 4,982 ms. The 500 ms critical section continued
            to serialize requests after the refactor allowed carrier unmounting.
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
st.subheader("Throughput and carrier pinning")

# Diagnostic ceiling toggle
include_nolock = st.toggle(
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

# Horizontal offsets keep trials with identical measurements individually inspectable.
# Both panels use identical treatment positions and the original, unshifted y values.
treatment_colors = {
    "synchronized": PALETTE["condition_sync"], "reentrant-lock": PALETTE["condition_lock"],
    "platform-synchronized": PALETTE["condition_platform"], "no-lock": PALETTE["condition_nolock"],
}
treatment_ticks = {"platform-synchronized": "platform<br>synchronized", "reentrant-lock": "reentrant<br>lock"}


def treatment_panel(metric: str, title: str, axis_title: str, value: str, mean_value: str) -> go.Figure:
    means = plot_df.groupby("condition_id")[metric].mean().reindex(filtered_treatments)
    positions = list(range(len(filtered_treatments)))
    fig = go.Figure(go.Bar(
        x=positions, y=means.values, width=.56, opacity=.76,
        marker_color=[treatment_colors[t] for t in filtered_treatments],
        customdata=filtered_treatments, name="Treatment mean",
        hovertemplate=hover_card("%{customdata}", mean_value, "Treatment mean"),
    ))
    for i, treatment in enumerate(filtered_treatments):
        trials = plot_df[plot_df["condition_id"] == treatment]
        offsets = np.linspace(-.17, .17, len(trials)) if len(trials) > 1 else np.array([0.])
        fig.add_scatter(
            x=i + offsets, y=trials[metric], mode="markers", cliponaxis=False,
            marker=dict(size=9, color="#f4f9ff", line=dict(width=1.5, color=PALETTE["bg_dark"])),
            customdata=trials[["run_id", "trial_id"]], name=treatment,
            hovertemplate=hover_card(treatment, value, "Run %{customdata[0]} · Trial %{customdata[1]}",
                                     treatment_colors[treatment]),
        )
    apply_dark_scientific_layout(fig, title=title, height=365)
    fig.update_layout(showlegend=False, yaxis_title=axis_title)
    fig.update_xaxes(tickmode="array", tickvals=positions, layer="below traces",
                     ticktext=[treatment_ticks.get(t, t) for t in filtered_treatments],
                     range=[-.5, len(positions)-.5])
    return fig


st.caption("Bars show treatment means. Each white dot is one trial. Hover a dot for its run ID and recorded value.")
panel_col1, panel_col2 = st.columns(2)
with panel_col1:
    fig_tp = treatment_panel("steady_throughput", "Hold-window throughput", "Throughput (req/s)",
                             "%{y:.4f} req/s", "%{y:.4f} req/s")
    if include_nolock:
        fig_tp.add_hline(
            y=16.67, line_dash="dash", line_width=1.5, line_color=PALETTE["accent_purple"],
            annotation_text="Model ceiling · 16.67 req/s", annotation_position="bottom left",
            annotation_bgcolor=PALETTE["card_dark"],
        )
    else:
        fig_tp.update_yaxes(range=[0, 2.5])
    st.plotly_chart(fig_tp, width="stretch", theme=None)

with panel_col2:
    fig_jfr = treatment_panel("jfr_pinning_count", "JFR pinning events · ≥20 ms", "Recorded events",
                              "%{y:d} events", "%{y:.2f} events")
    st.plotly_chart(fig_jfr, width="stretch", theme=None)

# Diagnostic warning for no-lock
if include_nolock:
    st.markdown(
        """
        <div class="callout-warning">
            <b>Methodological Invariant Caveat: <code>no-lock</code> is Strictly Diagnostic</b><br>
            The <code>no-lock</code> treatment achieves steady throughput of &approx; 16.5 req/s 
            (theoretical closed-loop ceiling <code>X = N / (S + Z) = 10 / (0.500 + 0.100) = 16.67 req/s</code>)
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

    fig_lat = apply_dark_scientific_layout(fig_lat, title="Hold-window latency", height=350, hover_value="%{y:,.1f} ms")
    fig_lat.update_layout(barmode="group", yaxis_title="Latency (ms)", xaxis_title="Treatment")
    st.plotly_chart(fig_lat, width="stretch", theme=None)

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

with st.expander("Migration guidance · Mutex refactoring"):
    st.markdown(
        """
        <div class="callout-box callout-guidance">
            <b>Engineering Migration Guidance:</b><br>
            These empirical synchronization measurements form the evidentiary basis for
            <b>Rule 1: The Mutex Refactoring Rule</b> (<span class="badge badge-primary">CLM-MIG-01</span>) and
            <b>Pattern 1: Safe Mutex Refactoring</b>. Unpinning carrier threads only recovers carrier availability
            for unrelated work—it does not relieve endpoint serialization governed by Amdahl's Law.<br>
            <i>Explore interactive Amdahl capacity sizing and production-grade refactoring patterns in
            <a href="./migration_guidelines">Page 07 · Migration Guidelines</a>.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )
