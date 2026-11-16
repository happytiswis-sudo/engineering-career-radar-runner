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
        self.assertIn("Warn when private Hugging Face mirror refresh is blocked or fails", text)
        self.assertIn("steps.publish-dashboard.outcome == 'failure'", text)
        self.assertIn("steps.storage-guardian-hf.outputs.hf_write_admitted != 'true'", text)

    def test_storage_guardian_is_provider_specific_and_precedes_each_write(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        supabase_guard = text.index("      - name: Enforce Supabase Storage Guardian before database writes")
        telemetry = text.index("      - name: Persist verified scan telemetry to private Supabase")
        shortlist = text.index("      - name: Persist completed shortlist to Supabase")
        hf_guard = text.index("      - name: Check Hugging Face Space capacity before mirror upload")
        publish = text.index("      - name: Publish private Space results")
        self.assertLess(supabase_guard, telemetry)
        self.assertLess(supabase_guard, shortlist)
        self.assertLess(hf_guard, publish)
        supabase_block = text[supabase_guard:telemetry]
        hf_block = text[hf_guard:publish]
        publish_block = text[publish:text.index("      - name: Verify private Space publication", publish)]
        self.assertIn("CHECK_SUPABASE_STORAGE: 'true'", supabase_block)
        self.assertIn("CHECK_HF_STORAGE: 'false'", supabase_block)
        self.assertIn("CHECK_SUPABASE_STORAGE: 'false'", hf_block)
        self.assertIn("CHECK_HF_STORAGE: 'true'", hf_block)
        self.assertIn("steps.storage-guardian-hf.outputs.hf_write_admitted == 'true'", publish_block)
        self.assertIn("python storage_preflight.py", supabase_block)
        self.assertIn("python storage_preflight.py", hf_block)

    def test_private_space_readback_is_required_after_private_results_upload(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: ${{ steps.publish-dashboard.outcome == 'success' }}", text)
        self.assertIn("Published jobs.json run_id does not match current GitHub run", text)
        self.assertIn("Current run is missing from the private Space search-history index", text)


if __name__ == "__main__":
    unittest.main()
