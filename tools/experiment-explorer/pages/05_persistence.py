"""Page 5: Relational Database Persistence Experiments."""
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
from lib.loaders import load_persistence_experiments
from lib.transformations import (
    PALETTE,
    apply_dark_scientific_layout,
    format_latency_ms,
    format_throughput,
)

page_heading("05", "Database Connection Contention")
st.markdown(
    "Evaluation of relational database access under Virtual Threads. Contrasts "
    "**Treatment A (pre-acquisition delay control; pool >98% idle)** against "
    "**Treatment B (active connection contention via `ConnectionCallback`)**."
)

# 1. Methodological Safeguard Callout
st.markdown(
    """
    <div class="callout-box">
        <b>Methodological Safeguard: Distinguishing Treatment A from Treatment B</b><br>
        <b>Treatment A (Stratum 7 · Excluded for Contention):</b> In initial persistence pilots, the synthetic delay 
        occurred <i>before</i> acquiring a JDBC connection (or pre-query sleep). The HikariCP pool was &gt;98% idle, 
        evaluating virtual thread sleep unmounting rather than connection contention (throughput &approx; 123 req/s regardless of pool size).<br>
        <b>Treatment B (Stratum 8 · Admitted Primary Ablation):</b> In <code>java21-orders-persistence-contention</code>, 
        the database connection was held across a 300 ms blocking delay via <code>ConnectionCallback</code> under 50 concurrent VUs. 
        Throughput strictly collapsed to Little's Law capacity ceiling (<code>X = K / T<sub>hold</sub></code>):
        <b>3.27 req/s for Pool 1</b> vs. <b>32.60 req/s for Pool 10</b> (9.97× scaling).<br>
        <i>Zero JFR pinning events</i> confirmed virtual threads unmounted cleanly via HikariCP's <code>LockSupport.parkNanos()</code>, 
        shifting the bottleneck from carrier threads to the database connection pool.
    </div>
    """,
    unsafe_allow_html=True,
)

pers_records = load_persistence_experiments()
df_pers = pd.DataFrame([r.__dict__ for r in pers_records])

# 2. Side-by-Side Visualizations (Throughput and Latency)
st.subheader("Factorial Comparison: Pool 1 vs. Pool 10 Across Treatments")

comp_col1, comp_col2 = st.columns([1, 1])

# Aggregate means for Plotly
tp_summary = df_pers.groupby(["treatment", "pool_size"])["hold_tp"].mean().reset_index()
p50_summary = df_pers.groupby(["treatment", "pool_size"])["hold_p50"].mean().reset_index()

with comp_col1:
    fig_tp = go.Figure()

    # Treatment A (Stratum 7)
    t_a_tp = tp_summary[tp_summary["treatment"].str.contains("Treatment A")]
    fig_tp.add_trace(
        go.Bar(
            name="A · Excluded control",
            x=["Pool 1", "Pool 10"],
            y=t_a_tp["hold_tp"],
            marker_color=PALETTE["accent_amber"],
            text=[f"{v:.2f} req/s" for v in t_a_tp["hold_tp"]],
            textposition="auto",
        )
    )

    # Treatment B (Stratum 8)
    t_b_tp = tp_summary[tp_summary["treatment"].str.contains("Treatment B")]
    fig_tp.add_trace(
        go.Bar(
            name="B · Active contention",
            x=["Pool 1", "Pool 10"],
            y=t_b_tp["hold_tp"],
            marker_color=PALETTE["accent_blue"],
            text=[f"{v:.2f} req/s" for v in t_b_tp["hold_tp"]],
            textposition="auto",
        )
    )

    fig_tp = apply_dark_scientific_layout(fig_tp, title="Hold-window throughput", height=360, hover_value="%{y:,.4f} req/s")
    fig_tp.update_layout(barmode="group", yaxis_title="Throughput (req/s)", xaxis_title="HikariCP Pool Size")
    st.plotly_chart(fig_tp, width="stretch", theme=None)

with comp_col2:
    fig_lat = go.Figure()

    t_a_p50 = p50_summary[p50_summary["treatment"].str.contains("Treatment A")]
    fig_lat.add_trace(
        go.Bar(
            name="A · Excluded control",
            x=["Pool 1", "Pool 10"],
            y=t_a_p50["hold_p50"],
            marker_color=PALETTE["accent_amber"],
            text=[f"{v:.0f} ms" for v in t_a_p50["hold_p50"]],
            textposition="auto",
        )
    )

    t_b_p50 = p50_summary[p50_summary["treatment"].str.contains("Treatment B")]
    fig_lat.add_trace(
        go.Bar(
            name="B · Active contention",
            x=["Pool 1", "Pool 10"],
            y=t_b_p50["hold_p50"],
            marker_color=PALETTE["accent_blue"],
            text=[f"{v:.0f} ms" for v in t_b_p50["hold_p50"]],
            textposition="auto",
        )
    )

    fig_lat = apply_dark_scientific_layout(fig_lat, title="Hold-window median latency", height=360, hover_value="%{y:,.1f} ms")
    fig_lat.update_layout(barmode="group", yaxis_title="Median Latency (ms)", xaxis_title="HikariCP Pool Size")
    st.plotly_chart(fig_lat, width="stretch", theme=None)

st.markdown("---")

# 3. HikariCP Connection Pool Telemetry (Stratum 8 Deep-Dive)
st.subheader("HikariCP Pool Telemetry Under Active Contention (Stratum 8)")
st.markdown(
    "Real-time pool instrumentation via Spring Boot Actuator sampled at 1-second intervals during Treatment B runs."
)

s8_df = df_pers[df_pers["treatment"].str.contains("Treatment B")].copy()

kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
with kpi_c1:
    st.metric("Pool 1 Throughput", "3.27 req/s", help="Little's Law ceiling: 1 conn / 0.300s = 3.33 req/s")
with kpi_c2:
    st.metric("Pool 10 Throughput", "32.60 req/s", help="Little's Law ceiling: 10 conn / 0.300s = 33.33 req/s")
with kpi_c3:
    st.metric("Queue Saturation", "40–49 VUs", help="Peak virtual threads queued in HikariCP ConcurrentBag")
with kpi_c4:
    st.metric("Connection Timeouts", "0", help="Zero connection acquisition timeouts across all trials")

# Table of all persistence trials
st.markdown("### Trial-by-Trial Persistence Ledger")

disp_table = df_pers[[
    "treatment", "pool_size", "trial", "run_id",
    "whole_tp", "hold_tp", "whole_p50", "hold_p50",
    "mean_active", "peak_pending", "status",
]].copy()

disp_table = disp_table.rename(
    columns={
        "treatment": "Treatment",
        "pool_size": "Pool",
        "trial": "Trial",
        "run_id": "Run ID",
        "whole_tp": "Whole TP",
        "hold_tp": "Hold TP",
        "whole_p50": "Whole p50",
        "hold_p50": "Hold p50",
        "mean_active": "Active Conns",
        "peak_pending": "Peak Queue",
        "status": "Admission Classification",
    }
)

st.dataframe(disp_table, hide_index=True, width="stretch", column_config={
    "Peak Queue": st.column_config.ProgressColumn(
        "Peak queue (VUs)", min_value=0, max_value=50, format="%.0f", color=PALETTE["accent_amber"],
        help="Peak waiting clients on the 50-VU workload scale",
    ),
    "Whole TP": st.column_config.NumberColumn("Full TP (req/s)", format="%.2f"),
    "Hold TP": st.column_config.NumberColumn("Hold TP (req/s)", format="%.2f"),
    "Whole p50": st.column_config.NumberColumn("Full p50 (ms)", format="%.2f"),
    "Hold p50": st.column_config.NumberColumn("Hold p50 (ms)", format="%.2f"),
})

with st.expander("Migration guidance · Pool sizing"):
    st.markdown(
        """
        <div class="callout-box callout-guidance">
            <b>Engineering Migration Guidance:</b><br>
            Stratum 8's Downstream Bottleneck Shift provides the direct empirical foundation for
            <b>Rule 3: The Connection Pool Sizing Fallacy</b> (<span class="badge badge-primary">CLM-MIG-03</span>).
            Do not scale database connection pools proportionally to virtual thread concurrency; size within database hardware
            capacity and enforce application-level semaphores and workload-aligned timeouts.<br>
            <i>Explore the interactive HikariCP Pool Sizing Calculator with Wooldridge hardware bounds in
            <a href="./migration_guidelines">Page 07 · Migration Guidelines</a>.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )
