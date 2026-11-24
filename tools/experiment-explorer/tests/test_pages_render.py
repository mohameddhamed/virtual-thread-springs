"""Regression test verifying that the main Streamlit application and all pages render without exceptions."""
from __future__ import annotations

import sys
from pathlib import Path

# Add explorer root
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize(
    "page_script",
    [
        "pages/01_overview.py",
        "pages/02_synchronization.py",
        "pages/03_runtime_comparison.py",
        "pages/04_native_boundary.py",
        "pages/05_persistence.py",
        "pages/06_trial_explorer.py",
        "pages/07_migration_guidelines.py",
        "pages/08_find_my_next_step.py",
    ],
)
def test_page_renders_without_exception(page_script: str):
    """Verify that each dashboard page compiles, runs, and renders without unhandled exceptions."""
    page_path = APP_DIR / page_script
    assert page_path.is_file(), f"Page script not found: {page_path}"

    at = AppTest.from_file(str(page_path))
    at.run()
    assert not at.exception, f"Page {page_script} threw an unhandled exception: {at.exception}"


def test_main_app_navigation_entry():
    """Verify that the entry point app.py executes cleanly."""
    app_path = APP_DIR / "app.py"
    assert app_path.is_file()

    at = AppTest.from_file(str(app_path))
    at.run()
    assert not at.exception, f"app.py threw an unhandled exception: {at.exception}"
