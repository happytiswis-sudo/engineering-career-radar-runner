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
        self.assertIn('"tracks": ["Airworthiness & Maintenance Planning", "Manufacturing & Production"]', workflow)
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

    def test_isolated_scanner_failure_reports_only_sanitized_diagnostics(self):
        workflow = (ROOT / ".github/workflows/tinyfish-firecrawl-isolated.yml").read_text(encoding="utf-8")
        scanner_step = workflow.split("Run bounded TinyFish-only scanner", 1)[1].split("Build sanitized provider summary", 1)[0]
        self.assertIn("failure_category", scanner_step)
        self.assertIn("Sanitized category", scanner_step)
        self.assertIn('printf -- \'- Sanitized category: %s\\n\' "$failure_category"', scanner_step)
        self.assertNotIn('echo "- Sanitized category: `', scanner_step)
        self.assertIn('runpy.run_path("radar.py", run_name="__main__")', scanner_step)
        self.assertIn("exception_class=", scanner_step)
        self.assertIn("traceback.extract_tb(exc.__traceback__)", scanner_step)
        self.assertIn("frame_file=", scanner_step)
        self.assertIn("frame_function=", scanner_step)
        self.assertIn("frame_line=", scanner_step)
        self.assertIn("Sanitized failure frame", scanner_step)
        self.assertIn("Sanitized exception class", scanner_step)
        self.assertNotIn("str(exc)", scanner_step)
        self.assertNotIn("repr(exc)", scanner_step)
        self.assertNotIn("traceback.print_exception", scanner_step.lower())
        self.assertNotIn("format_exc(", scanner_step.lower())
        self.assertIn("raw output withheld", scanner_step)
        self.assertIn("Raw scanner output: withheld", scanner_step)
        self.assertIn("rm -rf private-source", workflow)
        # The failure handler must never print the raw scanner log or upload it.
        self.assertNotRegex(scanner_step, r"cat\s+\"?\$scan_log")
        self.assertNotIn("upload-artifact", scanner_step)
        for secret in ("TINYFISH_API_KEY", "FIRECRAWL_API_KEY"):
            self.assertNotIn(secret + "=", scanner_step)
    def test_private_regression_routing_uses_current_main_for_diagnostics_pr(self):
        workflow = (ROOT / ".github/workflows/runner-workflow-validation.yml").read_text(encoding="utf-8")
        expression = next(line for line in workflow.splitlines() if "private_ref: ${{" in line)
        self.assertIn("sanitized TinyFish isolated scanner failure diagnostics", expression)
        self.assertIn("prevent shell substitution in TinyFish failure summary", expression)
        self.assertIn("safe TinyFish exception metadata diagnostics", expression)
        self.assertIn("&& 'main'", expression)
        self.assertIn("feat/tinyfish-firecrawl-retrieval-20261121", expression)

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
