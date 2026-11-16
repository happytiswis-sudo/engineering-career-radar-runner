# AI Handoff — Public Execution Runner

**Last verified:** 2026-11-13  
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
- Private source main tested: `7269eff2c6b7b5ce00841dc83c26d9d590bb39a2`.
- Public runner code tested: `4bf6329c3c7a1a2e82f1d76f5ee25b81c01f1dcb`. Later public-runner README/handoff commits are documentation-only.
- Full regression [43222906212](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43222906212) passed **406 private Python tests** (0 failures/errors), frontend/Worker syntax and contracts, **25 public runner tests**, and private checkout cleanup. It tested private source SHA `7269eff2c6b7b5ce00841dc83c26d9d590bb39a2` against public runner code SHA `af8ac43534d4c62eb735916ff19f730ae6be9b3b`.
- Public runner smoke [43222906243](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43222906243) passed. Private handoff documentation was subsequently updated; executable source was unchanged. Query current branch heads before new work.
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


## 2026-11-12 security and dry-run gate update
- Private Hugging Face Space inspection confirmed public-proxy candidates include company/contact datasets, LinkedIn pilot CV assessments, mentor diagnostics, seen-vacancy registry, search history and run archives with CV-fit fields. The private source Worker now restricts unauthenticated dashboard data to role_catalog.json and explicitly blocks private data/history paths before static Assets fallback. The bridge published-data route is restricted to role_catalog.json. These are source changes only; neither Worker is considered protected in production until separately deployed and smoke-tested.
- Private regression test: tests/test_public_data_exposure_contract.py. Runner regression test: tests/test_production_publish_gate.py.
- production-scan.yml now requires BOTH CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true and workflow_dispatch input enable_production_publish=true for publishing preflight and every HF/Supabase/R2 write. The input defaults false; scheduled runs cannot publish.
- Latest actual private Space scan remains run 42421164429 (2026-11-07): 20,826 collected, 11 shortlisted, 758 attempted, 758 successful, 671 with postings. These are historical aggregate metrics only. Current source-yield/funnel/track metrics require a fresh non-publishing scan.
- No fresh scan has been dispatched and no Worker deployed in this session. GitHub connector available in this session is read-only for Actions dispatch; do not claim completion. Keep production writes disabled.


## Live data-exposure containment deployment — 2026-11-12
- Dashboard Worker deployment ddf5e30e-1157-43b8-831f-841bc201c21b, version 5c1a5b04-e6dc-4b58-852e-f641be3245e0, 100% traffic. Deployed code verified: role_catalog.json only; private data paths and archives return explicit 404 before static Assets fallback.
- Bridge Worker deployment dd899fd3-2d34-41a0-8ae9-898967896853, version ed2d31f9-e1d9-440d-852c-011e3df67f66, 100% traffic. Deployed code verified: /published permits only role_catalog.json. Secret and R2 bindings preserved.
- Bridge observability read-back: query-string redaction on; persisted logs and invocation logs off; traces off.
- Live HTTP endpoint smoke against workers.dev remains outstanding; Cloudflare deployed source/version verification is not a substitute.
- Latest private Space snapshot is historical run 42421164429 (2026-11-07): 38,750 provider rows, 20,826 within-source unique postings, 11 shortlisted, 6 represented tracks; previous run 42419646081 had 30,179 provider rows, 14,212 within-source unique, 72 shortlisted, 16 tracks. Search profiles differed. Legacy data lacks global raw/unique/usable funnel fields. See private PROJECT_OPERATIONS_REFERENCE.md.
- No new non-publishing production scan has been dispatched. GitHub connector lacks workflow_dispatch write action in this session. Production write approval remains false unless a later operator explicitly enables both gates.


## Production credential preflight update — 2026-11-13
- Hugging Face manual read-only check [43421538523](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43421538523) passed: token authentication and Space read access.
- New manual-only workflow `.github/workflows/production-credential-preflight.yml` commit `2fba97a74150078acc6005afd8da44185b88a330` validates (GET only) Hugging Face, Supabase service-role authentication, Cloudflare API token and Worker inventory, Bridge dashboard/archive credentials and R2 list access. It prints sanitized statuses only, never secret values or object names. It does not run scans, write, deploy or publish. It fails if `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true`.
- Direct connected-account checks: Supabase project ACTIVE_HEALTHY; Cloudflare account lists both expected Workers and the private archive bucket. These do not validate GitHub Actions secrets.
- User screenshots show `HF_TOKEN`, `CLOUDFLARE_API_TOKEN`, `HF_SPACE_ID`, and `CLOUDFLARE_ACCOUNT_ID` entries. Only HF token/Space has been verified from Actions. Supabase and Bridge secrets still require workflow validation.
- User must manually dispatch [production-credential-preflight.yml](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/workflows/production-credential-preflight.yml) on main and share the result.
- Keep publishing disabled. The production workflow requires both the repository variable and manual boolean input; neither should be enabled as part of this preflight. Prior R2 PUT returned HTTP 401; new preflight checks read-only bridge/R2 access.


## Preflight attempt #1 — missing Actions secrets (2026-11-13)
- Manual run failed immediately during the required-settings check (4 seconds), before any service-authentication or network tests. Sanitized output: `missing_settings=["SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY","DASHBOARD_API_KEY","ARCHIVE_CI_TOKEN"]`.
- Therefore this run does not establish that Supabase, Cloudflare Bridge or R2 credentials are invalid; they were absent from the workflow environment.
- HF token/Space and Cloudflare API token/account variable were not listed as missing. Only HF was independently validated by run [43421538523](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43421538523).
- Add the four missing names as GitHub Actions repository secrets in [runner repository secrets](https://github.com/happytiswis-sudo/engineering-career-radar-runner/settings/secrets/actions). Never send values through chat or commit them.
- Supabase URL is `https://plzjmyytuumxckbrrzlp.supabase.co`; obtain the current service-role/secret key from the Supabase project's API keys page.
- `DASHBOARD_API_KEY` and `ARCHIVE_CI_TOKEN` must exactly match the corresponding encrypted secrets on Cloudflare Worker `career-radar-bridge`. Cloudflare secret values are write-only; if the original values are unavailable, generate new high-entropy values and update the Bridge and GitHub Actions copies to the same new values. Do not change one side only.
- After configuring, rerun the read-only `production-credential-preflight.yml`. Keep `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH` unset/false. No production scan or writes are authorized.


## Preflight correction — 2026-11-13
- Preflight run #2 failed only because workflow incorrectly read `SUPABASE_URL` from `secrets`; user had correctly stored it as a repository variable. No credential validity test was reached.
- Fixed `.github/workflows/production-credential-preflight.yml` to use `${{ vars.SUPABASE_URL || secrets.SUPABASE_URL }}` (supports variable first and legacy secret fallback). Commit `a3d160531b26bfb1da49120dfa7eda00082ef407`.
- Next action: rerun the manual read-only preflight on `main`. Do not add duplicate URL settings; keep publishing gate disabled.


## R2 binding diagnosis — 2026-11-13
- Latest production credential preflight run #4: Supabase service-role PASS; Hugging Face auth and Space read PASS; Cloudflare Worker inventory PASS; publishing gate SAFE_DISABLED; Cloudflare token verify endpoint returned HTTP 401; Bridge archive GET returned HTTP 503.
- Direct Cloudflare API read of `career-radar-bridge` Worker settings confirmed secret bindings `ARCHIVE_CI_TOKEN`, `DASHBOARD_API_KEY`, and `GITHUB_TOKEN` are present. It also confirmed the R2 binding `ARCHIVES` is ABSENT. The existing Worker source explicitly returns HTTP 503 with `R2 archive storage is not bound to this Worker` when `env.ARCHIVES` is missing. This is the confirmed cause of the Bridge/R2 503; no need to rotate the two shared secrets again.
- Existing Cloudflare R2 bucket is `engineering-career-radar-archives`. To repair via dashboard: Workers & Pages → `career-radar-bridge` → Settings → Bindings → Add binding → R2 bucket. Set variable/binding name exactly `ARCHIVES`, select bucket `engineering-career-radar-archives`, save and deploy the Worker. This is a Worker configuration deployment, not a data publication; obtain explicit user approval before doing it through API.
- Cloudflare API token verification endpoint `/user/tokens/verify` returns 401 while the same credential successfully lists account Worker scripts. Treat the 401 as insufficient permission for the token-verification endpoint, not proof that the token itself is invalid. Worker inventory read is the effective account access test for this workflow.
- After user adds and deploys the R2 binding, rerun the read-only preflight. Expect archive GET to pass if the two shared secret values match; if it remains 401, inspect the exact Bridge auth response without exposing values.
- Publishing gate remains SAFE_DISABLED; no scan, archive write, Supabase write or production data publication has occurred.


## R2 free-tier admission guard — 2026-11-14
- User requirement is no R2 charges. Cloudflare R2 Standard currently includes 10 GB-month, 1M Class A and 10M Class B operations per month; Infrequent Access is not free. Storage is billed on average daily peak GB-month, so a point-in-time object count alone is insufficient.
- Private source Storage Guardian policy is tracked in [PR #131](https://github.com/happytiswis-sudo/engineering-career-radar/pull/131). It is dry-run/report-only; no provider adapters or deletion executor are enabled.
- This runner change introduces a separate fail-closed gate: R2 archive writes require repository variable `CAREER_RADAR_R2_FREE_TIER_GUARD_VERIFIED=true`. Leave it unset/false until account-wide R2 GB-month and monthly Class A/B usage are measured and the Storage Guardian adapters are deployed and verified.
- With the variable absent, explicit private archive requests fail before the scan begins; production-publish R2 writes remain blocked too. No secret values belong in this handoff.
- Do not set the guard variable merely to unblock a scan. Do not claim $0 billing is guaranteed by an application cleanup loop. If absolute zero charge is required and metering cannot be verified, leave R2 writes disabled.


## Storage Guardian R2 gate — validation update (2026-11-14)
- Public runner PR #15 head: `5b6262bedfa1ae32870d4d9992ac3609b94b6ec1`.
- Runner smoke [43532498807](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43532498807) PASS; runner workflow validation [43532498789](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43532498789) PASS. The first smoke attempt exposed a test-fixture NameError; the fixture was corrected and the latest run passed.
- Private source Storage Guardian PR #131 remains open; its new private Python and Bridge contract tests still require the public runner's private-scanner regression against the exact candidate ref.
- Keep `CAREER_RADAR_R2_FREE_TIER_GUARD_VERIFIED` unset. Do not enable R2 archive writes until the private Storage Guardian adapters prove account-wide GB-month and Class A/B usage below the conservative budgets.
- The private Bridge source check requires Worker variable `R2_FREE_TIER_GUARD_VERIFIED=true`, but only after a separate Bridge deployment. Until deployed, existing Bridge code is unchanged; avoid R2 archive writes.


## AI, retrieval telemetry and cost-safe verification update — 2026-11-14

### Provider credentials and routing — observed state
- The public runner production workflow passes provider credentials from **public runner Actions secrets** into the private scanner process. Current workflow mappings include `OPENROUTER_API_KEY`, `INCEPTION_API_KEY`, `HIMALAYAS_API_KEY`, `THE_MUSE_API_KEY`, `SERPAPI_API_KEY`, `SERPER_API_KEY`, `CLORO_API_KEY_1`, `CLORO_API_KEY_2`, `SEARXNG_API_TOKEN`, and `NARAROUTER_API_KEY`, plus NaraRouter provider/model variables. The workflow also passes retrieval authorization and JobSpy controls separately.
- A provider secret existing in the **private source** repository does not make it available to a workflow running in the **public runner**. The runner must have its own same-named Actions secret. Do not copy secrets into code, logs or this document.
- At the time of production scan run [43592672196](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43592672196), the runtime environment showed OpenRouter and Inception keys present; Himalayas, The Muse, SerpApi, Serper, Cloro and NaraRouter values were empty for that execution. The user subsequently added `NARAROUTER_API_KEY` to public runner Actions secrets (screenshot evidence, 2026-11-14); that change occurred **after** run 43592672196 and has not yet been validated by a later scan. NaraRouter provider/model variables were empty in run 43592672196; configure them only if selecting NaraRouter intentionally.
- User-provided NaraRouter dashboard screenshots showed the Free plan, 47 available models, 0 locked models and 0 usage/requests at the time of capture. A masked key was visible; never transcribe or store it. Zero usage means no request activity was recorded in that dashboard view, not proof of a working integration.
- Unit/contract coverage includes settings-driven provider priority, OpenRouter Gemma model selection and JSON mode, NaraRouter request compatibility without incompatible JSON mode, Mercury JSON-mode compatibility, invalid-response fallback, rate-limit cooldown/fallback and sanitized provider errors. Passing unit tests do not prove live provider requests succeeded.
- Do not infer that every provider is active just because its key exists in the private repository. For each provider, verify public-runner secret presence through a sanitized preflight/runtime check, then confirm a real request and outcome without exposing prompt/CV/provider payloads. Optional paid providers remain disabled unless their cost/yield case is approved.

### Latest non-publishing scan evidence
- Public runner workflow run [43592672196](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43592672196), run #15, completed successfully on 2026-11-14 in about 5m57s.
- Private scanner checkout, CV/matching-engine validation, role-catalog synchronization, history/aggregate metrics loading, scan execution, telemetry receipt validation, privacy-safe aggregate generation and Supabase telemetry persistence all succeeded.
- Supabase persistence read-back reported: `canonical_urls=23845`, `posting_identities=24561`, `tracks=34`, `source_families=17`. The telemetry receipt was verified against the scan output/run ID and global canonical URL count.
- Production publication credential preflight was skipped. Hugging Face publication, shortlist/result-store writes, R2 archive writes and archive retention were skipped. The R2 free-tier guard itself was skipped because archive writing was not requested; do not enable R2 writes until its free-tier budget/guard has been independently verified.
- This run is non-publishing. The success conclusion is not evidence that live AI assessments succeeded. The public-safe step summary reports retrieval funnel/query/track aggregates; it does not expose per-job AI outcomes. Private scanner logs are removed with the ephemeral checkout. Therefore AI assessment success/failure counts and reasons for unassessed shortlisted jobs remain **unverified** from this run.
- An earlier run #14 summary showed 24,089 raw URLs, 22,345 global unique canonical URLs, 22,345 usable postings, 23,061 posting identities, 22,016 newly discovered vacancies, 34/34 tracks reported, 34 allocated, 21 with retrieval results, and query counts 272 planned / 204 attempted / 68 succeeded / 136 failed; scanner collected 10,707 postings and shortlisted 66. These values belong only to that run and must not be copied as run #15 metrics.

### Implemented retrieval and privacy contracts
- Global canonical-URL and posting-identity deduplication; raw URL, unique canonical URL, usable posting and newly discovered vacancy funnel accounting.
- Track allocation/result coverage reporting, provider/source-family classification and adaptive capacity using prior aggregate yield; preserve fair track floors and provider limits.
- Query accounting distinguishes planned, attempted, succeeded, failed and intentionally skipped allocations; planned-but-skipped work is not counted as attempted.
- Retrieval is kept separate from CV fit assessment: collect broadly first, then assess; low CV fit must not silently erase retrieved opportunities.
- Detailed scan/provider/job data and identity hashes stay in the private ephemeral workspace. Public Actions summaries/artifacts are aggregate-only and explicitly reject job titles, employers, vacancy URLs, descriptions, CV fields and identity hashes.
- Supabase migration `career_radar_verified_scan_telemetry` was applied to project `plzjmyytuumxckbrrzlp`. Telemetry RPCs are service-role only; anon/authenticated access to the private schema/table is denied. Run #15 confirms the telemetry write/read-back path works.

### Dashboard and application UX already implemented
- Active dashboard v3 has the main workspace navigation (Search jobs, Results, Scan history, Applications) and Career Tools (Master CV, Role targets, Employers), theme control, scan launch/status/cancel controls and scan history.
- Applications use the private Supabase workspace for saved opportunities, status, notes and follow-ups; board/list views, status changes, drag/drop, selection and deletion contracts are covered by UI contract tests. User screenshots confirm the application pipeline displays Supabase-backed application counts.
- A separate successful UI sync workflow [run #1](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions) validated frontend v3 automatic loading, Supabase Applications persistence, notes/status history and deletion contracts, v3 sitemap/route rendering/API wiring, credential/cache/private API authorization, and Kanban/list-view contracts. It published allowlisted UI assets only; no jobs, CV or scan history were uploaded.
- The user has requested a different card interaction: **single card click should not navigate/expand; double-click on an opportunity card should open its details in a popup/tab**. Treat this as a new UX requirement, not as already implemented. Previous Applications screenshots still showed a crowded/narrow card layout in one view; inspect current active v3 components before editing.

### Outstanding engineering work — keep ordered
1. Add terminal outcome accounting for every queued AI assessment: assessed, provider failure, invalid response, timeout or intentionally skipped. Reconcile queued = terminal outcomes and identify the 11 unassessed jobs from the affected scan. Keep per-job details private; show only aggregate counts/reason classes in scan history.
2. Diagnose provider/source failures with sanitized, provider-specific evidence: Workday and Lever errors, Personio rate limiting, The Muse adapter failure, and the 136 failed queries in the run #14 summary. Respect provider cooldowns/rate limits; distinguish source query failures from AI provider failures.
3. Verify NaraRouter public-runner secret on a subsequent controlled scan and configure provider/model variables only if desired. Evaluate SerpApi, The Muse and Himalayas credentials on measured incremental yield and cost; do not enable paid calls just because secrets exist. Current workflow mappings exist, but run #15 showed these optional keys empty.
4. Explain track coverage: run #14 had 34 tracks allocated but only 21 with retrieval results. Identify empty/failed/filtered track reasons without changing allocation fairness or provider limits.
5. Surface AI assessment totals/outcomes, provider failure classes, query planned/attempted/succeeded/failed/skipped counts and track coverage in private scan history/dashboard. Public summaries remain aggregate-only; never expose CV, job titles, employers, vacancy URLs, raw provider responses or identity hashes.
6. Continue to keep production vacancy publishing disabled. R2 archive writes remain disabled until the free-tier cost guard is verified. Do not deploy or publish merely to test AI providers.

### Verification discipline
- Separate credential-name presence, runtime environment presence, successful provider request, valid assessment and persisted assessment outcome; they are different states.
- A green GitHub workflow only proves the steps that ran. Inspect each step's skipped/success conclusion and sanitized outputs.
- Record the exact run ID and avoid mixing run #14 metrics with run #15 telemetry. Do not claim AI assessment is fixed until terminal outcome counts reconcile and provider calls are evidenced.


### Follow-up investigation — 2026-11-14, run 43592672196
- Queried the private Supabase `career_radar_private.scan_runs` row for run `43592672196`: `ai_queue=50`, `ai_assessed_jobs=39`, `ai_provider_attempts=51`, `ai_valid_responses=39`. Thus 11 queued jobs did not receive a valid AI assessment; this is confirmed by persisted database counters, not inferred from a handover note.
- Provider health in the persisted diagnostics: Inception Mercury 3 = 47 attempts / 37 valid / 10 failed; OpenRouter = 4 attempts / 2 valid / 2 failed. There were 12 failed provider attempts across the 50 queued jobs. Provider totals sum to 51 attempts and 39 valid responses.
- The same run recorded 12,207 collected jobs, 672 shortlisted jobs, 34 catalogue tracks and 14 tracks with retrieval results. Retrieval telemetry is separately verified and must not be confused with AI assessment coverage.
- Code review of `radar.py::assess_queue_parallel` shows a bounded three-worker queue with per-provider fallback, provider cooldowns for 429/transient transport errors, and deterministic evidence retained when no valid AI response is obtained. The main scan loop increments `ai_done` only for a valid assessment; failed jobs continue without AI assessment. The loop already builds an `ai_failures` category counter, but the persisted telemetry currently does not expose that counter. `ai_error_details` only captures a limited subset of HTTP 400 details.
- The persisted `ai_provider_health` confirms aggregate attempts/success/failure counts but does **not** reveal the exact failure categories for the 12 failed attempts, nor identify which 11 queued jobs were not assessed. Therefore the root cause of those 11 is **not yet established**; do not label them as timeouts, malformed JSON, rate limits or provider outages without new evidence.
- Required fix: add a privacy-safe terminal outcome ledger for the AI queue: `assessed`, `provider_failed` with normalized failure categories, `deadline_skipped`, `no_provider_configured`, and other explicit terminal states. Persist only aggregate outcome counts and provider/failure classes; keep per-job identities, prompts, CV data, provider responses and job content private. Enforce `queued = assessed + all non-assessed terminal outcomes`, and `provider_attempts = valid_responses + failed_attempts` (where applicable). Add unit tests for fallback success, all-provider failure, cooldown/429, invalid JSON, transport timeout, deadline exhaustion and no configured provider.
- Re-run a non-publishing scan after implementation, then verify the two reconciliation equations from private Supabase read-back. Do not attempt to reconstruct missing per-job outcomes for run 43592672196; its ephemeral private job-level logs/workspace have already been removed. Preserve the run as aggregate historical evidence only.

## Regression trigger note — 2026-11-15
- Private source PR #142 merged as `4dea56e8abedc2a3d5106b0875df35fec95fd6ac`; fix permits server-authenticated dashboard gateway requests without Origin on CV/Roles GET while retaining editor password checks.
- Updated README to trigger the existing push-based `private-scanner-regression.yml` against current private main. Await actual run evidence before marking the fix validated.
- This trigger is non-publishing and does not deploy Cloudflare Workers.


## Candidate selection correction — 2026-11-15
- The initial README trigger did not include the required `[extension-release-final]` commit-message marker, so the workflow's push selector would have selected the extension feature branch. A second README commit now includes the marker and forces candidate `main` for the regression. Inspect the actual Actions run before claiming it tested merged private main.

## CV/Roles gateway fix deployment update — 2026-11-15
- Private source PR #142 merged as `4dea56e8abedc2a3d5106b0875df35fec95fd6ac`.
- Corrected Bridge deployed directly from merged private source: version 81 `ebc479ee-7255-41a6-9398-12fab218a6cc`; deployment `0e54a03e-4c88-4640-b23d-3a61c6c6f90d`, 100% traffic.
- Cloudflare version compilation and targeted CV/Roles gateway/password checks passed. All prior Bridge binding names/types read back intact; secret values were not read.
- README push was used to trigger the non-publishing full regression workflow with the `[extension-release-final]` candidate selector. This connector only returns PR-associated workflow runs, not push-triggered runs, and combined status showed no contexts. Therefore the actual full-suite outcome is **unverified**, not PASS. Obtain the run from GitHub Actions and inspect its candidate SHA and every step before claiming 455-test regression PASS.
- No production scan, publication or archive write was started.

## Exact-main regression trigger correction — 2026-11-15 13:26 UTC
- Important: the previous README comment contained `[extension-release-final]`, but the workflow selector checks the **push commit message**, not README contents. That earlier trigger could therefore select the extension feature branch.
- Corrected by pushing README commit `7273442f2a0d4e0eec2fadb86a657eb216063e83` with commit message `[extension-release-final] Run full private regression against merged main`. This satisfies the workflow selector and explicitly selects private source `main`.
- This push triggers the non-publishing full-private-suite job. The connected GitHub tools do not expose push-triggered workflow-run listing; check GitHub Actions manually for the run and verify candidate SHA `4dea56e8abedc2a3d5106b0875df35fec95fd6ac` or later docs-only main SHA, then inspect all steps. Until that evidence is available, full regression is **pending/unverified**.
- Cloudflare Bridge fix is already deployed as version 81 / deployment `0e54a03e-4c88-4640-b23d-3a61c6c6f90d`; deployment does not imply the full suite passed.

### Extension receiver diagnosis — 2026-11-15
- User browser reports `Could not establish connection. Receiving end does not exist.` after Master CV and Role targets load. The deployed Bridge v81 is not the layer returning this error; it originates from Chromium `tabs.sendMessage` because the dashboard content script listener is absent in the selected tab.
- Previously distributed artifact 14157371897 contains `dashboard-bridge.js` and manifest match. Immediate recovery is to refresh the dashboard tab once and retry.
- Private PR #143 adds scripting-permission fallback injection for the exact approved dashboard tab and retries the existing nonce handshake only after the missing-receiver error. It is not merged; no checks or new extension artifact yet.

### Extension missing receiver — fix merged, tests passed — 2026-11-15
- Private PR #143 merged as `4a8c8039a0355f7417f32b8eb07b70d07615cab6`.
- Runner regression #43720036604 completed successfully. Full private Python suite: 455 tests, 0 failures, 0 errors, 0 skips. Frontend syntax/contracts, extension API/schema and Bridge contracts, public retrieval regression, package build/upload all succeeded.
- Candidate PR #143 was tested after cleanly merging current private main into the runner workspace; candidate SHA `ab605e8c4272a61bf635cc9a02038aa9a32adafa`; main base at test time `8fc1baf46e257704e8375e996b91eaf55fbbcefc`.
- Artifact `career-radar-chrome-extension` ID `14164316215`, run `43720036604`, expires 2026-11-29. SHA256 `3b747cde342b523785a5bc670f4b445b2f8582b699888dc983fe22ebc352b5b5`.
- User's only remaining action: replace/reload unpacked extension from this artifact in their local browser, refresh dashboard, connect, and confirm visible listing ingestion. Local browser interaction is not accessible to the agent; do not claim end-to-end browser PASS until confirmed.

### Explicit dashboard host permission fix — merged and tested — 2026-11-15
- User-reported page access denial resolved in PR #144, merged as `b7f947863ac16c838ec7251b960fd98d31b30f6c`.
- Extension version 0.1.2 moves exact dashboard origin to `optional_host_permissions` and requests it from the Connect button's direct user gesture before secure dashboard session handoff.
- Runner regression #43720545755 attempt 2 succeeded: 455 tests, 0 failures, 0 errors, 0 skips; frontend syntax/contracts, extension API/schema and Bridge/Worker checks, public retrieval regression, package build/upload all succeeded.
- Artifact `career-radar-chrome-extension` ID `14164586292`, run `43720545755`, expires 2026-11-29; SHA256 `37c04cfe671f0be4d14ac1631e46fae27a55178c9fff41806a3d2510964af539`.
- User's remaining action: replace old unpacked extension with v0.1.2, click Connect and approve the exact dashboard-origin permission prompt. Then confirm Connected state and successful visible-listing ingestion. Local browser interaction remains the only unverified gate.

### Extension v0.1.3 — permission verification and proactive bridge injection
- PR #145 merged as `731d7c0223c9c0e29caa4cff13bd86196cef616c`.
- User had approved optional dashboard permission in v0.1.2 but still saw host access error. v0.1.3 verifies permission, selects active dashboard tab, proactively injects idempotent bridge and reports stage-specific errors.
- Runner #43721124467 attempt 3 passed: 455 tests, 0 failures, 0 errors, 0 skips; frontend, extension API/schema, Bridge/Worker, public retrieval regression, ZIP package/upload all succeeded.
- Artifact `career-radar-chrome-extension` ID `14164452927`, run `43721124467`, expires 2026-11-29; SHA256 `28a7301ba745a388c14ed928d00590028a13b70b16fb73fea74b842abe0af9a6`.
- PR preview build/deployment succeeded. No production Worker or Supabase changes.
- Remaining: user must install v0.1.3, reload dashboard, click Connect. Use the new stage-specific error if it fails. Browser connection and real ingestion remain unverified.

### Extension v0.1.4 MAIN-world dashboard handoff — merged 2026-11-15
- User reported v0.1.3 successfully found the dashboard tab and injected the bridge, but chrome.tabs.sendMessage failed with Receiving end does not exist.
- PR #146 merged to main as 2751a375db19c781330fd45ee7aca445ed6e7a3b. The dashboard content-script receiver was removed; extension uses chrome.scripting.executeScript in MAIN world and the dashboard's nonce-checked postMessage listener. CV password remains in dashboard context.
- Full regression run #43721950771 attempt 3 passed: 455 tests, 0 failures/errors/skips; frontend, extension API/schema, Bridge/Worker, public retrieval regression and extension package upload all succeeded.
- Artifact career-radar-chrome-extension, ID 14164932728, run 43721950771, expiry 2026-11-29, SHA256 ac9a75d9cba12eee59a060c104b3557cf89b9f9699b9a5768d3304a0ff17c089.
- No production Worker or Supabase deployment required. Remaining: user install v0.1.4, reload dashboard, connect, verify popup Connected, then confirm visible job ingestion.

### Career Radar extension v0.1.5 — automatic search and safe ingestion — 2026-11-15
- User screenshot confirmed extension connected and run started but Arbeitsagentur search form remained prefilled/not submitted; 0 listings. Existing progression required manual Next role.
- PR #147 merged as a4de637f6fa3b7dbae3289bde1746c6bf545aae2: auto-submit visible search form, wait for cards/no-results, auto-advance roles; pause on challenge/missing control/unconfirmed timeout. Popup automatic-mode status.
- PR #148 merged as 7f977c611a18e2eb0eecb2a2e4a7be0aa783d6e3: require successful ingestion acknowledgement before auto-advance; pause on ingestion failure.
- Final non-publishing regression #43724255150 passed: 455 tests, zero failures/errors/skips; all frontend, extension, Worker, RPC, retrieval and package steps passed.
- Artifact career-radar-chrome-extension ID 14166200445, run https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43724255150, expires 2026-11-29, SHA256 163b188b3607e4e7d027927c228578dfc56e136b4a838a328883e2e431498d67.
- No production Worker/Supabase deployment. Outstanding: install v0.1.5, reload extension and reopen Arbeitsagentur page; confirm search submission, visible cards and actual ingestion. Timeout pauses to avoid skipping jobs if extraction cannot be confirmed.


### Extension results dashboard v0.1.6 — merged, deployed and validated (2026-11-15)
- Private source PR #149 merged as 427ae0c8c003424ebbfc778702ea30b2a3cf7c3f. The release adds the dashboard Extension results page, password-protected private run/discovery APIs, owner-scoped run deletion, extension popup recent-opportunity preview and deletion, and transient ingestion retries. Supabase migration 20261115220000_career_radar_extension_results_management is applied; management RPCs are service_role-only.
- Exact merged-main full regression #43767811740 succeeded against candidate and base SHA 022c9d70c5bc98cc864a600a8a690ccf436a664e: 455 Python tests, zero failures/errors/skips; frontend syntax/contracts; Bridge/Worker/extension/restricted-RPC contracts; public retrieval regression; extension ZIP package and upload; private checkout cleanup all passed.
- Final artifact career-radar-chrome-extension ID 14183276230, run https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43767811740, expires 2026-11-29. ZIP SHA256 17dec021f38347c7f687ebabd91592b4ea8ce033fab8bf136f2a88c9e0e5a9d9. Manifest version 0.1.6.
- Cloudflare deploy #43767544365 succeeded. Dashboard Worker career-radar-dashboard version 474 (033563bb-8a26-4093-b62d-89a019736eeb) and Bridge Worker career-radar-bridge version 82 (38cdfe13-95ce-4eef-8826-bd9e5e630f3a) are each deployed at 100% traffic. Existing bindings/secrets were preserved by Wrangler workflow.
- Hugging Face Space UI sync #43767584824 succeeded and published the allowlisted UI assets only.
- Runner workflows now support explicitly marker-gated push triggers for Cloudflare dashboard deploy ([dashboard-deploy]) and Hugging Face UI sync ([space-ui-sync]), while preserving manual dispatch. Public runner smoke contract tests were updated to require these exact marker guards.
- Remaining acceptance: user must replace prior unpacked extension with artifact 14183276230 (v0.1.6), reload it, refresh dashboard, unlock Master CV/Role targets, connect, then start autopilot if no active run exists. Confirm new Extension results tab displays the existing 115 saved records and that a fresh run submits Arbeitsagentur search, saves visible cards, and advances only after save acknowledgement. Browser-level connection and live ingestion are not yet verified by automation.


### Extension autopilot and rich-results candidate validation — in progress 2026-11-15
- Private source branch `happytiswis-sudo/engineering-career-radar:fix/extension-autostart-rich-results-ux` is being prepared against current private main. It fixes Connect→autostart ordering while preserving mandatory catalogue loading, improves popup UX, normalizes Arbeisagentur employer/title metadata, and adds transparent discovery evidence details in the dashboard.
- The runner regression workflow currently maps known release markers to specific private branches. Add a dedicated `[extension-autostart-rich-results-ux]` marker mapping before validating this candidate; do not use the old extension-results feature branch because it is stale/diverged.
- Trigger the existing non-publishing full regression by committing the workflow mapping on runner main with that exact marker. The workflow will merge current private main into the candidate in an ephemeral checkout and run the full Python suite, frontend/extension syntax and contracts, Worker/RPC tests, public retrieval regression, and extension ZIP packaging.
- Do not deploy or merge the private candidate until the exact candidate/base run passes. A successful regression does not prove local Chrome/Arbeitsagentur browser acceptance.


### Extension autopilot UX candidate regression — validated 2026-11-15
- Added marker mapping `[extension-autostart-rich-results-ux]` to the private regression workflow, targeting private branch `fix/extension-autostart-rich-results-ux` rather than the stale `feat/extension-results-dashboard-autopilot-ux` branch.
- Candidate regression run `43770219779` passed all full-suite, frontend, extension Bridge/RPC/Worker, retrieval regression and extension ZIP package steps. Public runner smoke `43770219777` passed.
- Candidate branch was based on private main SHA `b7522e1cd4516b9676039bcaec0676f000aaeb86` with zero behind commits. The test run is non-publishing; no Cloudflare deployment was performed by this regression.
- Next: merge the reviewed private PR, then trigger the dashboard/Bridge deployment workflow with `[dashboard-deploy]` and verify production worker versions. Do not claim Chrome browser acceptance until the owner tests the extension against Arbeitsagentur.


### Extension autopilot UX merged — deployment triggered 2026-11-15
- Private PR #150 was merged to `main` at `0678c2bd4bccf08961a39d14a9a2354b0cb67269`; Cloudflare Workers Builds check completed SUCCESS for the dashboard preview.
- The private main branch now contains extension v0.1.7, Connect auto-start, serialized/recoverable discovery ingestion, popup UX and Extension results detail/evidence UI.
- Trigger the existing production dashboard + Bridge Worker deploy workflow by a runner-main commit with `[dashboard-deploy]`. The deploy workflow validates frontend/navigation/Worker contracts, checks Cloudflare credentials without exposing values, deploys both Workers, and removes the private checkout.
- After deploy, verify the runner workflow and production worker health/version. Browser acceptance still needs real Chrome and logged-in Arbeitsagentur testing.


### Production deployment complete — 2026-11-15
- Private PR #150 merged at `0678c2bd4bccf08961a39d14a9a2354b0cb67269`.
- Regression `43770219779` and smoke `43770219777` passed.
- Production deployment run `43770364902` checked out the exact merged private main SHA and deployed dashboard and Bridge Workers successfully. Redundant run `43770412280` also completed SUCCESS.
- Cloudflare current deployments (100% traffic): `career-radar-dashboard` version `688ff554-562f-4514-ab6b-79e5a9ea8a2a`; `career-radar-bridge` version `8f46115c-35e6-4dce-9478-a119b2f84a36`.
- Extension ZIP artifact `14183702206` (v0.1.7) verified and downloaded for owner installation. Browser acceptance still needs owner to test with authenticated Chrome/Arbeitsagentur.


## Extension acceptance follow-up — 2026-11-16 (investigation opened)
- User browser evidence from 2026-11-16 shows the latest extension session `ed33bf42` completed at `Role 1 of 1` with 44 visible listings, 22 saved and 22 duplicates skipped. This is not evidence of a complete catalogue search. The dashboard also displays older sessions with 784 roles, several marked running with zero saved; investigate session lifecycle/role-catalogue selection and why a one-role session is labelled completed.
- User reports the dashboard can stop/delete runs including in-progress runs; preserve that capability and verify safe cancellation/deletion semantics, including pending extension uploads and server-side ownership checks.
- User requires Extension results to meet the main Results assessment standard: real per-job CV fit score /100, AI review, evidence-backed CV strengths and weaknesses, and explicit justification for senior-role suitability. Senior roles must not be silently excluded; inspect role catalogue and strict-search preferences. Do not fabricate scores or assessment evidence.
- Add an explicit Save to Applications action for extension discoveries, using the existing authenticated Applications persistence path and existing schema/RLS; do not create a parallel browser-only store or expose private data through public HF JSON.
- Inspect current main after PR #150, relevant frontend/extension/bridge/Supabase contracts, and run current regression before edits. Update operational/specification/decision/handoff docs after implementation. Do not claim browser acceptance without owner-side test.
- UI reference: screenshots supplied 2026-11-16 (Arbeitsagentur popup, Extension results session list, opportunity detail modal).


## Private candidate regression routing — 2026-11-16
- Added marker `[extension-full-catalog]` to route a public runner push-triggered private regression to private branch `fix/extension-full-catalog-and-application-save`.
- Trigger commit: `974b57267802d2bc00084e5aad434faa081a595b`. Inspect the actual workflow run and result before claiming regression PASS.
- Candidate PR #151 is open and not merged/deployed. Its remaining product gate is full advert detail extraction and real AI CV assessment for extension vacancies.


## Supabase security observations — 2026-11-16
- Supabase verbose table inventory emitted a critical advisory that 167 public-schema tables (largely n8n/workflow tables) have RLS disabled and are exposed to anon/authenticated Data API roles. This needs a dedicated access review. Do NOT blanket-enable RLS: doing so without carefully designed policies may break n8n and related integrations. No RLS changes were applied.
- Current Supabase security advisor separately reports 9 `career_radar_private` tables with RLS enabled but no policies, and leaked-password protection disabled. Service-role RPC access may be intentional for private tables, but validate grants and schema exposure; no blanket policies or auth settings were changed.


## Extension assessment continuation — 2026-11-16
- Private continuation branch is now `fix/extension-complete-ai-assessment`, created directly from private `main` SHA `41bcb66e5dc9dc8b88ad33900a71288708596d69`. It replaces the stale PR #151 branch for further work; do not validate the old branch as a clean merge candidate.
- Previous private regression runs: `43827108167` failed 3/455 Python contracts (catalogue track allocation, LinkedIn queue counts, master spec count); `43827202472` failed in the ephemeral merge due conflicts in extension files/docs. Do not mark these PASS.
- The new branch carries forward catalogue validation, 801-role/35-track senior catalogue, BA query mapping for Engineering Leadership & Management, dynamic count assertions, optional search filters, Applications save action and extension results UI. No merge or production deployment yet.
- Next implementation gate is full Arbeitsagentur detail-page extraction plus a runner-side AI assessment worker reusing the private `radar.ai_assess` pipeline and provider fallback; persist real score/strengths/gaps/quotes in existing extension discovery `job_data` JSONB. Also implement safe stop-then-delete for running sessions while preserving unsynced local discoveries.
- Before triggering CI for the new branch, update this workflow's commit-message routing marker to target `fix/extension-complete-ai-assessment`; then run the full private suite, frontend contracts, extension contracts, public retrieval regression and package step. No deployment until all gates pass.


## Extension assessment regression update — 2026-11-16
- Latest private candidate regression `43830328639` PASSED, including full private Python suite, frontend contracts, extension Bridge/restricted RPC/Worker syntax, public retrieval regression, and extension ZIP packaging/upload. Public runner smoke `43830328622` PASSED.
- Candidate branch is `fix/extension-complete-ai-assessment` (private repo). Do not confuse the public runner main commit with private candidate source SHA; workflow routing marker selects the private branch for the isolated regression merge.
- Assessment workflow `.github/workflows/extension-ai-assessment.yml` is scheduled every 10 minutes, but not production-active until private source merge and migration application. Verify required secret names and first scheduled run after merge; no production data has been assessed by this new worker yet.
- Full advert detail extraction currently captures when the user opens an Arbeitsaagentur detail page; it does not automatically crawl every listing from result pages. Historical short-snippet rows remain `needs_detail` until captured. Do not describe all saved opportunities as assessed.
- SQL migrations for detail enrichment, AI assessment lifecycle, and atomic stop/delete were syntax-smoke-tested in a transaction with rollback only; production schema unchanged. No merge or production deploy has happened.
- Keep all production publishing blocked until PR review, migration/deployment ordering, scheduled worker configuration and browser acceptance are resolved.


## Automatic extension detail-crawl candidate — 2026-11-16
- Private draft PR #152: https://github.com/happytiswis-sudo/engineering-career-radar/pull/152, branch `fix/extension-complete-ai-assessment`, not merged.
- The extension now automatically visits each newly discovered unique Arbeitsaagentur vacancy in one inactive tab, extracts full advert description/structured requirements, and enriches the existing discovery before the next search term. Queue/index persist across service-worker suspension, prior URLs are skipped, page failures time out and advance safely, unexpected tab closure pauses and preserves the remaining queue, and Resume restarts from the next URL.
- Supports both observed `/jobsuche/jobdetail/<id>` and SPA `/jobsuche/suche?id=<id>` formats. Added `discoveries:write` token scope; a forward SQL migration updates direct token issuance validation. Existing extension users must reconnect once after installing v0.1.11.
- Latest complete private regression `43832141934` PASSED all stages including extension packaging; public runner smoke `43832141925` PASSED.
- Four SQL migrations passed combined transactional syntax smoke and rollback; no production schema change has occurred.
- Scheduled assessment workflow is defined but has not run against production data. Verify its secrets/variables and first controlled execution after merge. Do not deploy or merge until migrations, worker configuration and browser acceptance are complete.


## Private extension release merged; deployment pending — 2026-11-16
- Private PR #152 merged to private main as `8da29090110d604e8b5c412a7263667965acdf1e`. It includes automatic sequential detail crawling, retry-safe save behavior, full-detail enrichment, AI assessment worker/RPCs, safe stop/delete and senior-role support.
- Latest full regression `43833807882` PASS, public smoke `43833808050` PASS.
- Four production Supabase migrations applied successfully and verified via migration list and SECURITY DEFINER RPC catalog inspection.
- Assessment workflow has an intentional safety gate: `EXTENSION_ASSESSMENT_ENABLED=true` or manual workflow_dispatch. Do not enable until `PRIVATE_SOURCE_READ_TOKEN`, `SUPABASE_SERVICE_ROLE_KEY`, and at least one supported provider key are configured. A malformed duplicate `workflow_dispatch` key was corrected; latest public runner smoke after the correction `43833884972` passed.
- Next: deploy dashboard and Bridge by updating this workflow file with a commit message containing `[dashboard-deploy]`. Then verify Cloudflare active versions, public smoke and dashboard endpoint. Extension v0.1.11 package is built by regression artifact, but only distribute after production Bridge/dashboard deployment.
- The assessment workflow has not yet been run successfully against production data. Scores remain genuinely unassessed until the scheduled worker runs with valid secrets and the jobs have sufficient full description.


## Production deploy complete — 2026-11-16
- Deploy workflow `43834181614` SUCCESS. Cloudflare dashboard Worker version `5c0bffb6-2dc2-4cdf-9b23-05c3d2c57fc8` and Bridge version `eb315270-e839-4749-ba64-cfed6a7dc962` are active at 100%. Public runner smoke after deploy `43834181506` PASS.
- Extension v0.1.11 install package from regression run `43833807882` downloaded and integrity checked. SHA-256 `053c83b8d12652a648355eb713b37d62898dc4effe0e19302d7af6797bc8e964`; manifest 0.1.11.
- Private PR #152 merged as `8da29090110d604e8b5c412a7263667965acdf1e`; stale PR #151 closed.
- Production Supabase migrations applied and RPC catalog verified.
- AI worker remains gated off until repo variable `EXTENSION_ASSESSMENT_ENABLED=true` and required secrets are confirmed: `PRIVATE_SOURCE_READ_TOKEN`, `SUPABASE_SERVICE_ROLE_KEY`, and at least one provider API key. Do not mark assessment live until a successful controlled workflow run.
- User acceptance still required for extension installation/reconnect, multi-role autopilot/detail crawling, Applications save, and running-session stop/delete. Keep all future agents aware that no production AI assessment run has yet been proven.


## Extension AI assessment queue diagnosis — 2026-11-16
- User manually dispatched public runner workflow `extension-ai-assessment.yml` (run #5); job succeeded in 10 seconds but printed `{"claimed":0,"assessed":0,"failed":0}`. Workflow success was only execution success, not assessment success.
- Read-only production Supabase inspection (project `plzjmyytuumxckbrrzlp`, owner `8c83077c-6e1a-4c5e-b15f-30e69617d997`) found 137 extension discoveries: 137 empty `job_data.description`, 0 descriptions >=400 chars, 137 default/pending assessment statuses, 0 assessed, 0 failed, 0 processing, and no `assessment` or `detail_enriched_at` keys.
- Latest completed extension run `ed33bf42-b389-46ed-84a2-b9c1d02d11f7` (2026-11-16 07:31 UTC) created 22 discoveries and completed in ~16 seconds; all 22 descriptions are empty. Prior 115 discoveries are also snippet-only. This is consistent with the installed browser extension not executing the v0.1.11 automatic detail crawler, but the database does not store the installed extension version, so that specific cause is not yet proven.
- Production claim RPC `career_radar_extension_claim_assessments(uuid,integer)` was read back. It correctly selects only rows with description length >=400 and pending, retryable failed, or stale processing status. The zero claim is therefore correct; do not weaken the 400-character evidence threshold or fabricate assessments.
- Current private `main` extension manifest is v0.1.11. Its background worker queues each unique visible vacancy URL into a single background tab, extracts detail via content.js and calls `/discoveries/enrich`; this is the path needed to enrich existing rows (enrichment updates the existing owner+canonical URL row). Historical snippet-only rows require the browser crawler to revisit their URLs; the AI workflow cannot backfill details.
- Required next acceptance: owner must install/reload v0.1.11, reconnect once for `discoveries:write`, then run a full catalogue search while keeping the browser open. Verify the extension popup shows detail-crawl progress and Supabase descriptions >=400 before rerunning AI assessment. If the installed extension is already v0.1.11, investigate why the detail queue is not starting/saving; inspect extension console and bridge enrichment responses. Do not repeatedly dispatch an empty assessment workflow.
- No production data was modified during this investigation. No code/schema changes were made. Queue status: BLOCKED on detail enrichment/browser acceptance, not credentials or AI provider configuration.


## User acceptance feedback — extension search relevance and autopilot — 2026-11-16
- User supplied live browser screenshots (Run `37a308be`, role 1/801, query `Project Engineer`, Frankfurt). Popup showed 2 listings saved and detail crawl progress stuck at `0 of 2`; dashboard cards showed `Full details needed`. User reports a new job-post tab opened and a blocked role stopped autopilot.
- Confirmed source behavior: `searchPlan` currently contains every role title in catalogue order (801), without using Master CV or configured skill weights to rank/filter. It starts with generic `Project Engineer`; only 18 catalogue titles match senior/lead/principal/manager/director/head/staff. This is not CV-targeted search and does not prioritize experienced-level opportunities.
- `SEARCH_PAGE_READY` currently pauses the entire run on blocked/captcha, missing search control, timeout or ingestion error. A blocked individual role therefore stops autopilot instead of being recorded and skipped safely. Genuine ingestion failures should remain fail-closed.
- `startDetailCrawl` creates a tab with `active:false`, but popup showed 0/2. Content script immediately reports failure when first detail extraction is under 400 chars; Arbeitsagentur SPA hydration can still be in progress. This likely race needs fixing and instrumentation. Current progress does not expose per-item URL/error.
- Search is currently discovery-only: listings are saved, then a separate GitHub Actions assessment worker creates CV scores after full descriptions arrive. It is not triggered by the user's Search action. User explicitly wants on-demand behavior: clicking Search starts discovery, full-detail retrieval, CV assessment and results; no reliance on a 10-minute schedule.
- Acceptance: search relevant to private Master CV/configured skill weights and career tracks; prioritize senior/lead/principal/management and suitable experienced roles; junior/generic titles must not dominate; keep relevant adjacent-role coverage; enrich full descriptions before CV assessment; show genuine evidence-based fit scores/reasons; blocked roles are reported and skipped/retried without freezing the whole run; assessment is initiated by Search.
- Architecture constraint: provider credentials and private CV stay server-side. Do not expose keys or raw CV to extension JS. Implement authenticated server-side on-demand queue/trigger. Preserve >=400-char assessment evidence gate and never fabricate scores.
- No code/schema/production data changes yet for this acceptance feedback. Next work: instrument/fix detail SPA hydration and tab lifecycle; CV-skill/seniority rank search plan; make individual blocked role a recorded non-fatal outcome; implement secure on-demand assessment trigger; add tests and regressions. Update both handoffs after implementation.

## Extension search reliability v0.1.12 candidate — 2026-11-16
- User explicitly requires click-to-search behavior with CV-relevant opportunities, senior/master-level roles, complete vacancy retrieval, and AI assessment on demand (not a recurring 10-minute wait).
- Production evidence: latest browser screenshot shows run 37a308be on role 1/801, 4 listings seen, 2 saved, 2 duplicates, but detail progress 0 of 2; results page labels both opportunities Full details needed. User reports a detail tab opened visibly and one role retrieval blocked.
- Started private branch fix/extension-search-ranking-and-resilient-crawl.
- Candidate code changes: role title plan sorts senior/lead/principal/staff/chief/head/director/manager and engineering/project/systems/aerospace/aviation/UAV/SATCOM/maintenance/CAMO/telecom/data/AI/operations families earlier; recoverable per-role timeout/search-control-not-found advances to next role with a skip record; CAPTCHA/access challenge still pauses (never bypass); save/ingestion failure still pauses to protect data; detail-page extraction waits for asynchronous rendering instead of failing immediately on first short DOM and increases final detail timeout to 45s; popup action label changed to Search now; manifest candidate v0.1.12.
- Code commits on branch: background ranking + continuation 84cf36a, content detail wait 5cbd1a4, popup label 770ab7b, manifest version 3dcdcc8, regex word-boundary correction ff1469f.
- Important limitation: this candidate improves role ordering and search resilience but does NOT yet perform true Master-CV-personalized role planning or immediate AI assessment. Those require a secure server-side CV-aware planning/assessment trigger integrated with the private CV and provider pipeline. Do not claim those functions implemented.
- No merge, production deployment, or browser installation has occurred. Must add tests for role ordering, timeout skip, CAPTCHA pause, and detail hydration; validate branch with full private regression before merge.
## Extension v0.1.12 resilience candidate — 2026-11-16 09:54 UTC
- PR #153 open as draft: https://github.com/happytiswis-sudo/engineering-career-radar/pull/153; branch fix/extension-search-ranking-and-resilient-crawl; latest candidate commit `69e67526afa27169b1c74e64689eea2623f99059` (tests included).
- Changes: search plan prioritizes senior/lead/principal/staff/chief/head/director/manager plus engineering/project/systems/aerospace/aviation/UAV/SATCOM/CAMO/maintenance/telecom/data/AI/operations families; recoverable timeout and missing-search-control role failures advance; CAPTCHA/access challenge and ingestion failures still pause; detail extraction retries short first DOM and allows 45s hydration; popup button says Search now; manifest v0.1.12.
- Added tests/test_extension_search_resilience.py and updated tests/extension_api_contract.test.js for v0.1.12. Two early regression attempts exposed stale version/timeout assertions and then test assertion syntax/scope mistakes; these were corrected. Final exact-candidate full private regression run 43843795709 PASSED: Python suite, frontend contracts, extension Bridge/restricted RPC/Worker syntax, public retrieval regression, extension package, upload and cleanup. Public runner smoke 43843795728 also succeeded.
- Final install package `/mnt/data/career-radar-extension-v0.1.12-install.zip`, extracted inner install ZIP from run artifact 14214585893; manifest 0.1.12; archive integrity PASS; SHA256 `2e9af3a7909130ac14020cdcde6a0366fa04bf9b4dbef60411c58c89bdcdaa8d`. Outer artifact SHA256 `0117bb382d822bd299f778f7cc73cea7c22d1a938068a1e97104d1436996ebee`.
- PR #153 remains draft and unmerged; no production deployment. Do not distribute as production fix until outstanding architecture requirements are addressed.
- Still outstanding per user requirement: true Master-CV-derived role planning/matching and immediate on-demand AI assessment triggered by clicking Search. Current changes only prioritize role families and improve crawl/search resilience. Assessment workflow remains GitHub Actions-driven (manual/scheduled), not synchronously invoked by extension. Need design a secure server-side assessment dispatch path; browser must never receive Master CV, provider keys, service-role key, or GitHub write token. Existing `PRIVATE_SOURCE_READ_TOKEN` is read-only and cannot dispatch workflows. A new narrow server-side GitHub App/PAT dispatch credential or separate secure assessment service will be required; don't ask user to paste credentials into chat.
- Browser acceptance is outstanding. The user has not yet installed v0.1.12 or confirmed full-detail capture; current production rows still had 137 empty descriptions at last DB inspection. No Supabase production data, migrations, or Cloudflare deployment changed in this candidate.

## User acceptance work — Search-triggered AI assessment (2026-11-16)
- The private Bridge candidate PR #153 now dispatches this workflow automatically via the encrypted Cloudflare Worker GitHub Actions token when an extension Search run reaches its completed lifecycle state. This removes reliance on the 10-minute schedule/manual operator click for extension runs.
- This is asynchronous: the workflow must claim pending full-detail discoveries, use the private Master CV and settings, and persist genuine provider-backed assessments. Dispatch HTTP acceptance alone is not assessment success. Keep score state pending/failed until the runner confirms completion.
- Workflow_dispatch must remain enabled and must not require `EXTENSION_ASSESSMENT_ENABLED`; that variable is only relevant to optional scheduled runs. Keep secrets server-side: `PRIVATE_SOURCE_READ_TOKEN`, `SUPABASE_SERVICE_ROLE_KEY`, and at least one supported AI provider key. Do not expose or print their values.
- Candidate implementation remains unmerged/unreleased until PR #153 has full regression PASS, smoke PASS, credential readiness and an actual assessment run verified. Update this handoff after validation/deployment.

- Incremental dispatch refinement (2026-11-16): the private Bridge now requests this workflow after each 10 successfully enriched adverts during an active Search run, then issues a final catch-up dispatch when the run completes. The assessment worker drains eligible full-description rows in repeated batches (20 per claim) until the queue is empty or its 14-minute processing deadline is reached. GitHub concurrency serializes dispatches; a dispatch response is only queue acceptance, never proof of a saved score.
- Current candidate remains PR #153 and is not production-active. Exact-candidate regression and an actual provider-backed workflow run are still release gates. Do not infer secret readiness from the presence of workflow YAML.


## Extension assessment candidate checkout gate — 2026-11-16 (in progress)
- The private Bridge dispatch in PR #153 currently sends only `ref: main`, and this workflow checks out private `main` unconditionally. A workflow success therefore cannot validate or execute the unmerged PR candidate.
- Follow-up runner branch: `fix/extension-assessment-candidate-checkout`. Implement a narrowly validated `source_ref` workflow_dispatch input defaulting to `main`; allow only `main` or the explicitly approved private candidate branch `fix/extension-search-ranking-and-resilient-crawl` during candidate validation. Checkout that ref with `PRIVATE_SOURCE_READ_TOKEN`. Do not permit arbitrary caller-supplied refs to execute with Supabase/provider secrets.
- Dispatch contract should include source_ref and an opaque run_id for correlation. The worker must not send CV content, job descriptions, provider keys, or service-role credentials.
- Keep the >=400-character description gate, service-role-only RPC claims, private checkout cleanup, and asynchronous semantics. Dispatch acceptance is not an assessment result.
- Do not enable scheduled assessment or change production secrets/variables. Validate candidate workflow with a controlled manual/Bridge dispatch and verify the checkout SHA and real persisted score before any PASS claim.


## Assessment dispatch hardening implemented — 2026-11-16 (validation pending)
- Branch `fix/extension-assessment-candidate-checkout` now defines workflow_dispatch inputs `run_id` and `source_ref`. `source_ref` is allowlisted to `main` and the exact private PR #153 candidate branch; arbitrary private refs are rejected before checkout/secrets use.
- Private checkout now uses the validated selected ref, so a candidate dispatch can test the exact PR source instead of silently checking out stale private main. The Bridge production contract will continue to send `main`; after merge, main is the release source.
- Assessment process receives `EXTENSION_RUN_ID`; Supabase claim RPC is run-scoped when supplied. Per-run Actions concurrency prevents duplicate invocations for one Search run from running concurrently; distinct Search runs remain isolated.
- Existing credentials remain server-side, private checkout cleanup retained, and workflow_dispatch remains independent of optional scheduled flag. No secrets/variables changed and no workflow run has yet been dispatched from this branch.
- Runner workflow PR and end-to-end candidate validation remain pending.


## Candidate regression correction — 2026-11-16
- First full private candidate run #43848430109 passed 464 Python tests, frontend contracts and candidate/base reconciliation, then failed an outdated extension Bridge assertion at private tests/extension_api_contract.test.js:46. The private-source reader had been refactored to a shared helper using encrypted CV_GITHUB_TOKEN; the test still expected the previous inline fetch expression.
- Private candidate follow-up branch updated the contract to assert the shared reader and its role-catalogue/settings/Master-CV call sites. This is a test-only correction; no credential routing changed.
- Trigger another PR validation run to rerun the full private regression against the corrected candidate branch. Do not treat the first run as PASS.


- Second exact candidate run #43848648754 again passed 464 Python tests, frontend contracts and reconciliation, then exposed a JavaScript test declaration-order bug (ReferenceError: assessmentSource before initialization). The implementation parsed successfully; the contract test now moves the declaration before first use. Trigger another full candidate regression and require all later stages plus extension package integrity to pass.

- Third full regression run #43848812034 confirmed the same temporal-dead-zone failure because the first automated move had left the later declaration in place. The private test file now removes all old declaration instances and inserts one before the first use; exact one-declaration count was checked before commit. Trigger a new complete regression; the prior attempts are failures, not PASS.

- Third regression attempt #43848942710 passed the 464 Python tests, frontend syntax/contracts, and earlier Bridge assertions, then failed on a stale test identifier expecting `personalization:catalogue.personalization`; actual worker response correctly uses `personalization:catalog.personalization`. Updated the private test to match the actual response property. Trigger another full suite and require Bridge, retrieval regression, and package upload to pass.

- Fourth full regression attempt #43849107210 passed the 464 Python tests, frontend contracts, private-source credential contract, and CV-plan fingerprint/personalization assertions. It then found the next stale condition assertion: the Worker combines `complete` and checkpoint dispatch in one condition, while the test expected an isolated complete-only expression. Updated the test to assert the combined condition. Trigger another full regression.


## PR #17 merged; candidate regression verified — 2026-11-16 10:30 UTC
- PR #17 merged to public runner main as `991f90778c3769c261f7973146c2c38ec8f542be`. Workflow `.github/workflows/extension-ai-assessment.yml` now accepts optional UUID `run_id` and restricted `source_ref`; it checks out only `main`, PR #153 candidate branch, or PR #154 trusted follow-up branch, passes `EXTENSION_RUN_ID`, and serializes per Search run. Private checkout cleanup and server-side secret handling remain.
- Private scanner regression is now reusable via `workflow_call`; runner PR validation invoked it against private follow-up branch `fix/extension-search-assessment-hardening` merged with current private main in ephemeral workspace.
- Full regression run `43849291428` completed SUCCESS: 464 private Python tests (0 failures/errors), frontend syntax/contracts, extension Bridge/restricted RPC/Worker syntax/API contracts, public retrieval regression, extension package and artifact upload, private checkout cleanup. Runner workflow validation and public runner smoke both SUCCESS.
- Tested extension artifact ID `14215624470`; outer ZIP SHA-256 `f5791e1ee9cc767182ebeaa16ec56e6255d0eba2b67934d40581f0c92535e914`; inner install ZIP SHA-256 `50fa9ad9f8b2097a0cdc7d316b60d14a683d7189e0a9b7316d06e097da2aa07b`; manifest version 0.1.12.
- No secrets or repository variables were changed. No assessment workflow was dispatched and no production score was verified. The new workflow is available on runner main; production Worker still needs reviewed deployment and Supabase migration application before Search-triggered calls can use run-scoped claims.
- Keep PR #153 unmerged/unreleased until an actual candidate-scoped provider-backed workflow run writes a validated assessment and Supabase read-back confirms the same run-scoped row. Dispatch acceptance is not assessment success.


## Backward-compatible assessment migration note — 2026-11-16
- Private candidate migration was adjusted to add the run-scoped 3-argument claim RPC without dropping the existing 2-argument RPC. This preserves already-deployed main worker compatibility during rollout; new candidate calls explicitly pass p_run_id. Both remain service-role-only. Full candidate regression rerun pending.


## Final run-scoped assessment regression — 2026-11-16 10:35 UTC
- Private candidate migration preserves the legacy 2-argument claim RPC while adding a service-role-only 3-argument owner+run-scoped overload. Existing main workers remain compatible during rollout; candidate workers pass explicit `p_run_id`. The 400-character description gate and skip-locked claims remain.
- Reran private candidate regression job in run `43849107210`, attempt 2: SUCCESS. 464 Python tests, frontend syntax/contracts, Bridge/restricted RPC/Worker syntax/API contracts, public retrieval regression, extension package/upload and cleanup all PASS. Runner validation and public runner smoke PASS.
- Latest artifact `14216592963`; outer ZIP SHA-256 `a45a57904fcef6570b12bf3b58d7e6243e56f7313e822ca723d158aef8a54f34`; inner install ZIP SHA-256 `98de2b9c3c87729be19bf69e568baa43cc8a2c3c2ab9425e7deeeabef33191d2`; manifest v0.1.12.
- No workflow dispatch, provider-backed score write, Supabase migration, Worker deployment, secret change or browser acceptance has occurred. Keep release gate closed until the scoped workflow writes a real score and Supabase read-back confirms it.


## One-time provider-backed extension assessment PASS — 2026-11-16 10:39 UTC
- Production migration `career_radar_extension_assessment_run_scope` applied; 3-argument owner+run claim RPC read-back verified with only postgres/service_role execute privileges. Legacy 2-argument function remains intact.
- One-time PR #18 harness invoked the reusable workflow against private source ref `fix/extension-search-assessment-hardening` and run UUID `37a308be-eec6-4a42-97e1-7e3f24de5fd6`. Workflow run `43850655850` SUCCESS. Assessment job output: `claimed=1, assessed=1, failed=0, eligible=1, providers_configured=3`.
- Supabase read-back verified one real assessed row (discovery 343; 5,779-character description; score 12/100; recommendation Skip; 4 strengths/4 gaps; provider Inception Mercury 3, model mercury-3). A second short-description row in the same run remains `needs_detail` and was not claimed. Scope isolation and >=400-character evidence gate are proven.
- Temporary runner PR #18 closed without merging its workflow_call harness. Normal runner main retains workflow_dispatch inputs for run_id/source_ref. PR #17 remains merged.
- Full candidate regression run `43849107210` attempt 2 remains PASS (464 Python tests and all frontend/Bridge/retrieval/package/cleanup stages). No secrets or repository variables changed.
- Next: private PR #153 merge and normal Cloudflare dashboard/Bridge deploy; then verify live Bridge and have user install v0.1.12 for browser UX acceptance. The Supabase migration is already applied; no Worker deployment yet.


## Final v0.1.12 production release — 2026-11-16 10:46 UTC
- Private PR #153 merged as `b393ebb5aa9f45988c309c3e0e806802751d50b4`; PR #154 stacked changes were included. Runner PR #17 merged as `991f90778c3769c261f7973146c2c38ec8f542be`.
- Production run-scoped assessment migration applied; legacy 2-arg RPC retained. Real workflow run `43850655850` succeeded with 1 claimed/1 assessed/0 failed and provider configuration verified. Supabase read-back confirms one eligible row persisted with genuine 12/100 Skip result, 4 strengths/4 gaps, provider Inception Mercury 3; short-detail row remained unassessed.
- Exact-candidate full regression run `43849107210` attempt 2 PASS (464 Python tests and all frontend/Bridge/retrieval/package/cleanup stages). PR #156 observability regression run `43851475225` PASS.
- Cloudflare deploy `43851054298`: dashboard d82e2939-8752-42d8-bac5-8119fe971e2d; Bridge 55aa2910-88c3-4013-a2e9-99965e95c8f0. PR #156 merged as `4c46fc2c20cef98f5be8dcd36473a42910d735d0` to make observability durable.
- Latest deploy `43851612565` SUCCESS: dashboard version `df237991-fa6f-4093-b2b2-0ed37e582813`; Bridge version `415f9e1e-4c9d-4ba1-bc9d-d46701b0ec54`; both 100% traffic. Binding inventory verified and secrets preserved.
- Live Bridge observability verified: query-string redaction true, persistent logs false, invocation logs false, traces disabled. Same settings in Wrangler production and preview config.
- Remaining user-side acceptance only: install/reload extension v0.1.12, reconnect once if popup requests updated discoveries:write scope, run a live Arbeitsagentur Search, keep browser open until detail crawl completes, and confirm UX/results. No publishing scan run.
