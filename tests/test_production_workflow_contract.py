from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/production-scan.yml").read_text(encoding="utf-8")


class ProductionWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_manual_and_scheduled_only(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertIn("schedule:", WORKFLOW)
        self.assertNotIn("\n  pull_request:", WORKFLOW)
        self.assertIn("permissions:\n  contents: read", WORKFLOW)

    def test_private_source_checkout_is_read_only_and_ephemeral(self):
        self.assertIn("repository: happytiswis-sudo/engineering-career-radar", WORKFLOW)
        self.assertIn("ref: main", WORKFLOW)
        self.assertIn("token: ${{ secrets.PRIVATE_SOURCE_READ_TOKEN }}", WORKFLOW)
        self.assertIn("path: private-source", WORKFLOW)
        self.assertIn("persist-credentials: false", WORKFLOW)
        self.assertIn("rm -rf private-source", WORKFLOW)

    def test_publication_is_explicitly_gated_and_preflighted(self):
        self.assertGreaterEqual(WORKFLOW.count("CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true'"), 5)
        self.assertIn("Verify publication credentials before any production write", WORKFLOW)
        for name in (
            "HF_TOKEN", "HF_SPACE_ID", "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY", "DASHBOARD_API_KEY", "ARCHIVE_CI_TOKEN",
        ):
            self.assertIn(name, WORKFLOW)

    def test_public_logs_and_artifacts_do_not_expose_private_scan_output(self):
        self.assertIn('python radar.py > "$RUNNER_TEMP/career-radar-scan.log" 2>&1', WORKFLOW)
        self.assertIn("Raw scanner output is withheld", WORKFLOW)
        self.assertIn("Posting titles, employer names, URLs and descriptions", WORKFLOW)
        self.assertNotIn("actions/upload-artifact", WORKFLOW)
        self.assertIn("CAREER_RADAR_SOURCE_REPOSITORY: happytiswis-sudo/engineering-career-radar", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
