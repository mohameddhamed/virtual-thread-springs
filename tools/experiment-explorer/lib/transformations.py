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


# The plotting field stays opaque for legible exports as well as on-screen use.
PALETTE = {
    "bg_dark": "#0d1117",
    "card_dark": "#111b29",
    "border_dark": "#2c3a4d",
    "text_primary": "#e8eff7",
    "text_muted": "#a5b4c8",
    "accent_blue": "#38bdf8",
    "accent_cyan": "#2dd4bf",
    "accent_amber": "#f59e0b",
    "accent_red": "#f43f5e",
    "accent_purple": "#a855f7",
    "accent_green": "#6ee7b7",
    "condition_sync": "#f43f5e",
    "condition_lock": "#38bdf8",
    "condition_platform": "#94a3b8",
    "condition_nolock": "#a855f7",
}
COLORWAY = [PALETTE[f"accent_{tone}"] for tone in ("blue", "cyan", "purple", "amber", "red", "green")]
SANS = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
MONO = "JetBrains Mono, SFMono-Regular, Menlo, monospace"


def hover_card(heading: str, value: str, detail: str = "", color: str = "#9dd4d5") -> str:
    """Build a Plotly hovertemplate. Callers supply the trace's units and precision."""
    return (
        f"<span style='color:{color}'>●</span> <b>{heading}</b><br>{value}"
        + (f"<br>{detail}" if detail else "")
        + "<extra></extra>"
    )


def shade_workload_stages(fig: go.Figure) -> None:
    """Mark the protocol intervals on an existing elapsed-time plot."""
    for start, end, label, shade in (
        (0, 15, "Ramp-up", "rgba(56,189,248,.065)"),
        (15, 45, "Hold", "rgba(45,212,191,.11)"),
        (45, 55, "Ramp-down", "rgba(168,85,247,.08)"),
    ):
        fig.add_vrect(x0=start, x1=end, fillcolor=shade, layer="below", line_width=0)
        fig.add_annotation(
            x=(start + end) / 2, y=1, yref="paper", yanchor="bottom", showarrow=False,
            text=label, font=dict(size=10, color=PALETTE["text_muted"]),
        )
    fig.update_xaxes(tickmode="array", tickvals=[0, 15, 30, 45, 55], ticksuffix=" s")


def apply_dark_scientific_layout(
    fig: go.Figure, title: str = "", height: int = 420, *, hover_value: str = "", hover_heading: str = "%{x}",
) -> go.Figure:
    """Style a figure without changing its observations, axis ranges or trace bindings."""
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=f"<b>{title}</b>" if title else "", x=0.035, xanchor="left",
                   y=.96, yanchor="top", font=dict(size=15, family=SANS)),
        paper_bgcolor=PALETTE["card_dark"], plot_bgcolor=PALETTE["bg_dark"],
        colorway=COLORWAY, font=dict(family=SANS, size=12, color=PALETTE["text_primary"]),
        height=height, margin=dict(l=22, r=22, t=62, b=35),
        hovermode="closest", bargap=.32,
        hoverlabel=dict(bgcolor="#182737", bordercolor="#506476", align="left",
                        font=dict(family=MONO, size=12, color="#f4f9ff"), namelength=-1),
        legend=dict(orientation="h", yanchor="top", y=-.24, xanchor="left", x=0,
                    font=dict(size=11, color=PALETTE["text_muted"]), bgcolor="rgba(0,0,0,0)"),
    )
    axis_style = dict(
        automargin=True, gridcolor="#1f2937", zerolinecolor=PALETTE["border_dark"],
        tickfont=dict(family=MONO, size=11, color=PALETTE["text_muted"]),
        title_font=dict(size=12, color=PALETTE["text_primary"]), title_standoff=9,
        separatethousands=True,
    )
    fig.update_xaxes(**axis_style, showgrid=False, zeroline=False)
    fig.update_yaxes(**axis_style)
    for trace in fig.data:
        if trace.type == "pie":
            fig.update_layout(uniformtext=dict(minsize=11, mode="hide"))
            trace.update(marker_line=dict(width=2, color=PALETTE["card_dark"]),
                         textinfo="percent", textposition="inside",
                         hovertemplate=hover_card("%{label}", hover_value or "%{value:,}", "%{percent} of total"))
        elif hover_value and trace.type in ("bar", "scatter"):
            color = trace.marker.color if trace.type == "bar" else trace.line.color
            trace.hovertemplate = hover_card(hover_heading, hover_value, trace.name or "",
                                             color if isinstance(color, str) else PALETTE["text_muted"])
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
