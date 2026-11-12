# Engineering Career Radar — Public Execution Runner

> **AI/operator entry point:** Read [AI_HANDOFF.md](AI_HANDOFF.md) first. It records the current repository split, safety invariants, latest validated test run, credential preflight and exact next steps. Then read the private source [AI_HANDOFF.md](https://github.com/happytiswis-sudo/engineering-career-radar/blob/main/AI_HANDOFF.md) and its `PROJECT_OPERATIONS_REFERENCE.md`.

This repository is the **public GitHub Actions execution plane** for the private Career Radar source repository. It exists so standard GitHub-hosted runner jobs execute from a public repository rather than consuming the private repository's included Actions compute allowance.

## Repository boundary

| Repository | Responsibility | Data classification |
|---|---|---|
| [engineering-career-radar](https://github.com/happytiswis-sudo/engineering-career-radar) | Authoritative scanner, matching/agent code, master CV, dashboard source, migrations, private history contracts | **Private — source of truth** |
| [engineering-career-radar-runner](https://github.com/happytiswis-sudo/engineering-career-radar-runner) | Workflow orchestration, regression runner, public-safe tests and operational runbooks | Public — no user data or credential values |

The public runner checks out private source into an ephemeral `private-source` directory using `PRIVATE_SOURCE_READ_TOKEN` (fine-grained token, only the private source repository, **Contents: Read-only**). All workflows set `persist-credentials: false`, and remove the private checkout after the job.

**Never copy** the master CV, private user/application data, private Space history, provider responses containing personal data, credentials, vacancy descriptions/URLs, or raw scan output into this public repository, public Actions artifacts, or public logs.

## Current workflows

| Workflow | Trigger | Purpose | Production writes |
|---|---|---|---|
| `runner-smoke.yml` | Push / PR / manual | Validates the public runner and public retrieval-intelligence tests | No |
| `private-scanner-regression.yml` | Selected public-runner pushes / manual | Read-only private checkout; full private Python/frontend/Worker contracts plus public runner tests | No |
| `production-scan.yml` | Weekday schedule / manual | Runs private scanner and matching engine on public hosted runner | **Disabled by default**; explicit publication gate |
| `deploy-cloudflare-dashboard.yml` | Manual only | Deploys dashboard Worker and assets from private source using Wrangler | Dashboard Worker/assets only; not bridge |
| `sync-space-ui.yml` | Manual only | Uploads an explicit UI-only allowlist to the private Hugging Face Space | UI files only; no jobs/CV/history |
| `audit-url-collisions.yml` | Manual only | Read-only URL collision audit against a selected private archive | No; aggregate-only public output |
| `investigate-new-opportunities.yml` | Manual only | Historical freshness/novelty analysis of private archives | No; sanitized aggregates only |
| `reconcile-seen-registry.yml` | Manual only, confirmation input | Repairs and verifies private seen-job registry from archives | Private HF registry only; serialized with production scan |
| `keep-n8n-space-awake.yml` | Every six hours / manual | Authenticated `/healthz` check for the n8n Hugging Face Space | No; skips when `N8N_SPACE_URL` is unset |

## Production scan safety gate

The production scan always checks out the private source repository's current `main` branch and logs only its commit SHA. Detailed scanner output is redirected to ephemeral runner temp storage; public step summaries contain aggregate counts only, never posting titles, employer names, vacancy URLs, descriptions, CV content or credentials. No scan-result artifacts are uploaded to this public repository.

A scan runs in **non-publishing mode** while the repository variable `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH` is absent or anything other than the literal string `true`. In that mode it performs retrieval and matching but writes no results to Supabase, R2 or Hugging Face. Local output is destroyed with the ephemeral runner.

Production publication is enabled only after:
1. All required secrets and variables below have been configured in this public runner repository.
2. The non-publishing dry run and regression suite have been reviewed.
3. The operator deliberately sets `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true`.

When enabled, the workflow validates publishing credentials, persists results/aggregate telemetry to Supabase, uploads and SHA-256 verifies the private R2 archive, and publishes the allowlisted dashboard bundle to the private Hugging Face Space. These external writes must not be enabled until credential preflight and dry-run review pass.

## Required Actions secrets

Create these under **Settings → Secrets and variables → Actions → Repository secrets** in this repository. Secret values cannot be read back or transferred automatically from the private repository; copy them from their original secure source. Never paste values into issues, PRs, documentation, or chat.

| Secret | Purpose |
|---|---|
| `PRIVATE_SOURCE_READ_TOKEN` | Fine-grained read-only checkout of the private source repository; proven by regression checkouts |
| `HF_TOKEN` | Private Career Radar Hugging Face Space access for scans, UI sync, audits, registry reconciliation and n8n health check |
| `SUPABASE_URL` | Career Radar Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side Supabase RPC access; never expose to browser |
| `DASHBOARD_API_KEY` | Authenticates the Cloudflare archive bridge |
| `ARCHIVE_CI_TOKEN` | Authenticates private R2 archive upload/read-back through the bridge |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with Workers Scripts: Edit permission for dashboard deployment |

Optional provider credentials (copy only if configured and valid):
- `SERPAPI_API_KEY`, `SERPER_API_KEY`, `CLORO_API_KEY_1`, `CLORO_API_KEY_2`, `SEARXNG_API_TOKEN`
- `OPENROUTER_API_KEY`, `INCEPTION_API_KEY`, `NARAROUTER_API_KEY`, `HIMALAYAS_API_KEY`, `THE_MUSE_API_KEY`

## Required / relevant Actions variables

- `HF_SPACE_ID` — private Space ID (currently documented as `Sidmed/engineering-career-radar`).
- `CLOUDFLARE_ACCOUNT_ID` — Cloudflare account ID for dashboard deployment.
- `N8N_SPACE_URL` — HTTPS n8n Space app URL ending in `.hf.space`; keepalive skips cleanly while unset.
- `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH` — leave unset until dry-run and credential checks pass; literal `true` enables production writes.
- `CARE_RADAR_BRIDGE_URL` — optional; default `https://career-radar-bridge.happytiswis.workers.dev`.
- Search variables: `JOBSPY_AUTHORIZED_SITES`, `LINKEDIN_RETRIEVAL_AUTHORIZED`, `JOBSPY_LINKEDIN_MODE`, `JOBSPY_LINKEDIN_FETCH_DESCRIPTION`, `JOBSPY_SCHEDULED_ENABLED`, `JOBSPY_RESULTS_PER_QUERY`, `JOBSPY_LINKEDIN_MAX_QUERIES_PER_RUN`, `JOBSPY_LINKEDIN_QUERY_DELAY_SECONDS`, `JOBSPY_LINKEDIN_RATE_LIMIT_COOLDOWN_HOURS`, `JOBSPY_LINKEDIN_RESET_PAUSE`, `SEARXNG_BASE_URL`, `NARAROUTER_PROVIDER`, `NARAROUTER_MODEL`.

Copy values from the private repository's current Variables page and validate against the current source workflow. A selected JobSpy platform is not authorization; retain each platform's independent permission gate. Do not use proxies, logins, CAPTCHA solving or access-control bypasses.

## Operating procedure

1. Read both repositories' `AI_HANDOFF.md` files and the private `PROJECT_OPERATIONS_REFERENCE.md` before making changes.
2. Confirm the latest private-scanner-regression run is green.
3. Run `production-scan.yml` manually with publication disabled. Review aggregate source yield, unique canonical URL funnel, usable postings, source errors, career-track coverage and runtime.
4. Dispatch `audit-url-collisions.yml` only with a valid request file; dispatch `investigate-new-opportunities.yml` only with a valid run ID. Their raw reports remain in ephemeral runner storage.
5. Dispatch `reconcile-seen-registry.yml` only when repair is needed. It shares the same concurrency group as production scan and Hugging Face UI sync.
6. For UI-only changes dispatch `sync-space-ui.yml` after source changes are merged and HF credentials are verified. For dashboard Worker/assets changes dispatch `deploy-cloudflare-dashboard.yml` only after Cloudflare token/account configuration is verified.
7. `keep-n8n-space-awake.yml` runs every six hours only after `N8N_SPACE_URL` is configured; it also requires `HF_TOKEN`.
8. The separate `career-radar-bridge` Worker is not deployed by the dashboard workflow. Deploy it only through a separately reviewed process that preserves its R2/service bindings and encrypted secrets, with rollback ready.
9. Do not enable production publication until dry-run acceptance and Supabase/R2/HF credential validation. Verify the same run ID in Supabase, R2 and the private Space after controlled publication.
10. Never claim the >20,000 unique URL objective without a measured production run.

## Current engineering status

- Private source PR #116 merged the split source/runner routing. Public production orchestration PR #2 and dashboard deployment PR #3 are merged.
- Private source workflows for scan, dashboard deployment, UI sync, verification, n8n keepalive, archive audits and registry reconciliation are retired tombstones with hard-disabled jobs. Do not re-enable them.
- Remaining private manual-only one-off workflows are `audit-run-40672442941.yml`, `linkedin-one-query-pilot.yml`, `migrate-archives-to-r2.yml`, `migrate-history-to-supabase.yml` and `source-probe.yml`. Dispatching them still consumes private Actions compute; do not use routinely. Port with equivalent privacy and rollback safeguards before recurring use.
- Latest full regression [43222906212](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43222906212) passed **406 private Python tests** (0 failures/errors), frontend/Worker syntax/contracts, **25 public runner tests**, and private checkout cleanup. It validated private source `7269eff2c6b7b5ce00841dc83c26d9d590bb39a2` against runner code `af8ac43534d4c62eb735916ff19f730ae6be9b3b`. Latest smoke [43222906243](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43222906243) passed. Private source handoff documentation was subsequently updated; executable source was unchanged.
- This is CI evidence only. No production scan dry run, Supabase/R2/HF publication, Cloudflare dashboard deployment from the new workflow, UI sync, audit dispatch or registry repair is claimed.
- Cloudflare read-only inspection: dashboard Worker deployed 2026-11-12 10:24 UTC; bridge Worker last deployed 2026-11-07 22:00 UTC. Dashboard source now enables query-string redaction for production and preview but this is not live until deployed. Bridge still has query-string redaction disabled and persisted invocation logs. Preserve all bindings/secrets before its separate deployment.
- Public runner credential preflight remains open: `HF_TOKEN`, `HF_SPACE_ID`, `N8N_SPACE_URL`, `CLOUDFLARE_API_TOKEN`, and `CLOUDFLARE_ACCOUNT_ID` must be verified through their respective workflow preflights. Secret values cannot be read back. Production publication remains disabled.

## Privacy / incident response

If a private CV, job data, token, or raw scan log is accidentally committed or emitted to a public log/artifact, stop publication, remove the exposed content from public history where possible, rotate the affected credential immediately, and review GitHub audit logs. Deleting a commit does not revoke a leaked secret. Keep private source checkout, raw logs, and transient results on the ephemeral hosted runner only.


## 2026-11-12 security and dry-run gate update
- Private Hugging Face Space inspection confirmed public-proxy candidates include company/contact datasets, LinkedIn pilot CV assessments, mentor diagnostics, seen-vacancy registry, search history and run archives with CV-fit fields. The private source Worker now restricts unauthenticated dashboard data to role_catalog.json and explicitly blocks private data/history paths before static Assets fallback. The bridge published-data route is restricted to role_catalog.json. These are source changes only; neither Worker is considered protected in production until separately deployed and smoke-tested.
- Private regression test: tests/test_public_data_exposure_contract.py. Runner regression test: tests/test_production_publish_gate.py.
- production-scan.yml now requires BOTH CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true and workflow_dispatch input enable_production_publish=true for publishing preflight and every HF/Supabase/R2 write. The input defaults false; scheduled runs cannot publish.
- Latest actual private Space scan remains run 42421164429 (2026-11-07): 20,826 collected, 11 shortlisted, 758 attempted, 758 successful, 671 with postings. These are historical aggregate metrics only. Current source-yield/funnel/track metrics require a fresh non-publishing scan.
- No fresh scan has been dispatched and no Worker deployed in this session. GitHub connector available in this session is read-only for Actions dispatch; do not claim completion. Keep production writes disabled.
