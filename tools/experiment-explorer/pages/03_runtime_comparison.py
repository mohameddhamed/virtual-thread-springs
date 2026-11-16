"""Page 3: Runtime Evolution (Java 21 vs. Java 24 / JEP 491)."""
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
    apply_dark_scientific_layout,
    compute_descriptive_stats,
    format_latency_ms,
    format_throughput,
)

st.title("03 · Runtime Evolution: Java 21 vs. Java 24")
st.markdown(
    "Empirical evaluation of **JEP 491 (Synchronize Virtual Threads without Pinning)**. "
    "Compares OpenJDK 21.0.8 LTS against OpenJDK 24.0.2 under identical single-carrier stress."
)

# 1. Architectural Context Callout
st.markdown(
    """
    <div class="callout-box">
        <b>JEP 491 Specification & Architectural Mechanics:</b><br>
        In Java 21, entering a <code>synchronized</code> block or calling <code>Object.wait()</code> pinned the virtual thread 
        to its carrier thread because HotSpot's object monitor implementation could not yield the underlying continuation.<br>
        <b>Java 24 (JEP 491)</b> redesigned the object monitor subsystem to support continuation parking (yielding the carrier).<br>
        <b>The Core Finding:</b> JEP 491 completely removes JVM carrier pinning (<b>108 &rarr; 0 pinning events</b>), 
        but does <b>not magically eliminate application-level serialization bottlenecks</b>. 
        Throughput remains strictly bound to &approx; 1.97 req/s by Amdahl's Law.
    </div>
    """,
    unsafe_allow_html=True,
)

trials_df = get_enriched_trials_df()

# Filter for the relevant Java 21 vs Java 24 comparison sets:
# Java 21: java21-primary-repeat (synchronized [3 trials] & reentrant-lock [3 trials])
# Java 24: java24-sync-repeat (synchronized [3 trials]) & java24-lock-repeat (reentrant-lock [3 trials])
j21_sync = trials_df[(trials_df["run_set"] == "java21-primary-repeat") & (trials_df["condition_id"] == "synchronized")].copy()
j21_lock = trials_df[(trials_df["run_set"] == "java21-primary-repeat") & (trials_df["condition_id"] == "reentrant-lock")].copy()
j24_sync = trials_df[(trials_df["run_set"] == "java24-sync-repeat")].copy()
j24_lock = trials_df[(trials_df["run_set"] == "java24-lock-repeat")].copy()

# Tag runtime label
j21_sync["Runtime_Condition"] = "Java 21 · synchronized"
j21_lock["Runtime_Condition"] = "Java 21 · ReentrantLock"
j24_sync["Runtime_Condition"] = "Java 24 · synchronized (JEP 491)"
j24_lock["Runtime_Condition"] = "Java 24 · ReentrantLock"

comp_df = pd.concat([j21_sync, j24_sync, j21_lock, j24_lock], ignore_index=True)

# 2. Three Visualizations
st.subheader("The Three Empirical Pillars of Runtime Comparison")

v_col1, v_col2, v_col3 = st.columns(3)

# 1. Throughput Comparison
with v_col1:
    agg_tp = comp_df.groupby("Runtime_Condition")["steady_throughput"].mean()
    order = [
        "Java 21 · synchronized",
        "Java 24 · synchronized (JEP 491)",
        "Java 21 · ReentrantLock",
        "Java 24 · ReentrantLock",
    ]
    vals_tp = [agg_tp.get(c, 0.0) for c in order]

    fig_tp = go.Figure()
    fig_tp.add_trace(
        go.Bar(
            x=["J21 Sync", "J24 Sync", "J21 Lock", "J24 Lock"],
            y=vals_tp,
            marker_color=[PALETTE["accent_red"], PALETTE["accent_blue"], PALETTE["accent_amber"], PALETTE["accent_cyan"]],
            text=[f"{v:.3f}" for v in vals_tp],
            textposition="auto",
        )
    )
    fig_tp = apply_dark_scientific_layout(fig_tp, title="1. Steady-State Throughput (req/s)", height=340)
    fig_tp.update_layout(yaxis=dict(range=[0, 2.5]), yaxis_title="Throughput (req/s)")
    st.plotly_chart(fig_tp, width="stretch")
    st.caption("Throughput is virtually identical (~1.967 req/s) across both runtimes.")

# 2. JFR Pinning Events Comparison
with v_col2:
    agg_jfr = comp_df.groupby("Runtime_Condition")["jfr_pinning_count"].mean()
    vals_jfr = [agg_jfr.get(c, 0) for c in order]

    fig_jfr = go.Figure()
    fig_jfr.add_trace(
        go.Bar(
            x=["J21 Sync", "J24 Sync", "J21 Lock", "J24 Lock"],
            y=vals_jfr,
            marker_color=[PALETTE["accent_red"], PALETTE["accent_blue"], PALETTE["accent_amber"], PALETTE["accent_cyan"]],
            text=[f"{int(v)}" for v in vals_jfr],
            textposition="auto",
        )
    )
    fig_jfr = apply_dark_scientific_layout(fig_jfr, title="2. JFR Pinning Events (>= 20ms)", height=340)
    fig_jfr.update_layout(yaxis_title="Pinning Event Count")
    st.plotly_chart(fig_jfr, width="stretch")
    st.caption("Java 24 object monitors emit strictly 0 pinning events (JEP 491).")

# 3. p95 Latency Comparison
with v_col3:
    agg_p95 = comp_df.groupby("Runtime_Condition")["steady_p95"].mean()
    vals_p95 = [agg_p95.get(c, 0.0) for c in order]

    fig_p95 = go.Figure()
    fig_p95.add_trace(
        go.Bar(
            x=["J21 Sync", "J24 Sync", "J21 Lock", "J24 Lock"],
            y=vals_p95,
            marker_color=[PALETTE["accent_red"], PALETTE["accent_blue"], PALETTE["accent_amber"], PALETTE["accent_cyan"]],
            text=[f"{v:.0f} ms" for v in vals_p95],
            textposition="auto",
        )
    )
    fig_p95 = apply_dark_scientific_layout(fig_p95, title="3. Steady-State p95 Latency (ms)", height=340)
    fig_p95.update_layout(yaxis_title="p95 Latency (ms)")
    st.plotly_chart(fig_p95, width="stretch")
    st.caption("p95 latency jumps to ~9,001 ms under unpinned monitor queueing.")

st.markdown("---")

# 3. Architectural Analysis: Why p95 Increased on Java 24
st.subheader("Architectural Analysis: The 4,983 ms vs. 9,001 ms p95 Divergence")
st.markdown(
    """
    A critical empirical discovery shown in Panel 3 is that steady-state **p95 latency rose from 
    &approx; 4,983 ms on Java 21 to &approx; 9,001 ms on Java 24** under `synchronized` contention:
    
    1. **In Java 21 (Pinned Execution):** The single carrier thread was pinned to the running virtual thread. 
       Other virtual threads remained blocked from executing on that carrier. The admission queue remained tightly coupled to carrier cycles.
    2. **In Java 24 (Unpinned Execution):** With JEP 491, virtual threads yield the carrier when blocked at `monitorenter`. 
       All 10 concurrent VUs successfully submit requests and park their continuations into the HotSpot monitor wait list. 
       Because 10 virtual threads are concurrently queued for a 500 ms serialized lock, the tail of the queue 
       experiences cumulative queueing delay approaching $10 \\times 500\\text{ ms} + \\text{overheads} \\approx 9,000\\text{ ms}$.
    3. **Conclusion for Engineering Teams:** JEP 491 prevents carrier starvation across independent endpoints, 
       but for requests that contend on the **same** shared critical section, queuing latency is determined by Amdahl's Law.
    """
)

st.markdown("---")

# 4. Authoritative Verification Table (Preserving Both Measurement Windows)
st.subheader("Authoritative Dual-Window Comparison Table (N=3 per condition)")
st.markdown(
    "Preserving both the **Full Run [0, 55s]** and **Steady-State Hold [15, 45s]** windows. "
    "Hold window metrics represent the constant-concurrency interval, not proof of statistical equilibrium."
)

summary_rows = []
for group_name in order:
    sub = comp_df[comp_df["Runtime_Condition"] == group_name]
    tp_stats = compute_descriptive_stats(sub["steady_throughput"])
    full_tp_stats = compute_descriptive_stats(sub["full_throughput"])
    p50_stats = compute_descriptive_stats(sub["steady_p50"])
    full_p50_stats = compute_descriptive_stats(sub["full_p50"])
    p95_stats = compute_descriptive_stats(sub["steady_p95"])
    jfr_count = int(sub["jfr_pinning_count"].iloc[0]) if not sub.empty else 0

    summary_rows.append({
        "Runtime & Condition": group_name,
        "Trials (N)": tp_stats["count"],
        "Full TP [0,55s] (req/s)": f"{full_tp_stats['mean']:.4f} ± {full_tp_stats['std']:.4f}",
        "Hold TP [15,45s] (req/s)": f"{tp_stats['mean']:.4f} ± {tp_stats['std']:.4f}",
        "Full p50 (ms)": f"{full_p50_stats['mean']:.1f} ± {full_p50_stats['std']:.1f}",
        "Hold p50 (ms)": f"{p50_stats['mean']:.1f} ± {p50_stats['std']:.1f}",
        "Hold p95 (ms)": f"{p95_stats['mean']:.1f} ± {p95_stats['std']:.1f}",
        "JFR Pins": jfr_count,
    })

st.dataframe(pd.DataFrame(summary_rows), hide_index=True, width="stretch")
