"""Statistical aggregations, descriptive dispersion metrics, and presentation styling."""
from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def compute_descriptive_stats(values: list[float] | pd.Series) -> dict[str, Optional[float]]:
    """Compute rigorous descriptive statistics for small-sample experimental series (N <= 3).

    Strictly descriptive: sample mean, sample std dev, min, max, and spread.
    Never manufactures confidence intervals or inferential hypothesis tests.
    """
    clean = [float(v) for v in values if pd.notna(v) and v is not None]
    if not clean:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "spread": None,
        }
    n = len(clean)
    mean_val = float(np.mean(clean))
    min_val = float(np.min(clean))
    max_val = float(np.max(clean))
    spread_val = max_val - min_val
    std_val = float(np.std(clean, ddof=1)) if n > 1 else 0.0

    return {
        "count": n,
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "spread": round(spread_val, 4),
    }


def aggregate_by_condition(
    df: pd.DataFrame,
    group_col: str = "condition_id",
    metrics: list[str] | None = None,
) -> pd.DataFrame:
    """Group experimental runs by condition and compute dual-window descriptive statistics."""
    if metrics is None:
        metrics = [
            "full_throughput", "steady_throughput",
            "full_p50", "steady_p50",
            "full_p95", "steady_p95",
            "full_p99", "steady_p99",
            "jfr_pinning_count",
        ]

    rows = []
    for grp_val, group in df.groupby(group_col):
        row: dict[str, Any] = {group_col: grp_val, "trials_count": len(group)}
        # Preserve first representative metadata
        for meta_col in ["condition_label", "jdk_major", "carrier_category", "stratum_name", "execution_mode"]:
            if meta_col in group.columns:
                row[meta_col] = group[meta_col].iloc[0]

        for m in metrics:
            if m in group.columns:
                stats = compute_descriptive_stats(group[m])
                row[f"{m}_mean"] = stats["mean"]
                row[f"{m}_std"] = stats["std"]
                row[f"{m}_min"] = stats["min"]
                row[f"{m}_max"] = stats["max"]
                row[f"{m}_spread"] = stats["spread"]

        rows.append(row)

    return pd.DataFrame(rows)


# Dark Scientific Color Palette
PALETTE = {
    "bg_dark": "#0e1117",
    "card_dark": "#161b22",
    "border_dark": "#30363d",
    "text_primary": "#f0f6fc",
    "text_muted": "#8b949e",
    "accent_blue": "#58a6ff",
    "accent_cyan": "#39c5bb",
    "accent_amber": "#f0883e",
    "accent_red": "#f85149",
    "accent_purple": "#bc8cff",
    "accent_green": "#3fb950",
    "condition_sync": "#f85149",      # Red for monitor pinning
    "condition_lock": "#58a6ff",      # Clean blue for ReentrantLock
    "condition_platform": "#8b949e",  # Neutral grey for platform
    "condition_nolock": "#bc8cff",    # Purple for diagnostic ceiling
}


def apply_dark_scientific_layout(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    """Apply polished, restrained dark scientific styling to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=14, color=PALETTE["text_primary"], family="monospace"),
            x=0.02,
            y=0.96,
        ),
        paper_bgcolor=PALETTE["card_dark"],
        plot_bgcolor="#0d1117",
        font=dict(family="sans-serif", size=12, color=PALETTE["text_primary"]),
        margin=dict(l=50, r=30, t=50, b=50),
        height=height,
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
            bgcolor="rgba(22,27,34,0.7)",
            bordercolor=PALETTE["border_dark"],
            borderwidth=1,
        ),
        xaxis=dict(
            gridcolor="#21262d",
            zerolinecolor="#30363d",
            tickfont=dict(size=11, color=PALETTE["text_muted"]),
            title_font=dict(size=12, color=PALETTE["text_primary"]),
        ),
        yaxis=dict(
            gridcolor="#21262d",
            zerolinecolor="#30363d",
            tickfont=dict(size=11, color=PALETTE["text_muted"]),
            title_font=dict(size=12, color=PALETTE["text_primary"]),
        ),
    )
    return fig


def format_throughput(val: Optional[float]) -> str:
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:.2f} req/s"


def format_latency_ms(val: Optional[float]) -> str:
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:.1f} ms"


def format_bytes(b: int) -> str:
    if b >= 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"
