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
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="auto",
)

# Streamlit's native theme also styles widgets and the canvas-based data grid.
st.html(APP_DIR / "explorer.css")

# Setup multipage navigation using st.navigation
pages = [
    st.Page("pages/01_overview.py", title="01 · Overview & Inventory", icon=":material/dashboard:", default=True),
    st.Page("pages/02_synchronization.py", title="02 · Synchronization Matrix", icon=":material/lock:"),
    st.Page("pages/03_runtime_comparison.py", title="03 · Java 21 vs Java 24", icon=":material/compare:"),
    st.Page("pages/04_native_boundary.py", title="04 · JNI Native Boundary", icon=":material/memory:"),
    st.Page("pages/05_persistence.py", title="05 · Database Persistence", icon=":material/database:"),
    st.Page("pages/06_trial_explorer.py", title="06 · Individual Trial Explorer", icon=":material/biotech:"),
    st.Page("pages/07_migration_guidelines.py", title="07 · Migration Guidelines", icon=":material/menu_book:"),
    st.Page("pages/08_find_my_next_step.py", title="08 · Find My Next Step", icon=":material/route:"),
]

nav = st.navigation(pages, position="hidden")
with st.sidebar:
    st.html("""
        <div class="lab-brand">
            <span class="lab-mark" aria-hidden="true"><i></i><i></i><i></i></span>
            <div><strong>Virtual Threads</strong><small>Experiment Explorer</small></div>
        </div>
    """)
    with st.container(key="lab_navigation"):
        for page in pages:
            st.page_link(page)
    with st.expander("Research environment", icon=":material/developer_board:"):
        st.markdown(
            "**Apple M1** · 8 cores · 8 GB  \n"
            "OpenJDK 21.0.8 LTS · k6 v1.7.1  \n"
            "Spring Boot MVC · MSc thesis  \n"
            "76 normalized trials · 8 strata"
        )

nav.run()
