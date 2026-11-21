import unittest
from pathlib import Path


class ProductionScanGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/production-scan.yml').read_text(encoding='utf-8')

    def test_scanner_step_has_stable_outcome_id(self):
        self.assertIn('      - name: Find jobs and compare against private master CV\n        id: scan\n', self.workflow)

    def test_supabase_shortlist_requires_successful_scan_and_identity_file(self):
        self.assertIn("steps.scan.outcome == 'success'", self.workflow)
        self.assertIn("hashFiles('private-source/private/retrieval-identity-hashes.json') != ''", self.workflow)
        self.assertIn("hashFiles('private-source/public/jobs.json') != ''", self.workflow)
        self.assertNotIn("&& always() && hashFiles('private-source/public/jobs.json')", self.workflow)

    def test_huggingface_mirror_requires_verified_supabase_persistence(self):
        self.assertIn("steps.persist-supabase.outcome == 'success'", self.workflow)


if __name__ == '__main__':
    unittest.main()
