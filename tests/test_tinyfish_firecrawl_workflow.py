import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TinyFishFirecrawlWorkflowTests(unittest.TestCase):
    def test_production_scan_injects_only_named_provider_secrets(self):
        workflow = (ROOT / ".github/workflows/production-scan.yml").read_text(encoding="utf-8")
        self.assertIn("TINYFISH_API_KEY: ${{ secrets.TINYFISH_API_KEY }}", workflow)
        self.assertIn("FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}", workflow)

    def test_isolated_provider_workflow_is_non_publishing_and_serialized_with_production(self):
        workflow = (ROOT / ".github/workflows/tinyfish-firecrawl-isolated.yml").read_text(encoding="utf-8")
        self.assertIn("group: career-radar-production-scan", workflow)
        self.assertIn('"sources": ["tinyfish"]', workflow)
        self.assertIn("TINYFISH_API_KEY: ${{ secrets.TINYFISH_API_KEY }}", workflow)
        self.assertIn("FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}", workflow)
        self.assertIn("api.firecrawl.dev/v2/team/credit-usage", workflow)
        self.assertIn("persistence\": \"none", workflow)
        self.assertIn("No Supabase, Hugging Face, R2", workflow)
        for secret in (
            "SUPABASE_SERVICE_ROLE_KEY", "HF_TOKEN", "R2_ACCESS_KEY_ID",
            "OPENROUTER_API_KEY", "INCEPTION_API_KEY", "NARAROUTER_API_KEY"
        ):
            self.assertNotIn("${{ secrets." + secret + " }}", workflow)
        self.assertNotIn("public/jobs.json\n", workflow.split("Upload aggregate-only provider summary")[-1])

    def test_runner_validation_targets_exact_private_tinyfish_candidate(self):
        workflow = (ROOT / ".github/workflows/runner-workflow-validation.yml").read_text(encoding="utf-8")
        self.assertIn("contains(github.event.pull_request.title, '[tinyfish-firecrawl-candidate]')", workflow)
        self.assertIn("feat/tinyfish-firecrawl-retrieval-20261121", workflow)

    def test_private_regression_is_called_for_this_pr(self):
        workflow = (ROOT / ".github/workflows/runner-workflow-validation.yml").read_text(encoding="utf-8")
        self.assertIn("cloro-private-candidate-regression:", workflow)
        self.assertIn("private-scanner-regression.yml", workflow)
        self.assertIn("feat/tinyfish-firecrawl-retrieval-20261121", workflow)


if __name__ == "__main__":
    unittest.main()
