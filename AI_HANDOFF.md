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
