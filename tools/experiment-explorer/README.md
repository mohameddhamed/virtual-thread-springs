# Virtual Threads Experiment Explorer

**Interactive Empirical Evidence Dashboard for MSc Thesis Research**  
*Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  

---

## 1. Overview & Research Objective

The **Virtual Threads Experiment Explorer** is a read-only, publication-grade scientific dashboard designed for academic review and empirical verification of my MSc thesis benchmarks. Instead of presenting static tables or disconnected benchmark screenshots, the explorer allows an academic supervisor to:
- Inspect all **76 normalized trial records** across **8 evidence strata**.
- Evaluate the **flagship synchronization matrix** where ReentrantLock completely eliminated 108 JFR pinning events while throughput remained bound to 1.97 req/s.
- Compare **Java 21 vs. Java 24 (JEP 491)** object monitor unpinning mechanics and latency queueing.
- Examine **JNI carrier captivity** during blocking native system calls (`nanosleep`) where JFR emitted zero pinning events despite carrier starvation.
- Contrast **relational persistence dynamics** between uncontended controls (Treatment A) and active connection-held contention (Treatment B / Stratum 8).
- Trace every displayed metric back to its **cryptographically verified raw JSONL, binary JFR, or telemetry CSV artifact**.

---

## 2. Technology Stack & Architectural Principles

- **Python 3.11+**
- **Streamlit** (Modern multipage routing via `st.navigation` & `st.Page`)
- **Plotly** (Publication-grade dark scientific interactive visualizations)
- **Pandas** (Data loading, grouping, and descriptive dispersion)
- **Pytest** (Automated empirical regression and cryptographic validation suite)

### Architectural Guardrails
1. **Zero UI Recalculation:** The dashboard never invents its own throughput or latency numbers. It strictly consumes verified records from `docs/evidence-freeze/metric-recalculations.csv` and `src/main/resources/static/data/normalized-evidence.json`.
2. **Dual-Window Reporting:** Every table and metric card exposes both the **Full Run [0, 55.0s]** and the **Steady-State Hold Window [15.0s, 45.0s]**. The hold window is explicitly identified as a constant-concurrency sampling interval, not proof of equilibrium.
3. **Descriptive Rigor ($N \le 3$):** Sample size restrictions are respected. The application displays sample means, standard deviations, min, max, and trial-level scatter overlays; it never manufactures artificial confidence intervals or false statistical significance.
4. **Offline & Standalone:** Operates directly on local repository files without external databases, container engines, or network calls.

---

## 3. Directory Layout

```
tools/experiment-explorer/
├── app.py                      # Main entry point & Streamlit configuration
├── DATA_CONTRACT.md            # Canonical data contract and schema definitions
├── requirements.txt            # Pinned Python package dependencies
├── README.md                   # Setup, execution, and walkthrough documentation
├── pages/
│   ├── 01_overview.py          # Overview, environment matrix & inventory reconciliation
│   ├── 02_synchronization.py   # Flagship sync matrix (sync vs lock vs platform vs no-lock)
│   ├── 03_runtime_comparison.py# Cross-runtime evaluation (Java 21 vs Java 24 JEP 491)
│   ├── 04_native_boundary.py   # Native JNI blocking & silent carrier starvation
│   ├── 05_persistence.py       # Relational persistence contention (Treatment A vs B)
│   ├── 06_trial_explorer.py    # Trial drill-down with live SHA-256 validation & downloads
│   └── 07_migration_guidelines.py # Chapter 7 interactive workbench & 6-stage triage pipeline
├── lib/
│   ├── __init__.py
│   ├── schemas.py              # Strict dataclass schemas & strata definitions
│   ├── loaders.py              # Authoritative file loaders with caching
│   ├── transformations.py      # Descriptive statistics & Plotly dark scientific styling
│   ├── provenance.py           # File presence & SHA-256 cryptographic verification
│   └── migration_data.py       # Domain models, queueing math, registries & audit pipeline
└── tests/
    ├── __init__.py
    ├── test_data_contract.py   # Population, schemas & 504 vs 543 reconciliation tests
    ├── test_metrics_integrity.py# Dual-window metrics, pinning & thesis findings tests
    ├── test_pages_render.py    # Headless Streamlit AppTest page execution & rendering tests
    ├── test_provenance_and_files.py # 226 raw file existence & SHA-256 validation tests
    ├── test_transformations.py # Statistical aggregation, dispersion & Plotly layout tests
    └── test_migration_guidelines.py # Queueing math, memory scaling & triage pipeline tests
```

---

## 4. Setup & Launch Instructions

### Prerequisites
- macOS / Linux / Windows
- Python 3.11+
- Working copy of the `virtual-thread-springs` repository

### 1. Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Pinned Dependencies
```bash
pip install -r tools/experiment-explorer/requirements.txt
```

### 3. Run Automated Validation Test Suite
Verify that all 76 trials, 226 admitted raw files, dual-window metrics, and SHA-256 hashes validate:
```bash
pytest tools/experiment-explorer/tests/ -v
```

### 4. Launch the Dashboard
```bash
streamlit run tools/experiment-explorer/app.py
```
Open your browser at `http://localhost:8501`.

---

## 5. Five-Minute Supervisor Demonstration Walkthrough

When presenting to your academic supervisor, focus on the scientific software laboratory workflow rather than generic UI navigation:

### Step 1: Overview & Experimental Scale (`01 · Overview & Inventory`)
- Point out the **76 normalized trials**, **8 evidence strata**, and **100% cryptographic hash matches**.
- Show the **reconciliation of the 504 vs. 543 artifact inventory**: explain that the 504 count was the freeze snapshot prior to running the Stratum 8 persistence suite (+39 files), while the core 76 trials remain 100% cryptographically identical.

### Step 2: The Core Thesis Discovery (`02 · Synchronization Matrix`)
- Direct attention to the two-panel comparison:
  - **Left Panel:** Steady-state throughput is virtually unchanged between `synchronized` (1.967 req/s) and `ReentrantLock` (1.956 req/s hold-window, $\Delta = 0.56\%$; 1.964 req/s whole-run for both).
  - **Right Panel:** All 108–110 `jdk.VirtualThreadPinned` events completely vanished with `ReentrantLock` (dropping to 0).
- Explain the discovery: *eliminating JVM-level carrier pinning does not remove application-level mutual exclusion serialization (Amdahl's Law).*
- Show the **ReentrantLock latency dispersion**: explain how AQS non-fair barging widens latency spread to 16–30 ms compared to object monitors ($\le 7.4\text{ ms}$).

### Step 3: Runtime Evolution (`03 · Java 21 vs Java 24`)
- Show that **JEP 491 in Java 24 GA** eliminates object monitor pinning (0 events), but steady throughput remains capped at 1.97 req/s.
- Highlight the **p95 latency jump from 4,983 ms to 9,001 ms**: explain that unpinned virtual threads now concurrently queue at the application lock, accumulating queueing delay at the tail.

### Step 4: Silent Carrier Starvation (`04 · JNI Native Boundary`)
- Show the CPU utilization time series during blocking JNI calls (`nanosleep`):
  - CPU averages **1.04%** during steady state.
  - Zero `jdk.VirtualThreadPinned` events are recorded despite carrier pool starvation.
  - Explain why: JNI blocking bypasses `Continuation.yield()`, exposing a critical blind spot in JFR observability.

### Step 5: Trial Explorer & Evidence Traceability (`06 · Individual Trial Explorer`)
- Select run `20261015-142534`.
- Show that every metric is traceable back to its underlying k6 JSON, manifest, and JFR binary.
- Trigger the **live cryptographic SHA-256 audit badge** to demonstrate empirical rigor and defensibility.

### Step 6: Engineering Migration Guidance & Triage Workbench (`07 · Migration Guidelines`)
- Demonstrate the **8-tab interactive workbench** synthesizing Chapter 7:
  - **Tab 2 (Triage Wizard):** Walk through the non-short-circuiting 6-stage audit pipeline, triggering dynamic composite risk calculations and prescribed actions.
  - **Tab 4 (Capacity Calculators):** Show the interactive Amdahl saturation curve and HikariCP pool sizing calculator with live empirical Stratum 8 overlay matching Little's Law within 5%.
  - **Tab 5 (Ecosystem Matrix):** Filter across the 14 verified dependencies to demonstrate risk classification (pgjdbc, MySQL 9.0, Jackson, Commons Pool 2, SQLite).
  - **Tab 6 (Refactoring Patterns):** Review production-grade Before vs. After Java diffs and explain the `CallerRunsPolicy` carrier-starvation trap.
  - **Tab 8 (Exportable Audit Report):** Generate and export comprehensive Markdown and JSON architectural audit reports.
