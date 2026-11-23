from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-scan.yml"


class PrivateSpaceResultsWorkflowTests(unittest.TestCase):
    def test_private_supabase_results_do_not_trigger_hugging_face_publication(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        start = text.index("      - name: Publish public Hugging Face mirror")
        end = text.index("      - name: Verify explicitly authorized Hugging Face publication", start)
        block = text[start:end]
        self.assertIn("steps.persist-supabase.outcome == 'success'", block)
        self.assertIn("vars.CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true'", block)
        self.assertIn("inputs.enable_production_publish == true", block)
        self.assertNotIn("github.event_name == 'schedule'", block)
        self.assertNotIn("inputs.enable_private_results == true", block)
        self.assertIn("continue-on-error: true", block)
        self.assertIn("Supabase is the primary results store", block)
        self.assertIn("upload_folder", block)

    def test_public_hugging_face_guard_is_skipped_without_explicit_authorization(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        start = text.index("      - name: Check Hugging Face Space capacity before mirror upload")
        end = text.index("      - name: Archive scan and merge private Hugging Face history", start)
        block = text[start:end]
        self.assertIn("vars.CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true'", block)
        self.assertIn("inputs.enable_production_publish == true", block)
        self.assertNotIn("github.event_name == 'schedule'", block)
        self.assertNotIn("inputs.enable_private_results == true", block)

    def test_storage_guardian_is_provider_specific_and_precedes_each_write(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        supabase_guard = text.index("      - name: Enforce Supabase Storage Guardian before database writes")
        telemetry = text.index("      - name: Persist verified scan telemetry to private Supabase")
        shortlist = text.index("      - name: Persist completed shortlist to Supabase")
        hf_guard = text.index("      - name: Check Hugging Face Space capacity before mirror upload")
        publish = text.index("      - name: Publish public Hugging Face mirror")
        self.assertLess(supabase_guard, telemetry)
        self.assertLess(supabase_guard, shortlist)
        self.assertLess(hf_guard, publish)
        archive = text.index("      - name: Archive scan and merge private Hugging Face history")
        self.assertLess(hf_guard, archive)
        supabase_block = text[supabase_guard:telemetry]
        hf_block = text[hf_guard:publish]
        publish_block = text[publish:text.index("      - name: Verify explicitly authorized Hugging Face publication", publish)]
        self.assertIn("CHECK_SUPABASE_STORAGE: 'true'", supabase_block)
        self.assertIn("CHECK_HF_STORAGE: 'false'", supabase_block)
        self.assertIn("CHECK_SUPABASE_STORAGE: 'false'", hf_block)
        self.assertIn("CHECK_HF_STORAGE: 'true'", hf_block)
        self.assertIn("steps.storage-guardian-hf.outputs.hf_write_admitted == 'true'", publish_block)
        self.assertIn("python storage_preflight.py", supabase_block)
        self.assertIn("python storage_preflight.py", hf_block)

    def test_hugging_face_readback_is_required_after_explicit_publication(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("steps.publish-dashboard.outcome == 'success'", text)
        self.assertIn("Published jobs.json run_id does not match current GitHub run", text)
        self.assertIn("Current run is missing from the private Space search-history index", text)


if __name__ == "__main__":
    unittest.main()
