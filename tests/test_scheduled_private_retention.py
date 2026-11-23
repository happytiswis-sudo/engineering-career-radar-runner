import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ScheduledPrivateRetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (ROOT / ".github/workflows/production-scan.yml").read_text()

    def test_schedule_enables_private_supabase_telemetry_without_manual_inputs(self):
        self.assertIn("github.event_name == 'schedule' || inputs.enable_private_telemetry == true", self.workflow)
        self.assertIn("id: persist-scan-telemetry", self.workflow)
        self.assertIn("if: ${{ github.event_name == 'schedule' || inputs.enable_private_telemetry == true }}", self.workflow)

    def test_schedule_enables_authoritative_supabase_shortlist_and_manifest(self):
        self.assertIn("github.event_name == 'schedule' || inputs.enable_private_results == true", self.workflow)
        self.assertIn("Persist completed shortlist to Supabase (primary results store)", self.workflow)
        self.assertIn("python publish_supabase_jobs.py", self.workflow)
        self.assertIn("Verify private result-store credentials before writing shortlisted jobs", self.workflow)

    def test_supabase_results_do_not_depend_on_private_huggingface_credentials(self):
        step = self.workflow.split("Verify private result-store credentials before writing shortlisted jobs", 1)[1].split("Persist completed shortlist to Supabase", 1)[0]
        self.assertNotIn("HF_TOKEN", step)
        self.assertNotIn("HF_SPACE_ID", step)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY", step)

    def test_private_archive_is_independent_and_schedule_eligible(self):
        self.assertIn("github.event_name == 'schedule' || inputs.enable_private_archive == true", self.workflow)
        self.assertIn("Store and verify current archive in private R2", self.workflow)
        self.assertIn("steps.r2-guardian-before-archive.outputs.r2_write_admitted == 'true'", self.workflow)

    def test_public_publication_still_requires_both_explicit_gates(self):
        self.assertGreaterEqual(
            self.workflow.count("vars.CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true' && inputs.enable_production_publish == true"),
            5,
        )
        self.assertIn("default: false", self.workflow)

    def test_telemetry_failure_does_not_block_supabase_results_attempt(self):
        block = self.workflow.split("id: persist-scan-telemetry", 1)[1].split("name: Warn when private telemetry", 1)[0]
        self.assertIn("continue-on-error: true", block)
        self.assertIn("authoritative", block)


if __name__ == "__main__":
    unittest.main()
