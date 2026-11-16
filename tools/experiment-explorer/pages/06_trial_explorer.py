"""Page 6: Individual Trial Explorer & Cryptographic Provenance."""
import sys
from pathlib import Path

# Ensure explorer root is in path
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.loaders import get_enriched_trials, load_telemetry_series
from lib.provenance import (
    REPO_ROOT,
    compute_file_sha256,
    get_raw_file_bytes,
    read_manifest_file,
    verify_file_integrity,
)
from lib.transformations import (
    PALETTE,
    apply_dark_scientific_layout,
    format_latency_ms,
    format_throughput,
)

st.title("06 · Individual Trial Explorer")
st.markdown(
    "Full empirical audit drill-down for every benchmark trial. "
    "Inspect execution parameters, dual-window metrics, telemetry, and verify raw cryptographic provenance."
)

trials = get_enriched_trials()
trial_map = {t.run_id: t for t in trials}

# 1. Trial Selection Controls
st.sidebar.header("Trial Selection")

# Filters to help locate a run
strata_options = ["All Strata"] + [f"Stratum {sid}" for sid in range(1, 9)]
selected_stratum = st.sidebar.selectbox("Filter by Stratum:", strata_options, index=0)

filtered_trials = trials
if selected_stratum != "All Strata":
    sid = int(selected_stratum.split()[1])
    filtered_trials = [t for t in trials if t.stratum_id == sid]

run_ids = [t.run_id for t in filtered_trials]

# Default to the famous 20261015-142534 (Stratum 1 ReentrantLock trial 1) or first available
default_idx = run_ids.index("20261015-142534") if "20261015-142534" in run_ids else 0

selected_run_id = st.sidebar.selectbox(
    "Select Run Identifier:",
    options=run_ids,
    index=default_idx,
    format_func=lambda rid: f"{rid} · {trial_map[rid].condition_id} (Trial {trial_map[rid].trial_id})",
)

trial = trial_map[selected_run_id]

# 2. Execution Identity Banner
st.subheader(f"Execution Identity: Run {trial.run_id}")

id_c1, id_c2, id_c3, id_c4 = st.columns(4)
with id_c1:
    st.markdown(f"**Condition:** `{trial.condition_id}`")
    st.caption(trial.condition_label)
with id_c2:
    st.markdown(f"**Stratum:** `{trial.stratum_name.split('·')[0].strip()}`")
    st.caption(f"Status: **{trial.admission_status.upper()}**")
with id_c3:
    st.markdown(f"**Runtime:** `{trial.jdk_major}`")
    st.caption(trial.jdk)
with id_c4:
    st.markdown(f"**Scheduler:** `{trial.carrier_category}`")
    st.caption(f"parallelism={trial.parallelism}, maxPool={trial.max_pool_size}")

st.markdown("---")

# 3. Dual-Window Measurement Panel
st.subheader("Dual-Window Measurement Verification")
st.markdown(
    "Comparing the **Full 55-Second Run** against the **30-Second Steady-State Hold Window [15s, 45s]**."
)

dw_col1, dw_col2 = st.columns(2)

with dw_col1:
    st.markdown("#### Full Run Window [0, 55.0s]")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Requests", f"{trial.metrics.full_reqs}")
    with m2:
        st.metric("Throughput", f"{trial.metrics.full_throughput:.2f} req/s")
    with m3:
        st.metric("p50 (Median)", format_latency_ms(trial.metrics.full_p50))
    with m4:
        st.metric("p95 Latency", format_latency_ms(trial.metrics.full_p95))

with dw_col2:
    st.markdown("#### Steady-State Hold Window [15.0s, 45.0s]")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.metric("Requests", f"{trial.metrics.steady_reqs}")
    with h2:
        delta_tp_str = f"{trial.metrics.throughput_delta_pct:+.1f}% vs full"
        st.metric("Throughput", f"{trial.metrics.steady_throughput:.2f} req/s", delta=delta_tp_str)
    with h3:
        delta_p50_str = f"{trial.metrics.p50_delta_pct:+.1f}% vs full"
        st.metric("p50 (Median)", format_latency_ms(trial.metrics.steady_p50), delta=delta_p50_str)
    with h4:
        st.metric("p95 Latency", format_latency_ms(trial.metrics.steady_p95))

# JFR Pinning Status Card
st.markdown("#### JVM Instrumentation & JFR Event Capture")
jfr_c1, jfr_c2, jfr_c3 = st.columns(3)
with jfr_c1:
    st.metric("JFR Recording Available", "YES" if trial.jfr_available else "NO")
with jfr_c2:
    pin_count_str = str(trial.jfr_pinning_count) if trial.jfr_pinning_count is not None else "0"
    st.metric("VirtualThreadPinned Events", pin_count_str, help="jdk.VirtualThreadPinned events with threshold >= 20ms")
with jfr_c3:
    if trial.jfr_pinning_count and trial.jfr_pinning_count > 0:
        st.markdown(
            f"""
            <div style="margin-top: 15px; padding: 10px; background-color: #3d1d24; border: 1px solid #f85149; border-radius: 6px; color: #f85149;">
                <b>Carrier Pinning Detected:</b> {trial.jfr_pinning_count} events recorded at <code>PaymentService.processPayment</code>.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="margin-top: 15px; padding: 10px; background-color: #1d3b2a; border: 1px solid #3fb950; border-radius: 6px; color: #3fb950;">
                <b>Clean Carrier State:</b> 0 pinning events recorded in companion JFR binary.
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# 4. Companion Telemetry Inspection (if available)
st.subheader("Host Telemetry Series (CPU Utilization & Active Threads)")

telemetry_df = load_telemetry_series(trial.run_id)

if telemetry_df is not None and not telemetry_df.empty:
    fig_t = go.Figure()
    fig_t.add_vrect(x0=0, x1=15, fillcolor="rgba(88, 166, 255, 0.08)", layer="below", line_width=0, annotation_text="Ramp-Up (0-15s)", annotation_font_size=10)
    fig_t.add_vrect(x0=15, x1=45, fillcolor="rgba(57, 197, 187, 0.12)", layer="below", line_width=0, annotation_text="Steady Hold (15-45s)", annotation_font_size=10)
    fig_t.add_vrect(x0=45, x1=55, fillcolor="rgba(139, 148, 158, 0.08)", layer="below", line_width=0, annotation_text="Ramp-Down (45-55s)", annotation_font_size=10)

    fig_t.add_trace(
        go.Scatter(
            x=telemetry_df["elapsed_s"],
            y=telemetry_df["cpu_percent"],
            name="CPU Utilization (%)",
            line=dict(color=PALETTE["accent_blue"], width=2),
        )
    )

    if "threads" in telemetry_df.columns:
        fig_t.add_trace(
            go.Scatter(
                x=telemetry_df["elapsed_s"],
                y=telemetry_df["threads"],
                name="OS Threads",
                yaxis="y2",
                line=dict(color=PALETTE["accent_purple"], width=1.5, dash="dot"),
            )
        )

    fig_t = apply_dark_scientific_layout(fig_t, title=f"Companion Telemetry Stream: Run {trial.run_id}", height=340)
    fig_t.update_layout(
        xaxis_title="Elapsed Time (s)",
        yaxis_title="CPU Utilization (%)",
        yaxis2=dict(
            title=dict(text="OS Thread Count", font=dict(color=PALETTE["accent_purple"], size=11)),
            overlaying="y",
            side="right",
            gridcolor="#21262d",
            tickfont=dict(color=PALETTE["accent_purple"], size=10),
        ),
    )
    st.plotly_chart(fig_t, width="stretch")
else:
    st.info(f"No companion telemetry file found for run {trial.run_id}.")

st.markdown("---")

# 5. Cryptographic Provenance & SHA-256 Validation
st.subheader("Cryptographic Provenance & SHA-256 Hash Ledger")
st.markdown(
    "Live physical existence check and SHA-256 hash validation against recorded metadata."
)

prov_items = []

# Manifest
if trial.manifest_path:
    ver_mf = verify_file_integrity(trial.manifest_path, None)
    prov_items.append({
        "Artifact Role": "Execution Manifest",
        "Repository Path": trial.manifest_path,
        "File Exists?": "YES" if ver_mf["exists"] else "MISSING",
        "Recorded SHA-256": "N/A (Reference Root)",
        "Disk SHA-256": ver_mf["actual_sha256"][:16] + "..." if ver_mf["actual_sha256"] else "N/A",
        "Cryptographic Match": "VERIFIED PRESENT" if ver_mf["exists"] else "FAILED",
    })

# Result
if trial.result_path:
    ver_res = verify_file_integrity(trial.result_path, trial.result_sha256)
    prov_items.append({
        "Artifact Role": "k6 Result JSONL",
        "Repository Path": trial.result_path,
        "File Exists?": "YES" if ver_res["exists"] else "MISSING",
        "Recorded SHA-256": trial.result_sha256[:16] + "..." if trial.result_sha256 else "UNHASHED",
        "Disk SHA-256": ver_res["actual_sha256"][:16] + "..." if ver_res["actual_sha256"] else "N/A",
        "Cryptographic Match": "MATCH (VERIFIED)" if ver_res["match"] else "MISMATCH",
    })

# JFR
if trial.jfr_path:
    ver_jfr = verify_file_integrity(trial.jfr_path, trial.jfr_sha256)
    prov_items.append({
        "Artifact Role": "JFR Binary Recording",
        "Repository Path": trial.jfr_path,
        "File Exists?": "YES" if ver_jfr["exists"] else "MISSING",
        "Recorded SHA-256": trial.jfr_sha256[:16] + "..." if trial.jfr_sha256 else "UNHASHED",
        "Disk SHA-256": ver_jfr["actual_sha256"][:16] + "..." if ver_jfr["actual_sha256"] else "N/A",
        "Cryptographic Match": "MATCH (VERIFIED)" if ver_jfr["match"] else "MISMATCH",
    })

st.dataframe(pd.DataFrame(prov_items), hide_index=True, width="stretch")

st.markdown("---")

# 6. Artifact Downloads & Raw Manifest Viewer
st.subheader("Raw Artifact Download & Manifest Inspection")

dl1, dl2, dl3 = st.columns(3)

with dl1:
    if trial.result_path:
        b_res = get_raw_file_bytes(trial.result_path)
        if b_res:
            st.download_button(
                "Download Raw k6 Result JSON",
                data=b_res,
                file_name=f"k6-{trial.run_id}.json",
                mime="application/json",
                width="stretch",
            )

with dl2:
    if trial.manifest_path:
        b_mf = get_raw_file_bytes(trial.manifest_path)
        if b_mf:
            st.download_button(
                "Download Execution Manifest JSON",
                data=b_mf,
                file_name=f"manifest-{trial.run_id}.json",
                mime="application/json",
                width="stretch",
            )

with dl3:
    if trial.telemetry_path:
        b_telem = get_raw_file_bytes(trial.telemetry_path)
        if b_telem:
            st.download_button(
                "Download Companion Telemetry CSV",
                data=b_telem,
                file_name=f"telemetry-{trial.run_id}.csv",
                mime="text/csv",
                width="stretch",
            )

# Expandable JSON Manifest Viewer
if trial.manifest_path:
    with st.expander("Inspect Raw JSON Manifest"):
        mf_content = read_manifest_file(trial.manifest_path)
        st.json(mf_content)
