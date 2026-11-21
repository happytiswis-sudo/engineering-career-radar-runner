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

    def test_private_regression_triggers_on_tinyfish_adapter_changes(self):
        workflow = (ROOT / ".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        for path in (
            "deep_search.py", "public_source_adapters.py",
            "cloudflare/search-worker.js", "public/frontend-v3.js",
            "tests/test_deep_search.py", "tests/test_public_source_adapters.py",
            "tests/test_source_selection_contract.py"
        ):
            self.assertIn("- " + path, workflow)


if __name__ == "__main__":
    unittest.main()
