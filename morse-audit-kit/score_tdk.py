#!/usr/bin/env python3
"""Validate and total the fixed ELTE IK TDK 50-item Boolean ledger."""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


GROUPS: "OrderedDict[str, Tuple[str, int]]" = OrderedDict(
    [
        ("N", ("Novelty and quality of development", 8)),
        ("T", ("Topic and content", 8)),
        ("V", ("Verification of results", 8)),
        ("L", ("Literature review", 6)),
        ("F", ("Formal presentation and style", 6)),
        ("S", ("Scientific value", 6)),
        ("Q", ("Summary opinion and overall quality", 8)),
    ]
)
EXPECTED_IDS: List[str] = [
    f"{prefix}{number:02d}"
    for prefix, (_, maximum) in GROUPS.items()
    for number in range(1, maximum + 1)
]
VALID_STATUSES = {"awarded", "not_awarded", "unverified", "pending"}
RESOLVED_STATUSES = {"awarded", "not_awarded"}


class LedgerError(ValueError):
    """Raised when a review ledger does not match the fixed schema."""


def no_duplicate_object_pairs(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LedgerError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle, object_pairs_hook=no_duplicate_object_pairs)
    except (OSError, json.JSONDecodeError, LedgerError) as exc:
        raise LedgerError(f"{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LedgerError(f"{path}: top level must be an object")
    return data


def validate_and_score(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    reviewer = data.get("reviewer", Path(source).stem)
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise LedgerError(f"{source}: reviewer must be a non-empty string")

    items = data.get("items")
    if not isinstance(items, dict):
        raise LedgerError(f"{source}: items must be an object keyed by rubric ID")

    actual = set(items)
    expected = set(EXPECTED_IDS)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        parts = []
        if missing:
            parts.append("missing=" + ",".join(missing))
        if extra:
            parts.append("extra=" + ",".join(extra))
        raise LedgerError(f"{source}: invalid item set ({'; '.join(parts)})")

    normalized: Dict[str, Dict[str, str]] = {}
    for item_id in EXPECTED_IDS:
        record = items[item_id]
        if not isinstance(record, dict):
            raise LedgerError(f"{source}: {item_id} must be an object")
        status = record.get("status")
        evidence = record.get("evidence")
        if status not in VALID_STATUSES:
            raise LedgerError(
                f"{source}: {item_id} has invalid status {status!r}; "
                f"expected one of {sorted(VALID_STATUSES)}"
            )
        if not isinstance(evidence, str) or not evidence.strip():
            raise LedgerError(f"{source}: {item_id} requires a non-empty evidence string")
        normalized[item_id] = {"status": status, "evidence": evidence.strip()}

    subtotals: Dict[str, Dict[str, Any]] = {}
    total_awarded = 0
    total_unresolved = 0
    total_resolved = 0
    for prefix, (title, maximum) in GROUPS.items():
        ids = [f"{prefix}{number:02d}" for number in range(1, maximum + 1)]
        statuses = [normalized[item_id]["status"] for item_id in ids]
        awarded = statuses.count("awarded")
        unresolved = statuses.count("unverified") + statuses.count("pending")
        resolved = sum(status in RESOLVED_STATUSES for status in statuses)
        total_awarded += awarded
        total_unresolved += unresolved
        total_resolved += resolved
        subtotals[prefix] = {
            "criterion": title,
            "awarded": awarded,
            "unresolved": unresolved,
            "maximum": maximum,
            "final": awarded if unresolved == 0 else None,
            "range": [awarded, awarded + unresolved],
        }

    complete = total_unresolved == 0
    return {
        "reviewer": reviewer.strip(),
        "source": source,
        "complete": complete,
        "resolved_items": total_resolved,
        "awarded": total_awarded,
        "unresolved": total_unresolved,
        "maximum": 50,
        "final_score": total_awarded if complete else None,
        "range": [total_awarded, total_awarded + total_unresolved],
        "subtotals": subtotals,
    }


def compare(first: Dict[str, Any], second: Dict[str, Any]) -> Dict[str, Any]:
    if not first["complete"] or not second["complete"]:
        return {
            "complete": False,
            "mean": None,
            "difference": None,
            "reconciliation_required": None,
            "note": "No mean calculated because both written reviews are not complete.",
        }
    score_a = first["final_score"]
    score_b = second["final_score"]
    difference = abs(score_a - score_b)
    return {
        "complete": True,
        "mean": (score_a + score_b) / 2,
        "difference": difference,
        "reconciliation_required": difference > 15,
        "note": (
            "Difference is strictly greater than 15; flag reconciliation and, "
            "if unresolved, a third written review."
            if difference > 15
            else "Difference does not trigger the strictly-greater-than-15 rule."
        ),
    }


def score_text(review: Dict[str, Any]) -> str:
    if review["complete"]:
        return f"{review['final_score']}/50"
    low, high = review["range"]
    return f"{low}–{high}/50"


def render_markdown(reviews: List[Dict[str, Any]], comparison: Dict[str, Any] | None) -> str:
    lines: List[str] = []
    for review in reviews:
        lines.extend(
            [
                f"## {review['reviewer']}",
                "",
                f"- Result: **{score_text(review)}**",
                f"- Resolved items: {review['resolved_items']}/50",
                f"- Unresolved items: {review['unresolved']}",
                "",
                "| Criterion | Awarded | Unresolved | Maximum | Result |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for subtotal in review["subtotals"].values():
            if subtotal["final"] is None:
                low, high = subtotal["range"]
                result = f"{low}–{high}"
            else:
                result = str(subtotal["final"])
            lines.append(
                f"| {subtotal['criterion']} | {subtotal['awarded']} | "
                f"{subtotal['unresolved']} | {subtotal['maximum']} | {result} |"
            )
        lines.append("")

    if comparison is not None:
        lines.extend(["## Two-reviewer comparison", ""])
        if comparison["complete"]:
            lines.extend(
                [
                    f"- Mean written score: **{comparison['mean']:.1f}/50**",
                    f"- Absolute difference: {comparison['difference']}",
                    f"- Reconciliation required: {'yes' if comparison['reconciliation_required'] else 'no'}",
                    f"- Note: {comparison['note']}",
                ]
            )
        else:
            lines.append(f"- {comparison['note']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and total the fixed ELTE IK TDK 50-item Boolean rubric."
    )
    parser.add_argument("review", type=Path, help="JSON ledger for the first reviewer")
    parser.add_argument("--second", type=Path, help="optional JSON ledger for a second reviewer")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()

    try:
        first = validate_and_score(load_json(args.review), str(args.review))
        reviews = [first]
        comparison = None
        if args.second:
            second = validate_and_score(load_json(args.second), str(args.second))
            reviews.append(second)
            comparison = compare(first, second)
    except LedgerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps({"reviews": reviews, "comparison": comparison}, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(reviews, comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
