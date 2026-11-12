from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/production-scan.yml").read_text(encoding="utf-8")


class ProductionWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_manual_and_scheduled_only(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertIn("schedule:", WORKFLOW)
        self.assertNotIn("\n  pull_request:", WORKFLOW)
        self.assertIn("permissions:\n  contents: read", WORKFLOW)

    def test_private_source_checkout_is_read_only_and_ephemeral(self):
        self.assertIn("repository: happytiswis-sudo/engineering-career-radar", WORKFLOW)
        self.assertIn("ref: main", WORKFLOW)
        self.assertIn("token: ${{ secrets.PRIVATE_SOURCE_READ_TOKEN }}", WORKFLOW)
        self.assertIn("path: private-source", WORKFLOW)
        self.assertIn("persist-credentials: false", WORKFLOW)
        self.assertIn("rm -rf private-source", WORKFLOW)

    def test_publication_is_explicitly_gated_and_preflighted(self):
        self.assertGreaterEqual(WORKFLOW.count("CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true'"), 5)
        self.assertIn("Verify publication credentials before any production write", WORKFLOW)
        for name in (
            "HF_TOKEN", "HF_SPACE_ID", "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY", "DASHBOARD_API_KEY", "ARCHIVE_CI_TOKEN",
        ):
            self.assertIn(name, WORKFLOW)

    def test_primary_supabase_and_history_publish_steps_are_preserved(self):
        self.assertIn("Persist completed shortlist to Supabase (primary results store)", WORKFLOW)
        self.assertIn("run: python publish_supabase_jobs.py", WORKFLOW)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}", WORKFLOW)
        self.assertIn("run: python publish_history.py", WORKFLOW)
        self.assertIn('python radar.py > "$RUNNER_TEMP/career-radar-scan.log" 2>&1', WORKFLOW)
        self.assertIn("HIMALAYAS_API_KEY: ${{ secrets.HIMALAYAS_API_KEY }}", WORKFLOW)

    def test_public_logs_and_artifacts_do_not_expose_private_scan_output(self):
        self.assertIn('python radar.py > "$RUNNER_TEMP/career-radar-scan.log" 2>&1', WORKFLOW)
        self.assertIn("Raw scanner output is withheld", WORKFLOW)
        self.assertIn("Job titles, employer names, vacancy URLs, descriptions and CV content", WORKFLOW)
        self.assertNotIn("actions/upload-artifact", WORKFLOW)
        self.assertIn("CAREER_RADAR_RUNNER_REPOSITORY: happytiswis-sudo/engineering-career-radar-runner", WORKFLOW)


DEPLOY_WORKFLOW = Path(".github/workflows/deploy-cloudflare-dashboard.yml").read_text(encoding="utf-8")


class CloudflareDeploymentWorkflowContractTests(unittest.TestCase):
    def test_dashboard_deployment_is_manual_only(self):
        self.assertIn("workflow_dispatch:", DEPLOY_WORKFLOW)
        self.assertNotIn("\n  push:", DEPLOY_WORKFLOW)
        self.assertNotIn("\n  schedule:", DEPLOY_WORKFLOW)
        self.assertIn("permissions:\n  contents: read", DEPLOY_WORKFLOW)

    def test_private_dashboard_source_is_read_only_and_ephemeral(self):
        self.assertIn("repository: happytiswis-sudo/engineering-career-radar", DEPLOY_WORKFLOW)
        self.assertIn("ref: main", DEPLOY_WORKFLOW)
        self.assertIn("token: ${{ secrets.PRIVATE_SOURCE_READ_TOKEN }}", DEPLOY_WORKFLOW)
        self.assertIn("persist-credentials: false", DEPLOY_WORKFLOW)
        self.assertIn("rm -rf private-source", DEPLOY_WORKFLOW)

    def test_cloudflare_credentials_are_required_and_not_embedded(self):
        self.assertIn("secrets.CLOUDFLARE_API_TOKEN", DEPLOY_WORKFLOW)
        self.assertIn("vars.CLOUDFLARE_ACCOUNT_ID", DEPLOY_WORKFLOW)
        self.assertIn("workingDirectory: private-source", DEPLOY_WORKFLOW)
        self.assertNotIn("apiToken: ", DEPLOY_WORKFLOW.replace("apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}", ""))


SPACE_UI_WORKFLOW = Path(".github/workflows/sync-space-ui.yml").read_text(encoding="utf-8")


class SpaceUiSyncWorkflowContractTests(unittest.TestCase):
    def test_space_ui_sync_is_manual_and_read_only_checkout(self):
        self.assertIn("workflow_dispatch:", SPACE_UI_WORKFLOW)
        self.assertNotIn("\n  push:", SPACE_UI_WORKFLOW)
        self.assertIn("permissions:\n  contents: read", SPACE_UI_WORKFLOW)
        self.assertIn("repository: happytiswis-sudo/engineering-career-radar", SPACE_UI_WORKFLOW)
        self.assertIn("token: ${{ secrets.PRIVATE_SOURCE_READ_TOKEN }}", SPACE_UI_WORKFLOW)
        self.assertIn("persist-credentials: false", SPACE_UI_WORKFLOW)
        self.assertIn("rm -rf private-source", SPACE_UI_WORKFLOW)

    def test_space_ui_sync_has_explicit_asset_allowlist_and_no_private_data_upload(self):
        for asset in ("README.md", "index.html", "frontend-v3.js", "frontend-v3.css", "ui-v2.js", "ui-v2.css", "roles-manager.js"):
            self.assertIn('"' + asset + '"', SPACE_UI_WORKFLOW)
        self.assertIn("secrets.HF_TOKEN", SPACE_UI_WORKFLOW)
        self.assertIn("vars.HF_SPACE_ID", SPACE_UI_WORKFLOW)
        self.assertIn("No jobs, CV, secrets, or scan history were uploaded.", SPACE_UI_WORKFLOW)


KEEPALIVE_WORKFLOW = Path(".github/workflows/keep-n8n-space-awake.yml").read_text(encoding="utf-8")


class KeepaliveWorkflowContractTests(unittest.TestCase):
    def test_keepalive_is_scheduled_and_manual_without_private_checkout(self):
        self.assertIn('cron: "17 */6 * * *"', KEEPALIVE_WORKFLOW)
        self.assertIn("workflow_dispatch:", KEEPALIVE_WORKFLOW)
        self.assertIn("permissions:\n  contents: read", KEEPALIVE_WORKFLOW)
        self.assertNotIn("actions/checkout", KEEPALIVE_WORKFLOW)
        self.assertNotIn("engineering-career-radar", KEEPALIVE_WORKFLOW)

    def test_keepalive_fails_closed_and_uses_authenticated_health_check(self):
        self.assertIn("secrets.HF_TOKEN", KEEPALIVE_WORKFLOW)
        self.assertIn("vars.N8N_SPACE_URL", KEEPALIVE_WORKFLOW)
        self.assertIn("if: ${{ vars.N8N_SPACE_URL != '' }}", KEEPALIVE_WORKFLOW)
        self.assertIn('url = base + "/healthz"', KEEPALIVE_WORKFLOW)
        self.assertIn('"Authorization": "Bearer " + token', KEEPALIVE_WORKFLOW)
        self.assertIn("sys.exit(1)", KEEPALIVE_WORKFLOW)


COLLISION_AUDIT_WORKFLOW = Path(".github/workflows/audit-url-collisions.yml").read_text(encoding="utf-8")
VACANCY_AUDIT_WORKFLOW = Path(".github/workflows/investigate-new-opportunities.yml").read_text(encoding="utf-8")
REGISTRY_RECONCILE_WORKFLOW = Path(".github/workflows/reconcile-seen-registry.yml").read_text(encoding="utf-8")
PRODUCTION_SCAN_WORKFLOW = Path(".github/workflows/production-scan.yml").read_text(encoding="utf-8")


class PrivateAuditWorkflowContracts(unittest.TestCase):
    def test_collision_audit_is_manual_private_checkout_and_sanitized(self):
        self.assertIn("workflow_dispatch:", COLLISION_AUDIT_WORKFLOW)
        self.assertIn("PRIVATE_SOURCE_READ_TOKEN", COLLISION_AUDIT_WORKFLOW)
        self.assertIn("persist-credentials: false", COLLISION_AUDIT_WORKFLOW)
        self.assertIn("AUDIT_REQUEST_FILE", COLLISION_AUDIT_WORKFLOW)
        self.assertIn("collision-audit-private.json", COLLISION_AUDIT_WORKFLOW)
        self.assertIn("Sanitized collision audit summary", COLLISION_AUDIT_WORKFLOW)
        self.assertNotIn("actions/upload-artifact", COLLISION_AUDIT_WORKFLOW)
        self.assertIn("rm -rf private-source", COLLISION_AUDIT_WORKFLOW)
        self.assertNotIn("\n  push:", COLLISION_AUDIT_WORKFLOW)

    def test_vacancy_audit_redacts_individual_postings_and_urls(self):
        self.assertIn("workflow_dispatch:", VACANCY_AUDIT_WORKFLOW)
        self.assertIn("PRIVATE_SOURCE_READ_TOKEN", VACANCY_AUDIT_WORKFLOW)
        self.assertIn("all-history-private.txt", VACANCY_AUDIT_WORKFLOW)
        self.assertIn("new-vacancies-private.txt", VACANCY_AUDIT_WORKFLOW)
        self.assertIn("Sanitized vacancy audit summary", VACANCY_AUDIT_WORKFLOW)
        self.assertNotIn("actions/upload-artifact", VACANCY_AUDIT_WORKFLOW)
        self.assertIn("rm -rf private-source", VACANCY_AUDIT_WORKFLOW)
        self.assertNotIn("\n  push:", VACANCY_AUDIT_WORKFLOW)

    def test_registry_reconcile_is_serialized_and_sanitized(self):
        self.assertIn("workflow_dispatch:", REGISTRY_RECONCILE_WORKFLOW)
        self.assertIn("career-radar-production-scan", REGISTRY_RECONCILE_WORKFLOW)
        self.assertIn("PRIVATE_SOURCE_READ_TOKEN", REGISTRY_RECONCILE_WORKFLOW)
        self.assertIn("registry-private.txt", REGISTRY_RECONCILE_WORKFLOW)
        self.assertIn("Sanitized registry verification", REGISTRY_RECONCILE_WORKFLOW)
        self.assertIn("rm -rf private-source", REGISTRY_RECONCILE_WORKFLOW)
        self.assertNotIn("actions/upload-artifact", REGISTRY_RECONCILE_WORKFLOW)
        self.assertNotIn("\n  push:", REGISTRY_RECONCILE_WORKFLOW)

    def test_operational_audits_are_never_push_triggered(self):
        for workflow in (COLLISION_AUDIT_WORKFLOW, VACANCY_AUDIT_WORKFLOW, REGISTRY_RECONCILE_WORKFLOW):
            self.assertNotIn("\n  push:", workflow)
            self.assertIn("workflow_dispatch:", workflow)

PRIVATE_REGRESSION_WORKFLOW = Path(".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")


class PrivateRegressionWorkflowContractTests(unittest.TestCase):
    def test_default_regression_targets_current_private_main_read_only(self):
        self.assertIn('default: "main"', PRIVATE_REGRESSION_WORKFLOW)
        self.assertIn("repository: happytiswis-sudo/engineering-career-radar", PRIVATE_REGRESSION_WORKFLOW)
        self.assertIn("ref: ${{ steps.private-refs.outputs.candidate }}", PRIVATE_REGRESSION_WORKFLOW)
        self.assertIn("PRIVATE_SOURCE_READ_TOKEN", PRIVATE_REGRESSION_WORKFLOW)
        self.assertIn("Remove private checkout", PRIVATE_REGRESSION_WORKFLOW)
        self.assertIn("tests/**", PRIVATE_REGRESSION_WORKFLOW)
        self.assertIn("unittest discover -s tests -v", PRIVATE_REGRESSION_WORKFLOW)

    def test_all_private_huggingface_writers_share_production_scan_lock(self):
        group = "group: career-radar-production-scan"
        self.assertIn(group, PRODUCTION_SCAN_WORKFLOW)
        self.assertIn(group, REGISTRY_RECONCILE_WORKFLOW)
        self.assertIn(group, SPACE_UI_WORKFLOW)


if __name__ == "__main__":
    unittest.main()
