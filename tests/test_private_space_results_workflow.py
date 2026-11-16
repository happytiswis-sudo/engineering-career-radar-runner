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
        self.assertIn("continue-on-error: true", block)
        self.assertIn("Supabase is the primary results store", block)
        self.assertIn("upload_folder", block)
        self.assertIn("Warn when private Hugging Face mirror refresh fails", text)
        self.assertIn("steps.publish-dashboard.outcome == 'failure'", text)

    def test_storage_guardian_runs_before_any_supabase_or_hf_result_write(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        guard = text.index("      - name: Enforce Storage Guardian before provider writes")
        telemetry = text.index("      - name: Persist verified scan telemetry to private Supabase")
        shortlist = text.index("      - name: Persist completed shortlist to Supabase")
        publish = text.index("      - name: Publish private Space results")
        self.assertLess(guard, telemetry)
        self.assertLess(guard, shortlist)
        self.assertLess(guard, publish)
        block = text[guard:telemetry]
        self.assertIn("python storage_preflight.py", block)
        self.assertIn("CHECK_SUPABASE_STORAGE", block)
        self.assertIn("CHECK_HF_STORAGE", block)
        self.assertIn("git lfs version", block)

    def test_private_space_readback_is_required_after_private_results_upload(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: ${{ steps.publish-dashboard.outcome == 'success' }}", text)
        self.assertIn("Published jobs.json run_id does not match current GitHub run", text)
        self.assertIn("Current run is missing from the private Space search-history index", text)


if __name__ == "__main__":
    unittest.main()
