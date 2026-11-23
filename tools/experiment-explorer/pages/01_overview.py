"""Page 1: Overview & Experimental Inventory."""
import sys
from pathlib import Path

# Ensure explorer root is in path
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.presentation import page_heading
from lib.loaders import (
    load_all_runs_df,
    load_artifact_inventory_df,
)
from lib.provenance import get_raw_file_bytes
from lib.schemas import STRATA
from lib.transformations import COLORWAY, PALETTE, apply_dark_scientific_layout, hover_card

page_heading("01", "Overview & Experimental Inventory")
st.markdown(
    "Explore the frozen evidence from the Spring Boot MVC virtual-thread experiments, "
    "from the physical artifact inventory to individual executions."
)

# 1. Master KPI Cards
with st.container(key="overview_metrics"):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Normalized Trials", "76", help="Curated trial records in normalized-evidence.json")
    with col2:
        st.metric("Evidence Strata", "8", help="Non-overlapping epistemic strata defined in Adjudication Charter")
    with col3:
        st.metric("Admitted Hash Rate", "100%", help="151/151 normalized result/JFR hashes match disk files")
    with col4:
        st.metric("Manifest-Backed Runs", "75", help="Admitted runs backed by JSON manifests (+1 CPU control = 76)")
    with col5:
        st.metric("Total Disk Artifacts", "543", help="Total physical benchmark artifacts enumerated in results/")

inventory, executions, environment, exports = st.tabs([
    "Artifact census", "Executions & filters", "Environment & strata", "Evidence exports",
])

with inventory:
    st.subheader("Physical artifact inventory")
    st.html("""
        <div class="freeze-strip">
            <div><small>Earlier freeze</small><strong>504</strong></div>
            <span class="freeze-arrow" aria-hidden="true">→</span>
            <div><small>Disk inventory</small><strong>543</strong></div>
            <p><b>39 additional files</b><br>30 persistence ablation artifacts and 9 validation files</p>
        </div>
    """)
    inv_df = load_artifact_inventory_df()

    # Breakdown by physical type
    type_col1, type_col2 = st.columns([1, 1])

    with type_col1:
        type_counts = inv_df["artifact_type"].value_counts().reset_index()
        type_counts.columns = ["Artifact Type", "Count"]
        file_labels = {
            "manifest_json": "Manifest JSON", "k6_json": "k6 result JSON", "jfr_binary": "JFR recording",
            "telemetry_csv": "Telemetry CSV", "markdown_report": "Markdown report",
        }
        type_counts["File type"] = type_counts["Artifact Type"].replace(file_labels)
        fig_types = px.pie(
            type_counts,
            names="File type",
            values="Count",
            color="Artifact Type",
            color_discrete_sequence=COLORWAY,
            color_discrete_map={
                "manifest_json": PALETTE["accent_blue"],
                "k6_json": PALETTE["accent_cyan"],
                "jfr_binary": PALETTE["accent_purple"],
                "telemetry_csv": PALETTE["accent_amber"],
                "markdown_report": PALETTE["text_muted"],
            },
            hole=0.64,
        )
        fig_types = apply_dark_scientific_layout(fig_types, title="Physical file types", height=360, hover_value="%{value:,} files")
        fig_types.add_annotation(text=f"<b>{len(inv_df):,}</b><br>files", xref="paper", yref="paper", x=.5, y=.5, showarrow=False, font_size=17)
        st.plotly_chart(fig_types, width="stretch", theme=None)

    with type_col2:
        status_counts = inv_df["candidate_status"].value_counts().reset_index()
        status_counts.columns = ["Admission Status", "Count"]
        fig_status = px.bar(
            status_counts,
            y="Admission Status",
            x="Count",
            orientation="h",
            text="Count",
            title="Admission & Candidate Status Breakdown",
            color="Admission Status",
            color_discrete_sequence=COLORWAY,
            color_discrete_map={
                "admitted_normalized": PALETTE["accent_blue"],
                "historical_baseline": PALETTE["accent_amber"],
                "diagnostic": PALETTE["accent_purple"],
                "exploratory_uninstrumented": PALETTE["accent_red"],
                "unmapped": PALETTE["text_muted"],
            },
        )
        fig_status = apply_dark_scientific_layout(fig_status, title="Admission breakdown", height=360)
        fig_status.update_layout(showlegend=False, xaxis_title="Files", yaxis_title=None)
        fig_status.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=status_counts["Admission Status"],
                                tickmode="array",
                                tickvals=status_counts["Admission Status"],
                                ticktext=status_counts["Admission Status"].str.replace("_", " "))
        fig_status.update_traces(textposition="auto", hovertemplate=hover_card("%{y}", "%{x:,} files"))
        st.plotly_chart(fig_status, width="stretch", theme=None)

    with st.expander("Snapshot reconciliation and storage ledger"):
        st.markdown(
            """
                <div class="callout-box">
                    <b>Forensic Reconciliation: Resolving the 504 vs. 543 Artifact Discrepancy</b><br>
                    Earlier working documents and Chapter 5 cited <b>504 physical artifacts</b>. The active disk enumeration
                    reports exactly <b>543 physical artifacts</b> (+39 files).<br><br>
                    <b>Root Cause:</b> The 504-count reflected an initial evidence freeze taken prior to executing
                    the <b>Stratum 8 Relational Persistence Contention Ablation</b> suite (<code>java21-orders-persistence-contention</code>)
                    which contributed 6 manifests, 6 k6 JSONs, 6 JFRs, and 12 process/pool telemetry CSVs (30 files), plus
                    preliminary persistence validation runs (+9 files).<br>
                    Across both snapshots, the <b>76 normalized trial records</b> (226 admitted raw files) remain 100% stable
                    with zero missing files and 100% cryptographic hash fidelity.
                </div>
            """,
            unsafe_allow_html=True,
        )
        status_summary = inv_df.groupby("candidate_status").agg(
            Count=("artifact_id", "count"),
            Size_MB=("size_bytes", lambda s: round(s.sum() / (1024 * 1024), 2)),
        ).reset_index()
        status_summary = status_summary.rename(columns={"candidate_status": "Candidate Status"})
        st.dataframe(status_summary, hide_index=True, width="stretch", column_config={
            "Count": st.column_config.ProgressColumn("Files", min_value=0, max_value=len(inv_df), format="%d",
                                                   help="Count within the physical inventory"),
            "Size_MB": st.column_config.NumberColumn("Size (MiB)", format="%.2f"),
        })

with executions:
    all_runs_df = load_all_runs_df()

    # Execution filters
    st.subheader("Interactive Research Census & Run Filter")
    st.markdown(
        "Filter all 126 experimental executions by research family, runtime, admission status, or lock treatment."
    )

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)

    with f_col1:
        family_options = ["All Families"] + sorted(all_runs_df["run_family"].dropna().unique().tolist())
        sel_family = st.selectbox("Experimental Family:", options=family_options, index=0)

    with f_col2:
        jdk_options = ["All Runtimes", "Java 21", "Java 24", "Java 25 (Exploratory)"]
        sel_jdk = st.selectbox("Runtime Version:", options=jdk_options, index=0)

    with f_col3:
        adm_options = ["All Statuses"] + sorted(all_runs_df["admission_status"].unique().tolist())
        sel_adm = st.selectbox("Admission Status:", options=adm_options, index=0)

    with f_col4:
        lock_options = ["All Treatments"] + sorted(all_runs_df["lock_variant"].dropna().unique().tolist())
        sel_lock = st.selectbox("Synchronization Treatment:", options=lock_options, index=0)

    # Apply filters
    filtered_df = all_runs_df.copy()
    if sel_family != "All Families":
        filtered_df = filtered_df[filtered_df["run_family"] == sel_family]
    if sel_jdk != "All Runtimes":
        filtered_df = filtered_df[filtered_df["jdk_major_label"] == sel_jdk]
    if sel_adm != "All Statuses":
        filtered_df = filtered_df[filtered_df["admission_status"] == sel_adm]
    if sel_lock != "All Treatments":
        filtered_df = filtered_df[filtered_df["lock_variant"] == sel_lock]

    st.caption(f"{len(filtered_df)} of {len(all_runs_df)} executions match the selected filters.")
    if filtered_df.empty:
        st.info("No executions match this combination. Choose a broader filter to see runs.")

    # Display table
    view_cols = [
        "run_id", "run_family", "condition_id", "lock_variant",
        "jdk_version", "carrier_category", "target_vus",
        "is_in_normalized_set", "stratum_id", "admission_status"
    ]
    display_filtered = filtered_df[view_cols].copy()
    display_filtered = display_filtered.rename(
        columns={
            "run_id": "Run ID",
            "run_family": "Family",
            "condition_id": "Condition",
            "lock_variant": "Lock",
            "jdk_version": "JDK",
            "carrier_category": "Carrier",
            "target_vus": "VUs",
            "is_in_normalized_set": "Normalized?",
            "stratum_id": "Stratum",
            "admission_status": "Status",
        }
    )
    st.dataframe(display_filtered, hide_index=True, width="stretch", column_config={
        "Run ID": st.column_config.TextColumn(pinned=True),
        "VUs": st.column_config.NumberColumn("Target VUs"),
    })

    # Runtime distribution
    st.subheader("Execution Population & Runtime Distribution (126 Executions)")
    st.markdown(
        "Macro breakdown across the entire benchmark repository census ($N=126$ runs in `run-family-matrix.csv`), "
        "including exploratory Java 25 executions, historical pilots, and excluded persistence runs."
    )

    macro_c1, macro_c2, macro_c3 = st.columns(3)

    with macro_c1:
        jdk_dist = all_runs_df["jdk_major_label"].value_counts().reset_index()
        jdk_dist.columns = ["Runtime Version", "Execution Count"]
        fig_macro_jdk = px.pie(
            jdk_dist,
            names="Runtime Version",
            values="Execution Count",
            color="Runtime Version",
            color_discrete_sequence=COLORWAY,
            color_discrete_map={
                "Java 21": PALETTE["accent_blue"],
                "Java 24": PALETTE["accent_cyan"],
                "Java 25 (Exploratory)": PALETTE["accent_purple"],
                "Other / Template": PALETTE["text_muted"],
            },
            hole=0.64,
        )
        fig_macro_jdk = apply_dark_scientific_layout(fig_macro_jdk, title="Runtime versions", height=345, hover_value="%{value:,} executions")
        st.plotly_chart(fig_macro_jdk, width="stretch", theme=None)

    with macro_c2:
        adm_dist = all_runs_df["admission_status"].value_counts().reset_index()
        adm_dist.columns = ["Admission Status", "Executions"]
        fig_macro_adm = px.bar(
            adm_dist,
            x="Admission Status",
            y="Executions",
            color="Admission Status",
            color_discrete_sequence=COLORWAY,
            color_discrete_map={
                "primary": PALETTE["accent_blue"],
                "ablation": PALETTE["accent_cyan"],
                "supporting": PALETTE["accent_green"],
                "historical": PALETTE["accent_amber"],
                "exploratory": PALETTE["accent_purple"],
                "excluded": PALETTE["accent_red"],
            },
        )
        fig_macro_adm = apply_dark_scientific_layout(fig_macro_adm, title="Admission classes", height=345, hover_value="%{y:,} executions")
        fig_macro_adm.update_layout(showlegend=False)
        st.plotly_chart(fig_macro_adm, width="stretch", theme=None)

    with macro_c3:
        carrier_dist = all_runs_df["carrier_category"].value_counts().reset_index()
        carrier_dist.columns = ["Carrier Configuration", "Executions"]
        fig_macro_carrier = px.pie(
            carrier_dist,
            names="Carrier Configuration",
            values="Executions",
            color="Carrier Configuration",
            color_discrete_sequence=COLORWAY,
            color_discrete_map={
                "1-carrier": PALETTE["accent_blue"],
                "8-carrier/default": PALETTE["accent_amber"],
                "4-carrier": PALETTE["accent_purple"],
                "unspecified": PALETTE["text_muted"],
            },
            hole=0.64,
        )
        fig_macro_carrier = apply_dark_scientific_layout(fig_macro_carrier, title="Carrier configurations", height=345, hover_value="%{value:,} executions")
        st.plotly_chart(fig_macro_carrier, width="stretch", theme=None)

with environment:
    # Environment identity matrix
    st.subheader("Experimental Environment & Hardware Identity")
    st.markdown(
        "Authoritative execution boundaries from the **Experimental Identity Matrix**. "
        "Single-carrier mechanism isolation runs and historical 8-carrier baseline experiments remain strictly separated."
    )

    env_col1, env_col2 = st.columns([1, 1])

    with env_col1:
        env_data = [
            {"Property": "Host System", "Specification": "Apple M1 (Apple Silicon arm64)"},
            {"Property": "Operating System", "Specification": "Darwin 25.2.0 (macOS)"},
            {"Property": "Logical Processors", "Specification": "8 (4 performance + 4 efficiency)"},
            {"Property": "Physical Memory", "Specification": "8 GB Unified Memory"},
            {"Property": "Primary Runtime", "Specification": "OpenJDK 21.0.8 LTS (build 21.0.8)"},
            {"Property": "Secondary Runtimes", "Specification": "OpenJDK 24.0.2 (JEP 491 GA) & OpenJDK 25-ea"},
            {"Property": "Framework", "Specification": "Spring Boot 3.5.12 (Spring MVC / Tomcat)"},
        ]
        st.dataframe(pd.DataFrame(env_data), hide_index=True, width="stretch")

    with env_col2:
        workload_data = [
            {"Dimension": "Load Generator", "Value": "k6 v1.7.1 (closed-loop model)"},
            {"Dimension": "Staged Profile", "Value": "15s ramp-up, 30s steady hold, 10s ramp-down (55s total)"},
            {"Dimension": "Inter-Request Think Time", "Value": "sleep(0.1), giving Z = 0.100 s"},
            {"Dimension": "Primary Scheduler Control", "Value": "-Djdk.virtualThreadScheduler.parallelism=1, maxPoolSize=1"},
            {"Dimension": "Historical Baseline Pool", "Value": "Default 8-carrier ForkJoinPool (Stratum 5 only)"},
            {"Dimension": "/payments Critical Section", "Value": "500 ms simulated serialized business logic"},
            {"Dimension": "/cpu Computational Workload", "Value": "5,000,000 iterations of Math.fma and Math.sqrt"},
        ]
        st.dataframe(pd.DataFrame(workload_data), hide_index=True, width="stretch")

    # Evidence strata
    st.subheader("The Eight Authoritative Evidence Strata")
    st.markdown(
        "All 125 physical executions (+1 template) are partitioned into eight non-overlapping epistemic strata "
        "under the Stage 1.3 Adjudication Charter and Chapter 5 results ledger."
    )

    strata_table = []
    for sid, sdef in sorted(STRATA.items()):
        strata_table.append({
            "Stratum": f"Stratum {sid}",
            "Name": sdef.name.split("·")[-1].strip(),
            "Target Population": sdef.target_count,
            "Carrier Constraint": sdef.expected_carrier,
            "Admission Class": sdef.admission_status.upper(),
            "Scope & Epistemic Role": sdef.description,
        })

    st.dataframe(pd.DataFrame(strata_table), hide_index=True, width="stretch")

with exports:
    st.subheader("Authoritative Evidence Exports")
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        inv_bytes = get_raw_file_bytes("docs/evidence-freeze/artifact-inventory.csv")
        if inv_bytes:
            st.download_button(
                "Download Artifact Inventory CSV (543 files)",
                data=inv_bytes,
                file_name="artifact-inventory.csv",
                mime="text/csv",
                width="stretch",
            )

    with dl_col2:
        recalc_bytes = get_raw_file_bytes("docs/evidence-freeze/metric-recalculations.csv")
        if recalc_bytes:
            st.download_button(
                "Download Metric Recalculations CSV",
                data=recalc_bytes,
                file_name="metric-recalculations.csv",
                mime="text/csv",
                width="stretch",
            )

    with dl_col3:
        family_bytes = get_raw_file_bytes("docs/evidence-freeze/run-family-matrix.csv")
        if family_bytes:
            st.download_button(
                "Download Run Family Matrix CSV",
                data=family_bytes,
                file_name="run-family-matrix.csv",
                mime="text/csv",
                width="stretch",
            )
