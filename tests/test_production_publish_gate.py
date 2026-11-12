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

if __name__=='__main__':
    unittest.main()
