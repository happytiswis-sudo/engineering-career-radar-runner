# AI Handoff — Public Execution Runner

**Last verified:** 2026-11-12  
**Public execution repository:** https://github.com/happytiswis-sudo/engineering-career-radar-runner  
**Private source of truth:** https://github.com/happytiswis-sudo/engineering-career-radar

## Read first, in this order
1. This file.
2. This repository's `README.md` — workflow catalogue, secrets/variables and operating procedure.
3. Private source `AI_HANDOFF.md`.
4. Private source `PROJECT_OPERATIONS_REFERENCE.md`.
5. Private source `PROJECT_MASTER_SPECIFICATION.md` and the latest `PROJECT_DECISION_LOG.md`.

Do not rely on old audit reports or historic run IDs as current production proof. Check current branch heads and latest Actions runs before changing anything.

## Repository boundary and privacy invariants
- Private source repository owns scanner/agent/matching code, master CV, role catalogues, dashboard and Worker source, Supabase migrations, private vacancy history and user/application data.
- This public repository owns GitHub Actions execution, public-safe tests and runbooks only.
- Private source is checked out read-only using `PRIVATE_SOURCE_READ_TOKEN` (fine-grained PAT scoped only to private source, Contents: Read-only), into an ephemeral directory with `persist-credentials: false`. Cleanup is unconditional.
- Never commit or log the CV, private job/application data, vacancy URLs/descriptions, provider response bodies, tokens, passwords, or raw reports. Never upload private data as public Actions artifacts.
- Raw archive audit reports are redirected to runner temp files; only explicit aggregate whitelists are printed.

## Current workflows on this repository's main
- `runner-smoke.yml`: public-safe runner and retrieval regression tests.
- `private-scanner-regression.yml`: read-only private checkout; full private Python/frontend/Worker contracts plus public runner tests. It never publishes.
- `production-scan.yml`: scheduled/manual scanner run. All production writes require explicit `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true`; keep disabled until dry-run approval.
- `deploy-cloudflare-dashboard.yml`: manual-only dashboard Worker/assets deployment from private source. It does not deploy the separate bridge Worker.
- `sync-space-ui.yml`: manual-only allowlisted dashboard UI sync to private Hugging Face Space; no vacancy/CV/history uploads.
- `audit-url-collisions.yml`: manual private archive collision audit; aggregate-only public output.
- `investigate-new-opportunities.yml`: manual private archive freshness/novelty analysis; sanitized aggregate output.
- `reconcile-seen-registry.yml`: manual registry repair; shares the production scan concurrency lock.
- `keep-n8n-space-awake.yml`: six-hour authenticated `/healthz` check; job skips while `N8N_SPACE_URL` is unset.

All Hugging Face writers (`production-scan.yml`, `sync-space-ui.yml`, `reconcile-seen-registry.yml`) share concurrency group `career-radar-production-scan` so they cannot write the Space concurrently.

## Verified integration evidence
- Private source main tested: `885b74f1b1c9bb49891dabba6755e17d034fc99a`.
- Public runner code tested: `4bf6329c3c7a1a2e82f1d76f5ee25b81c01f1dcb`. Later public-runner README/handoff commits are documentation-only.
- Full regression [43202937967](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43202937967) passed **406 private Python tests** (0 failures/errors), frontend/Worker syntax and contracts, **25 public runner tests**, and private checkout cleanup.
- Public runner smoke [43202937956](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43202937956) passed.
- This proves CI integration only. It does NOT prove production scan, publication, Cloudflare deployment, HF UI sync, archive audit dispatch, registry repair or live dashboard smoke.

## Completed migrations and private workflow retirement
Merged:
- Private source routing PR #116: `4a99c85a452753a918619fade171971b55783151`.
- Public production orchestration PR #2.
- Public dashboard deployment PR #3: `36ade53a54ef35485e4ade1cebcbde8d3ad7d781`.

Private source counterparts are visible tombstones with hard-disabled jobs. Never re-enable:
- `scan-and-publish.yml`
- `deploy-cloudflare-dashboard.yml`
- `sync-space-ui.yml`
- `sync-dashboard-ui.yml`
- `publish-interface.yml`
- `verify.yml`
- `keep-n8n-space-awake.yml`
- `audit-url-collisions.yml`
- `investigate-new-opportunities.yml`
- `reconcile-seen-registry.yml`

Remaining private manual-only one-off workflows: `audit-run-40672442941.yml`, `linkedin-one-query-pilot.yml`, `migrate-archives-to-r2.yml`, `migrate-history-to-supabase.yml`, and `source-probe.yml`. They still consume private Actions compute if dispatched. Do not use routinely; port to public runner with private checkout, sanitized output and rollback safeguards before recurring use. The push trigger was removed from `audit-run-40672442941.yml`.

## Credentials and variables — values are never documented here
Secret values are write-only and cannot be read back. Do not claim a credential is configured/valid without a successful workflow preflight.

Required/used by public runner:
- `PRIVATE_SOURCE_READ_TOKEN` — proven by successful read-only checkout.
- `HF_TOKEN`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DASHBOARD_API_KEY`, `ARCHIVE_CI_TOKEN` — required for controlled production publication.
- `CLOUDFLARE_API_TOKEN` — Workers Scripts: Edit, dashboard deployment.
- Optional provider keys as listed in README.

Relevant repository variables:
- `HF_SPACE_ID=Sidmed/engineering-career-radar`.
- `CLOUDFLARE_ACCOUNT_ID`.
- `N8N_SPACE_URL` — HTTPS Space URL ending in `.hf.space`; keepalive skips when unset.
- `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH` — leave unset until dry-run and credential review pass.
- Search/provider configuration variables from README.

Current credential preflight status: `PRIVATE_SOURCE_READ_TOKEN` is proven. Public runner HF/Supabase/Cloudflare credentials and `N8N_SPACE_URL` have not been independently verified. Do not copy secret values into chat, issues, commits or docs.

## Cloudflare deployed-state audit (read-only, 2026-11-12)
- `career-radar-dashboard`: latest observed deployment 2026-11-12 10:24:26 UTC; deployment `4e700252-0763-45a4-aaa1-a5b4b6fb1eea`, version `e77a40e6-038a-41bb-aac0-27d096ed7421`. Bindings: ASSETS, BRIDGE service to `career-radar-bridge`, DASHBOARD_API_KEY.
- `career-radar-bridge`: latest observed deployment 2026-11-07 22:00:14 UTC; deployment `f4381187-08f7-48a9-b4b2-8a60cd485b5f`, version `d0f7476f-b488-46ea-812e-f2c7e413b48c`. Binding ARCHIVES → `engineering-career-radar-archives`; secret binding names include distinct `GITHUB_TOKEN` and `CV_GITHUB_TOKEN`, plus HF/Supabase/archive/CV/dashboard secrets.
- Dashboard observability: logs/traces non-persistent, invocation logs off, 10% traces. Private `wrangler.jsonc` now enables query-string redaction for production and preview; it is not live until dashboard deployment.
- Bridge observability: invocation logs and log persistence on, traces off, query-string redaction off. Harden before next bridge deployment.
- The dashboard deployment version is not correlated to a Git commit. The bridge deployment predates the current source routing changes.
- Preserve R2/service bindings and existing encrypted secrets during any bridge deployment. Do not rotate `GITHUB_TOKEN` or `CV_GITHUB_TOKEN` without a tested rollback plan. The dashboard deployment workflow does not update the bridge.

## Exact next steps
1. Query current private and public `main` SHAs and latest Actions runs; later documentation commits may have advanced beyond the validated code baseline above.
2. Verify public runner credential preflight for HF/Supabase/R2/bridge before any scan publication. Keep publication gate disabled.
3. Configure/verify `HF_TOKEN`, `HF_SPACE_ID`, `N8N_SPACE_URL`; then confirm `keep-n8n-space-awake.yml` succeeds. It skips when the URL variable is unset.
4. Manually dispatch `production-scan.yml` with publication disabled. Review aggregate source yield, raw/unique/usable/new URL funnel, career-track coverage, source diagnostics and runtime. Do not infer production performance from tests.
5. Only after dry-run review, explicitly enable `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true` for a controlled publication. Verify the same run ID in Supabase, R2 SHA-256 read-back and private Space.
6. For dashboard UI changes, dispatch `sync-space-ui.yml` after source tests and HF preflight. For dashboard Worker/assets changes, dispatch `deploy-cloudflare-dashboard.yml` only after Cloudflare credential preflight; then verify actual dashboard and authenticated API.
7. Separately plan bridge Worker deployment from current private source, with binding/secret preservation and rollback. Enable query-string redaction; review persisted invocation logs.
8. Dispatch archive audits only with valid request/run IDs. Dispatch registry reconciliation only when repair is needed; it is serialized with scan and UI sync.
9. Port remaining private manual-only one-off workflows before routine use. Never dispatch private workflows casually.
10. Do not claim the >20,000 unique URL objective, production dashboard health or successful data publication without measured live evidence.

## Authentication note
The old `public/ui-v2.js` Supabase email OTP/magic-link helper and form handler were removed. The active v3 dashboard already had no magic-link path. A regression test forbids reintroducing OTP/magic-link code. Do not configure Supabase email redirects/SMTP for this legacy flow or restore it.

## Handoff maintenance rule
Whenever workflow ownership, secrets/variables, deployment state, data contracts or release gates change, update this file, README.md, and the private source `AI_HANDOFF.md`, `PROJECT_OPERATIONS_REFERENCE.md`, `PROJECT_MASTER_SPECIFICATION.md` and `PROJECT_DECISION_LOG.md` in the same work session. Record exact PRs, commits and Actions run IDs, never secret values.
