"""Page 7: Chapter 7 Migration Guidelines & Architectural Triage Workbench.

Comprehensive interactive workbench synthesizing Chapter 7 Migration Guidance,
the Claim-to-Evidence Ledger, and empirical findings across Strata 1-8.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add explorer root
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.presentation import page_heading
from lib.loaders import load_persistence_experiments
from lib.migration_data import (
    CORE_RULES,
    DEPENDENCIES_REGISTRY,
    REFACTORING_PATTERNS,
    DependencyEntry,
    MigrationRule,
    RefactoringPattern,
    TriageAssessment,
    calculate_downstream_pool_capacity,
    calculate_service_demand_capacity,
    calculate_threadlocal_heap_footprint,
    evaluate_migration_readiness,
)
from lib.transformations import (
    PALETTE,
    apply_dark_scientific_layout,
    format_bytes,
    format_latency_ms,
    hover_card,
)

# Page header
page_heading("07", "Migration Guidelines & Triage Workbench")
st.markdown(
    "Evidence-bounded architectural migration framework for adopting Java 21 Virtual Threads "
    "within enterprise Spring Boot MVC systems. Calibrated against empirical findings from Strata 1–8."
)

# Setup the 8 tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Overview", "Triage", "Rules", "Calculators", "Dependencies", "Refactoring", "JFR", "Audit export",
])


# ==============================================================================
# TAB 1: Executive Overview & Prerequisites
# ==============================================================================
with tab1:
    st.header("Executive Overview & Technical Prerequisites")
    st.markdown(
        """
        This workbench synthesizes the HotSpot runtime mechanics, the 125 benchmark executions 
        (119 baseline runs across Strata 1–7 and 6 persistence runs in Stratum 8), and queueing-theoretic derivations 
        into an actionable, correctness-preserving migration framework for enterprise Spring Boot MVC systems.
        """
    )

    # Epistemic Grounding Banner
    st.markdown(
        """
        <div class="callout-box">
            <b>Epistemic Integrity Notice (§7.1):</b><br>
            Every guideline, refactoring pattern, and diagnostic rule in this workbench is calibrated against the 
            evidentiary framework established in Chapter 3 (§3.13) and traceable to the frozen 
            <b>Claim-to-Evidence Ledger</b>: 
            <span class="badge badge-primary">[MEASURED]</span>, 
            <span class="badge badge-supporting">[EXTERNALLY SUPPORTED]</span>, 
            <span class="badge badge-historical">[HEURISTIC / LITERATURE]</span>, and 
            <span class="badge badge-diagnostic">[THEORETICAL / CONDITIONAL]</span>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Target System Characteristics
    st.subheader("Target System Architectural Scope (§7.1.1)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            * **Synchronous Servlet Architecture:** Systems built on Spring Boot 3.x and Apache Tomcat (or Jetty / Undertow) 
              utilizing synchronous HTTP request-response paradigms rather than reactive event loops (e.g. WebFlux).
            * **Relational Database Persistence:** Workloads interacting with relational databases via standard JDBC, 
              Spring `JdbcTemplate`, or Spring Data JPA / Hibernate managed by HikariCP.
            """
        )
    with c2:
        st.markdown(
            """
            * **Heterogeneous Runtime Dependencies:** Codebases integrating third-party libraries, native bindings 
              (JNI / Project Panama FFM), or legacy drivers.
            * **High-Concurrency Workloads:** Services where platform thread pool exhaustion historically limited system scalability.
            """
        )

    # Technical Prerequisites
    st.subheader("Mandatory Technical Prerequisites (§7.1.2)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric(label="JDK Runtime Baseline", value="OpenJDK 21 LTS")
        st.caption("Java 24+ for JEP 491 monitor unpinning; Java 25+ for JEP 506 Scoped Values standard.")
    with p2:
        st.metric(label="Framework Baseline", value="Spring Boot 3.2.0+")
        st.caption("This study evaluated Boot 3.5.12 with spring.threads.virtual.enabled: true.")
    with p3:
        st.metric(label="Observability Baseline", value="Continuous JFR")
        st.caption("Infrastructure capable of capturing jdk.VirtualThreadPinned streams and OS metrics.")

    # Dean's Directive Disclosure Box
    st.markdown(
        """
        <div class="callout-box callout-disclosure">
            <b>Point-of-Use AI Disclosure (Dean's Directive 1/2026):</b><br>
            Generative AI assistance (Claude 3.5 Sonnet) was utilized in drafting and formatting the checklist outlines 
            and decision tree prose in this migration guide. All architectural rules, refactoring patterns, and diagnostic 
            procedures were formulated, tested, and validated by the author based on empirical findings. 
            Full compliance details are formalized in §3.15.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Four-Phase Pre-Migration Pipeline
    st.subheader("The Four-Phase Pre-Migration Inventory Pipeline (§7.2)")
    st.markdown(
        """
        Enabling Virtual Threads in production without prior architectural auditing introduces severe failure modes, 
        including silent carrier starvation, connection pool exhaustion, and memory bloat. 
        Engineering teams must conduct this systematic four-phase inventory:
        """
    )

    pipe_col1, pipe_col2, pipe_col3, pipe_col4 = st.columns(4)
    with pipe_col1:
        st.markdown(
            """
            <div class="lab-card">
                <div style="color: var(--lab-blue); font-weight: 700; margin-bottom: 6px;">Phase 1: Code Audit</div>
                <ul style="font-size: 0.82rem; padding-left: 16px; margin: 0;">
                    <li>Scan <code>synchronized</code> blocks wrapping I/O or sleep</li>
                    <li>Inventory <code>ThreadLocal</code> usage across filters</li>
                    <li>Identify foreign JNI / Panama FFM bindings</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with pipe_col2:
        st.markdown(
            """
            <div class="lab-card">
                <div style="color: var(--lab-teal); font-weight: 700; margin-bottom: 6px;">Phase 2: Dependencies</div>
                <ul style="font-size: 0.82rem; padding-left: 16px; margin: 0;">
                    <li>Run <code>mvn dependency:tree -Dverbose</code></li>
                    <li>Verify JDBC drivers: pgjdbc &ge; 42.6.0, mysql &ge; 9.0.0</li>
                    <li>Verify Jackson Databind &ge; 2.16.0 buffer pooling</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with pipe_col3:
        st.markdown(
            """
            <div class="lab-card">
                <div style="color: var(--lab-amber); font-weight: 700; margin-bottom: 6px;">Phase 3: Database Pool</div>
                <ul style="font-size: 0.82rem; padding-left: 16px; margin: 0;">
                    <li>Audit connection checkout lifecycles vs transactions</li>
                    <li>Calibrate HikariCP sizing to DB hardware limits</li>
                    <li>Set workload-aligned connection timeouts</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with pipe_col4:
        st.markdown(
            """
            <div class="lab-card">
                <div style="color: var(--lab-violet); font-weight: 700; margin-bottom: 6px;">Phase 4: Observability</div>
                <ul style="font-size: 0.82rem; padding-left: 16px; margin: 0;">
                    <li>Deploy continuous JFR with custom thresholds</li>
                    <li>Track carrier worker queue dwell metrics</li>
                    <li>Monitor OS kernel thread wait-states (pidstat)</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 2: Interactive Decision Engine & Triage Wizard
# ==============================================================================
with tab2:
    st.header("Interactive Decision Engine & Architectural Triage Wizard (§7.6.2)")
    st.markdown(
        "Evaluate an enterprise component or request path against the non-short-circuiting 6-stage audit pipeline. "
        "Configure your component attributes below to generate an authoritative risk assessment and action plan."
    )

    triage_col_left, triage_col_right = st.columns([1, 1])

    with triage_col_left:
        st.subheader("Component Attributes & Questionnaire")

        # Stage 1: Dependencies
        st.markdown("**Stage 1: Third-Party Dependencies**")
        all_artifact_ids = [d.artifact_id for d in DEPENDENCIES_REGISTRY]
        selected_unverified = st.multiselect(
            "Select any unverified, legacy, or hazardous dependencies present in your application:",
            options=all_artifact_ids,
            default=[],
            help="Select dependencies that are either below baseline thresholds or hazardous (e.g. sqlite-jdbc, commons-pool2).",
        )

        # Stage 2: Native Boundary
        st.markdown("**Stage 2: Native & Foreign Functions (JNI / Panama FFM)**")
        q_has_jni = st.checkbox("Component invokes native C/C++ methods via JNI or Panama FFM", value=False)
        q_jni_blocking = False
        if q_has_jni:
            q_jni_blocking = st.checkbox(
                "Native call executes blocking syscalls (nanosleep, blocking read, POSIX mutex) or slow C computations",
                value=True,
            )

        # Stage 3: Synchronization
        st.markdown("**Stage 3: Synchronization & Lock Scopes**")
        q_target_jdk = st.selectbox("Target OpenJDK Runtime Baseline:", options=[21, 24, 25], index=0)
        q_has_sync = st.checkbox("Code uses 'synchronized' keyword enclosing blocking I/O, database access, or sleep", value=False)
        q_is_bottleneck = True
        if q_has_sync:
            q_is_bottleneck = st.checkbox(
                "The critical section serializes a shared domain resource (e.g. single-account payment gateway)",
                value=True,
                help="If True, Amdahl's Law caps throughput regardless of lock refactoring.",
            )

    with triage_col_right:
        st.subheader("Persistence, Context & Observability")

        # Stage 4: Database Connection Pool
        st.markdown("**Stage 4: Relational Database Persistence (HikariCP)**")
        q_uses_db = st.checkbox("Component acquires JDBC database connections", value=True)
        q_hold_time_ms = 300.0
        q_pool_size = 10
        q_concurrency_vus = 50
        q_timeout_ms = 30000.0
        q_has_semaphore = False
        if q_uses_db:
            db_c1, db_c2 = st.columns(2)
            with db_c1:
                q_hold_time_ms = float(st.slider("Connection Hold Time across Transaction (ms):", 10, 1000, 300, 10))
                q_pool_size = int(st.slider("HikariCP maximumPoolSize:", 1, 50, 10, 1))
            with db_c2:
                q_concurrency_vus = int(st.slider("Concurrent Request Concurrency (VUs):", 10, 200, 50, 10))
                q_timeout_ms = float(st.select_slider("HikariCP connectionTimeout (ms):", options=[250, 500, 1000, 5000, 30000], value=30000))
            q_has_semaphore = st.checkbox("Application-level Semaphore gates connection-acquiring operations", value=False)

        # Stage 5: Context & ThreadLocal
        st.markdown("**Stage 5: Context Propagation & ThreadLocal Lifecycle**")
        q_uses_tl = st.checkbox("Component uses ThreadLocal for request context (e.g. SecurityContext, TenantContext)", value=True)
        q_has_finally = True
        q_threads = 10000
        q_payload_kb = 50.0
        if q_uses_tl:
            q_has_finally = st.checkbox("Cleanup is guaranteed via try-finally { context.remove(); }", value=True)
            tl_c1, tl_c2 = st.columns(2)
            with tl_c1:
                q_threads = int(st.slider("Target Concurrent Virtual Threads:", 1000, 100000, 10000, 1000))
            with tl_c2:
                q_payload_kb = float(st.slider("Context Payload Size per Thread (KB):", 5, 200, 50, 5))

        # Stage 6: Observability
        st.markdown("**Stage 6: Observability Infrastructure**")
        q_jfr_enabled = st.checkbox("Java Flight Recorder (JFR) continuous recording enabled", value=True)
        q_jfr_thresh = 20.0
        if q_jfr_enabled:
            q_jfr_thresh = float(st.slider("jdk.VirtualThreadPinned threshold (ms):", 1, 30, 20, 1))
        q_carrier_metrics = st.checkbox("Scheduler carrier queue latency & OS thread metrics monitored", value=False)
        q_compute_work = st.checkbox("Component executes heavy CPU-bound computation", value=False)

    # Run Triage Audit Pipeline
    assessment = evaluate_migration_readiness(
        unverified_dependencies=selected_unverified,
        has_jni=q_has_jni,
        jni_is_blocking_or_unpredictable=q_jni_blocking,
        has_blocking_sync=q_has_sync,
        is_domain_bottleneck=q_is_bottleneck,
        target_jdk_version=q_target_jdk,
        uses_database=q_uses_db,
        connection_hold_time_ms=q_hold_time_ms,
        hikari_pool_size=q_pool_size,
        concurrent_vus=q_concurrency_vus,
        connection_timeout_ms=q_timeout_ms,
        has_app_semaphore=q_has_semaphore,
        uses_threadlocal=q_uses_tl,
        has_finally_remove=q_has_finally,
        estimated_context_kb=q_payload_kb,
        expected_concurrent_threads=q_threads,
        has_jfr_enabled=q_jfr_enabled,
        jfr_threshold_ms=q_jfr_thresh,
        monitors_carrier_metrics=q_carrier_metrics,
        has_compute_bound_work=q_compute_work,
    )

    st.markdown("---")
    st.subheader("Architectural Triage Assessment & Scorecard")

    # Composite Risk Card
    risk_colors = {
        "CRITICAL": "#fb7185",
        "HIGH": "#fdba74",
        "MEDIUM": "#fbbf24",
        "LOW": PALETTE["accent_blue"],
        "CLEAN": PALETTE["accent_green"],
    }
    comp_color = risk_colors.get(assessment.composite_risk, PALETTE["text_muted"])

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(
            f"""
            <div class="lab-card risk-summary">
                <small>Composite readiness risk</small>
                <span class="badge badge-status" style="--badge-color: {comp_color}">{assessment.composite_risk}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m_col2:
        st.metric("Blocking Issues (Critical/High)", assessment.blocking_issues_count)
    with m_col3:
        st.metric("Advisory Warnings (Med/Low)", assessment.advisory_issues_count)
    with m_col4:
        st.metric("Prescribed Rules / Patterns", f"{len(assessment.prescribed_rules)} Rules · {len(assessment.prescribed_patterns)} Patterns")

    # Stage-by-Stage Results Table
    st.markdown("#### Stage-by-Stage Non-Short-Circuiting Audit Results")
    stage_rows = []
    for s in assessment.stage_results:
        stage_rows.append({
            "Stage": f"Stage {s['stage']}",
            "Audit Checkpoint": s["name"],
            "Risk Level": s["risk"],
            "Detailed Findings": s["details"],
        })
    st.dataframe(pd.DataFrame(stage_rows), hide_index=True, width="stretch")

    # Prescribed Actions
    c_act1, c_act2 = st.columns([3, 2])
    with c_act1:
        st.markdown("#### Prescribed Corrective Actions")
        if assessment.prescribed_actions:
            for act in assessment.prescribed_actions:
                st.markdown(f"* ⚠️ **Action:** {act}")
        else:
            st.success("✅ No corrective actions required. Component is compliant with virtual-thread architectural standards.")

    with c_act2:
        st.markdown("#### Applicable Invariant Rules & Patterns")
        if assessment.prescribed_rules:
            st.markdown("**Governing Rules:**")
            for r_num in assessment.prescribed_rules:
                r_obj = CORE_RULES[r_num]
                st.markdown(f"* **Rule {r_num}** ({r_obj.claim_id}): {r_obj.name}")
        if assessment.prescribed_patterns:
            st.markdown("**Prescribed Refactoring Patterns:**")
            for p_id in assessment.prescribed_patterns:
                p_obj = REFACTORING_PATTERNS[p_id]
                st.markdown(f"* **{p_id}**: {p_obj.title}")

    # Dual Card / Mermaid view
    st.markdown("---")
    st.subheader("Audit Pipeline Decision Path Visualizer")
    view_mode = st.radio("Select View Mode:", options=["Stage cards", "Mermaid diagram source"], horizontal=True)

    if view_mode == "Mermaid diagram source":
        st.markdown(
            """
            ```mermaid
            graph TD
                Start["Begin Audit Pipeline"] --> CheckDeps{"1. Dependencies Baseline?"}
                CheckDeps -- "Fail / Hazardous" --> S1Fail["Stage 1: Resolve Dependencies (Table 7.1)"]
                CheckDeps -- "Pass" --> CheckJNI
                S1Fail --> CheckJNI

                CheckJNI{"2. Foreign JNI Boundary?"}
                CheckJNI -- "Blocking / Slow C" --> S2Fail["Stage 2: Offload to Platform Pool (Pattern 2)"]
                CheckJNI -- "None or In-Memory" --> CheckSync
                S2Fail --> CheckSync

                CheckSync{"3. Synchronized Monitors?"}
                CheckSync -- "Java 24+" --> S3Pass["Stage 3: JEP 491 Unpinned (Audit Residuals)"]
                CheckSync -- "Java 21 Domain Bottleneck" --> S3Serial["Stage 3: Preserve Serialization (Rule 1)"]
                CheckSync -- "Java 21 Starving Carrier" --> S3Refactor["Stage 3: ReentrantLock (Pattern 1)"]
                CheckSync -- "None" --> CheckDB
                S3Pass --> CheckDB
                S3Serial --> CheckDB
                S3Refactor --> CheckDB

                CheckDB{"4. Database Connection Checkout?"}
                CheckDB -- "Queue Wait > Timeout" --> S4Cascade["Stage 4: Timeout Cascade Risk (Rule 3)"]
                CheckDB -- "Pool Sized / Semaphore" --> S4Pass["Stage 4: Pool Sizing Calibrated"]
                CheckDB -- "No DB" --> CheckTL
                S4Cascade --> CheckTL
                S4Pass --> CheckTL

                CheckTL{"5. ThreadLocal Context?"}
                CheckTL -- "Missing finally remove" --> S5Leak["Stage 5: Memory Bloat Hazard (Rule 5)"]
                CheckTL -- "Finally remove / Java 25" --> S5Pass["Stage 5: Scoped Values / Clean Lifecycle"]
                CheckTL -- "No TL" --> CheckObs
                S5Leak --> CheckObs
                S5Pass --> CheckObs

                CheckObs{"6. Continuous JFR & Telemetry?"}
                CheckObs -- "Threshold > 5ms / No OS Metrics" --> S6Advisory["Stage 6: Deploy low-threshold.jfc"]
                CheckObs -- "Full Telemetry" --> Done["Complete Audit with Measured Evidence"]
                S6Advisory --> Done
            ```
            """
        )
    else:
        for s in assessment.stage_results:
            color = risk_colors.get(s["risk"], "#8b949e")
            st.markdown(
                f"""
                <div class="lab-card">
                    <div class="lab-card-heading">
                        <span style="font-weight: 700; color: var(--lab-ink);">Stage {s['stage']}: {s['name']}</span>
                        <span class="badge badge-status" style="--badge-color: {color}">{s['risk']}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--lab-muted); margin-top: 6px;">{s['details']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==============================================================================
# TAB 3: The Five Core Architectural Rules
# ==============================================================================
with tab3:
    st.header("The Five Core Architectural Migration Rules (§7.3)")
    st.markdown(
        "Formally proven architectural propositions governing virtual thread adoption, "
        "calibrated against empirical benchmarks and traceable to the Claim-to-Evidence Ledger."
    )

    selected_rule_id = st.radio(
        "Select Architectural Rule to Inspect:",
        options=[1, 2, 3, 4, 5],
        format_func=lambda r: f"Rule {r}: {CORE_RULES[r].name} ({CORE_RULES[r].claim_id})",
        horizontal=True,
    )

    rule = CORE_RULES[selected_rule_id]

    st.markdown(
        f"""
        <div class="lab-card">
            <div class="lab-card-heading">
                <span style="font-size: 1.2rem; font-weight: 700; color: var(--lab-blue);">Rule {rule.rule_number}: {rule.name}</span>
                <span>
                    <span class="badge badge-primary">{rule.claim_id}</span>
                    <span class="badge badge-supporting">{rule.epistemic_badge}</span>
                </span>
            </div>
            <div style="font-style: italic; color: var(--lab-ink); font-size: 0.95rem; border-left: 3px solid #58a6ff; padding-left: 12px; margin-bottom: 14px;">
                "{rule.proposition}"
            </div>
            <div style="font-size: 0.88rem; color: var(--lab-muted); line-height: 1.5;">
                <b style="color: var(--lab-ink);">Queueing Reality:</b> {rule.queueing_reality}<br><br>
                <b style="color: var(--lab-ink);">Empirical Grounding:</b> {rule.rationale}<br><br>
                <b style="color: var(--lab-ink);">Evidentiary Stratum:</b> {rule.evidence_stratum}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # When to Apply vs When Not to Apply
    st.subheader("Application Boundary & Decision Matrix")
    rule_app_c1, rule_app_c2 = st.columns(2)

    with rule_app_c1.container(border=True):
        st.badge("When to apply", color="green")
        if selected_rule_id == 1:
            st.markdown(
                "- When measured deployment shows carrier scarcity (e.g. parallelism=1 or pinned workers).\n"
                "- When carrier pinning by Service X blocks or starves unrelated Services Y and Z.\n"
                "- When lock duration is unpredictable or dominated by network I/O."
            )
        elif selected_rule_id == 2:
            st.markdown(
                "- Any JNI or Panama FFM call executing POSIX blocking calls (nanosleep, read, connect).\n"
                "- C database drivers (e.g. SQLite C engine) or hardware HSM libraries.\n"
                "- Any native operation exceeding 50 µs without cooperative JVM yield points."
            )
        elif selected_rule_id == 3:
            st.markdown(
                "- When migrating Spring Boot MVC workloads with JDBC / JPA persistence to virtual threads.\n"
                "- When concurrent request ingress scales from 10 to 1,000+ virtual threads.\n"
                "- When calibrating HikariCP maximumPoolSize and acquisition timeouts."
            )
        elif selected_rule_id == 4:
            st.markdown(
                "- Production APM and continuous monitoring architectures.\n"
                "- Whenever evaluating virtual thread unmounting behavior across native or third-party boundaries.\n"
                "- Pre-production load tests where micro-pinning (< 20 ms) must be diagnosed."
            )
        elif selected_rule_id == 5:
            st.markdown(
                "- High-throughput request paths using ThreadLocal for security, tenancy, or MDC logging.\n"
                "- In Java 21 LTS: whenever ThreadLocal.set() is invoked in filters or interceptors.\n"
                "- In Java 25 LTS: standard migration from ThreadLocal to Scoped Values."
            )

    with rule_app_c2.container(border=True):
        st.badge("Anti-patterns", color="orange")
        if selected_rule_id == 1:
            st.markdown(
                "- Do NOT refactor when the critical section represents an application domain serialization bottleneck.\n"
                "- Do NOT replace fast in-memory synchronized blocks (< 10 µs); unpinning yields 0% benefit and introduces AQS barging jitter.\n"
                "- Do NOT refactor without guaranteed try-finally unlock."
            )
        elif selected_rule_id == 2:
            st.markdown(
                "- Do NOT offload pure Java blocking I/O (RestTemplate, JDBC, Kafka) — virtual threads unmount natively!\n"
                "- Do NOT offload fast in-memory SIMD or native hashing (< 10 µs) — adds thread pool context-switch overhead.\n"
                "- NEVER configure CallerRunsPolicy on the platform offloading pool (causes instant carrier starvation!)."
            )
        elif selected_rule_id == 3:
            st.markdown(
                "- Do NOT scale HikariCP pool size proportionally to virtual thread concurrency (e.g. 500 connections for 500 VUs).\n"
                "- Do NOT rely on HikariCP's default 30-second connection acquisition timeout under high concurrency.\n"
                "- Do NOT hold physical JDBC connections across external HTTP calls or pre-query delays."
            )
        elif selected_rule_id == 4:
            st.markdown(
                "- NEVER enable -Djdk.tracePinnedThreads in high-throughput production (induces severe console I/O serialization).\n"
                "- Do NOT assume 0 JFR pinning events means carrier availability (native blocking emits 0 pinning events!).\n"
                "- Do NOT query ForkJoinPool.commonPool() for virtual thread carrier metrics."
            )
        elif selected_rule_id == 5:
            st.markdown(
                "- Do NOT pool virtual threads to avoid ThreadLocal allocations (pooling virtual threads is an explicit anti-pattern).\n"
                "- Do NOT enable Scoped Values in Java 21 production without executive preview flag approval.\n"
                "- Do NOT omit try-finally { remove(); } on ThreadLocal request-scoped contexts."
            )

    # Jump Buttons / Navigation Guidance
    st.markdown("---")
    st.markdown("#### Traceable Empirical Evidence in Experiment Explorer")
    if selected_rule_id == 1:
        st.info("💡 **Evidence Page:** Inspect empirical single-carrier synchronization benchmarks on **Page 02 · Synchronization Matrix** (Stratum 1 & 5).")
    elif selected_rule_id == 2:
        st.info("💡 **Evidence Page:** Inspect native C blocking and 0-pinning silent carrier starvation on **Page 04 · JNI Native Boundary** (Stratum 3).")
    elif selected_rule_id == 3:
        st.info("💡 **Evidence Page:** Inspect connection contention ablation and Little's Law pool saturation on **Page 05 · Database Persistence** (Stratum 8).")
    elif selected_rule_id == 4:
        st.info("💡 **Evidence Page:** Compare multi-tier telemetry and diagnostic JFR events across **Page 02 · Synchronization** and **Page 04 · JNI Boundary**.")
    elif selected_rule_id == 5:
        st.info("💡 **Evidence Page:** Review baseline request context models and memory profiling on **Page 01 · Overview & Inventory**.")


# ==============================================================================
# TAB 4: Mathematical Capacity & Sizing Calculators
# ==============================================================================
with tab4:
    st.header("Mathematical Capacity & Sizing Calculators (§7.3 & §6.1–6.2)")
    st.markdown(
        "Interactive queueing-theoretic calculators modeling Amdahl's Law, Little's Law, "
        "and ThreadLocal heap footprint scaling under virtual threads."
    )

    calc_sub1, calc_sub2, calc_sub3 = st.tabs([
        "Mutex saturation",
        "HikariCP pool",
        "ThreadLocal heap",
    ])

    # 1. Mutex Saturation Calculator
    with calc_sub1:
        st.subheader("Mutex Serialization Saturation Calculator (Amdahl's Law)")
        st.markdown(
            "When a critical section serializes requests, maximum throughput is strictly capped by "
            "$\\mu = 1 / T_{\\text{critical}}$, regardless of whether `synchronized` or `ReentrantLock` is used."
        )

        c_s1, c_s2 = st.columns(2)
        with c_s1:
            sl_crit_ms = float(st.slider("Critical Section Service Demand S (ms):", 10.0, 1000.0, 500.0, 10.0))
        with c_s2:
            sl_vus = int(st.slider("Concurrent Virtual Users N:", 1, 100, 10, 1))

        demand_calc = calculate_service_demand_capacity(service_demand_ms=sl_crit_ms, concurrent_vus=sl_vus)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Amdahl Theoretical Ceiling", f"{demand_calc['max_throughput_rps']:.2f} req/s")
        m2.metric("Achieved Closed-Loop TP", f"{demand_calc['achieved_throughput_rps']:.2f} req/s")
        m3.metric("Expected Response Time", f"{demand_calc['expected_latency_ms']:.1f} ms")
        m4.metric("Bottleneck Saturation", f"{demand_calc['saturation_ratio'] * 100:.1f} %")

        # Generate Plotly Curve: Concurrency vs Throughput & Latency
        vu_range = np.arange(1, 101, 1)
        tp_curve = []
        lat_curve = []
        for vu in vu_range:
            c_res = calculate_service_demand_capacity(service_demand_ms=sl_crit_ms, concurrent_vus=int(vu))
            tp_curve.append(c_res["achieved_throughput_rps"])
            lat_curve.append(c_res["expected_latency_ms"])

        fig_mutex = go.Figure()
        fig_mutex.add_trace(go.Scatter(
            x=vu_range,
            y=tp_curve,
            name="Achieved Throughput (req/s)",
            line=dict(color=PALETTE["accent_blue"], width=2.5),
            yaxis="y1",
        ))
        fig_mutex.add_trace(go.Scatter(
            x=[1, 100],
            y=[demand_calc["max_throughput_rps"], demand_calc["max_throughput_rps"]],
            name=f"Amdahl Capacity Ceiling ({demand_calc['max_throughput_rps']:.2f} req/s)",
            line=dict(color=PALETTE["accent_red"], width=1.5, dash="dash"),
            yaxis="y1",
        ))
        fig_mutex.add_trace(go.Scatter(
            x=vu_range,
            y=lat_curve,
            name="Expected Latency (ms)",
            line=dict(color=PALETTE["accent_amber"], width=2, dash="dot"),
            yaxis="y2",
        ))

        # Stratum 1 Empirical Point Overlay (if S=500 ms)
        if abs(sl_crit_ms - 500.0) < 1e-3:
            fig_mutex.add_trace(go.Scatter(
                x=[10],
                y=[1.97],
                mode="markers",
                name="Stratum 1 Empirical (1.97 req/s, 4,960 ms)",
                marker=dict(size=12, color=PALETTE["accent_green"], symbol="diamond"),
                yaxis="y1",
            ))

        fig_mutex.update_layout(
            xaxis_title="Concurrent Clients (VUs)",
            yaxis=dict(title="Throughput (req/s)", side="left", gridcolor="#21262d"),
            yaxis2=dict(title="Response Time (ms)", side="right", overlaying="y", gridcolor="#21262d", showgrid=False),
        )
        fig_mutex = apply_dark_scientific_layout(
            fig_mutex,
            title=f"Mutex saturation · {sl_crit_ms:.0f} ms demand",
            height=400,
        )
        for trace in fig_mutex.data:
            unit_value = "%{y:,.1f} ms" if trace.yaxis == "y2" else "%{y:.3f} req/s"
            trace.hovertemplate = hover_card(trace.name, unit_value, "Clients · %{x}",
                                            trace.marker.color or trace.line.color)
        st.plotly_chart(fig_mutex, width="stretch", theme=None)

        if abs(sl_crit_ms - 500.0) < 1e-3 and sl_vus == 10:
            st.success(
                "🎯 **Empirical Match:** Theoretical Little's Law capacity is **2.00 req/s** and **5,000 ms**. "
                "Stratum 1 measured **1.97 req/s** and **4,960 ms** (conforming within 1.5% of theory!)."
            )

    # 2. HikariCP Pool Sizing Calculator
    with calc_sub2:
        st.subheader("HikariCP Connection Pool Sizing & Contention (Stratum 8 Validation)")
        st.markdown(
            "Downstream Bottleneck Shift: Virtual threads eliminate carrier pool constraints, transferring queue formation "
            "in full to HikariCP. Maximum capacity is strictly bounded by $X_{\\text{max}} = K / T_{\\text{hold}}$."
        )

        h_c1, h_c2, h_c3 = st.columns(3)
        with h_c1:
            h_hold_ms = float(st.slider("Hold Time T_hold across Transaction (ms):", 50.0, 1000.0, 300.0, 25.0))
            h_pool_k = int(st.slider("HikariCP Pool Size K:", 1, 50, 10, 1))
        with h_c2:
            h_vus_n = int(st.slider("Offered Concurrency N (Virtual Users):", 10, 100, 50, 5))
            h_timeout_ms = float(st.select_slider("Acquisition Timeout (ms):", options=[250, 500, 1000, 5000, 15000, 30000], value=30000))
        with h_c3:
            db_cores = int(st.number_input("Database Server Physical Cores:", min_value=1, max_value=64, value=4))
            db_spindles = int(st.number_input("Effective Disk Spindle Count:", min_value=1, max_value=16, value=1))
            wooldridge_bound = (db_cores * 2) + db_spindles
            st.markdown(
                f"""
                <div class="lab-card">
                    <div style="font-size: 0.75rem; color: var(--lab-muted);">Wooldridge Hardware Sizing Bound:</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--lab-teal);">{wooldridge_bound} Connections</div>
                    <div style="font-size: 0.75rem; color: var(--lab-muted);">(Cores × 2 + Spindles)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        pool_calc = calculate_downstream_pool_capacity(
            pool_size=h_pool_k,
            hold_time_ms=h_hold_ms,
            concurrent_vus=h_vus_n,
            connection_timeout_ms=h_timeout_ms,
        )

        p_m1, p_m2, p_m3, p_m4 = st.columns(4)
        p_m1.metric("Pool Throughput Capacity", f"{pool_calc['max_throughput_rps']:.2f} req/s")
        p_m2.metric("Closed-Loop Latency", f"{pool_calc['closed_loop_latency_ms']:.1f} ms")
        p_m3.metric("HikariCP Queue Wait", f"{pool_calc['queue_wait_ms']:.1f} ms")
        p_m4.metric("Active / Queued Conns", f"{pool_calc['active_connections']} / {pool_calc['queued_requests']}")

        # Plotly chart: Pool Size K vs Throughput & Queue Latency
        k_range = np.arange(1, 31, 1)
        k_tp = []
        k_lat = []
        for k_val in k_range:
            p_res = calculate_downstream_pool_capacity(pool_size=int(k_val), hold_time_ms=h_hold_ms, concurrent_vus=h_vus_n)
            k_tp.append(p_res["closed_loop_throughput_rps"])
            k_lat.append(p_res["closed_loop_latency_ms"])

        fig_pool = go.Figure()
        fig_pool.add_trace(go.Scatter(
            x=k_range,
            y=k_tp,
            name="Modeled closed-loop throughput",
            line=dict(color=PALETTE["accent_blue"], width=2.5),
            yaxis="y1",
        ))
        fig_pool.add_trace(go.Scatter(
            x=k_range,
            y=k_lat,
            name="Expected Response Time (ms)",
            line=dict(color=PALETTE["accent_amber"], width=2, dash="dot"),
            yaxis="y2",
        ))

        # Overlay Stratum 8 Empirical Points (if hold_time = 300 ms and N = 50 VUs)
        if abs(h_hold_ms - 300.0) < 1e-3 and h_vus_n == 50:
            s8_records = [r for r in load_persistence_experiments() if "Stratum 8" in r.treatment]
            p1_runs = [r for r in s8_records if r.pool_size == 1]
            p10_runs = [r for r in s8_records if r.pool_size == 10]

            if p1_runs:
                avg_p1_tp = sum(r.hold_tp for r in p1_runs) / len(p1_runs)
                avg_p1_lat = sum(r.hold_p50 for r in p1_runs) / len(p1_runs)
                fig_pool.add_trace(go.Scatter(
                    x=[1],
                    y=[avg_p1_tp],
                    mode="markers",
                    name="Pool 1 · measured throughput",
                    marker=dict(size=12, color=PALETTE["accent_purple"], symbol="diamond"),
                    yaxis="y1",
                ))
                fig_pool.add_trace(go.Scatter(
                    x=[1],
                    y=[avg_p1_lat],
                    mode="markers",
                    name="Pool 1 · measured p50",
                    marker=dict(size=10, color=PALETTE["accent_purple"], symbol="circle-open"),
                    yaxis="y2",
                ))
            if p10_runs:
                avg_p10_tp = sum(r.hold_tp for r in p10_runs) / len(p10_runs)
                avg_p10_lat = sum(r.hold_p50 for r in p10_runs) / len(p10_runs)
                fig_pool.add_trace(go.Scatter(
                    x=[10],
                    y=[avg_p10_tp],
                    mode="markers",
                    name="Pool 10 · measured throughput",
                    marker=dict(size=12, color=PALETTE["accent_green"], symbol="diamond"),
                    yaxis="y1",
                ))
                fig_pool.add_trace(go.Scatter(
                    x=[10],
                    y=[avg_p10_lat],
                    mode="markers",
                    name="Pool 10 · measured p50",
                    marker=dict(size=10, color=PALETTE["accent_green"], symbol="circle-open"),
                    yaxis="y2",
                ))

        # Add Wooldridge hardware ceiling dashed line
        fig_pool.add_vline(
            x=wooldridge_bound,
            line_dash="dash",
            line_color=PALETTE["accent_cyan"],
            annotation_text=f"Wooldridge · {wooldridge_bound} conns", line_width=1.5,
            annotation_font_color=PALETTE["accent_cyan"], annotation_bgcolor=PALETTE["card_dark"],
            annotation_position="top right",
        )

        fig_pool.update_layout(
            xaxis_title="HikariCP maximumPoolSize (K)",
            yaxis=dict(title="Throughput (req/s)", side="left", gridcolor="#21262d"),
            yaxis2=dict(title="Response Time (ms)", side="right", overlaying="y", gridcolor="#21262d", showgrid=False),
        )
        fig_pool = apply_dark_scientific_layout(
            fig_pool,
            title=f"Pool scaling · {h_hold_ms:.0f} ms hold · {h_vus_n} VUs",
            height=420,
        )
        for trace in fig_pool.data:
            unit_value = "%{y:,.1f} ms" if trace.yaxis == "y2" else "%{y:.3f} req/s"
            trace.hovertemplate = hover_card(trace.name, unit_value, "Connections · %{x}",
                                            trace.marker.color or trace.line.color)
        st.plotly_chart(fig_pool, width="stretch", theme=None)

        if pool_calc["timeout_vulnerable"]:
            st.error(
                f"🚨 **Timeout Cascade Risk:** Queue wait time ({pool_calc['queue_wait_ms']:.1f} ms) exceeds the configured "
                f"acquisition timeout ({h_timeout_ms:.1f} ms). Virtual threads will throw SQLTransientConnectionException!"
            )

    # 3. ThreadLocal Heap Memory Scaling Calculator
    with calc_sub3:
        st.subheader("ThreadLocal Heap Memory Scaling Calculator (Rule 5 / CLM-RQ2-07)")
        st.markdown(
            "In traditional bounded platform thread pools, total ThreadLocal retained memory is bounded by "
            "$N_{\\text{workers}} \\times M_{\\text{context}}$. Under unconstrained virtual threads, memory scales to "
            "$N_{\\text{virtual}} \\times M_{\\text{context}}$."
        )

        tl_c1, tl_c2, tl_c3 = st.columns(3)
        with tl_c1:
            sl_threads = int(st.slider("Concurrent Virtual Threads:", 1000, 200000, 100000, 5000))
        with tl_c2:
            sl_ctx_kb = float(st.slider("Context Payload Size per Thread (KB):", 1.0, 200.0, 50.0, 5.0))
        with tl_c3:
            sl_plat_workers = int(st.slider("Platform Thread Pool Size:", 50, 500, 200, 25))

        mem_calc = calculate_threadlocal_heap_footprint(
            concurrent_virtual_threads=sl_threads,
            context_payload_kb=sl_ctx_kb,
            platform_pool_workers=sl_plat_workers,
        )

        tm1, tm2, tm3, tm4 = st.columns(4)
        tm1.metric("Platform Thread Memory", f"{mem_calc['platform_heap_mb']:.2f} MB")
        tm2.metric("Virtual Thread Memory", f"{mem_calc['virtual_heap_gb']:.3f} GB")
        tm3.metric("Heap Expansion Ratio", f"{mem_calc['expansion_ratio']:.1f} ×")
        tm4.metric("Retention Risk Rating", mem_calc["risk_level"])

        # Plotly Bar Chart: Platform vs Virtual Thread Retention
        fig_mem = go.Figure()
        fig_mem.add_trace(go.Bar(
            x=["Platform Threads (Bounded)", "Virtual Threads (Unbounded)"],
            y=[mem_calc["platform_heap_mb"], mem_calc["virtual_heap_mb"]],
            text=[f"{mem_calc['platform_heap_mb']:.1f} MB", f"{mem_calc['virtual_heap_mb']:.1f} MB ({mem_calc['virtual_heap_gb']:.2f} GB)"],
            textposition="auto",
            marker_color=[PALETTE["accent_blue"], PALETTE["accent_red"] if mem_calc["risk_level"] == "CRITICAL" else PALETTE["accent_amber"]],
        ))
        fig_mem.update_layout(
            yaxis_title="Retained Memory Footprint (MB)",
        )
        fig_mem = apply_dark_scientific_layout(
            fig_mem,
            title=f"Modeled heap · {sl_ctx_kb:.0f} KB per thread", hover_value="%{text}",
            height=380,
        )
        st.plotly_chart(fig_mem, width="stretch", theme=None)

        st.caption(
            "Note: This calculation represents an arithmetic theoretical worst-case projection (CLM-RQ2-07). "
            "Actual heap consumption depends on GC cadence, payload deep object reachability, and virtual thread transience."
        )


# ==============================================================================
# TAB 5: Ecosystem & Dependency Matrix
# ==============================================================================
with tab5:
    st.header("Third-Party Ecosystem & Dependency Matrix (§7.2.2 & Table 7.1)")
    st.markdown(
        "Evaluated dependency baselines, socket-lock compatibility, and carrier-risk triage across "
        "14 critical enterprise Java artifacts (5 from Chapter 7 Table 7.1 and 9 extended from the Invariant Ledger)."
    )

    dep_f1, dep_f2 = st.columns(2)
    with dep_f1:
        cat_filter = st.selectbox(
            "Filter by Risk Category:",
            options=["All Categories"] + sorted(list({d.risk_category for d in DEPENDENCIES_REGISTRY})),
            index=0,
        )
    with dep_f2:
        risk_filter = st.selectbox(
            "Filter by Evaluated Risk Level:",
            options=["All Risk Levels", "SAFE", "ACTION_REQUIRED", "HAZARDOUS"],
            index=0,
        )

    # Filter dependencies
    filtered_deps = DEPENDENCIES_REGISTRY
    if cat_filter != "All Categories":
        filtered_deps = [d for d in filtered_deps if d.risk_category == cat_filter]
    if risk_filter != "All Risk Levels":
        filtered_deps = [d for d in filtered_deps if d.risk_level == risk_filter]

    # Metrics Summary
    safe_cnt = sum(1 for d in DEPENDENCIES_REGISTRY if d.risk_level == "SAFE")
    act_cnt = sum(1 for d in DEPENDENCIES_REGISTRY if d.risk_level == "ACTION_REQUIRED")
    haz_cnt = sum(1 for d in DEPENDENCIES_REGISTRY if d.risk_level == "HAZARDOUS")

    dm1, dm2, dm3, dm4 = st.columns(4)
    dm1.metric("Total Cataloged Artifacts", len(DEPENDENCIES_REGISTRY))
    dm2.metric("Safe / Remediated", safe_cnt)
    dm3.metric("Action Required", act_cnt)
    dm4.metric("Hazardous / Unremediated", haz_cnt)

    # Interactive Table
    dep_table_data = []
    for d in filtered_deps:
        dep_table_data.append({
            "Artifact ID": d.artifact_id,
            "Component Name": d.component_name,
            "Evaluated Baseline": d.evaluated_baseline,
            "Resolved in Study": d.resolved_in_study or "N/A",
            "Category": d.risk_category,
            "Risk Level": [d.risk_level],
        })
    st.caption(f"{len(dep_table_data)} of {len(DEPENDENCIES_REGISTRY)} dependencies match the filters.")
    if dep_table_data:
        st.dataframe(pd.DataFrame(dep_table_data), hide_index=True, width="stretch", column_config={
            "Component Name": st.column_config.TextColumn(pinned=True),
            "Risk Level": st.column_config.MultiselectColumn(
                options=["SAFE", "ACTION_REQUIRED", "HAZARDOUS"],
                color=[PALETTE["accent_green"], PALETTE["accent_amber"], PALETTE["accent_red"]],
            ),
        })
    else:
        st.info("No dependencies match these filters.")

    # Detailed Accordions
    st.subheader("Detailed Technical Rationale & Remediation Actions")
    for d in filtered_deps:
        with st.expander(f"{d.component_name} ({d.artifact_id}) — {d.risk_level}"):
            st.markdown(
                f"""
                * **Artifact:** ` {d.artifact_id} `
                * **Evaluated Baseline:** **{d.evaluated_baseline}**
                * **Resolved in This Study:** ` {d.resolved_in_study or 'N/A'} `
                * **Risk Category:** {d.risk_category}
                * **Rationale:** {d.rationale}
                * **Source / Issue:** {d.source_issue}
                * **Remediation Action:** **{d.remediation_action}**
                """
            )


# ==============================================================================
# TAB 6: Correctness-Preserving Refactoring Patterns
# ==============================================================================
with tab6:
    st.header("Correctness-Preserving Refactoring Patterns (§7.4)")
    st.markdown(
        "Production-grade 'Before & After' implementation patterns demonstrating safe refactoring "
        "for enterprise Spring Boot MVC systems adopting Virtual Threads."
    )

    pat_sel = st.selectbox(
        "Select Refactoring Pattern to Inspect:",
        options=list(REFACTORING_PATTERNS.keys()),
        format_func=lambda k: f"{k}: {REFACTORING_PATTERNS[k].title}",
    )

    pat = REFACTORING_PATTERNS[pat_sel]

    st.markdown(
        f"""
        <div class="lab-card">
            <div class="lab-card-heading">
                <span style="font-size: 1.15rem; font-weight: 700; color: var(--lab-blue);">{pat.pattern_id}: {pat.title}</span>
                <span>
                    <span class="badge badge-supporting">{pat.target_jdk}</span>
                    <span class="badge badge-primary">{pat.epistemic_class}</span>
                </span>
            </div>
            <div style="color: var(--lab-muted); font-size: 0.88rem;">{pat.problem_statement}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    code_tab_before, code_tab_after = st.tabs(["Before · Anti-pattern", "After · Refactored Java"])
    with code_tab_before:
        st.code(pat.before_code, language="java")
    with code_tab_after:
        st.code(pat.after_code, language="java")

    # Invariants and Implementation Gotchas
    st.subheader("Architectural Invariants & Implementation Gotchas")
    for g in pat.invariants_and_gotchas:
        st.markdown(
            f"""
            <div class="callout-box" style="margin-bottom: 8px;">
                {g}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 7: Observability & JFR Protocol
# ==============================================================================
with tab7:
    st.header("Post-Migration Observability & Verification Protocol (§7.5)")
    st.markdown(
        "Multi-tier telemetry architecture combining Java Flight Recorder (JFR) continuous streaming, "
        "application queue metrics, and OS kernel thread monitoring."
    )

    # Diagnostic Flag Distinction Callout
    st.markdown(
        """
        <div class="callout-warning">
            <b>Diagnostic Flag Distinction (§7.5.1):</b><br>
            The JVM flag <code>-Djdk.tracePinnedThreads=short</code> (or <code>=full</code>) is a 
            <b>diagnostic console tracing mechanism</b> designed for local defect reproduction. 
            It prints call stacks directly to stderr/stdout. It must <b>NOT</b> be enabled in high-throughput 
            production environments, as synchronous console I/O induces severe thread serialization and carrier contention.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Interactive JFR Configuration & Flag Generator")
    jfr_c1, jfr_c2, jfr_c3 = st.columns(3)
    with jfr_c1:
        dump_exit = st.checkbox("Dump on JVM Exit (dumponexit)", value=True)
        disk_rec = st.checkbox("Disk-Backed Recording (disk)", value=True)
    with jfr_c2:
        max_age = st.selectbox("Max Recording Age (maxage):", ["1h", "6h", "12h", "24h"], index=2)
        max_size = st.selectbox("Max Recording Size (maxsize):", ["1g", "2g", "5g", "10g"], index=2)
    with jfr_c3:
        stack_depth = st.selectbox("Flight Recorder Stack Depth:", [64, 128, 256], index=1)
        jfr_threshold = st.selectbox("Pinning Threshold:", ["20 ms (Default profile.jfc)", "5 ms (low-threshold.jfc)"], index=1)

    # Generated Flag String
    rec_settings = f"dumponexit={'true' if dump_exit else 'false'},disk={'true' if disk_rec else 'false'},maxage={max_age},maxsize={max_size}"
    if "5 ms" in jfr_threshold:
        rec_settings += ",settings=low-threshold.jfc"
    else:
        rec_settings += ",settings=profile.jfc"

    jvm_flag_str = f'JAVA_OPTS="-XX:StartFlightRecording={rec_settings} -XX:FlightRecorderOptions=stackdepth={stack_depth}"'
    st.code(jvm_flag_str, language="bash")

    # low-threshold.jfc XML viewer
    st.subheader("Custom Staging Profile: `low-threshold.jfc`")
    st.markdown(
        "To reduce the default 20 ms blind spot in pre-production staging environments, deploy this custom JFC configuration:"
    )
    jfc_xml = """<configuration version="2.0" label="Virtual Threads Low-Threshold Profile">
  <!-- Enable continuous monitoring of virtual thread pinning with 5 ms threshold -->
  <event name="jdk.VirtualThreadPinned">
    <setting name="enabled">true</setting>
    <setting name="threshold">5 ms</setting>
    <setting name="stackTrace">true</setting>
  </event>
  <event name="jdk.VirtualThreadSubmitFailed">
    <setting name="enabled">true</setting>
    <setting name="stackTrace">true</setting>
  </event>
</configuration>"""
    st.code(jfc_xml, language="xml")

    # Observability Blind Spot Warning
    st.markdown(
        """
        <div class="callout-box">
            <b>Observability Caveat (§7.5.1 & CLM-METH-04):</b><br>
            A 5 ms threshold significantly reduces the 20 ms blind spot, but does not capture micro-pinning lasting &lt; 5 ms. 
            Furthermore, direct native C blocking calls (JNI / Panama) bypass continuation yielding completely and emit 
            <b>strictly 0 jdk.VirtualThreadPinned events</b>. JFR must therefore be complemented with OS-level telemetry 
            (<code>pidstat -t -p &lt;pid&gt;</code>, <code>top -H</code>, or eBPF off-CPU tracing) to detect captive carrier workers.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Verification Checklist (§7.5.2)
    st.subheader("Dual-Window Verification Protocol Checklist (§7.5.2 / CLM-METH-02)")
    chk1 = st.checkbox("Window Isolation: Ramp-up [0, 15s] strictly isolated from steady-state hold window [15, 45s].", value=True)
    chk2 = st.checkbox("Zero HTTP Defect Rate: Verify HTTP 5xx error rate remains strictly at 0.000%.", value=True)
    chk3 = st.checkbox("Carrier CPU Telemetry: Steady-state carrier CPU reflects active execution rather than idle wait-queue captivity.", value=True)
    chk4 = st.checkbox("HikariCP Pool Health: No connection acquisition timeouts or runaway pending queue escalations.", value=True)
    chk5 = st.checkbox("Heap Retention Audit: MAT / JProfiler heap dump confirms ThreadLocalMap objects do not accumulate.", value=True)


# ==============================================================================
# TAB 8: Master Decision Table & Exportable Audit Report
# ==============================================================================
with tab8:
    st.header("Master Decision Table & Exportable Audit Report (§7.6 & §7.7)")
    st.markdown(
        "Synthesized triage matrix and exportable architectural audit report generated from your active configuration."
    )

    # Table 7.2: Master Architectural Migration Decision Table
    st.subheader("Master Architectural Migration Triage and Action Matrix (Table 7.2)")
    table_7_2_data = [
        {
            "Observed Code / Architectural Pattern": "synchronized block wrapping socket / database I/O",
            "Direct Evidence": "jdk.VirtualThreadPinned >= 20 ms in JFR (CLM-RQ1-01)",
            "Risk": "CRITICAL",
            "Verification Check": "Verify whether critical section serializes a shared domain resource",
            "Safe Action": "Refactor to ReentrantLock (Pattern 1) if carriers starved; or evaluate Java 24 (JEP 491).",
            "Epistemic Status": "[MEASURED & EXT_SUPP]",
        },
        {
            "Observed Code / Architectural Pattern": "synchronized block protecting fast in-memory state",
            "Direct Evidence": "Zero JFR pinning events; duration < 10 µs",
            "Risk": "LOW",
            "Verification Check": "Verify no I/O, sleep, or network calls exist inside lock",
            "Safe Action": "Retain synchronized. Avoid refactoring to prevent AQS non-fair barging jitter.",
            "Epistemic Status": "[HEURISTIC / LITERATURE]",
        },
        {
            "Observed Code / Architectural Pattern": "Foreign function call via JNI (blocking system call)",
            "Direct Evidence": "Carrier starvation, ~1% CPU, 0 JFR pinning events (CLM-RQ2-01)",
            "Risk": "CRITICAL",
            "Verification Check": "Audit C/C++ source for blocking syscalls or long computations",
            "Safe Action": "Isolate blocking native calls to a dedicated bounded platform pool (Pattern 2).",
            "Epistemic Status": "[MEASURED & THEORETICAL]",
        },
        {
            "Observed Code / Architectural Pattern": "HikariCP database pool under high virtual thread load",
            "Direct Evidence": "Queueing bottleneck: pool 1 caps TP to 3.27 req/s; pool 10 scales to 32.60 req/s (CLM-RQ2-03)",
            "Risk": "HIGH",
            "Verification Check": "Measure connection hold time, arrival rate, active/pending counts, timeouts",
            "Safe Action": "Calibrate pool size and connectionTimeout; enforce application-level semaphores (Rule 3).",
            "Epistemic Status": "[MEASURED & EXT_SUPP]",
        },
        {
            "Observed Code / Architectural Pattern": "Heavy ThreadLocal usage in per-request filter chains",
            "Direct Evidence": "Theoretical heap expansion under load; uncollected ThreadLocal maps (CLM-RQ2-07)",
            "Risk": "MEDIUM",
            "Verification Check": "Audit heap dump under 10^5 concurrent requests for ThreadLocalMap",
            "Safe Action": "Enforce finally { remove(); } (Pattern 3A) or Scoped Values in Java 25 (Pattern 3B).",
            "Epistemic Status": "[THEORETICAL / CONDITIONAL]",
        },
        {
            "Observed Code / Architectural Pattern": "Legacy database driver (pgjdbc < 42.6.0, mysql < 9.0)",
            "Direct Evidence": "Internal monitor pinning reported in driver socket read methods",
            "Risk": "HIGH",
            "Verification Check": "Run mvn dependency:tree; inspect socket read call stacks in JFR",
            "Safe Action": "Upgrade dependency to evaluated version baseline (Table 7.1).",
            "Epistemic Status": "[EXTERNALLY SUPPORTED]",
        },
    ]
    st.dataframe(pd.DataFrame(table_7_2_data), hide_index=True, width="stretch")

    # Downstream Constraints Cards (§7.7)
    st.subheader("Systemic Boundaries and Downstream Constraints (§7.7)")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown(
            """
            <div class="lab-card">
                <b style="color: var(--lab-blue);">1. Database Server Hardware Capacity:</b><br>
                Virtual threads eliminate servlet-thread limits but do not increase database CPU, disk I/O, or WAL capacity. 
                Unconstrained traffic can overwhelm the relational engine. Coordinate with DBAs on <code>max_connections</code>.
            </div>
            <div class="lab-card">
                <b style="color: var(--lab-teal);">2. Downstream Network & Socket Starvation:</b><br>
                Multiplying outbound client concurrency by 100x can saturate downstream HTTP endpoints, NAT tables, 
                and exhaust ephemeral local ports (<code>TIME_WAIT</code> socket exhaustion). Bound outbound HTTP client pools.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with dc2:
        st.markdown(
            """
            <div class="lab-card">
                <b style="color: var(--lab-amber);">3. Kernel & Scheduler Switching Costs:</b><br>
                Carrier threads remain subject to operating system kernel scheduling. Repeated native blocking or page faults 
                induce scheduler context switching; evaluate with OS-level telemetry.
            </div>
            <div class="lab-card">
                <b style="color: var(--lab-violet);">4. Database Administrator (DBA) Coordination:</b><br>
                Any changes to HikariCP connection pool configurations or transaction boundaries must be coordinated 
                with DBA teams to prevent connection table exhaustion and memory pressure on the database server.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Exportable Architectural Audit Report
    st.markdown("---")
    st.subheader("Exportable Architectural Audit Report")
    st.markdown("Generate and download a comprehensive audit report based on the active triage evaluation from the Triage tab.")

    # Generate Markdown Report
    audit_params_summary = f"""* **Target OpenJDK Runtime:** OpenJDK {q_target_jdk}
* **Unverified / Legacy Dependencies:** {', '.join(selected_unverified) or 'None (All baseline compliant)'}
* **Foreign Function Boundary (JNI/Panama):** {'Yes (Blocking / slow calls: ' + str(q_jni_blocking) + ')' if q_has_jni else 'No'}
* **Synchronization around Blocking I/O:** {'Yes (Domain bottleneck: ' + str(q_is_bottleneck) + ')' if q_has_sync else 'No'}
* **Database Persistence (HikariCP):** {'Yes (Hold: ' + str(q_hold_time_ms) + ' ms, Pool: ' + str(q_pool_size) + ', VUs: ' + str(q_concurrency_vus) + ', Timeout: ' + str(q_timeout_ms) + ' ms, Semaphore: ' + str(q_has_semaphore) + ')' if q_uses_db else 'No'}
* **Context Propagation (ThreadLocal):** {'Yes (Guaranteed finally remove: ' + str(q_has_finally) + ', Threads: ' + str(q_threads) + ', Payload: ' + str(q_payload_kb) + ' KB)' if q_uses_tl else 'No'}
* **Continuous JFR Recording:** {'Enabled (Threshold: ' + str(q_jfr_thresh) + ' ms)' if q_jfr_enabled else 'Disabled'}
* **Carrier & OS Metrics Monitored:** {q_carrier_metrics}
* **Compute-Bound Algorithmic Work:** {q_compute_work}"""

    report_md = f"""# Virtual Threads Architectural Migration Audit Report
**Generated by Virtual Threads Experiment Explorer (Page 07)**  
**Target OpenJDK Runtime:** OpenJDK {q_target_jdk}  
**Framework Baseline:** Spring Boot 3.2.0+ (Evaluated: 3.5.12)  
**Composite Readiness Risk:** **{assessment.composite_risk}**  

---

## 1. Executive Summary
* **Composite Readiness Risk:** `{assessment.composite_risk}`
* **Blocking Architectural Issues:** `{assessment.blocking_issues_count}`
* **Advisory Warnings:** `{assessment.advisory_issues_count}`
* **Prescribed Migration Rules:** {', '.join([f'Rule {r} ({CORE_RULES[r].claim_id})' for r in assessment.prescribed_rules]) or 'None'}
* **Prescribed Refactoring Patterns:** {', '.join(assessment.prescribed_patterns) or 'None'}

---

## 2. Audit Questionnaire & Configured Parameters
{audit_params_summary}

---

## 3. Stage-by-Stage Non-Short-Circuiting Audit Findings
"""
    for s in assessment.stage_results:
        report_md += f"### Stage {s['stage']}: {s['name']}\n"
        report_md += f"* **Risk Level:** `{s['risk']}`\n"
        report_md += f"* **Details:** {s['details']}\n\n"

    report_md += "## 4. Prescribed Action Plan\n"
    if assessment.prescribed_actions:
        for act in assessment.prescribed_actions:
            report_md += f"* [ ] {act}\n"
    else:
        report_md += "* Component is compliant with virtual-thread architectural standards.\n"

    report_md += "\n---\n*Report generated in compliance with Chapter 7 Migration Guidance and the Claim-to-Evidence Ledger.*\n"

    # Generate JSON Report
    report_json_dict = {
        "report_metadata": {
            "title": "Virtual Threads Architectural Migration Audit Report",
            "target_jdk": q_target_jdk,
            "spring_boot_evaluated": "3.5.12",
        },
        "audit_parameters": {
            "target_jdk_version": q_target_jdk,
            "unverified_dependencies": selected_unverified,
            "has_jni": q_has_jni,
            "jni_is_blocking_or_unpredictable": q_jni_blocking,
            "has_blocking_sync": q_has_sync,
            "is_domain_bottleneck": q_is_bottleneck,
            "uses_database": q_uses_db,
            "hikari_pool_size": q_pool_size if q_uses_db else None,
            "connection_hold_time_ms": q_hold_time_ms if q_uses_db else None,
            "concurrent_vus": q_concurrency_vus if q_uses_db else None,
            "connection_timeout_ms": q_timeout_ms if q_uses_db else None,
            "has_app_semaphore": q_has_semaphore if q_uses_db else None,
            "uses_threadlocal": q_uses_tl,
            "has_finally_remove": q_has_finally if q_uses_tl else None,
            "expected_concurrent_threads": q_threads if q_uses_tl else None,
            "estimated_context_kb": q_payload_kb if q_uses_tl else None,
            "has_jfr_enabled": q_jfr_enabled,
            "jfr_threshold_ms": q_jfr_thresh if q_jfr_enabled else None,
            "monitors_carrier_metrics": q_carrier_metrics,
            "has_compute_bound_work": q_compute_work,
        },
        "assessment": {
            "composite_risk": assessment.composite_risk,
            "blocking_issues_count": assessment.blocking_issues_count,
            "advisory_issues_count": assessment.advisory_issues_count,
            "prescribed_rules": assessment.prescribed_rules,
            "prescribed_patterns": assessment.prescribed_patterns,
            "prescribed_actions": assessment.prescribed_actions,
            "stage_results": assessment.stage_results,
        },
    }
    report_json = json.dumps(report_json_dict, indent=2)

    rep_col1, rep_col2 = st.columns(2)
    with rep_col1:
        st.download_button(
            label="📥 Download Audit Report (.md)",
            data=report_md,
            file_name="virtual-threads-audit-report.md",
            mime="text/markdown",
            width="stretch",
        )
    with rep_col2:
        st.download_button(
            label="📥 Download Audit Data (.json)",
            data=report_json,
            file_name="virtual-threads-audit-report.json",
            mime="application/json",
            width="stretch",
        )
