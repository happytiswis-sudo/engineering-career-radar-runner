from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-scan.yml"


class PrivateTelemetryWorkflowTests(unittest.TestCase):
    def test_private_writes_are_explicit_opt_in_and_separate_from_result_publish(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("enable_private_archive:", text)
        self.assertIn("enable_private_telemetry:", text)
        self.assertIn("default: false", text)
        self.assertIn("inputs.enable_private_archive == true", text)
        self.assertIn("inputs.enable_private_telemetry == true", text)
        self.assertIn("CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH", text)
        self.assertIn("inputs.enable_production_publish == true", text)

    def test_public_artifact_uses_aggregate_builder_only(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("from scan_telemetry import public_aggregate_artifact", text)
        self.assertIn("safe=public_aggregate_artifact(data,receipt)", text)
        self.assertIn("career-radar-source-yield", text)
        self.assertNotIn("'slug':row.get('slug')", text)
        self.assertNotIn("'source_board_metrics': [", text)

    def test_private_telemetry_step_does_not_publish_vacancies(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run: python persist_scan_telemetry.py", text)
        self.assertIn("no vacancy rows", text.lower())
        self.assertIn("private/scan-telemetry.json", text)

    def test_private_archive_uses_existing_private_r2_bridge_and_readback(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Store and verify current archive in private R2", text)
        self.assertIn("/archives?key=", text)
        self.assertIn("R2 SHA-256 read-back verification failed", text)
        self.assertIn("inputs.enable_private_archive == true", text)

    def test_public_artifact_does_not_contain_full_scan_archive_paths(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("path: private-source/source-yield-history.json", text)
        artifact = text.split("name: Prepare privacy-safe source-yield history artifact", 1)[1]
        artifact = artifact.split("name: Retain aggregate source-yield history", 1)[0]
        self.assertNotIn("public/history/run-", artifact)
        self.assertNotIn("private/master_cv.md", artifact)


if __name__ == "__main__":
    unittest.main()
