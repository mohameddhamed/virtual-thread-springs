"""Virtual Threads Experiment Explorer - Main Streamlit Application."""
import sys
from pathlib import Path

# Add explorer directory to sys.path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Virtual Threads Experiment Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom dark scientific CSS styling
st.markdown(
    """
    <style>
    /* Dark scientific typography and card styling */
    .stApp {
        background-color: #0d1117;
        color: #f0f6fc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Metrics and cards */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 14px 18px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    div[data-testid="stMetricValue"] {
        font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
        font-weight: 700;
        color: #58a6ff;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #8b949e;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-family: monospace;
    }
    .badge-primary { background-color: #1f3a5f; color: #58a6ff; border: 1px solid #388bfd40; }
    .badge-supporting { background-color: #1a3d36; color: #39c5bb; border: 1px solid #39c5bb40; }
    .badge-historical { background-color: #3b331c; color: #f0883e; border: 1px solid #f0883e40; }
    .badge-diagnostic { background-color: #342445; color: #bc8cff; border: 1px solid #bc8cff40; }
    .badge-excluded { background-color: #3d1d24; color: #f85149; border: 1px solid #f8514940; }
    .badge-ablation { background-color: #1d3b2a; color: #3fb950; border: 1px solid #3fb95040; }
    
    /* Sidebar header */
    .sidebar-header {
        padding: 6px 0 16px 0;
        border-bottom: 1px solid #30363d;
        margin-bottom: 14px;
    }
    .sidebar-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f0f6fc;
        margin: 0;
    }
    .sidebar-subtitle {
        font-size: 0.78rem;
        color: #8b949e;
        margin-top: 4px;
    }
    
    /* Information callout boxes */
    .callout-box {
        background-color: #161b22;
        border-left: 4px solid #58a6ff;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        margin: 12px 0;
        font-size: 0.88rem;
    }
    .callout-warning {
        background-color: #1c1516;
        border-left: 4px solid #f85149;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        margin: 12px 0;
        font-size: 0.88rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar metadata
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-header">
            <div class="sidebar-title">Virtual Threads Explorer</div>
            <div class="sidebar-subtitle">MSc Thesis Research Laboratory<br>Spring Boot MVC & Java 21 Virtual Threads</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        **Thesis Evaluation Environment:**
        * **Host:** Apple M1 (8 cores, 8 GB)
        * **Primary Runtime:** OpenJDK 21.0.8 LTS
        * **Load Generator:** k6 v1.7.1
        * **Evidence Population:** 76 Trials · 8 Strata
        """
    )
    st.markdown("---")

# Setup multipage navigation using st.navigation
pages = [
    st.Page("pages/01_overview.py", title="01 · Overview & Inventory", icon=":material/dashboard:", default=True),
    st.Page("pages/02_synchronization.py", title="02 · Synchronization Matrix", icon=":material/lock:"),
    st.Page("pages/03_runtime_comparison.py", title="03 · Java 21 vs Java 24", icon=":material/compare:"),
    st.Page("pages/04_native_boundary.py", title="04 · JNI Native Boundary", icon=":material/memory:"),
    st.Page("pages/05_persistence.py", title="05 · Database Persistence", icon=":material/database:"),
    st.Page("pages/06_trial_explorer.py", title="06 · Individual Trial Explorer", icon=":material/biotech:"),
    st.Page("pages/07_migration_guidelines.py", title="07 · Migration Guidelines", icon=":material/menu_book:"),
]

nav = st.navigation(pages)
nav.run()
