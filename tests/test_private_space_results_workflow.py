from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-scan.yml"


class PrivateSpaceResultsWorkflowTests(unittest.TestCase):
    def test_private_results_refreshes_private_space_without_public_publish_gate(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        start = text.index("      - name: Publish private Space results")
        end = text.index("      - name: Verify private Space publication", start)
        block = text[start:end]
        self.assertIn("inputs.enable_private_results == true", block)
        self.assertIn("CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH", block)
        self.assertIn("continue-on-error: ${{ inputs.enable_private_results != true }}", block)
        self.assertIn("upload_folder", block)
        self.assertNotIn("continue-on-error: true", block)

    def test_private_space_readback_is_required_after_private_results_upload(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: ${{ steps.publish-dashboard.outcome == 'success' }}", text)
        self.assertIn("Published jobs.json run_id does not match current GitHub run", text)
        self.assertIn("Current run is missing from the private Space search-history index", text)


if __name__ == "__main__":
    unittest.main()
