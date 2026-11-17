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

    def test_private_space_mirror_is_best_effort_after_supabase_persistence(self):
        workflow=(ROOT/'.github/workflows/production-scan.yml').read_text()
        publish_step=workflow.split('id: publish-dashboard',1)[1].split('id: ',1)[0]
        self.assertIn('continue-on-error: true', publish_step)
        self.assertIn('Supabase is the primary results store', publish_step)
        self.assertIn('Warn when a requested Hugging Face mirror refresh is blocked or fails', workflow)
        self.assertIn("steps.publish-dashboard.outcome == 'failure'", workflow)
        self.assertIn('Supabase remains authoritative', workflow)
        self.assertIn("steps.storage-guardian-hf.outputs.hf_write_admitted == 'true'", workflow)

    def test_r2_writes_fail_closed_without_fresh_account_wide_guardian(self):
        workflow=(ROOT/'.github/workflows/production-scan.yml').read_text()
        guardian=(ROOT/'scripts/r2_free_tier_guard.py').read_text()
        self.assertNotIn('CAREER_RADAR_R2_FREE_TIER_GUARD_VERIFIED', workflow)
        self.assertIn('R2_GUARD_API_TOKEN', workflow)
        self.assertIn('DASHBOARD_API_KEY', workflow)
        migration=(ROOT/'.github/workflows/migrate-space-history-to-r2.yml').read_text()
        self.assertIn('DASHBOARD_API_KEY', migration)
        self.assertIn('R2_GUARD_API_TOKEN', migration)
        self.assertIn('X-Dashboard-Key', guardian)
        self.assertIn('r2_free_tier_guard.py', workflow)
        self.assertIn('r2-guardian-before-archive', workflow)
        self.assertIn("steps.r2-guardian-before-archive.outputs.r2_write_admitted == 'true'", workflow)
        self.assertIn("steps.r2-guardian-before-refresh.outputs.r2_write_admitted == 'true'", workflow)
        self.assertIn('return 0 if admitted else 1', guardian)
        self.assertIn('unknown_operations', guardian)
        self.assertIn('metrics_complete', guardian)

if __name__=='__main__':
    unittest.main()
