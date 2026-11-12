import json
import unittest
from pathlib import Path


class N8nWorkflowTests(unittest.TestCase):
    def test_importable_workflow_has_authenticated_webhook_and_safe_payload(self):
        path = Path(__file__).resolve().parents[1] / "integrations" / "n8n" / "career-radar-scan-completed.json"
        workflow = json.loads(path.read_text(encoding="utf-8"))
        nodes = {node["name"]: node for node in workflow["nodes"]}
        self.assertIn("Receive Career Radar event", nodes)
        self.assertEqual(nodes["Receive Career Radar event"]["parameters"]["authentication"], "headerAuth")
        self.assertIn("Normalize safe scan summary", nodes)
        code = nodes["Normalize safe scan summary"]["parameters"]["jsCode"]
        self.assertIn("safe_to_forward", code)
        self.assertNotIn("master_cv", code)
        self.assertNotIn("job_description", code)
        self.assertFalse(workflow["active"])


if __name__ == "__main__":
    unittest.main()
