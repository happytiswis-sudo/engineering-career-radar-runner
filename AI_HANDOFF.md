# AI Handoff — Public Execution Runner

**Last verified:** 2026-11-12  
**This repository:** https://github.com/happytiswis-sudo/engineering-career-radar-runner  
**Private source of truth:** https://github.com/happytiswis-sudo/engineering-career-radar

## Read first
1. This file.
2. `README.md` — workflow catalogue, secret/variable inventory and operating procedure.
3. Private source `AI_HANDOFF.md`.
4. Private source `PROJECT_OPERATIONS_REFERENCE.md`, `PROJECT_MASTER_SPECIFICATION.md`, and latest `PROJECT_DECISION_LOG.md`.

## Role and privacy boundary
This public repository is the GitHub Actions execution plane only. Private scanner, CV, role catalogue, dashboard and Cloudflare Worker source live in the private source repository. Never copy private data, secrets, provider response bodies, vacancy URLs/descriptions, CVs or personal application data here. Checkout private source only with `PRIVATE_SOURCE_READ_TOKEN` (Contents: Read-only), `persist-credentials: false`, an ephemeral workspace and unconditional cleanup.

## Merged workflows on main
- `runner-smoke.yml`: public-safe unit and workflow-contract tests.
- `private-scanner-regression.yml`: read-only private checkout, reconciles current private main in runner workspace, runs private Python/frontend/Worker checks and public retrieval regression tests. No publication.
- `production-scan.yml`: scheduled/manual production scanner orchestration. Production writes are gated; keep the gate disabled until preflight and dry-run approval.
- `deploy-cloudflare-dashboard.yml`: manual-only dashboard Worker/assets deployment using private source main and Wrangler. Does not deploy the separate `career-radar-bridge` Worker.
- `sync-space-ui.yml`: manual-only Hugging Face dashboard UI sync with an explicit asset allowlist; does not upload jobs, CV, secrets or history.
- `audit-url-collisions.yml`: manual read-only collision analysis; emits aggregate metrics only.
- `investigate-new-opportunities.yml`: manual archive freshness/novelty analysis; emits sanitized aggregates only.
- `reconcile-seen-registry.yml`: manual registry repair serialized with production scan.
- `keep-n8n-space-awake.yml`: six-hour authenticated HF Space health check; requires `HF_TOKEN` and `N8N_SPACE_URL`.

## Completed migration evidence
- Public production orchestration PR #2 merged.
- Private routing PR #116 merged in private source as `4a99c85a452753a918619fade171971b55783151`.
- Dashboard deploy PR #3 merged here as `36ade53a54ef35485e4ade1cebcbde8d3ad7d781`.
- Private-main regression after PR #116 passed on run [43197668524](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43197668524): 404 Python tests, frontend/Worker checks, 14 private contract tests, public retrieval tests and private checkout cleanup.
- Public runner smoke after PR #3 passed on run [43197668470](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43197668470).
- Earlier pre-merge integration run [43197068804](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43197068804) also passed 404 Python tests and 11 public retrieval regression tests.
- A prior failed smoke on the dashboard deploy PR was caused by incorrectly escaped newline literals in the new static contract test; fixed in commit `f7641992f6e158c75505de675df27039e2b59cbb`. The final smoke on merged main passed. The failure is historical, not the current main status.

## Exact next steps
1. Verify Actions status on current `main` before each operational change.
2. Verify (do not print) presence of `PRIVATE_SOURCE_READ_TOKEN`, `CLOUDFLARE_API_TOKEN`, and repository variable `CLOUDFLARE_ACCOUNT_ID`. For scan dry-run, verify HF/Supabase/R2/bridge credentials and required variables. GitHub secret values are not readable; only a successful authenticated preflight proves usability.
3. Do NOT enable `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH` yet. First perform a non-publishing dry run, inspect aggregate source yield/unique canonical URL funnel/usable postings/errors/runtime/track coverage, and validate persistence permissions without writing production records.
4. Once dashboard deployment credentials are verified, dispatch `deploy-cloudflare-dashboard.yml` manually. Smoke-test the public dashboard and authenticated API. This workflow does not update the separate search bridge Worker.
5. Manually dispatch `sync-space-ui.yml` only after confirming `HF_TOKEN` and `HF_SPACE_ID`; inspect the exact allowlist and verify the Space update without overwriting jobs/history.
6. Create a separate reviewed bridge deployment procedure and plan secret rotation before deploying `career-radar-bridge`.
7. Private source counterparts for scan, dashboard deploy and UI publishing are hard-disabled tombstones; do not re-enable them or create duplicate writers.
8. Keep README and both repositories' handoff/operations/decision documents synchronized whenever workflow ownership or release state changes.

## Secrets and variables
See README.md. Never record secret values. Current existence/validity of the public-runner Cloudflare credentials is not verified by source inspection. The dashboard workflow will fail closed if token/account ID are absent. Scan publication remains gated.

## Current status after operations workflow migration
- Public runner `sync-space-ui.yml` is merged on main. Private `sync-space-ui.yml`, `sync-dashboard-ui.yml`, and `publish-interface.yml` are retired tombstones.
- Private `scan-and-publish.yml` and `deploy-cloudflare-dashboard.yml` are also retired tombstones. All five private workflows have hard-disabled jobs.
- The dashboard deployment workflow's Cloudflare credentials, UI sync HF credentials and n8n keepalive HF credentials/URL are not verified. No deployment, Space sync, archive audit, registry repair or keepalive success is claimed.

## Non-goals until approved
- No production scan publication, Supabase/R2/HF writes or production data mutation.
- No Cloudflare bridge deployment or credential rotation without explicit preflight/rollback.
- No claim of production dashboard smoke, end-to-end search or 20,000+ URL yield until a real run verifies it.

## Handoff maintenance rule
Update this file and README.md whenever workflow ownership, credentials, test gates, release status or next actions change. Link the exact PRs, commits and Actions runs; never copy private information.
