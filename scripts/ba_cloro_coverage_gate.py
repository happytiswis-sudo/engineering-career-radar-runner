#!/usr/bin/env python3
"""Fail-closed coverage gate for the isolated Bundesagentur + Cloro workflow.

This script intentionally reports incomplete coverage through GitHub Actions
outputs without failing immediately, so the sanitized aggregate artifact can
still be uploaded before the workflow's explicit final gate fails the job.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if parsed >= 0 else None


def evaluate_source_coverage(row: Any) -> dict[str, Any]:
    """Require every attempted unit to succeed, zero errors and usable postings."""
    if not isinstance(row, dict):
        return {"passed": False, "reason": "source_metrics_missing"}

    attempted = _non_negative_int(row.get("attempted_units"))
    succeeded = _non_negative_int(row.get("successful_units"))
    errors = _non_negative_int(row.get("errors"))
    postings = _non_negative_int(row.get("unique_postings"))

    if None in (attempted, succeeded, errors, postings):
        return {"passed": False, "reason": "source_metrics_missing_or_invalid"}
    if attempted == 0:
        return {"passed": False, "reason": "no_units_attempted"}
    if succeeded != attempted:
        return {"passed": False, "reason": "incomplete_unit_coverage"}
    if errors != 0:
        return {"passed": False, "reason": "provider_errors_reported"}
    if postings == 0:
        return {"passed": False, "reason": "no_usable_postings"}

    return {"passed": True, "reason": "complete_coverage"}


def evaluate_gate(summary: dict[str, Any]) -> dict[str, Any]:
    source_yield = summary.get("source_yield")
    if not isinstance(source_yield, dict):
        source_yield = {}
    ba = evaluate_source_coverage(source_yield.get("bundesagentur"))
    cloro = evaluate_source_coverage(source_yield.get("cloro"))
    return {
        "ba_full_coverage": ba["passed"],
        "cloro_full_coverage": cloro["passed"],
        "both_sources_passed": ba["passed"] and cloro["passed"],
        "ba_reason": ba["reason"],
        "cloro_reason": cloro["reason"],
    }


def write_github_outputs(result: dict[str, Any], output_path: str | Path) -> None:
    """Write standard newline-delimited GITHUB_OUTPUT records."""
    lines = [
        f"both_sources_passed={'true' if result['both_sources_passed'] else 'false'}",
        f"ba_full_coverage={'true' if result['ba_full_coverage'] else 'false'}",
        f"cloro_full_coverage={'true' if result['cloro_full_coverage'] else 'false'}",
    ]
    with Path(output_path).open("a", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(lines) + "\n")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: ba_cloro_coverage_gate.py SUMMARY_JSON", file=sys.stderr)
        return 2

    summary_path = Path(sys.argv[1])
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not isinstance(summary, dict):
            raise ValueError("summary root must be an object")
        result = evaluate_gate(summary)
        summary["coverage_gate"] = result
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "ba_full_coverage": False,
            "cloro_full_coverage": False,
            "both_sources_passed": False,
            "ba_reason": "summary_unreadable",
            "cloro_reason": "summary_unreadable",
        }
        print(f"::error::Sanitized coverage summary could not be validated: {type(exc).__name__}")
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        print("::error::GITHUB_OUTPUT is not configured.")
        return 2
    write_github_outputs(result, output_path)
    print(
        "BA full coverage: {ba}; Cloro full coverage: {cloro}".format(
            ba=result["ba_full_coverage"], cloro=result["cloro_full_coverage"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
