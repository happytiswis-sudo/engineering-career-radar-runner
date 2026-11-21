import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TinyFishFirecrawlWorkflowTests(unittest.TestCase):
    def test_reusable_regressions_are_isolated_from_other_callers(self):
        reusable = (ROOT / ".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        self.assertIn("group: private-scanner-regression-${{ github.workflow }}-${{ github.ref }}", reusable)
        self.assertIn("cancel-in-progress: false", reusable)
        guardian = (ROOT / ".github/workflows/r2-guardian-private-regression.yml").read_text(encoding="utf-8")
        self.assertNotIn("- .github/workflows/private-scanner-regression.yml", guardian)
        self.assertIn("!contains(github.event.pull_request.title, '[tinyfish-enrichment-rank]')", guardian)

    def test_production_scan_injects_only_named_provider_secrets(self):
        workflow = (ROOT / ".github/workflows/production-scan.yml").read_text(encoding="utf-8")
        self.assertIn("TINYFISH_API_KEY: ${{ secrets.TINYFISH_API_KEY }}", workflow)
        self.assertIn("FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}", workflow)

    def test_isolated_provider_workflow_is_non_publishing_and_serialized_with_production(self):
        workflow = (ROOT / ".github/workflows/tinyfish-firecrawl-isolated.yml").read_text(encoding="utf-8")
        self.assertIn("group: career-radar-production-scan", workflow)
        self.assertIn('"sources": ["tinyfish"]', workflow)
        self.assertIn('"tracks": ["Airworthiness & Maintenance Planning", "Manufacturing & Production"]', workflow)
        search_request_env = next(line for line in workflow.splitlines() if "SEARCH_REQUEST:" in line)
        self.assertIn('"tracks":["Airworthiness & Maintenance Planning","Manufacturing & Production"]', search_request_env)
        self.assertNotIn('"tracks":[]', search_request_env)
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
        workflow = (ROOT / ".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        self.assertIn("safe TinyFish exception metadata diagnostics", workflow)
        self.assertIn("pass selected tracks through TinyFish SEARCH_REQUEST override", workflow)
        self.assertIn('candidate="main"', workflow)

    def test_pull_request_private_ref_is_selected_independently_of_runner_sha(self):
        workflow = (ROOT / ".github/workflows/runner-workflow-validation.yml").read_text(encoding="utf-8")
        pr_section = workflow.split("cloro-private-candidate-regression:", 1)[1].split("private-candidate-regression:", 1)[0]
        self.assertIn("private_ref: main", pr_section)
        self.assertIn("private_fallback_ref: 453298f4fed0404a4c9413e3dcb787deb4062c0b", pr_section)
        regression = (ROOT / ".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        self.assertIn("PR_HEAD_SHA", regression)
        self.assertIn('[tinyfish-enrichment-rank]', regression)

    def test_private_regression_routing_targets_ranked_enrichment_candidate(self):
        workflow = (ROOT / ".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        self.assertIn('[tinyfish-enrichment-rank]', workflow)
        self.assertIn('candidate="fix/tinyfish-enrichment-candidate-ranking-20261121"', workflow)

    def test_runner_validation_targets_exact_private_tinyfish_candidate(self):
        workflow = (ROOT / ".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        self.assertIn('[tinyfish-firecrawl-candidate]', workflow)
        self.assertIn('candidate="feat/tinyfish-firecrawl-retrieval-20261121"', workflow)

    def test_private_scanner_regression_maps_ranked_tinyfish_title_to_private_branch(self):
        workflow = (ROOT / ".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        self.assertIn('[tinyfish-enrichment-rank]', workflow)
        self.assertIn('candidate="fix/tinyfish-enrichment-candidate-ranking-20261121"', workflow)

    def test_private_regression_is_called_for_this_pr(self):
        workflow = (ROOT / ".github/workflows/runner-workflow-validation.yml").read_text(encoding="utf-8")
        pr_section = workflow.split("cloro-private-candidate-regression:", 1)[1].split("private-candidate-regression:", 1)[0]
        self.assertIn("private-scanner-regression.yml", pr_section)
        self.assertIn("private_ref: main", pr_section)
