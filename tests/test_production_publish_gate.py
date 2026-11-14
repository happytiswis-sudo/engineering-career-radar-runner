import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ProductionPublishGateTests(unittest.TestCase):
    def test_manual_publish_requires_explicit_dispatch_approval(self):
        workflow=(ROOT/'.github/workflows/production-scan.yml').read_text()
        self.assertIn('enable_production_publish:',workflow)
        self.assertIn('default: false',workflow)
        self.assertGreaterEqual(workflow.count("inputs.enable_production_publish == true"),5)
        self.assertIn("vars.CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true'",workflow)

    def test_r2_writes_fail_closed_without_verified_free_tier_guard(self):
        self.assertIn('CAREER_RADAR_R2_FREE_TIER_GUARD_VERIFIED', workflow)
        self.assertIn('R2 archive writes are blocked', workflow)
        self.assertIn("vars.CAREER_RADAR_R2_FREE_TIER_GUARD_VERIFIED == 'true'", workflow)

if __name__=='__main__':
    unittest.main()
