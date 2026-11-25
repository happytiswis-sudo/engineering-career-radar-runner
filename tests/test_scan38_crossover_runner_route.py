from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "private-scanner-regression.yml"
HANDOFF = ROOT / "docs" / "AI_HANDOFF_SCAN38_REVIEW_ADDENDUM_20261125.md"
PRIVATE_BRANCH = "feat/scan38-crossover-instrumentation-20261125"
PRIVATE_SHA = "1e03cf40aca15156ffc4227acd2d65a752cfe1e9"
MARKER = "[scan38-crossover-manifest]"


class Scan38CrossoverRunnerRouteTests(unittest.TestCase):
    def test_marker_routes_to_exact_private_candidate_branch(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(MARKER, text)
        marker_at = text.index(MARKER)
        route = text[marker_at:marker_at + 220]
        self.assertIn(PRIVATE_BRANCH, route)
        self.assertIn('candidate="' + PRIVATE_BRANCH + '"', route)

    def test_runner_checks_out_and_asserts_the_resolved_private_ref(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("repository: happytiswis-sudo/engineering-career-radar", text)
        self.assertIn("ref: ${{ steps.private-refs.outputs.candidate }}", text)
        self.assertIn("Private checkout does not match the resolved candidate ref.", text)
        self.assertIn("git rev-parse HEAD", text)
        self.assertIn("github.event_name == 'workflow_dispatch'", text)


    def test_merge_conflict_policy_preserves_candidate_code_and_current_append_only_logs(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('radar.py)', text)
        self.assertIn('git checkout --ours -- "$path"', text)
        self.assertIn('PROJECT_DECISION_LOG.md|PROJECT_OPERATIONS_REFERENCE.md)', text)
        self.assertIn('git checkout --theirs -- "$path"', text)
        self.assertIn("current private main's append-only canonical history", text)
        self.assertIn('Unexpected conflict; refusing automatic resolution:', text)

    def test_route_is_non_publishing_and_cleans_private_checkout(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Run private full Python suite without printing private test output", text)
        self.assertIn("Run private frontend syntax and contract tests", text)
        self.assertIn("Run extension Bridge contract, restricted RPC and Worker syntax tests", text)
        self.assertIn("Run public retrieval-engine regression tests", text)
        self.assertIn("Remove private checkout", text)
        self.assertNotIn("uses: ./.github/workflows/production-scan.yml", text)
        self.assertNotIn("uses: ./.github/workflows/deploy-cloudflare-dashboard.yml", text)

    def test_handoff_pins_the_current_private_candidate_and_release_thresholds(self):
        text = HANDOFF.read_text(encoding="utf-8")
        self.assertIn(PRIVATE_SHA, text)
        self.assertIn("245 planned logical query units", text)
        self.assertIn("30 distinct eligible posting identities per arm", text)
        self.assertIn("20% aggregate uplift", text)
        self.assertIn("USER-APPROVED", text)


if __name__ == "__main__":
    unittest.main()
