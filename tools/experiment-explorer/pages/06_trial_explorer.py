"""Page 6: Individual Trial Explorer & Cryptographic Provenance."""
import sys
from pathlib import Path

# Ensure explorer root is in path
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.presentation import page_heading
from lib.loaders import get_enriched_trials, load_telemetry_series
from lib.provenance import (
    get_raw_file_bytes,
    read_manifest_file,
    verify_file_integrity,
)
from lib.transformations import (
    PALETTE,
    apply_dark_scientific_layout,
    format_latency_ms,
    format_throughput,
    hover_card,
    shade_workload_stages,
)

page_heading("06", "Individual Trial Explorer")
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

if not run_ids:
    st.info("This stratum has no normalized trials. Select another stratum to inspect a run.")
    st.stop()

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

measurements, telemetry, provenance = st.tabs(["Measurements", "Host telemetry", "Provenance & downloads"])

with measurements:
    # 3. Dual-Window Measurement Panel
    st.subheader("Dual-Window Measurement Verification")
    st.markdown(
        "Comparing the **Full 55-Second Run** against the **30-Second Steady-State Hold Window [15s, 45s]**."
    )

    m = trial.metrics
    rows = [
        ("Requests", str(m.full_reqs), str(m.steady_reqs), "—"),
        ("Throughput", format_throughput(m.full_throughput), format_throughput(m.steady_throughput),
         f"{m.throughput_delta_pct:+.1f}%"),
        ("p50 latency", format_latency_ms(m.full_p50), format_latency_ms(m.steady_p50), f"{m.p50_delta_pct:+.1f}%"),
        ("p95 latency", format_latency_ms(m.full_p95), format_latency_ms(m.steady_p95), "—"),
    ]
    body = "".join(
        f'<tr><th scope="row">{label}</th><td>{full}</td><td>{hold}</td><td>{delta}</td></tr>'
        for label, full, hold, delta in rows
    )
    st.html(f"""
        <div class="window-ledger" tabindex="0" role="region" aria-label="Dual-window measurements">
        <table><thead><tr><th scope="col">Measure</th><th scope="col">Full run <small>0–55 s</small></th>
        <th scope="col">Hold <small>15–45 s</small></th><th scope="col">Δ vs full</th></tr></thead>
        <tbody>{body}</tbody></table></div>
    """)

    st.subheader("JFR event capture")
    jfr_count = trial.jfr_pinning_count if trial.jfr_available else None
    jfr_c1, jfr_c2 = st.columns(2)
    jfr_c1.metric("Companion JFR recording", "Available" if trial.jfr_available else "Unavailable")
    jfr_c2.metric("VirtualThreadPinned events", jfr_count if jfr_count is not None else "N/A",
                  help="jdk.VirtualThreadPinned events with a duration of at least 20 ms")
    if jfr_count is None:
        st.badge("Pin count unavailable", color="gray")
    elif jfr_count > 0:
        st.badge("Carrier pinning detected", color="orange")
    else:
        st.badge("Zero recorded pins at the 20 ms threshold", color="blue")

with telemetry:
    # 4. Companion Telemetry Inspection (if available)
    st.subheader("Host Telemetry Series (CPU Utilization & Active Threads)")

    telemetry_df = load_telemetry_series(trial.run_id)

    if telemetry_df is not None and not telemetry_df.empty:
        fig_t = go.Figure()
        fig_t.add_trace(
            go.Scatter(
                x=telemetry_df["elapsed_s"],
                y=telemetry_df["cpu_percent"],
                name="Process CPU",
                hovertemplate=hover_card("Process CPU", "%{y:.2f}%", "Elapsed · %{x:.1f} s", PALETTE["accent_blue"]),
                line=dict(color=PALETTE["accent_blue"], width=2),
            )
        )

        if "threads" in telemetry_df.columns:
            fig_t.add_trace(
                go.Scatter(
                    x=telemetry_df["elapsed_s"],
                    y=telemetry_df["threads"],
                    name="OS threads",
                    hovertemplate=hover_card("OS threads", "%{y:,d}", "Elapsed · %{x:.1f} s", PALETTE["accent_purple"]),
                    yaxis="y2",
                    line=dict(color=PALETTE["accent_purple"], width=1.5, dash="dot"),
                )
            )

        shade_workload_stages(fig_t)
        fig_t = apply_dark_scientific_layout(fig_t, title=f"Host telemetry · {trial.run_id}", height=390)
        fig_t.update_layout(
            xaxis_title="Elapsed Time (s)",
            yaxis_title="CPU Utilization (%)",
            yaxis2=dict(
                title=dict(text="OS Thread Count", font=dict(color=PALETTE["accent_purple"], size=11)),
                overlaying="y",
                side="right",
                showgrid=False, automargin=True,
                tickfont=dict(color=PALETTE["accent_purple"], size=10),
            ),
        )
        st.plotly_chart(fig_t, width="stretch", theme=None)
    else:
        st.info(f"No companion telemetry file found for run {trial.run_id}.")

with provenance:
    # 5. Cryptographic Provenance & SHA-256 Validation
    st.subheader("Cryptographic Provenance & SHA-256 Hash Ledger")
    st.markdown(
        "Live physical existence check and SHA-256 hash validation against recorded metadata."
    )

    status_colors = {
        "Verified match": PALETTE["accent_green"], "Present · no reference hash": "#43566e",
        "Missing file": PALETTE["accent_red"], "Hash mismatch": PALETTE["accent_red"],
    }
    status_labels = {
        "VERIFIED": "Verified match", "UNHASHED_PRESENT": "Present · no reference hash",
        "MISSING_FILE": "Missing file", "HASH_MISMATCH": "Hash mismatch",
    }
    prov_items = []
    for role, path, expected in (
        ("Execution manifest", trial.manifest_path, None),
        ("k6 result JSONL", trial.result_path, trial.result_sha256),
        ("JFR recording", trial.jfr_path, trial.jfr_sha256),
    ):
        if path:
            check = verify_file_integrity(path, expected)
            prov_items.append({
                "Artifact": role, "Verification": [status_labels[check["status"]]],
                "Repository path": path, "Recorded SHA-256": expected or "No reference hash",
                "Disk SHA-256": check["actual_sha256"] or "Unavailable",
            })

    st.dataframe(pd.DataFrame(prov_items), hide_index=True, width="stretch", column_config={
        "Artifact": st.column_config.TextColumn(pinned=True),
        "Verification": st.column_config.MultiselectColumn(width="medium", options=list(status_colors),
                                                          color=list(status_colors.values())),
        "Recorded SHA-256": st.column_config.TextColumn(width="large"),
        "Disk SHA-256": st.column_config.TextColumn(width="large"),
    })

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
