"""Test suite for statistical transformations, dispersion analysis, and aggregations."""
from __future__ import annotations

import sys
from pathlib import Path

# Add explorer root
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import numpy as np
import pandas as pd
import pytest
from lib.loaders import get_enriched_trials_df
from lib.transformations import (
    aggregate_by_condition,
    compute_descriptive_stats,
    format_bytes,
    format_latency_ms,
    format_throughput,
)


def test_descriptive_stats_calculation():
    """Verify sample statistics calculation (mean, std dev with ddof=1, min, max, spread)."""
    # Empty
    empty_stats = compute_descriptive_stats([])
    assert empty_stats["count"] == 0
    assert empty_stats["mean"] is None

    # Single value (N=1) -> std must be 0.0, not NaN or crash
    single_stats = compute_descriptive_stats([42.0])
    assert single_stats["count"] == 1
    assert single_stats["mean"] == 42.0
    assert single_stats["std"] == 0.0
    assert single_stats["min"] == 42.0
    assert single_stats["max"] == 42.0
    assert single_stats["spread"] == 0.0

    # Three values (N=3, standard experimental repeat)
    vals = [1.9667, 1.9667, 1.9667]
    stats = compute_descriptive_stats(vals)
    assert stats["count"] == 3
    assert abs(stats["mean"] - 1.9667) < 1e-4
    assert abs(stats["std"] - 0.0) < 1e-4
    assert stats["spread"] == 0.0

    # Dispersion in latencies
    lat_vals = [4966.78, 4972.15, 4964.80]
    lat_stats = compute_descriptive_stats(lat_vals)
    assert lat_stats["count"] == 3
    assert lat_stats["min"] == 4964.80
    assert lat_stats["max"] == 4972.15
    assert abs(lat_stats["spread"] - 7.35) < 1e-2
    assert lat_stats["std"] is not None and lat_stats["std"] > 0


def test_aggregate_by_condition():
    """Verify grouping and dual-window statistical aggregation."""
    df = get_enriched_trials_df()
    agg = aggregate_by_condition(df, group_col="condition_id")

    assert not agg.empty
    assert "steady_throughput_mean" in agg.columns
    assert "full_throughput_mean" in agg.columns
    assert "steady_p50_mean" in agg.columns
    assert "jfr_pinning_count_mean" in agg.columns

    # Verify synchronized row
    sync_row = agg[agg["condition_id"] == "synchronized"].iloc[0]
    assert sync_row["trials_count"] >= 3
    assert abs(sync_row["steady_throughput_mean"] - 1.9667) < 0.05


def test_formatting_helpers():
    """Verify formatting helpers for presentation."""
    assert format_throughput(1.9667) == "1.97 req/s"
    assert format_throughput(None) == "N/A"

    assert format_latency_ms(4966.78) == "4966.8 ms"
    assert format_latency_ms(None) == "N/A"

    assert format_bytes(500) == "500 B"
    assert format_bytes(2048) == "2.0 KB"
    assert format_bytes(5 * 1024 * 1024) == "5.00 MB"
    assert format_bytes(2 * 1024 * 1024 * 1024) == "2.00 GB"


def test_apply_dark_scientific_layout():
    """Verify that apply_dark_scientific_layout applies styling without invalid Plotly property errors."""
    import plotly.graph_objects as go
    from lib.transformations import PALETTE, apply_dark_scientific_layout

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["A", "B"], y=[1, 2]))
    styled_fig = apply_dark_scientific_layout(fig, title="Test Figure", height=400)
    assert styled_fig is not None
    assert styled_fig.layout.paper_bgcolor == PALETTE["card_dark"]
    assert styled_fig.layout.plot_bgcolor == "#0d1117"
    # Check that x and y axis styling is valid and present
    assert styled_fig.layout.xaxis.tickfont.color == PALETTE["text_muted"]
    assert styled_fig.layout.yaxis.tickfont.color == PALETTE["text_muted"]
    assert styled_fig.layout.xaxis.title.font.size == 12
    assert styled_fig.layout.yaxis.title.font.size == 12
