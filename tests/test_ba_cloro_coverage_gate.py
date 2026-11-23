from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ba_cloro_coverage_gate import evaluate_gate, evaluate_source_coverage  # noqa: E402


def source(attempted=8, succeeded=8, errors=0, postings=13):
    return {
        "attempted_units": attempted,
        "successful_units": succeeded,
        "errors": errors,
        "unique_postings": postings,
    }


class CloroCoverageGateTests(unittest.TestCase):
    def test_complete_ba_and_cloro_coverage_passes(self):
        result = evaluate_gate({
            "source_yield": {
                "bundesagentur": source(attempted=12, succeeded=12, postings=40),
                "cloro": source(attempted=8, succeeded=8, postings=13),
            }
        })
        self.assertTrue(result["ba_full_coverage"])
        self.assertTrue(result["cloro_full_coverage"])
        self.assertTrue(result["both_sources_passed"])

    def test_partial_cloro_board_success_fails_even_with_postings(self):
        result = evaluate_gate({
            "source_yield": {
                "bundesagentur": source(attempted=12, succeeded=12, postings=40),
                "cloro": source(attempted=8, succeeded=2, errors=6, postings=13),
            }
        })
        self.assertTrue(result["ba_full_coverage"])
        self.assertFalse(result["cloro_full_coverage"])
        self.assertFalse(result["both_sources_passed"])
        self.assertEqual(result["cloro_reason"], "incomplete_unit_coverage")

    def test_any_ba_unit_failure_fails_gate(self):
        result = evaluate_gate({
            "source_yield": {
                "bundesagentur": source(attempted=5, succeeded=4, errors=1, postings=10),
                "cloro": source(),
            }
        })
        self.assertFalse(result["ba_full_coverage"])
        self.assertFalse(result["both_sources_passed"])

    def test_missing_source_metrics_fail_closed(self):
        self.assertFalse(evaluate_source_coverage(None)["passed"])
        self.assertFalse(evaluate_gate({"source_yield": {}})["both_sources_passed"])

    def test_zero_attempts_or_zero_postings_fail(self):
        self.assertFalse(evaluate_source_coverage(source(attempted=0, succeeded=0))["passed"])
        self.assertFalse(evaluate_source_coverage(source(postings=0))["passed"])

    def test_errors_fail_even_if_success_count_matches(self):
        self.assertFalse(evaluate_source_coverage(
            source(attempted=4, succeeded=4, errors=1)
        )["passed"])

    def test_invalid_or_boolean_metrics_fail_closed(self):
        invalid = source()
        invalid["attempted_units"] = True
        self.assertFalse(evaluate_source_coverage(invalid)["passed"])
        invalid = source()
        invalid["errors"] = "not-a-number"
        self.assertFalse(evaluate_source_coverage(invalid)["passed"])

    def test_cli_writes_real_newline_delimited_github_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            summary_path = Path(directory) / "summary.json"
            output_path = Path(directory) / "github-output.txt"
            summary_path.write_text(json.dumps({
                "source_yield": {
                    "bundesagentur": source(),
                    "cloro": source(attempted=8, succeeded=2, errors=6, postings=13),
                }
            }), encoding="utf-8")
            env = dict(os.environ, GITHUB_OUTPUT=str(output_path))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "ba_cloro_coverage_gate.py"), str(summary_path)],
                cwd=ROOT, env=env, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            raw = output_path.read_bytes()
            self.assertEqual(raw.count(b"\n"), 3)
            self.assertNotIn(b"\\n", raw)
            self.assertEqual(raw.decode("utf-8").splitlines(), [
                "both_sources_passed=false",
                "ba_full_coverage=true",
                "cloro_full_coverage=false",
            ])
            updated = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertFalse(updated["coverage_gate"]["both_sources_passed"])


if __name__ == "__main__":
    unittest.main()
