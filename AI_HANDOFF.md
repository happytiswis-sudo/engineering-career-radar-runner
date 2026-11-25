# LATEST STATUS — Cloudflare production deployment (2026-11-25)

- **Authorization:** Explicit user authorization received for the Cloudflare dashboard/Bridge deployment only. Do not infer authorization for a production scan.
- **Workflow:** `.github/workflows/deploy-cloudflare-dashboard.yml`, manually dispatched Run [#34](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45512873816), completed SUCCESS (38 seconds; no errors).
- **Source:** Workflow checked out private repository `happytiswis-sudo/engineering-career-radar` `main` at `716b65283e681c3e13f6680073d9293f2ed90e7e` using a read-only token. Cloudflare credential-presence preflight passed; no credential values were printed or changed.
- **Dashboard Worker:** `career-radar-dashboard`, deployment `b6f961cb-5989-4843-93db-0bdc3c0aaa7e`, version `bc6526ba-3de3-45f1-b3be-66356d3132e6`, 100% traffic.
- **Bridge Worker:** `career-radar-bridge`, deployment `d8d02055-e280-4188-9965-9a65c5a6674b`, version `97806124-2698-4358-8e97-653008bf2019`, 100% traffic.
- **Post-deploy API read-back:** Dashboard ASSETS, BRIDGE service, and DASHBOARD_API_KEY bindings remain. Bridge ARCHIVES R2 bucket, rate-limit bindings, and all existing secret-text binding names remain. Secret values were not accessed. No R2 objects or recovery snapshots were modified.
- **Scope clarification:** This workflow deploys the dashboard Worker/assets and the search Bridge Worker. Stage 3 provider compatibility correction is Python scanner source in private `radar.py` (PR #260); the next production scan will consume that merged code. No production scan/provider request was started. Do not run `production-scan.yml` or trigger provider activity without separate explicit authorization.
- **No Supabase writes/migrations, HF publication, R2 object writes, archive mutations, secret changes, or recovery-snapshot modifications.**
- **Next:** User performs dashboard UX acceptance. Keep any production scan as a separate approval gate.

---

# AI Handoff — Public Execution Runner

**Last verified:** 2026-11-16  
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
- `production-scan.yml`: manual-only scanner run initiated by dashboard **⌕ Search jobs** (`workflow_dispatch`). It has no cron/schedule trigger. Preserve the dashboard dispatch path; never restore automatic scans. Public publication remains behind both explicit authorization gates.
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


## Bachelor's / non-senior Search release — 2026-11-16
- Private PR #157 merged as `160f52fdcd15906a425c733dcd5c462274463895`; follow-up PR #158 merged as `8e42eb742f739128d45f0184accedfa4d823efe9`.
- Full candidate regression #43867285315 passed 468 Python tests and all frontend, Bridge, RPC, retrieval, packaging and cleanup stages. Follow-up regression #43868423081 passed the same 468 tests after mixed-clause qualification hardening. Runner validation and smoke #43868423083 passed.
- Temporary validation PRs #20, #21 and #22 were closed without merging; no temporary workflow pointer is left in runner main.
- Production deployment trigger commit: `0093368a5369b2e3a9d1427a50102a5dcfcceab5`. Cloudflare control-plane read-back confirms dashboard version 485 `3f6fdc63-8db4-4aba-9386-126a69209fe4`, deployment `ecfc2a85-579b-4f83-aed4-5b19ce2a2b0d`, 100%; Bridge version 88 `79a6ce27-bc5e-42c7-9a30-c047455cd00d`, deployment `3e62ab3f-92be-4bac-8803-96a8a135f72f`, 100%.
- Deployed Bridge source read-back includes the new configured senior-title exclusions and bachelor profile fields. Bindings preserved: R2 ARCHIVES, both rate limiters, CV_GITHUB_TOKEN, CV_PASSWORD, DASHBOARD_API_KEY, GITHUB_TOKEN, HF_SPACE_ID/HF_TOKEN, SUPABASE_URL/ANON/SERVICE_ROLE, ARCHIVE_CI_TOKEN and pairing secret. No secret values were read.
- Bridge observability read-back: query-string redaction true; logs enabled but persist false and invocation logs false; traces disabled and persist false. Dashboard settings read-back also confirms query-string redaction and non-persisted logs; its traces remain enabled with persistence false (unchanged configuration).
- No production scan or publishing workflow was dispatched. HTTP smoke via available web fetch was unable to reach workers.dev; direct public response checks and user browser acceptance remain open. The user should refresh dashboard and start a new Search; existing sessions are not rewritten.


## Follow-up qualification parser hardening — 2026-11-16
- Private PR #158 merged as `8e42eb742f739128d45f0184accedfa4d823efe9`. It splits comma-separated qualification clauses after checking genuine Bachelor-or-Master alternatives across the complete line, so an optional Bachelor's mention cannot cancel a mandatory Master's requirement.
- Exact candidate regression [43868423081](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43868423081) passed 468 tests with 0 failures/errors/skips, plus all frontend, Worker, Bridge, RPC, retrieval, packaging and cleanup checks. Public runner smoke [43868423083](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43868423083) passed.
- This is private Python source only; no additional Cloudflare deployment was required. Next production scan and extension assessment workflows check out private `main` and will use the updated qualification parser.


## Senior-scope exclusion follow-up — 2026-11-16
- Private PR #159 merged as `29935bfac576c91da1f4c5867465e83f2ff74ffa`. The shared seniority gate now checks both excluded title terms and clear senior responsibilities (5+ years, management/direct reports, budget or strategic ownership), with junior/entry-level exceptions.
- Exact candidate regression [43869306927](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43869306927) passed 468 Python tests with 0 failures/errors/skips plus all frontend, Worker, Bridge, RPC, retrieval, packaging and cleanup checks. Public runner smoke [43869306925](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43869306925) passed.
- No Cloudflare deployment required for PR #159 because it changes only private Python scanner/assessment logic. No production scan or publication was dispatched. The next scan/extension assessment uses private `main` automatically.


## Private candidate validation for Arbeitsagentur API harvester — 2026-11-16
- Private candidate branch: `happytiswis-sudo/engineering-career-radar:feat/arbeitsagentur-api-harvester-score-filter`.
- Candidate adds native-module API adapter `extension/arbeitsagentur-api.mjs`, unit tests `tests/arbeitsagentur_api.test.js`, API-first role capture/automatic role advancement in extension background, host permission for public BA API, and extension version 0.1.13. Dashboard adds a minimum CV score filter for the currently loaded page.
- Runner regression workflow must explicitly checkout this private branch, run `node --check extension/arbeitsagentur-api.mjs`, and execute `node --test tests/arbeitsagentur_api.test.js` in addition to existing private suite and package checks. Add commit-message routing tag `[arbeitsagentur-api-harvester]` so a runner workflow update triggers the exact candidate.
- No production deployment or live search has been initiated. Do not merge candidate until full suite and adapter tests pass.


## Private candidate validation dispatch — 2026-11-16
- Candidate branch: `feat/arbeitsagentur-api-harvester-score-filter` in the private source repository.
- Validation is non-publishing. `private-scanner-regression.yml` checks out the candidate read-only, merges current private `main` in the ephemeral runner workspace, runs the full private Python suite, frontend/Worker/extension contracts, API adapter Node unit tests, public retrieval regression, and packages the extension as an artifact. It does not deploy, scan, or publish.
- The workflow's push selector already maps commit message marker `[arbeitsagentur-api-harvester]` to this candidate branch. A comment-only workflow commit is being used to trigger the validation; it does not change execution logic.
- Previous candidate attempt `43879487199` passed 468 private Python tests but failed the embedded frontend contract because `public/index.html` did not yet mirror `public/frontend-v3.js`. That synchronization is now included; the new run must prove all gates.
- Current runner credential boundary unchanged; no production credentials are read or changed. Publication remains disabled.


## Candidate regression retry — 2026-11-16
- First retry run `43880257856` again passed the private Python suite (468 tests) but stopped at the frontend embedded-source equality assertion: the inline production script lacked exactly one final newline compared with `public/frontend-v3.js`.
- Private candidate fixed `public/index.html` to match the standalone frontend source byte-for-byte. Re-trigger full private regression with marker `[arbeitsagentur-api-harvester]`; runner workflow logic is unchanged and remains non-publishing.

## Production scan 43918807407 — Supabase accepted, Hugging Face quota exhausted (2026-11-16)
- Run [43918807407](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43918807407) completed with failure only at the private Hugging Face Space upload. Retrieval and all 468 private Python tests passed; scan runtime was ~4m21s.
- Verified aggregate artifact `14254760366` / `career-radar-source-yield.zip`: 27,288 raw URLs; 24,771 unique canonical URLs; 24,771 usable postings; 25,465 posting identities; 35/35 catalogue tracks allocated; 23 tracks returned vacancies; 280 planned / 210 attempted / 210 successful / 0 failed / 70 skipped queries; 13,111 collected; 617 shortlisted; 37 AI-assessed.
- Supabase verified run `43918807407`: 617 scan_jobs rows, 17 source_metrics rows, 13,111 collected, 617 shortlisted, 35 catalogue tracks, 23 retrieval tracks; AI queue 50, AI assessed 37. Supabase is authoritative results storage.
- Hugging Face upload failed with HTTP 403: Space storage limit reached (maximum 1 GB). Remote Space contains numerous historical run archives, including multiple 16 MB LFS files. Do not delete historical records to make a new upload fit. Space mirror is secondary.
- Found a duplicate tracks_with_results key in publish_supabase_jobs.py: shortlist-track count (18) overwrote retrieval-track count (23). Private PR #161 merged as c1f0be6ad73b2a3738d012e881b5bba1cc2c3e5d; it preserves 23 retrieval tracks and separately records 18 shortlisted tracks. Existing Supabase run was corrected from the verified aggregate artifact; scan_runs.tracks_with_results=23 and diagnostics.shortlisted_tracks_with_results=18.
- Public runner PR #25 merged as 780077d1d1c6d2ac91f5bdbbf326707820ed66d8: Supabase-first persistence remains blocking/verified; HF Space mirror upload is now best-effort with an explicit Actions warning if unavailable. Public runner smoke and workflow validation passed after updating the legacy expectation.
- Next verification: exact-main private regression must run after PR #161 merge. Then a new production scan can confirm the workflow reports success with a warning if the HF Space remains full. Do not claim the Space mirror refreshed; do not enable public publishing or R2 writes.
- Browser extension v0.1.14 remains under user manual testing. Real BA API search/detail, ingestion acknowledgement and role progression are still not browser-accepted.

## Final verification after scan quota/telemetry fixes — 2026-11-16 18:27 UTC
- Private source main is `02e51f04ef30daff1e8a8dd44962f6dd28f052fe`. Exact-main non-publishing regression [43928983943](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43928983943) SUCCESS: **469 Python tests, 0 failures/errors/skips**, frontend syntax/contracts, Extension Bridge/restricted RPC/Worker syntax, public retrieval regression, extension ZIP packaging/upload, and private checkout cleanup all passed.
- Public runner smoke [43928984304](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43928984304) SUCCESS. Runner workflow-validation and smoke for PR #25 also passed; PR #25 merged as `780077d1d1c6d2ac91f5bdbbf326707820ed66d8`.
- Exact-main extension artifact ID `14257881797`. Nested ZIP manifest verified as MV3 version 0.1.14; install ZIP SHA-256 `0ac9622c0b4c161b58368b0f7590c29713d78e436d880731fe4db62bcd30efff`. The telemetry publisher/test changes do not change extension runtime code; existing v0.1.14 installation remains current.
- Private scan `43918807407` Supabase persistence was directly verified: 617 shortlist rows, 17 source metric rows; retrieval artifact verifies 23 tracks with results. The Space upload failed only because the private Hugging Face Space reached 1 GB. Public runner now treats this mirror as best-effort after Supabase verification and emits a warning rather than failing the scan.
- Credential preflight for run `43918807407` proved HF_TOKEN, HF_SPACE_ID, SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY were present (values remain secret). The HF quota, not credentials, blocked the mirror update.
- Next operational gate: dispatch a fresh private-results scan on current runner main with private results/telemetry enabled and public publishing/private R2 archive disabled. Verify overall run success plus explicit HF warning, Supabase rows and dashboard result visibility. Do not claim the Hugging Face mirror is refreshed until a later successful upload.
- Browser acceptance remains user-owned: Chrome v0.1.14 is under test; verify BA live search/detail, successful ingestion acknowledgement, role progression and minimum-score filter. Stop on provider access denial, rate limiting or challenge pages.

## Storage Guardian provider preflight — validated on exact main (2026-11-16 18:40 UTC)
- Runner PR #26 merged as `babee176515cb3b7a384912b3ad6a93bf103133e`. Storage preflight runs before Supabase telemetry/results and HF Space writes; it checks only the providers selected by the dispatch inputs.
- Exact private source main tested: `5b88764c7847b1501de6912b7648732a01f43f96`. Regression [43931218981](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43931218981) PASS: 476 tests, zero failures/errors/skips; frontend, Bridge/RPC/Worker, retrieval, packaging and cleanup PASS. Public smoke [43931218952](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43931218952) PASS.
- Supabase storage usage RPC migration applied and verified: DB 77,960,883 bytes, Storage 0 bytes / 0 objects; service_role-only execution. Free-plan quotas: 500 MiB DB/project, 1 GiB Storage.
- HF preflight inventories unique LFS objects across all reachable Space refs and projected new content, with 20% reserved headroom and fail-closed behavior. Live Actions execution with HF credentials is still pending.
- R2 still uses only the manual `R2_FREE_TIER_GUARD_VERIFIED` switch; no live account-wide usage/operation adapter yet. GitHub artifacts and ephemeral runner disk/cache also outstanding. Do not describe Storage Guardian as fully universal yet.
- Next: user must manually dispatch `production-scan.yml` with private results and/or telemetry enabled, public publishing false, private archive false. Verify Supabase admission report and HF LFS inventory result before considering the adapters production-validated.


## Extension ingestion 413 and provider-isolated Storage Guardian recovery — 2026-11-16 19:14 UTC
- User screenshot showed extension session d03ea349 paused at role 263/782 with ingestion-error, 577 extracted, 284 saved, 293 duplicates, 95 pending, and "Discovery batch exceeds 180KB". Read-only Supabase verification confirms run d03ea349-99fe-4b64-ba5b-1ec7ffeba6c6 remains paused with 284 server-side discoveries; the 95 unsynced records remain in browser-local chrome.storage.local.pendingDiscoveries and were not modified by this work.
- Root cause: extension sent 50 discoveries without measuring serialized UTF-8 request size; Worker rejects bodies above 180,000 bytes. PR #165 merged as e68163e2b9a426a4224fe1ddd2f8f311da7a7151. Extension v0.1.15 now builds batches <=150,000 bytes (175,000 single-item ceiling), adapts downward after 413, preserves pending items until server acknowledgement, and resumes the same role through API-first harvesting after an ingestion-error queue is successfully retried. No new run or destructive local reset is created.
- Exact-main private regression [43936935083](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43936935083) PASS on private source SHA c0ebbd26fa89d76f758fb2d97a2654fdbb6cf4e2: 479 Python tests, 0 failures/errors/skips; frontend contracts, extension/Bridge/RPC/Worker syntax, retrieval tests, extension packaging and cleanup all PASS. Public runner smoke [43936934988](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43936934988) PASS.
- Extension workflow artifact ID 14260885916; nested install ZIP SHA-256 de82a0cd344e2c59d3ad6fa43a153d28d29aa15185b61a7f358dd373b13887b1. User-facing verified ZIP: /mnt/data/career-radar-chrome-extension-v0.1.15-install.zip. Manifest MV3 v0.1.15 and all extension JS modules passed node --check.
- Storage PR #166 merged as f1547e72e499f8958b0158c2aa97f02edbe362d2; a follow-up main correction 828929d8e31fb8209706809ef800cfaf17c0b63c fixed Git blob hash headers and GITHUB_OUTPUT newline delimiters. Runner PR #27 merged as f8977e73a073110a10335a482734c392479a894a. Workflow now performs blocking Supabase-only admission before DB writes, then an HF-only capacity check immediately before mirror upload. Unknown/full HF status skips only mirror upload and warns; Supabase persistence can continue. HF inventory uses non-bare no-checkout clone, Git pack accounting and unique LFS object sizes, 1,000,000,000-byte quota with 20% reserve.
- Previous production scan [43932076168](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43932076168) failed at the combined guard because HF returned blocked_unknown_usage. Direct Supabase read-back confirms the scan nevertheless persisted 590 shortlisted job rows and 17 source metric rows for run 43932076168; scan summary had 12,384 collected and 590 shortlisted. It did not refresh HF. The revised workflow has not yet been live-dispatched with Actions secrets; live HF adapter verification remains pending.
- Next manual browser acceptance: install/update v0.1.15 by extracting ZIP, open chrome://extensions, Reload/Load unpacked from the extracted extension folder; return to Career Radar and click Retry pending saves (95). Verify pending count reaches zero, server saved count increases and role 263 resumes automatically. If it remains paused after all saves are confirmed, click Resume. Do not clear extension storage or delete the run.
- Next workflow acceptance: user manually dispatches production-scan.yml with private results/telemetry enabled, public publishing false and private R2 archive false. Confirm Supabase preflight allowed, HF preflight produces a measured report or safe skip, and workflow succeeds with a mirror warning if necessary.
- R2 account-wide usage/operation adapter, GitHub artifact usage and runner disk/cache adapters remain outstanding. Do not claim universal all-provider storage coverage.


## Production scan #22 and Hugging Face storage API correction — 2026-11-16 19:55 UTC
- User-provided screenshots/logs show runner workflow_dispatch #22 / GitHub Actions run [43939586446](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43939586446) completed SUCCESS in 6m24s. Summary: 26,834 raw URLs; 24,318 unique canonical URLs; 24,318 usable postings; 25,012 posting identities; 23,722 newly discovered; 35/35 tracks allocated; 17 track/source families with retrieval results; 280 planned / 210 attempted / 210 succeeded / 0 failed; 12,678 collected; 597 shortlisted.
- Log confirms private Supabase telemetry receipt and finalization: run 43939586446, 12,678 collected, 597 shortlisted, 17 source metric rows. Supabase Storage Guardian passed at 15.42% projected DB use and 0% Storage use; no public publishing and no private R2 archive writes. This is a successful scan and persisted results.
- Hugging Face mirror still skipped: HF-only Storage Guardian step returned blocked_unknown_usage. Earlier code used Git clone plus git-lfs inventory and did not print safe measurement failure reason. This is a mirror-only degradation, not a scan failure.
- HF connector independently confirms private Space Sidmed/engineering-career-radar exists and is private (hf_fs stat/owner listing); connector identity can see it. This does not prove GitHub Actions secret token can read it.
- PR #167 merged as 391a5362575b6f74abd04545e2bc87b569972222. storage_preflight.py now queries authenticated Hub API /api/spaces/{space}?expand[]=usedStorage, reads usedStorage, adds conservative allowlisted incoming upload bytes, and emits sanitized reason codes for 401/403/404/network/invalid metadata. This removes the runner's Git-LFS dependency. It fails closed when usedStorage is missing/invalid and does not delete any Space data.
- Fixed the Supabase output delimiter to write a real newline in GITHUB_OUTPUT (commit c143f979e6111dd54ce967018f4420594a55b63d). Exact-main private regression [43944024227](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43944024227) PASS on candidate SHA c143f979e6111dd54ce967018f4420594a55b63d: 482 Python tests, zero failures/errors/skips; frontend, extension, Bridge/RPC/Worker, retrieval and package checks passed.
- Runner regression now maps [hf-space-storage-api] to the source candidate branch; [extension-release-final] validates current source main. The temporary CI selection marker was committed to runner README. A first racing run before mapping was updated failed while selecting the default branch; the correctly mapped candidate run passed.
- Remaining live gate: manually dispatch production-scan.yml with private results=true, private telemetry=true, public publishing=false, private archive=false. Confirm the HF guard prints a measured usage result and either allows upload or gives an actionable sanitized reason. If API returns 401/403/404, correct the GitHub Actions HF_TOKEN permission/space access; do not weaken the guard. Then verify private Space read-back and publication. Universal storage coverage remains incomplete for R2 account-wide usage/operations, GitHub artifact usage and runner disk/cache.


## Production scan #23 — HF storage root cause established — 2026-11-16
- User supplied screenshots of workflow_dispatch #23. GitHub run [43944744072](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43944744072) completed SUCCESS in 5m47s, runner SHA 016e72a919b3419e3405817c87b29f543f29b781.
- Summary: raw URLs 27,289; unique canonical URLs 24,775; usable postings 24,775; posting identities 25,469; newly discovered 24,103; 35/35 tracks allocated; 280 planned / 210 attempted / 210 succeeded / 0 failed; 13,147 collected; 610 shortlisted. Private telemetry and shortlist persistence steps succeeded.
- Crucial: the new authenticated Hugging Face Hub storage measurement worked. Log reports Space used_bytes=999,931,761 of quota 1,000,000,000 (99.99%); incoming allowlisted mirror payload=10,847,824 bytes; projected usage=1,010,779,585 bytes; 80% stop threshold=800,000,000. Admission was explicitly blocked_capacity_guard, not unknown usage and not an auth failure. This conclusively explains the skipped mirror upload: target Space is effectively full.
- No Space history or existing data was deleted. Do not bypass the guard or automatically delete old history. To restore mirror updates, either increase the actual Space storage allowance/plan if available, or establish an explicitly approved retention/compaction policy and prove the retained history is recoverable before deleting anything. Supabase remains authoritative and current scan persisted there.
- User-facing workflow warning remains generic even though the actual guard result is blocked_capacity_guard; improve warning output to surface sanitized reason and measured usage in a later small PR, without leaking tokens or private record contents.
- End-to-end status: scan and Supabase persistence PASS; HF usage measurement PASS; HF upload correctly BLOCKED by capacity; private Space refresh NOT PASS. Next step is user decision on quota increase versus retention/compaction policy. Do not request another scan solely to test the same guard until capacity is resolved.

## Hugging Face quota plan investigation — 2026-11-16
- User explicitly instructed: do not delete anything; first establish whether the Space storage allowance can be increased.
- Connected Hugging Face identity verified read-only: Sidmed personal account, is_pro=false, no org memberships. OAuth scopes include read-repos but no billing/payment scope. No billing settings, payment method, or invoice data were accessed; no purchase or settings change was made.
- Current official Hub Storage Limits documentation says Free accounts have 100GB private repository storage; PRO has 1TB private repository storage. Current PRO page advertises $9/month. Billing docs say PRO subscription is purchased by credit card and renews automatically; user must explicitly approve and complete any purchase. Public storage add-ons are not applicable to this private Space.
- Important correction to earlier diagnosis: source storage_preflight.py sets HF_SPACE_DEFAULT_QUOTA = 1_000_000_000 bytes as a project hard-coded conservative decimal-GB interpretation of the observed limit. This is NOT the documented Hugging Face Free private repository quota. HF API usedStorage is documented as the size of that individual Space on the Hub, not the account-wide storage quota. The run's 999,931,761 bytes is therefore the Space repo size; it does not prove the entire account is at 99.99% of its provider allowance.
- The Space is private and static; its repo is Git-backed. Current Spaces disk docs say runtime disk is ephemeral and recommend Storage Buckets for persistent runtime data. The old request_space_storage persistent Space disk tiers are deprecated; do not use the old storage tier operation. PRO raises private repo storage quota, not a dedicated per-Space persistent runtime disk.
- hf_fs inventory found Sidmed owns private Spaces engineering-career-radar, n8n, executive-auditor, clawdbot, and private dataset executive-auditor-storage, plus public Space Ollama; no models listed. Account-wide used storage was NOT independently measured. Official HF API docs state list_user_repos() returns all repos with per-repo storage bytes; the runner token has read-repos scope, so next implementation should measure aggregate private repo usage across all owned repo types, then compare against documented 100GB Free private quota (or 1TB for PRO) and keep the existing 80% safety reserve.
- Therefore: increasing storage is possible by upgrading personal account to PRO ($9/month, 1TB private storage), but no upgrade is currently justified. The immediate block is caused by our incorrect 1GB internal cap, not a verified Hugging Face account quota. Do not buy PRO or change the guard to 100GB based only on this one-repo measurement; first implement and test account-wide usage aggregation, and ensure usage measurement fails closed.
- No files, refs, repo history, Space settings, billing settings, or data were modified. No deletion or retention policy was designed or applied.

## Account-wide Hugging Face Free quota implementation — 2026-11-16
- User requirement: keep the entire dashboard and Chrome extension fully usable on Free; no PRO purchase, no automatic deletion, no history rewrite. User explicitly requested account-wide repository measurement, actual Free quota comparison, 20% reserve, fail-closed incomplete measurement, and zero deletion.
- Hugging Face docs confirm list_user_repos() enumerates all models, datasets, Spaces and buckets and returns per-repository storage; endpoint is /api/settings/repositories. Free private repository allowance is 100 GB. Public storage is best-effort and is reported separately; only aggregate private storage is compared against the 100 GB private quota.
- PR #168 opened: https://github.com/happytiswis-sudo/engineering-career-radar/pull/168. Branch fix/hf-account-wide-storage-quota. Candidate head currently 1adc532f428ea962f35dd253ff4e71607293c2ec (storage adapter, unit tests, account-wide metrics). The old hard-coded 1 GB per-Space assumption has been replaced with a fixed decimal 100,000,000,000-byte Free private quota; the 80% stop remains. Public and private totals/counts are reported separately. Inventory validation fails closed for malformed/empty inventory, missing target Space, foreign namespace, duplicates, invalid visibility/type/storage. No cleanup code is invoked.
- Runner private regression workflow was updated with marker [hf-account-storage-quota] mapping to candidate branch, and runner README was corrected to remove the obsolete claim that HF quota is 1 GiB. Push trigger commits: 4eaa23f471db6668421594583208a00bdb9a496a and 67162557038c828a4687baff25f4e062c191cb18. The available connector cannot list push-triggered workflow runs; do not claim test PASS until run is observed.
- Need confirm the real authenticated endpoint response shape and actual aggregate usage in CI. If API response lacks complete storage metadata, inventory is rejected and HF mirror remains blocked. Do not relax schema checks to make it pass. No Space upload or production scan triggered by this change.
- User's screenshot of active extension run 0cd5275b: role 291/782; 9,045 listings seen; 3,884 saved; 5,161 duplicates skipped; 0/25 full-advert details in the current search; history says 3,919 saved and session running. Do not interrupt the active scan. Extension pause paths in current source include API 401/403/429, access challenge, unconfirmed ingestion, and full-detail save failure. User reported one unexplained pause that resumed successfully. After scan completes, inspect captured pause/error state and evaluate results against the Master CV and role requirements before changing matching strictness.

## Free-only Hugging Face account storage — implementation candidate refreshed 2026-11-16
- User requirement remains absolute: dashboard and extension must work fully on Free; no PRO purchase; no deletion, cleanup, retention pruning or history rewrite without separate explicit approval.
- PR #168 was closed without merge because main handover commits advanced after branch creation. Replacement PR #169 is open and based directly on current main: https://github.com/happytiswis-sudo/engineering-career-radar/pull/169; branch fix/hf-account-wide-storage-quota-v2; head b68f7a9c604a9e615c224d7d8f382c3e120afef1; base main 155384e5b43828699a898d03334308e971c9a420; compare ahead 2 / behind 0.
- Candidate changes storage_preflight.py and tests/test_storage_preflight.py only. It queries documented /api/settings/repositories inventory, validates every record, aggregates private bytes across all repo types, separately reports public bytes, verifies target Space exists and is private, applies fixed decimal 100,000,000,000-byte Free private quota, and keeps 80% stop threshold. No environment override can increase the Free quota. Missing/incomplete inventory blocks HF mirror upload.
- Runner workflow marker [hf-account-storage-quota] now selects branch fix/hf-account-wide-storage-quota-v2. Runner workflow update commit d3f09406ee57a18b314c6d582fddef57f38b832c and README trigger commit 5b3159eeaa8289fea54dd21f7c5a9de6fbaa2bc3. Combined commit statuses currently show no checks; the connector lacks a list-push-workflow-runs action. Do not claim CI passed. Need obtain workflow run status/logs from GitHub Actions UI/API before merge.
- Public docs evidence: Hugging Face list_user_repos() includes models, datasets, Spaces and buckets with per-repo storage; Free private quota is 100 GB. Public storage is best-effort and reported separately. This inventory adapter has unit tests but the real authenticated JSON schema/aggregate has not yet been verified in CI. Fail closed if API shape differs.
- User screenshot active extension run 0cd5275b: role 291/782, 9,045 listings seen, 3,884 saved, 5,161 duplicates skipped, 0/25 detail captures in current search, history 3,919 saved, session running. Do not interrupt. User reported one unexplained pause that resumed normally. Extension code pause paths include API auth/rate limit, access challenge, unconfirmed ingestion, and full-detail save failure; investigate recorded error after completion.
- After scan completes, perform a quality audit on retrieved jobs against the user's actual target roles, location/seniority constraints and Master CV; quantify irrelevant/senior mismatches and missed suitable roles before tightening match thresholds. Keep retrieval broad and CV assessment separate.

## Hugging Face Free-tier account storage candidate — 2026-11-16
- User explicitly requires no PRO purchase and full functionality on Free; no automatic deletion or historical rewrite.
- Source PR #170 is open: https://github.com/happytiswis-sudo/engineering-career-radar/pull/170. Branch fix/hf-account-wide-storage-quota-v3, latest head after handover docs 1239d429b34f420e749303cba57a85cbb8c982f4, based on main with no behind commits.
- Runner workflow marker [hf-account-storage-quota] maps to the v3 source branch. Latest push trigger is README commit 6ab328f50973519c32fc964b9ff583bc2a35d69a. The workflow uses private-scanner-regression.yml and runs the full private Python suite, frontend/Worker/extension contracts and package build. The GitHub connector cannot enumerate push-triggered runs and combined statuses are empty, so do not report CI PASS without checking Actions run details.
- Actual /api/settings/repositories account inventory remains to be verified in a credentialed workflow. The candidate fails closed if the response schema is incomplete. Do not run a production scan or upload until validation is complete. No Space data or history changed.
- User's active extension scan 0cd5275b was shown at role 291/782, 9,045 seen, 3,884 saved, 5,161 duplicates skipped, 0/25 full details; history reports 3,919 saved. Do not interrupt; inspect post-run quality and pause reason after completion.

## Read-only Hugging Face account storage audit workflow — 2026-11-16
- Added runner workflow `.github/workflows/hf-storage-audit.yml` in runner repo; commit 3d0b78a28e263bd853b4c2a3b892df299dc0a883. Push path trigger should run automatically; workflow_dispatch is also enabled.
- Workflow uses existing HF_TOKEN secret and GET /api/settings/repositories only. It validates every record, sums private/public/combined storage, verifies the private target Space, reports private usage against fixed 100 GB Free quota and 80% stop threshold, and writes only aggregate metrics to job summary. It performs no writes/deletions and never prints repository names or token.
- The available GitHub connector cannot enumerate push-triggered workflow runs and combined status is empty. Audit result/actual account total remains pending; obtain the Actions run output before claiming measurement complete.

## Production persistence and account-wide Hugging Face admission — 2026-11-16 22:10 UTC
- Production scan #24 / run [43964037664](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43964037664) succeeded as a retrieval run (24,362 raw URLs; 22,503 unique canonical and usable postings; 35/35 career tracks; 10,861 collected; 58 shortlisted). However, its dispatch had both `enable_private_telemetry=false` and `enable_private_results=false`; the Supabase guard, both Supabase persistence steps, the HF guardian and mirror upload were skipped. Its aggregate artifact is not a replacement for the private job rows. No run #43964037664 row exists in `career_radar_private.scan_runs`.
- Direct read-only Supabase reconciliation confirms prior run [43944744072](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43944744072): 13,147 collected, 610 shortlisted, 610 `scan_jobs` rows and 17 `source_metrics` rows. This is a verified persisted run. The latest Hugging Face Space mirror still contains run 42421164429 (2026-11-07); no newer scan was mirrored.
- Account-wide read-only Hugging Face audit [43962870506](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43962870506) passed using official SDK 1.26.0: 6 personal resources reconciled (1 dataset, 5 Spaces; 0 models; 0 buckets), private usage 999,931,761 / 100,000,000,000 bytes (0.9999%), public usage 0, 80% stop threshold 80,000,000,000 bytes, remaining headroom to stop 79,000,068,239 bytes. Current account usage is below stop; this does not itself publish a scan.
- Runner PR #28 merged workflow changes: manual dispatch defaults now enable aggregate Supabase telemetry and shortlisted-job persistence; production publishing remains false and dual-gated. A real Supabase service-role/usage-RPC/80%-admission preflight now runs before scanning when persistence is enabled. The Hugging Face warning now distinguishes a skipped check from a failed/denied requested check and reports actual sanitized decision fields.
- Runner PR #32 moved the account-wide HF guardian before BOTH production Space writers (`publish_history.py` and the dashboard mirror); both require `hf_write_admitted == true`. Runner PR #33 applied the same account-wide fail-closed guard to the separate allowlisted UI-sync workflow. No HF writer in these two workflows may proceed on unknown/incomplete measurements. No data deletion or cleanup is implemented.
- Validation: runner full exact-main regression [43967320881](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43967320881) passed on private source SHA `6d02d44c9c58fa9bd8536a500bf67c6e244fdda7`: 488 Python tests, 0 failures/errors/skips; frontend contracts, extension/Bridge/RPC/Worker checks, retrieval regression, extension package and cleanup all passed. Runner smoke [43967320700](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43967320700) passed. Runner workflow YAML validation [43967126947](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43967126947) passed. Current runner main at this record: `98f6e530ac07641a2ec0e776579927a130938229`.
- Next action: user manually dispatches one production scan with the two private Supabase options left at their new default true values and `enable_production_publish=false). Before scanner start, Supabase credentials and storage admission must pass. After retrieval, Supabase telemetry and shortlist persistence each perform read-back verification. HF account-wide guard then runs before any HF write; only if admitted will history and mirror writes occur, followed by remote `jobs.json` run-ID and `search-history.json` publication read-back. No new scan was launched as part of this workflow repair because the previous #24 output was not retained as full job records.

## Hugging Face per-Space 1 GB repository cap and production run #43967894248 — 2026-11-16 22:36 UTC
- Final run [43967894248](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43967894248) succeeded. Direct Supabase SQL read-back: `career_radar_private.scan_runs` contains run 43967894248, collected_jobs=10,891, shortlisted_jobs=59, telemetry verified=true; 59 `scan_jobs` rows and 14 `source_metrics` rows. Publisher log independently confirms finalized/read-back verified scan. Supabase is authoritative for this run.
- Retrieval summary: 24,308 raw URLs; 22,529 globally unique canonical URLs and usable postings; 23,223 posting identities; 22,139 newly discovered; career tracks 35/35; 280/210/209/1 queries planned/attempted/succeeded/failed; 10,891 collected and 59 shortlisted.
- Actual HF account guard admitted: 999,931,761 private bytes plus 2,490,304 allowlisted incoming bytes, projected 1,002,422,065 / 100,000,000,000, below account 80% stop of 80,000,000,000. Actual `upload_folder` was rejected with HTTP 403 `Storage limit reached for this space (Max: 1 GB)`. This is a distinct per-Git-backed-Space repo cap, not the 100 GB account quota. No Space files/history were deleted.
- Merged private PR #171 (`8ad1c0250eb8378f1dfd635c2f84420b9fc92fa6`): `storage_preflight.py` now measures the target Space `used_storage` separately and checks a 1,000,000,000-byte repository cap with conservative 95% stop and allowlisted incoming bytes. Existing account-wide 80% check remains; either decision blocks all HF writers. Python preflight now prints plain WARNING text rather than `::warning::` workflow commands, so mocked unit tests no longer create misleading GitHub annotations.
- Merged runner PR #35 (`fa0c1e844ef4a3ef2ecd5e6c720d1f906a562db1`): production and UI-sync warning steps select the actually blocked HF report row (account-wide vs target Space), and show measured/incoming/projected/quota/stop values accurately.
- Runner full private-main regression [43971543284](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43971543284) passed on exact private candidate/base SHA `8ad1c0250eb8378f1dfd635c2f84420b9fc92fa6`: 490 Python tests, 0 failures, 0 errors, 0 skips; frontend contracts, extension Bridge/RPC/Worker tests, public retrieval regression, extension packaging and cleanup all passed. Runner workflow validation [43971311246](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43971311246) and smoke [43971310998](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/43971310998) passed.
- One earlier push regression [43971342565] selected legacy `feat/chrome-extension-backend-v1` and hit unexpected conflicts against current main before tests. It is superseded by exact-main validation 43971543284; no conflict resolutions or private source mutations were made in that failed run.
- Important: this does NOT make the 1 GB Space repo able to accept more writes. It prevents wasting future attempts and accurately blocks publication at 95% target-repo threshold. Space mirror remains stale; do not delete or rewrite historical Space data. Supabase is the primary store. A separate, explicit architecture decision is required to relocate long-lived scan history/results to Supabase/R2 or another repository before Space publication can resume.
- No further production scan or deployment was run. Do not launch another scan merely to validate the guard: Supabase run #43967894248 is already fully verified. A future scan should remain Supabase-persisted and its HF write should be blocked by the new target-Space check until storage architecture/retention is explicitly approved.
## R2 archive destination selected and live account usage measured — 2026-11-17
- User selected existing Cloudflare R2 as the primary historical archive destination; Google Drive is optional later, not part of the scanner dependency.
- Existing private bucket `engineering-career-radar-archives` in WEUR, Standard class, is already provisioned. Cloudflare Bridge `career-radar-bridge` currently has an `ARCHIVES` R2 binding to that exact bucket (read-only settings verified).
- Live R2 bucket inventory: 3 objects, 11,218,146 payload bytes (11.22 MB decimal), metadata 363 bytes. Keys are three `career-radar/history/run-*.json` archives. No R2 writes/deletes were performed during this measurement.
- Cloudflare GraphQL R2 metrics for 2026-10-18 through 2026-11-17 show 30-day operations: ListObjects 27, PutObject 3, PutBucket 1, HeadObject 6, GetObject 3, GetBucketCors 1, GetBucketLifecycleConfiguration 1, HeadBucket 56. Class A observed 31 (ListObjects + PutObject + PutBucket); Class B observed 67 (HeadObject/GetObject/GetBucket*). These are far below published Standard free allowances (1,000,000 Class A and 10,000,000 Class B monthly).
- Storage samples over the available period show a peak of 11,218,146 bytes and 3 objects, well below the 10 GB-month free storage allowance. This is a point-in-time/available-period usage view, not a billing invoice or guarantee against charges from other account activity. Keep a safety margin and continue monitoring.
- Existing private workflow `.github/workflows/migrate-archives-to-r2.yml` has dry-run-first validation, upload, inventory listing and SHA-256 read-back, but it lives in private source and is manual-only; standard production runner is the public runner. It migrates indexed history archives and preserves HF originals. It does not prune Space data.
- Public runner production workflow already contains R2 archive upload/read-back via the Bridge, but archive writes are additionally gated by `CAREER_RADAR_R2_FREE_TIER_GUARD_VERIFIED=true`. Earlier handoff says this must remain unset until the R2 free-tier Storage Guardian (GB-month and Class A/B) is independently implemented and verified. Do not flip this gate solely because current measured usage is low.
- No R2 migration or Hugging Face deletion was performed yet. Next: port the existing dry-run migration to public runner (private source read-only checkout, aggregate-only logs, manifest, checksum read-back); validate exact historical index + all Space archive files. Then implement a separate prune phase only after R2 copies and manifest verify, dashboard/history reads are switched or safely fall back to R2, and `seen-jobs.json` semantics remain intact. Delete only eligible historical Space copies, preserve latest archive and dashboard files, and measure actual HF `used_storage` after deletion. Do not rewrite Git/LFS history unless the ordinary delete path fails to reclaim storage and an explicit verified rollback exists.
- Preserve the separate Hugging Face account-wide 80 GB stop threshold. R2 capacity/free-tier controls are separate; unknown or incomplete R2 usage must block R2 writes. Supabase remains authoritative for applications and structured scan records.
## Space history to R2 migration (2026-11-17)
- Public-runner port is under review in PR #38: https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/38 (PR #37 was closed as superseded). It adds `scripts/migrate_space_history_to_r2.py`, a manual-only workflow defaulting to dry-run, and tests for index/archive integrity and preservation metadata.
- The current private Space inventory has 13 indexed `history/run-<id>.json` archives, matching the 13 published rows in `search-history.json`. The migration validator is intentionally fail-closed for duplicate IDs/paths, missing files, unindexed archive files, filename/index mismatches and embedded run-ID mismatches.
- Manifest design records every archive's run ID/path/size/SHA-256/run URL/published timestamp, the source index checksum, and checksums for retained `search-history.json`, `jobs.json`, `seen-jobs.json`, `index.html`, `frontend-v3.js` and `frontend-v3.css`. No Space files are deleted or modified.
- **Live migration remains blocked:** the Bridge rejects all archive API operations unless `R2_FREE_TIER_GUARD_VERIFIED=true`; keep this gate unset. Do not bypass it. The existing bridge currently permits archive-key PUT/GET only for `history/run-*.json` or `history/legacy-*.json`; the migration manifest is stored under a legacy timestamp key with `artifact_type=migration_manifest` to use the supported route.
- No R2 uploads, Space deletions, storage reclamation, dashboard-history compatibility proof, or production scan were performed by this port. Do not claim tasks complete until a dry-run and live read-back are verified and the dashboard is proven compatible. Preserve the current dashboard snapshot and `seen-jobs.json`.

## Space history migration — runner port merged (2026-11-17)
- Public runner PR #39 merged to `main`: https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/39. Merge commit: `d9568f64b4ad3ae212734f3c9ce1a343ab43b30c`.
- The exact PR head `30cfd5348566f0200b92209378c86607f2fa2877` passed `runner-smoke` (unittest discovery and retrieval intelligence tests) and `runner-workflow-validation` (workflow YAML/safety contracts). The `private-candidate-regression / full-private-suite` check was skipped because this runner-only PR did not modify private source. No full private regression is claimed.
- Migration workflow is `.github/workflows/migrate-space-history-to-r2.yml`, script `scripts/migrate_space_history_to_r2.py`, tests `tests/test_space_history_migration.py`. Workflow is manual-only and defaults to dry-run.
- **Remaining live blocker:** the deployed `career-radar-bridge` Worker rejects archive GET/PUT/list while `R2_FREE_TIER_GUARD_VERIFIED` is not the literal `true`. Current Worker settings read-back shows the variable is not configured; do not set it manually or bypass the guard. R2 account GraphQL read-only check for 2026-10-18 through 2026-11-17: observed 66 Class A and 68 Class B requests across the account; R2 storage sample peak 11,218,146 payload bytes (+363 metadata bytes) in the existing bucket. This confirms low current use, not a dynamic monthly guardian.
- R2 free-tier guardian still needs a verified account-wide GB-month + Class A/B adapter, conservative stop thresholds, and fail-closed behavior. The 13 archive migration remains unrun; no R2 writes or Space deletions. Preserve latest Space dashboard, search-history.json, jobs.json, seen-jobs.json and all 13 history files.


## 2026-11-17 — R2 guardian and dashboard history follow-up (not implemented)
- User explicitly authorized work on (1) a real R2 free-tier guardian and fail-closed verification and (2) dashboard history retrieval from R2 while preserving the latest dashboard snapshot and `seen-jobs.json`.
- Reconfirmed current deployed Bridge `career-radar-bridge`: `ARCHIVES` is bound to `engineering-career-radar-archives`; `ARCHIVE_CI_TOKEN` exists; `R2_FREE_TIER_GUARD_VERIFIED` is absent. Current R2 metrics are 3 standard objects / 11,218,146 payload bytes and 363 metadata bytes. These are observations, not a dynamic admission control.
- Inspected deployed Bridge archive routes: `/archives` list/PUT and `/archives/history/...` GET all require `X-Archive-CI-Token` and are globally blocked unless the static Worker variable is literal `true`. This is not dashboard-compatible authorization and must not be enabled manually.
- Public runner migration currently uploads the 13 indexed archives and a manifest, but requires all six `PRESERVE_FILES` to exist and only records their checksums; it does not upload the latest `jobs.json` snapshot or `seen-jobs.json` as durable R2 objects.
- The Space inventory still has 13 history archives, `search-history.json`, `jobs.json`, `seen-jobs.json`, `index.html`, `frontend-v3.js`, and `frontend-v3.css`. No migration or destructive action was run.
- Implementation remains blocked pending a safe account-wide usage data source usable by the Bridge/CI guardian (storage GB-month plus Class A/B operation consumption and conservative projected usage), and source-level dashboard Worker/frontend paths/contracts for authenticated history fallback. Do not substitute the static boolean for this guardian. Do not prune Space objects or enable R2 writes until the guardian is independently tested and the dashboard can retrieve the same run detail from R2.
- Next agent: inspect current Bridge source and dashboard Worker/frontend source in private main; design guardian with fail-closed behavior for missing/stale/incomplete metrics, explicit headroom thresholds and no credential leakage; expose dashboard-only authenticated GET history endpoints separately from CI archive writes; make migration upload latest snapshot + seen registry + manifest and verify read-back; add regression tests; update both handoffs and decision log. Preserve Supabase as structured scan/application authority and retain Space as fallback until end-to-end history parity is proven.


## 2026-11-17 — Dynamic R2 guardian and dashboard history migration (PR candidate)
- Added account-wide R2 guardian script `scripts/r2_free_tier_guard.py`, unit tests and hourly/manual workflow. It queries account-wide GraphQL operation and storage groups plus the account-level R2 metrics endpoint. Operation usage is measured over a current UTC calendar month; storage uses a conservative sum of each bucket's maximum payload+metadata observed over 31 days. This storage bound upper-bounds GB-month usage; it is not an exact billing calculation.
- Admission thresholds reserve a 30% safety margin: storage upper bound <7 GB, Class A <700,000, Class B <7,000,000. Unknown operations, missing/truncated datasets, stale storage samples, Infrequent Access use, API errors or missing configuration fail closed.
- The report is HMAC-signed with existing `ARCHIVE_CI_TOKEN`, published through the Bridge with both `X-Archive-CI-Token` and `X-Dashboard-Key`, and expires after 90 minutes. Production archive uploads and live migration run fresh preflights; the old static `CAREER_RADAR_R2_FREE_TIER_GUARD_VERIFIED` variable is no longer used.
- Required new GitHub Actions secret: `R2_GUARD_API_TOKEN` with Cloudflare Account Analytics:Read and Workers R2 Storage Read. Keep existing `CLOUDFLARE_API_TOKEN` (Workers Scripts:Edit) unchanged. Existing `CLOUDFLARE_ACCOUNT_ID`, `ARCHIVE_CI_TOKEN` and `DASHBOARD_API_KEY` are required.
- Migration copies indexed history archives, manifest, and exact root snapshots `search-history.json`, `jobs.json`, `seen-jobs.json`; every object is SHA-256/size read-back verified. The Space `jobs.json` is a dashboard metrics snapshot with `run_id`, `generated_at` and `total_shortlisted`, not a jobs array. The seen registry is copied byte-for-byte. No Space files are deleted.
- Private-source regression is invoked by `.github/workflows/r2-guardian-private-regression.yml` against private branch `feat/r2-guardian-dashboard-history` with current private `main` as base. Keep the general extension candidate regression manual on PRs.
- No live guardian report, R2 migration, production deployment or Space cleanup has occurred. Configure the new API token, deploy Bridge/UI, verify guardian admission, run migration dry-run, then explicitly authorize live migration only after checks.


## 2026-11-17 — Post-merge validation corrections
- PR #41 was merged to runner main as `d28fb2034ef2474086c55b39c2c5fa593ec4e3c5`; private source PR #172 was merged as `01a88ad940903c3acded52452f48b8659f631b0f`. Runner deployment successfully deployed dashboard Worker version `41cee52b-97e7-49a4-b2b6-730ede826194` and Bridge Worker version `776c5d79-9450-4ccf-8835-d9611e3762c4` from private main. This was a code deploy only; no archive migration.
- First post-merge private regression failed before tests because it merged the already-merged feature branch with later private-main commits, causing unrelated extension add/add conflicts. The regression caller now targets private `main` directly so the merged candidate can be tested without stale branch conflicts.
- Follow-up hardening: account-level R2 metrics must include every class/state payload, metadata and object-count field or admission fails closed. R2 operation quotas are measured from UTC calendar-month start. New token permissions are exactly `Account Analytics:Read` and `Workers R2 Storage Read`.
- Corrected production workflow: the second guardian preflight runs after the first archive upload succeeds, and the reconciled archive update is gated on that second preflight. Static guard remains removed.
- Current Cloudflare metrics readback: Standard published 3 objects / 11,218,146 payload bytes / 363 metadata bytes; Standard uploaded zero; Infrequent Access zero. GraphQL operations observed 27 ListObjects, 3 GetObject, 3 PutObject, 1 PutBucket, 1 GetBucketCors, 33 ListBuckets, 6 HeadObject, 1 GetBucketLifecycleConfiguration, 56 HeadBucket. Storage dataset returned 492 rows; latest sample 2026-11-16T23:30:00Z. Metrics access and low usage verified; guardian job still needs to pass with dedicated GitHub token and publish signed report.
- No R2 archive migration or Space deletion has occurred.


## 2026-11-17 — Guardian hardening, release validation and migration dry-run retry
- Exact private-source regression on merged private `main` passed 498 tests (0 failures/errors/skips) at SHA `7aad50880b6f51fe9bc632ba02d9cb8b811f8aaa`. Public runner smoke passed 60 tests at runner SHA `16dd8f70e19833509daa7d58fcb085cdd1ca55d5`.
- Private source PR #172 merged as `01a88ad940903c3acded52452f48b8659f631b0f`; runner PR #41 merged as `d28fb2034ef2474086c55b39c2c5fa593ec4e3c5`. Deployment succeeded for dashboard Worker `41cee52b-97e7-49a4-b2b6-730ede826194` and Bridge Worker `776c5d79-9450-4ccf-8835-d9611e3762c4`.
- Guardian now measures operation usage from UTC calendar-month start, validates all required account metric fields, rejects unknown operations, pending multipart uploads, stale samples per bucket and any Infrequent Access storage, and uses conservative current-month per-bucket storage peaks. Thresholds remain 70% of the published Standard free-tier allowances. Token permissions: `Account Analytics:Read` and `Workers R2 Storage Read`.
- Production workflow's first archive write and post-novelty reconciled write each require a separate fresh guardian result. Old static guard variable has been removed. Private regression caller uses merged private `main`; its commit-message selector has a dedicated `[r2-guardian]` path.
- Migration workflow now automatically runs a read-only dry-run when migration code/workflow changes. First run #44104843932 failed before script execution because setup-python pip cache requires a requirements/pyproject file, which this runner repo does not have. Cache was removed. Retry #44104917460 is in progress; inspect and record its final outcome. HF Jobs attempt was unavailable (402 Payment Required), so GitHub Actions is the execution path.
- Cloudflare account metrics verified directly: Standard published 3 objects / 11,218,146 payload bytes / 363 metadata bytes; Standard uploaded zero; Infrequent Access zero. GraphQL current-month account data showed 9 known operation groups and 492 storage rows, latest sample 2026-11-16T23:30:00Z. This does not replace a fresh signed guardian report.
- No live R2 migration, R2 object upload, Space file deletion or storage reclamation has happened. The new secret `R2_GUARD_API_TOKEN` must exist in runner Actions with the exact permissions above before a successful signed guardian report can be confirmed. Do not use generic `R2:Read` wording.


## 2026-11-17 — History migration dry-run PASS
- Read-only migration workflow run #44104917460 completed successfully against the private Space. It validated all 13 indexed history archives, 80,692,241 archive bytes, all 3 required root snapshot objects (`search-history.json`, `jobs.json`, `seen-jobs.json`), and 6 preserved Space files (including the active dashboard assets). The manifest was generated with SHA-256 `61fc3f432b5fde402bb9134f68a5d055bef251f8d90879ba0f9c4c0bb6d577f5` and planned key `history/legacy-20261117143635.json`.
- Result explicitly reported `dry_run: true` and `DRY RUN: no R2 writes; no Space files changed.` This verifies source inventory/schema and migration planning only. It does not verify R2 upload/read-back, guardian admission or dashboard parity against R2.
- The workflow now auto-runs read-only migration validation whenever the migration script or workflow changes; manual `workflow_dispatch` remains dry-run by default. Live mode still requires explicit `dry_run=false` and a fresh signed guardian preflight.
- Runner smoke after migration workflow fix passed. Remaining release gate: confirm scheduled guardian job can access the new `R2_GUARD_API_TOKEN`, publishes a signed admitted report, then explicitly run live migration only after that PASS. Do not delete/rewrite Space files.


## 2026-11-17 — Final Bridge fallback deployment and regression
- Private Bridge fallback update deployed successfully in Cloudflare: dashboard Worker version `a43ab2a7-8544-4eb5-8a89-e9b95e203277`; Bridge Worker version `83274571-894a-45f6-a8eb-0c7da94402f2`. Cloudflare source read-back confirms R2-first / private Space fallback on R2 object absence, invalid JSON, oversized object or read error; static guard flag absent.
- Exact private-main regression passed again: 498 tests, 0 failures/errors/skips, candidate/base SHA `4f59c67381165d4dad47c4f83aa6c2e72bc3db57`. Runner smoke passed after workflow fixes.
- Migration dry-run #44104917460 passed: 13 archives / 80,692,241 bytes; 3 root snapshots; 6 preserved Space files; no R2 writes or Space modifications. Snapshot sizes: search-history 12,590 B, jobs metrics snapshot 379,962 B, seen-jobs registry 1,142,570 B. Existing R2 storage is 11,218,146 payload bytes + 363 metadata bytes; estimated total after copy ~93.45 MB before R2 metadata.
- Remaining: scheduled guardian must confirm `R2_GUARD_API_TOKEN` is configured with Account Analytics:Read + Workers R2 Storage Read and publish a fresh admitted lease. Then live migration must verify every object size/SHA-256. Do not delete Space files.


## 2026-11-17 — Final archived vacancy history release validation
- Pinned exact private source SHA `2cf1f9fc25734c48582214edef35292a0a69df7c` and full private suite passed 499 tests (0 failures/errors/skips). Runner smoke passed 61 tests.
- Final Cloudflare deployment succeeded: dashboard Worker `0137f991-e424-4684-b25c-1c47a3e6a0f7`; Bridge Worker `e2a74ff1-fcb8-4037-92db-c1ec9c03ff37`. Deployed Bridge source read-back verifies 20MB raw JSON history responses, R2-first/Space fallback, month-to-date guardian report schema and removal of static guard.
- The active v3 History panel renders compact archived vacancy `jobs[]` records with safe HTTP(S) links, assessments, skills and 50-row pagination. Archive schema migration checks now require schema_version 1, archive=true, matching run ID and jobs array.
- Read-only migration dry-run #44106227866 passed for all 13 archives (80,692,241 bytes), all 3 root snapshots and all 6 preserved files. It confirmed `dry_run:true`, no R2 writes and no Space modifications. Existing R2 object inventory remains 3 objects. No live migration has happened.
- Remaining: scheduled guardian must confirm `R2_GUARD_API_TOKEN` is configured with `Account Analytics:Read` + `Workers R2 Storage Read`, publish a fresh admitted lease, then live migration and SHA-256 read-back. Never delete Space originals.


## 2026-11-17 — Guardian credential blocker confirmed; fail-closed report active
- Guardian run #44107811690 executed against the deployed Bridge and failed closed because runner Actions secret `R2_GUARD_API_TOKEN` is empty/missing. The log explicitly reports: `R2_GUARD_API_TOKEN is missing; create a dedicated Cloudflare token with Account Analytics:Read and Workers R2 Storage Read`.
- The signed failure report was successfully written to R2 key `career-radar/_guard/latest.json` (about 501 bytes) with `admitted:false`. The Bridge therefore rejects archive list/read/write endpoints until a fresh admitted report replaces it. The private dashboard continues to fall back to the Space for historical reads.
- R2 bucket inventory now contains 4 objects: the 3 pre-existing history archives plus the fail-closed guardian report. No migration archives or snapshots have been uploaded. No Space files were changed or deleted.
- After diagnostic improvements, private regression passed 499 tests and runner smoke passed. Guardian workflow now runs on code changes and hourly at minute 17 UTC. The migration workflow is safe by default on pushes; a live push requires the explicit `[r2-migrate-live]` commit marker and a fresh guardian preflight. Manual dispatch remains dry-run by default.
- Manual blocker: add repository Actions secret `R2_GUARD_API_TOKEN` with only Cloudflare Account Analytics:Read and Workers R2 Storage Read scoped to account `02e8abc1853165520174d6a71b3a8b2d`, then run the `R2 free-tier guardian` workflow. Do not trigger live migration until it reports `admitted:true`.


## 2026-11-17 — R2 guardian credential added; rerun triggered
- User confirmed the repository Actions secret `R2_GUARD_API_TOKEN` is present in `happytiswis-sudo/engineering-career-radar-runner` (GitHub UI showed Last updated: now). Secret value was not exposed or read.
- Triggered the guardian's existing push-path workflow by a comment-only update to `.github/workflows/r2-free-tier-guardian.yml`; trigger commit: `4334ba8ec28e355366aedb76033d2d64ef2a984a`. The workflow's scheduled and manual triggers remain unchanged.
- GitHub combined commit-status query returned no status entries at the time of inspection, so the guardian outcome is still unverified. Next agent must inspect the Actions run for this commit (or the next scheduled guardian run), confirm Cloudflare API access and a freshly signed report with `admitted:true`, and inspect R2 `career-radar/_guard/latest.json` before any migration.
- The prior fail-closed report may remain active until the new run succeeds. No live migration has been triggered; no archive/snapshot objects have been uploaded; no Space files may be deleted. Only proceed with live migration after a verified fresh admission.


## 2026-11-17 — Guardian API failure safely instrumented
- After the user added `R2_GUARD_API_TOKEN`, guardian workflow commit `4334ba8ec28e355366aedb76033d2d64ef2a984a` ran but failed in the Cloudflare usage-query step. GitHub accepted the secret entry, but this does not prove its value, token scope, account scope or the repository account-ID variable is valid.
- Screenshot showed only the generic `Cloudflare API returned an unsuccessful response`; no admission was granted. No migration was triggered.
- Updated `scripts/r2_free_tier_guard.py` to safely surface bounded Cloudflare HTTP/API error codes and messages, while never logging request headers or token values; URL/network failures report only safe exception classes. Change commit `23fcf5c7aef25c4399a2d8aba6476e5ae700ebcf` automatically triggers guardian workflow again.
- Next agent: inspect latest guardian run logs. Use the specific Cloudflare error to determine whether Account Analytics:Read, Workers R2 Storage Read, token account scope, or `CLOUDFLARE_ACCOUNT_ID` repository variable is wrong. Do not guess or request broader permissions until the error confirms the missing permission. Verify the signed report at `career-radar/_guard/latest.json` has a fresh timestamp and `admitted:true` before live migration. Preserve all Space originals; no migration writes have occurred.


## 2026-11-17 — R2 GraphQL response-format defect identified and corrected (PR validation pending)
- The post-diagnostic guardian run on commit `23fcf5c7aef25c4399a2d8aba6476e5ae700ebcf` failed with `Cloudflare returned success=false without structured errors`.
- Root cause: `cloudflare_request()` incorrectly required the REST envelope field `success: true` for the Cloudflare GraphQL Analytics endpoint. Cloudflare GraphQL returns the GraphQL specification shape `{data, errors}`; successful responses commonly have `errors: null` and no `success` field. This was confirmed against the official Cloudflare GraphQL API documentation: https://developers.cloudflare.com/analytics/graphql-api/errors/ and https://developers.cloudflare.com/analytics/graphql-api/getting-started/querying-basics/.
- Candidate fix on branch `fix/r2-graphql-response-format`: add an explicit GraphQL response mode that validates `data` and `errors`, while retaining strict `success: true` validation for the R2 account-metrics REST endpoint. Added regression tests for successful GraphQL response, GraphQL error response and unchanged REST fail-closed behavior.
- No token permission changes are justified by the previous response. Do not broaden or rotate `R2_GUARD_API_TOKEN` unless the corrected run returns a real permission/scope error.
- Current release gate remains closed: obtain passing runner tests, merge the fix, verify the next guardian run publishes a fresh signed report with `admitted:true`, then verify the report in R2. Live migration remains prohibited; preserve all Hugging Face originals.


## 2026-11-17 — R2 guardian GraphQL response fix merged
- Public runner PR #42 merged to `main` as `7691361cafbd30cd82964cd5ea13f5c9e9377a59`. The fix explicitly validates Cloudflare Analytics GraphQL responses as `{data, errors}` and retains strict `success: true` validation for R2 account-metrics REST responses.
- Regression tests cover GraphQL success without a REST `success` field, GraphQL errors, and REST rejection when `success` is false.
- Verified CI on candidate head `3ce190941d6830de810e222dc64ed1ea56ca5220`: public runner smoke run #44191723312 passed 65 tests; workflow validation run #44191722036 passed; private-source full regression run #44191721820 passed and completed private checkout cleanup.
- Initial smoke attempt #44191629464 failed due to a malformed escaped newline in the first candidate commit; corrected on the PR branch and the final 65-test smoke run passed. Do not treat the earlier failed attempt as current status.
- Merge automatically triggers the R2 guardian because the script path changed on main. Inspect the post-merge guardian run. A code fix and green CI are not an admission: only a fresh signed report with `admitted:true`, complete metrics, and successful R2 read-back permits live migration. Keep Space originals and do not migrate/delete anything until then.


## 2026-11-17 — R2 guardian admitted PASS and signed report read-back
- Post-merge guardian run [44191844414](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44191844414) succeeded on code commit `7691361cafbd30cd82964cd5ea13f5c9e9377a59`. Sanitized metrics: `admitted=true`, `metrics_complete=true`, storage upper bound 0.011219 GB, Class A 74, Class B 84, unknown operations 0, one account bucket, `guardian_error=null`.
- Direct Cloudflare R2 GET read-back of `career-radar/_guard/latest.json` from bucket `engineering-career-radar-archives` confirmed a stored signed report with `schema_version=1`, pinned account ID `02e8abc1853165520174d6a71b3a8b2d`, `admitted=true`, `metrics_complete=true`, `storage_class=standard_only`, `storage_peak_bytes=11219237`, Class A 74, Class B 84, `unknown_operations=[]`, `guardian_error=null`, observed at `2026-11-17T22:37:31Z`.
- Main-branch runner smoke [44191844359](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44191844359) passed; full private regression [44191844370](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44191844370) passed 499 tests (0 failures/errors/skips), public retrieval tests, frontend/Worker/extension contracts and private checkout cleanup.
- Admission is now genuinely PASS. This does not itself execute migration. Live migration remains a separate controlled operation; preserve Space originals, verify every copied object by size/SHA-256, and do not perform cleanup in the migration run.


## 2026-11-17 — Live Space history migration PASS; dashboard UI smoke pending
- Approved live migration workflow [#44192961402](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44192961402) passed after setting a descriptive `User-Agent: CareerRadarArchiveMigrator/1.0`. Cloudflare had rejected Python's default signature with edge error 1010; the named client was accepted.
- All 13 indexed Space history archives (80,692,241 bytes total) and three root snapshots (`search-history.json` 12,590 B, `jobs.json` 379,962 B, `seen-jobs.json` 1,142,570 B) uploaded through Bridge.
- The workflow verified exact byte length and SHA-256 after reading back all 16 data objects plus manifest (17/17). Manifest key `history/legacy-20261117224443.json`; manifest SHA-256 `39bc33b1399d1a0442f26588f3ab582a055cdf25bac3c08d097f49ff95941ffb`; `deletion_performed:false`.
- Cloudflare R2 independent listing matched every manifest size: 16/16 migrated data objects present, no missing/mismatched objects. Total bucket listing is 21 objects / 93,452,872 bytes, including the 16 migrated objects, manifest, guardian and three pre-existing archives.
- Re-listed HF Space after migration: all 13 archives and all six preserved files remain intact. No Space deletion or modification occurred.
- Post-migration guardian run #44193306294 succeeded: fresh signed report observed `2026-11-17T22:46:41Z`, admitted true, metrics complete, Class A 86, Class B 123, unknown operations 0, no guardian error. Note its storage sample timestamp is 21:40Z (pre-migration); the direct R2 listing is the current measured object total.
- Cloudflare deployed Bridge source confirms private `/published` history reads are R2-first after CV-password + fresh-guardian checks, with Hugging Face fallback. Dashboard Worker proxy forwards `X-CV-Password` and injects `X-Dashboard-Key`. Active frontend-v3 History requests `search-history.json` and archive details through `/published`.
- Manual UX acceptance pending: user should unlock Master CV in dashboard, open Scan history, confirm the 13 archives display, and open an archive to confirm archived vacancies render. Never request or log the CV password. Keep all Space originals until this manual check passes.
- Diagnostic/test follow-ups: safe HTTP error reporting added to migration script; final public runner smoke #44193447189 passed 66 tests. Post-fix migration dry-run #44193447134 passed for 13 archives / 3 snapshots without writing. One intermediate smoke failed due to an over-escaped sanitizer regex; fixed in commit `fcad67e4fffd923d02247ca4c7a26b08274b5e54`. Earlier live attempts #44192548216 and #44192757040/#44192855913 failed before uploads due to edge 1010; later attempt #44192961402 is the successful final live migration.

## 2026-11-17 — Production UI rollout after R2 history migration
- Dashboard deploy [#44194365352](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44194365352) passed source validation, Cloudflare credential preflight, dashboard Worker/assets deployment and Bridge Worker deployment. Cloudflare Worker metadata confirms dashboard assets present and both Workers modified at 22:53 UTC.
- UI-only Hugging Face sync [#44194231924](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44194231924) validated but correctly skipped writes because the target Space was 999,931,761 / 1,000,000,000 bytes; projected upload exceeded quota and the 950MB stop threshold. No Space files changed. Never bypass the guard or delete the original archives/snapshots.
- The current private source `public/index.html` is R2-aware, but the Hugging Face Space inline index remains stale until a future admitted sync. The Cloudflare dashboard Worker/assets deployment is the active production UI target.
- Manual browser acceptance remains pending: unlock Master CV, open Scan history, verify 13 archive summaries, open one archive and verify vacancy/source diagnostics. Do not ask for or log the CV password.


## 2026-11-18 — Live Cloudflare dashboard availability investigation
- User reports that https://career-radar-dashboard.happytiswis.workers.dev/ does not load. Treat live browser availability as FAIL / unresolved; do not describe the dashboard as user-accepted or healthy based only on deployment success.
- Cloudflare control-plane read-back confirms both Workers are deployed and their workers.dev subdomains are enabled. Dashboard deployment: 2026-11-17T22:53:43.661Z, deployment 10af122c-f451-44f0-8c93-4a41fd7a2d2e, version ad189e92-1e8d-4e01-9777-9fdcfe89085d. Bridge deployment: 2026-11-17T22:53:48.947Z, deployment b9ff0aeb-a007-4ac3-a259-0c93338a3a58, version b53c45ef-e3d0-4050-a98d-db6cc7e3a506. Dashboard bindings include ASSETS, BRIDGE service and DASHBOARD_API_KEY; Bridge bindings include ARCHIVES -> engineering-career-radar-archives and required secret bindings. Both script subdomains report enabled=true.
- GitHub runner deploy workflow #44194365352 completed successfully; all eight deploy/validation/cleanup steps passed. This is control-plane/deployment evidence only, not an HTTP/browser smoke test.
- Current Cloudflare Workers observability telemetry query returned no event rows for the queried 24-hour window, so it did not identify a runtime exception. Do not infer no requests or no errors from this empty result.
- Dashboard source uses Worker Assets fallback for the root path; dashboard gateway handles /api/bridge/* and proxies to the Bridge service. The Bridge explicitly allows the dashboard workers.dev origin. The user's exact browser failure mode is still needed to distinguish network/Cloudflare edge failure from Worker runtime, static asset, or browser-side failure.
- Next action: obtain the exact browser error/status (Cloudflare error code, HTTP status, blank page, timeout, or DNS/TLS failure) or a screenshot from the Cloudflare URL. Do not change CORS allowlists, rotate secrets, detach/re-attach workers.dev, or redeploy blindly before the failure mode is known. Once identified, fix, run tests, deploy via the public runner, verify a real HTTP/browser response, and update this handoff.

## 2026-11-18 — User-confirmed dashboard root-page smoke test
- User supplied a browser screenshot showing https://career-radar-dashboard.happytiswis.workers.dev/ loaded successfully and rendered the Career Radar workspace, Search jobs page, sidebar navigation, and scan configuration. Mark root-page/browser availability smoke test PASS based on this screenshot.
- This resolves the previously reported 'not loading' incident at the dashboard root. Do not leave it marked as an active outage.
- R2 Scan history end-to-end UX acceptance is still separate and pending: user has not yet confirmed that the 13 migrated archives appear and that an opened archive loads vacancy/source-diagnostic details. Do not mark that check PASS until explicitly confirmed.

## 2026-11-19 — Production scan #28 verified
- GitHub Actions production scan run #44540433068 completed with conclusion=success; job `scan-score-publish` succeeded. Runtime 7m21s. Run URL: https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44540433068
- Privacy-safe funnel reported raw_urls=24,039; global_unique_canonical_urls=22,292; usable_postings=22,292; posting_identities=22,977; newly_discovered=21,901; career_tracks=35/35 (allocated 35); retrieval_queries planned/attempted/succeeded/failed=280/210/210/0; scanner_collected=10,673; shortlisted=60; source_families=14.
- Private Supabase telemetry persisted and verified: canonical_urls=22,292, posting_identities=22,977, tracks=35, source_families=14, ai_queued=50, ai_assessed=32, ai_terminal_outcomes=50. Supabase shortlisted-results publication succeeded: collected=10,673, shortlisted=60, source_metrics=14.
- Source-yield aggregate artifact `career-radar-source-yield` uploaded (artifact ID 14539191453; SHA-256 c0254f5f4915496e2b527359b56caa4d7933083d3248c5ceaa81726acdc92055).
- Storage Guardian admitted Supabase database writes: used 103,708,339 / 524,288,000 bytes (19.78%), incoming 3,865,986 bytes. Supabase Storage used 0 / 1,073,741,824 bytes.
- Hugging Face Space mirror refresh was correctly blocked: target Space 999,931,761 / 1,000,000,000 bytes (99.99%); incoming 2,521,129 bytes would exceed the 950,000,000-byte stop threshold and quota. No historical Space data was deleted.
- IMPORTANT: this run did NOT create/store a new R2 archive. Steps `Ensure private archive exists for explicit retention`, `Refresh account-wide R2 free-tier admission before archive upload`, and `Store and verify current archive in private R2` were skipped. Workflow config shows `enable_private_archive` defaults to false and R2 archive writing is opt-in; production publish is also separately gated. The R2 history UI may therefore show only the 13 migrated historical archives, not this new run. Do not claim run #44540433068 is in R2.
- Follow-up decision: consider changing `enable_private_archive` to default true for manual scans and explicitly enable private-only R2 archiving for scheduled scans, while keeping production publication/HF mirroring disabled and retaining Storage Guardian admission. Do not change without preserving the separation between private archive writes and public/HF publication.
- R2 Scan history user acceptance remains pending: user has not yet shown the Scan history page with the 13 archive entries and an opened archive's vacancy/source-diagnostic detail.

## 2026-11-19 — Private R2 archive-by-default workflow change merged
- Implemented and merged runner PR #43: https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/43. Merge commit `eb58ad660058c8c00fb9ab43b578644b99a64330` on runner `main`.
- `.github/workflows/production-scan.yml`: `enable_private_archive` now defaults true for manual `workflow_dispatch`; scheduled events are explicitly treated as archive-enabled because they do not have workflow inputs.
- The R2 Guardian is run for every scheduled scan and every manual scan with private archiving enabled. It remains fail-closed: the R2 upload only runs when the signed Guardian output is `r2_write_admitted=true`.
- Guardian denial/unavailability and R2 upload failure no longer stop the scan before private Supabase result persistence. The workflow emits a run-summary warning when a scheduled/default-private archive did not complete a verified upload. Upload still validates archive run ID, byte size and SHA-256 read-back.
- Private R2 archive permission is now separate from production publishing. `enable_production_publish` remains default false and its description now refers to Hugging Face/public dashboard/vacancy publication. No public/HF publishing was enabled by PR #43.
- PR validation PASS: `validate` workflow YAML/safety assertions, `runner-smoke`, and `full-private-regression / full-private-suite` all succeeded. PR was mergeable and merged; main-branch read-back confirms default=true, schedule condition, Guardian gate and warning step.
- No production scan was launched as part of this configuration-only change. The next scheduled/manual scan is the first live verification of the new default; check its run summary for `R2 archive verified: history/run-<run_id>.json` and the R2 warning section if Guardian denies admission.
- The other proposed retrieval enhancements (per-family reweighting of the 70 unused query budget, pre-AI ranking, applied/dismissed/saved feedback, cross-source identity+content dedupe, matrix parallelism/rate limits, and stage timing/cap telemetry) are separate follow-up work and were not changed by PR #43.

## 2026-11-19 — First post-merge R2 archive verification pending
- Re-read runner `main` workflow after PR #43 merge. The manual `workflow_dispatch` form defaults `enable_private_archive=true`; keep `enable_production_publish=false`. Scheduled runs also take the private archive path.
- No post-merge scan had yet run at the time of this handover update, so there is no live archive/SHA-256 proof for the new default yet.
- The connected GitHub tool surface exposes workflow/run reads and reruns, but no `workflow_dispatch` create/run action. Do not claim a scan was started. To initiate verification, an operator must open Actions → `Career Radar production scan (private source, public runner)` → Run workflow on `main`, leave private archive enabled, and leave production publishing disabled.
- After the run, inspect the `Refresh account-wide R2 free-tier admission before archive upload` and `Store and verify current archive in private R2` steps. Require Guardian admission true, upload step success, log `R2 archive verified: history/run-<run_id>.json (<bytes> bytes).`, and matching SHA-256 from R2 read-back. If denied, report the Guardian reason and do not bypass it.
- Confirm no Hugging Face/public publishing was authorized. Record run ID, archive object key, byte count and SHA-256 in both handovers once the actual run evidence is available.

## 2026-11-20 — First post-merge private R2 archive PASS (manual run #29)
- User launched `workflow_dispatch` run #29 after PR #43 merge. GitHub run ID `44547402747`, commit `23cf8b0da958cf05d860a39c79c3dcf317bb8d65`, completed successfully 2026-11-19 14:52:22Z. Run URL: https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44547402747
- Job `scan-score-publish` succeeded. Step `Refresh account-wide R2 free-tier admission before archive upload` succeeded; Guardian receipt at 2026-11-19T14:51:33Z reported `admitted:true`, `metrics_complete:true`, `guardian_error:null`, 1 bucket, Class A operations MTD 105, Class B 195, unknown operations 0, storage peak upper bound 0.093455 GB.
- Step `Store and verify current archive in private R2` succeeded. Exact log: `R2 archive verified: history/run-44547402747.json (3276886 bytes).` The publisher computed SHA-256 from the local archive, PUT the object, confirmed stored=true and matching size, fetched the object back from the Bridge/R2 read route, then compared byte length and SHA-256. The equality assertion passed; the workflow wrote `verified=true`, `sha256=<digest>`, and `bytes=3276886` to the step outputs. The raw digest value is not printed in public logs, so do not invent or claim to know its hex string.
- Supabase finalized the same scan successfully: collected=13,020, shortlisted=608, source_metrics=17.
- Public dashboard publication was explicitly false (`DASHBOARD_PUBLISHED=false`); HF mirror refresh was not performed and was safely blocked by the Space capacity guard (99.99% used, projected over quota/stop threshold). No historical Space data was deleted.
- This completes the first post-merge R2 archive acceptance test: Guardian PASS + R2 object write/read-back size and SHA-256 comparison PASS. The full scan job conclusion was success.
- User screenshot also showed run #29 completed successfully in 5m45s and aggregate retrieval summary: raw URLs 26,980; unique canonical URLs 24,493; usable postings 24,493; posting identities 25,178; newly discovered 23,891; career tracks 35/35; retrieval queries 280/210/209/1; collected 13,020; shortlisted 608. Treat workflow log as primary source for R2 acceptance.
- Note: exact SHA-256 hex was stored as a step output but not echoed in logs. If future audit needs the literal digest, change the archive step to print the digest (not secrets) or add it to a signed non-sensitive run summary.

## 2026-11-20 — Pre-opportunity-expansion backup initiated (do not begin feature work until DB export is complete)
- Immutable Git recovery refs created at exact pre-change `main` commits: private source `backup/pre-opportunity-expansion-20261120` -> `593d1761ef0f499c50e55db1e2a3e3a53a581347`; public runner `backup/pre-opportunity-expansion-20261120` -> `ed352eeea044466f019cdeb410075cccaa66fad1`. These preserve the full Git trees/history at the pre-upgrade baseline. Cloudflare Workers source and dashboard assets are in the private source repository.
- Cloudflare control-plane read-back: account `02e8abc1853165520174d6a71b3a8b2d`; dashboard Worker active version `ad189e92-1e8d-4e01-9777-9fdcfe89085d`, deployment `10af122c-f451-44f0-8c93-4a41fd7a2d2e`; Bridge active version `b53c45ef-e3d0-4050-a98d-db6cc7e3a506`, deployment `b9ff0aeb-a007-4ac3-a259-0c93338a3a58`. Both workers.dev subdomains enabled. Dashboard bindings ASSETS, BRIDGE service, DASHBOARD_API_KEY. Bridge ARCHIVES binding to `engineering-career-radar-archives`; secret binding names recorded, values intentionally not exportable/readable. Cloudflare retains prior worker deployments/versions (dashboard deployment history reports 511 total; Bridge 92 total at inventory time).
- R2 bucket `engineering-career-radar-archives` remains the authoritative private scan archive store. Previously verified historical migration: 13 original run archives plus three root snapshots and migration manifest. Latest post-merge live archive proof: `career-radar/history/run-44547402747.json`, 3,276,886 bytes, Guardian admitted and R2 SHA-256 read-back comparison passed. No R2 objects modified during backup preparation.
- Hugging Face Space `Sidmed/engineering-career-radar` originals are retained. Space storage was previously measured at 999,931,761 / 1,000,000,000 bytes (99.99%); do not upload or delete files during this work. Six rollback root files and 13 original history archives were confirmed present on 2026-11-17.
- Supabase inventory: project `plzjmyytuumxckbrrzlp` (`career-radar-n8n`), region eu-west-1, PostgreSQL 17.11.0.011, ACTIVE_HEALTHY. Organization plan is `free`, so Supabase does NOT provide automatic daily backups. This database is mixed-use: n8n plus Career Radar; includes public n8n tables, `career_radar_private` (9 tables; estimated 44,358 rows / 82,010,112 bytes), Auth (27 tables), public (174 tables), storage (0 buckets / 0 objects), migrations and Vault. Full logical database export is therefore mandatory before feature work; do not export only Career Radar tables or expose n8n credentials.
- Current DB relation-size estimate from pg_stat_user_tables: auth 1,515,520 bytes; career_radar_private 82,010,112 bytes; public 7,561,216 bytes; realtime 57,344 bytes; storage 344,064 bytes; supabase_migrations 163,840 bytes; vault 24,576 bytes. Estimated total ~91 MB relation storage. Row estimates are approximate.
- Supabase tool integration has no database dump/backup download action. Official current Supabase docs state Free projects should regularly export with `supabase db dump` and maintain off-site backups; Storage API objects are excluded from DB dumps. This project currently has 0 Storage buckets and 0 Storage objects. Supabase daily backup availability must not be assumed.
- Backup gate: GitHub code snapshots, Cloudflare deployment metadata, R2 scan archive evidence, and HF originals are preserved. Supabase full logical dump is NOT YET CREATED. Before opportunity feature implementation, build/run an encrypted `pg_dump` export to private R2. Likely required user-side GitHub Actions secrets: `SUPABASE_DB_URL` (session-mode direct connection string from Supabase Connect dialog) and `BACKUP_ENCRYPTION_PASSPHRASE`; never request values in chat. Use existing private R2 bridge CI credentials and Guardian. Encrypted backup must be size/hash verified after R2 read-back, and restore instructions recorded. If required secrets cannot be configured, stop feature work and tell user precisely.
- Do not change live schema, n8n workflows, Cloudflare bindings/secrets, R2 history objects or HF originals during backup preparation. Do not start opportunity classification/retrieval/dashboard feature implementation until encrypted Supabase backup is verified.

## 2026-11-20 — Backup infrastructure code merged; database backup still pending
- Private Bridge encrypted-backup route PR #176 merged to private source main as commit `16205744afcbd0c843ae2f7efb4705c3acf6ad01`. Its Worker Build check passed. Route is restricted to the existing archive CI authorization and fresh signed Guardian, a dedicated `backups/pre-opportunity-expansion-YYYYMMDD/` namespace, strict JSON envelope schema, GPG-AES256 marker, SHA-256 metadata, and private R2 storage.
- Runner backup workflow PR #44 merged to runner main as commit `13185082e8c5e5a35da4f0676d1a77e6d5b08dae`. Verified PR checks: full private regression (including Python suite, frontend syntax/contracts, Bridge restricted-RPC/Worker contracts and public retrieval-engine tests) PASS; runner smoke PASS; workflow validation PASS. Workflow is manual-only, full PostgreSQL 17 custom-format pg_dump, GPG AES256/SHA512, Guardian-gated, private R2 read-back SHA-256, restore manifest, and plaintext cleanup.
- Runner deployment trigger commit `2db993851cc5fd9bc83351421e3cc7e750ada014` started Cloudflare deployment run `44732349280` (dashboard Worker and Bridge Worker). At last check the dashboard deploy step was still running; verify run completion and active Bridge version before starting backup workflow.
- Backup workflow is present on runner main at `.github/workflows/backup-system-before-opportunity-expansion.yml`. It needs GitHub Actions secrets `SUPABASE_DB_URL` (TLS, project plzjmyytuumxckbrrzlp, PostgreSQL session mode port 5432), `BACKUP_ENCRYPTION_PASSPHRASE`, and existing `ARCHIVE_CI_TOKEN`, `DASHBOARD_API_KEY`, `R2_GUARD_API_TOKEN`, `PRIVATE_SOURCE_READ_TOKEN`; variable `CLOUDFLARE_ACCOUNT_ID`. Values must never be pasted into chat or logs.
- No DB dump has yet been created. No Supabase data/schema was changed. No feature implementation may start until the manual backup workflow completes successfully and both encrypted dump and manifest have verified R2 read-back hashes. User must run the workflow manually from GitHub Actions after confirming required secrets are present; this tool integration supports GitHub workflow/run read and rerun operations but not workflow_dispatch or secret administration.


## 2026-11-20 — Backup Bridge deployed to production; database dump gate remains
- Cloudflare deployment run `44732349280` completed SUCCESS: https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44732349280. Dashboard Worker and search Bridge Worker deployment steps both passed.
- Cloudflare API read-back after deployment: dashboard active version `f9751907-1197-4400-8211-b23c89ea1276` (deployment `eb6346e0-ac04-4913-b04b-4d8cb629b2e5`, 100% traffic); Bridge active version `eda8faab-af28-425d-91ba-1929c49be01c` (deployment `0e40cf02-4cd4-4a02-a6bf-71feac1f4b74`, 100% traffic). Existing bindings and secrets preserved; dashboard still has ASSETS, BRIDGE service and DASHBOARD_API_KEY; Bridge still has ARCHIVES bucket plus all existing secret and rate-limit bindings.
- Bridge source now accepts backup keys only under the dated pre-opportunity-expansion namespace, while keeping existing 20 MiB request cap. The backup workflow deliberately fails closed if the compressed/encrypted backup envelope exceeds that cap; no oversized upload will be attempted. (If that occurs, implement bounded chunked encrypted uploads as a separate reviewed change; do not raise Worker request/memory limits blindly.)
- Git recovery refs and Cloudflare historical versions remain available. No database dump has yet been generated or stored. No feature implementation has started.
- Only remaining user action: ensure GitHub Actions secrets/variable exist (never paste values into chat), then run Actions > "Encrypted full-system database backup to private R2" > Run workflow on main. Required secrets: `SUPABASE_DB_URL` (PostgreSQL 17-compatible, TLS required, correct Supavisor session mode port 5432), `BACKUP_ENCRYPTION_PASSPHRASE`, `ARCHIVE_CI_TOKEN`, `DASHBOARD_API_KEY`, `R2_GUARD_API_TOKEN`, `PRIVATE_SOURCE_READ_TOKEN`; variable `CLOUDFLARE_ACCOUNT_ID`. Wait for green workflow and verify R2 dump+manifest SHA-256 read-back receipts before beginning opportunity expansion.


## 2026-11-20 — Final backup gate update
- Cloudflare deploy run `44732349280` succeeded; dashboard active Worker version `f9751907-1197-4400-8211-b23c89ea1276`, Bridge active Worker version `eda8faab-af28-425d-91ba-1929c49be01c`, both at 100% traffic. Existing production bindings/secrets were read back and preserved.
- Private Bridge backup namespace PR #176 and runner workflow PR #44 are merged. Runner full private regression, workflow YAML validation and smoke tests all passed on PR head `8049de364a2e37fc45da100830583bd15bd8a2be`.
- Backup workflow is manual-only and not yet run. Required GitHub Actions secrets/variable and user manual launch are documented in private-source `AI_HANDOFF.md` and `docs/RESTORE_PRE_OPPORTUNITY_EXPANSION.md`.
- Upload cap remains 20 MiB in Bridge and workflow. If actual encrypted envelope exceeds this, workflow exits before PUT; do not bypass. Design bounded chunked backup objects and update restore procedure/tests in a separate reviewed PR.
- Feature work remains blocked until the encrypted full database dump and manifest are uploaded to R2 and their read-back SHA-256 checks pass.


## 2026-11-20 — Backup workflow GPG verification fix merged; full database backup still pending
- User-dispatched backup workflow run #4 (`44734886203`) passed required-secret validation, TLS/connection-target validation, immutable source checkout, and fresh R2 Guardian admission. PostgreSQL `pg_dump --format=custom` and `pg_restore --list` completed; the job then failed before any R2 upload. Run URL: https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44734886203
- Root cause: `gpg --batch --list-packets` on the encrypted payload attempts to inspect/decrypt encrypted packet contents without loopback passphrase input; logs showed `problem with the agent: Inappropriate ioctl for device` and `decryption failed: Bad session key`. This was not proof of a wrong secret. The actual encryption command had already completed.
- Fixed runner PR #45: https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/45, merged squash as `f30c37f1ed0a3169a99e4b8788695f50da8efb2c`. It replaces packet listing with explicit `gpg --batch --yes --pinentry-mode loopback --passphrase-file ... --decrypt ...`, compares decrypted bytes to the original pg_dump using `cmp`, and deletes the temporary verification plaintext before continuing.
- PR checks PASS: full private regression (`backup-source-regression / full-private-suite`), public runner smoke, and workflow validation. Local GPG AES256/SHA512 encrypt → loopback decrypt → byte-for-byte comparison test also PASS. No secrets were read or changed.
- Next action: user must manually dispatch the updated backup workflow from runner `main` (commit `f30c37f1ed0a3169a99e4b8788695f50da8efb2c`). If it passes encryption, it will proceed to Guardian-gated R2 upload and encrypted-object read-back verification, then manifest upload/read-back. Inspect both hashes and exact R2 object sizes before declaring backup complete.
- Current gate remains BLOCKED: no verified Supabase full logical dump has yet been uploaded to R2; all opportunity-expansion feature work remains prohibited until the workflow succeeds and the backup is independently verified. No Supabase schema/data, production scan data, HF originals, or historical R2 archives were modified.

## 2026-11-20 — Backup run #5 diagnosed; GPG shell continuation correction in progress
- User-dispatched backup workflow run [44734886203](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44734886203) passed required secret/variable preflight, PostgreSQL TLS/target validation, immutable source checkout and R2 Storage Guardian admission. Guardian report at 2026-11-20T12:28:33Z: one bucket, complete metrics, zero unknown operations, 114 Class A and 211 Class B operations month-to-date, storage peak upper bound 0.099973 GB.
- The combined dump/encryption step failed before either R2 upload step; both R2 upload/read-back steps were skipped. GPG emitted `no command supplied` and `can't open '\\'`. No evidence of R2 upload, manifest creation or a verified database backup exists.
- Root cause: the decrypt invocation in `.github/workflows/backup-system-before-opportunity-expansion.yml` had two literal backslashes at each of three line endings, unlike the valid encryption command's single shell continuation. Bash passed malformed arguments and GPG treated a backslash as an input filename. This error does not implicate the passphrase; do not change the secret based on this evidence.
- Correct the decrypt command to use one shell continuation backslash per YAML block line; strengthen `tests/test_encrypted_system_backup_workflow.py` to reject the malformed doubled-backslash form. Validate workflow YAML, shell parsing, and a GPG AES256/SHA512 encrypt/decrypt byte-comparison fixture before merging.
- Release gate remains BLOCKED. Do not begin opportunity expansion until a later manual run creates the full PostgreSQL logical dump, verifies GPG decrypt/cmp, uploads encrypted dump and recovery manifest to private R2, then verifies exact R2 read-back sizes and SHA-256 hashes for both objects.

## 2026-11-20 — Backup run #6 reached R2 dump verification; manifest schema mismatch diagnosed and fix in progress
- Manual backup run [44737243622](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44737243622) passed credential/TLS checks, immutable source checkout, R2 Guardian admission, full PostgreSQL logical dump, GPG AES256/SHA512 encrypt/decrypt byte comparison, and encrypted dump R2 upload plus exact object read-back verification.
- Dump evidence from the successful dump step: plaintext 12,198,898 bytes; plaintext SHA-256 `c4faf9a30b88a8f071a3c269484819e2762950192b2cd6ca17791e52e0f1e832`; encrypted bytes 11,202,482; ciphertext SHA-256 `6d487f4f0c1aa75c3b1adffa59c1ed684b62967b2f77581a886cc496e63ad494`; restore catalog 2,501 entries. Encrypted R2 object read-back passed, object SHA-256 `e170797ae8c3379a3d25a8addb1b05f669ca801caf95e75681df35ae78e513ba`.
- The only failing step was manifest PUT. Root cause is a producer/validator contract mismatch: the Bridge's `validManifest` admission check requires `database_dump_sha256` at the top level, while the workflow only emitted it nested under `database_dump.database_dump_sha256`. Bridge correctly rejected the manifest with HTTP 400. No manifest was stored/read back; workflow summary was skipped. Do not rerun until fixed.
- Fix: add the same plaintext dump SHA-256 at the manifest root (preserve the detailed nested `database_dump` structure) and add a workflow regression assertion. This is a workflow metadata-only correction; no secret, encryption, database, or Bridge admission changes.
- Release gate remains BLOCKED until a fresh run verifies both encrypted database object and recovery manifest R2 read-back size/SHA-256. The already-uploaded encrypted database object from run #6 is present under the fixed pre-opportunity-expansion key; a rerun may safely replace the same key only after Guardian admission and must verify the new manifest refers to the final object's digest.

## 2026-11-20 — Backup manifest schema fix merged; fresh full backup dispatch required
- Run #6 [44737243622](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44737243622) proved the full PostgreSQL dump and GPG AES256/SHA512 encryption/decryption byte comparison. Dump: 12,198,898 plaintext bytes (SHA-256 `c4faf9a30b88a8f071a3c269484819e2762950192b2cd6ca17791e52e0f1e832`); 11,202,482 encrypted bytes (SHA-256 `6d487f4f0c1aa75c3b1adffa59c1ed684b62967b2f77581a886cc496e63ad494`); restore catalog 2,501 entries.
- Encrypted envelope upload and R2 read-back size/SHA-256 passed; R2 object SHA-256 `e170797ae8c3379a3d25a8addb1b05f669ca801caf95e75681df35ae78e513ba`. Manifest upload failed because workflow nested `database_dump_sha256` while Bridge admission requires that field at root.
- Runner PR #47 merged as `8f97d0b331f1af9a6c8bba683e6edd1f32174db1`. Workflow now emits root `database_dump_sha256` while retaining nested database metadata; regression test asserts it. PR workflow validation and public runner smoke passed. Post-merge public smoke passed; post-merge full private scanner regression run `44738614108` was still in progress at last check.
- Do not rerun old run #6: it is pinned to pre-fix commit `53f5cdd5bf17699d4261df48e465089d6e6c98c0`. A fresh manual `workflow_dispatch` on runner `main` is required. This connector exposes rerun operations but no workflow-dispatch action; user must open the workflow page and dispatch current main.
- Release gate remains BLOCKED until the fresh run confirms encrypted object and recovery manifest both uploaded and read back with exact sizes/SHA-256, and the workflow summary is published. The existing encrypted object under the fixed backup key may be replaced by the new verified run; ensure the final manifest references the final object digest. No opportunity-expansion feature work, production scan or Supabase mutation before that.

## 2026-11-20 — Full encrypted pre-expansion database backup VERIFIED (run #7)
- Manual GitHub Actions run [44743162368](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44743162368) completed SUCCESS on runner main commit `4dc0d252b539f21f689486ba89564b6146f5e277`.
- Every workflow step passed: required credentials, immutable pre-change source snapshot, PostgreSQL target confirmation, fresh account-wide R2 Guardian admission, full PostgreSQL logical dump, GPG AES256 encryption with SHA512 S2K, encrypted object upload and R2 read-back, recovery manifest upload and R2 read-back, verification summary publication, and plaintext/private checkout cleanup.
- Verified dump receipt: plaintext 12,198,898 bytes; plaintext SHA-256 `fa1a62b1a4c350c1d58712f87294fe1a426a3a179547768ed9ba4d7112af50b7`; ciphertext 11,202,486 bytes; ciphertext SHA-256 `ed11f514034acde6a5354afffb029fa926e7eb1e507a7d141fd301ad8fae96ed`; PostgreSQL restore catalog 2,501 entries.
- Encrypted R2 envelope: `backups/pre-opportunity-expansion-20261120/database.dump.gpg.json`; 14,937,074 object bytes; object SHA-256 `68eb64d14923faaa30ff8993cd955c449b0767cb1f37fcecd5bfe1109507ac24`. Ciphertext SHA-256 and byte count were revalidated after R2 read-back.
- Recovery manifest: `backups/pre-opportunity-expansion-20261120/manifest.json`; 7,803 bytes; SHA-256 `68fc6af7bd3650c315a31dae4c149eb719f9ae0b8f6abfce933c895f037a6661`. R2 read-back exact byte length and SHA-256 passed.
- GitHub Actions summary explicitly states `Pre-opportunity-expansion backup — VERIFIED` and `All R2 object read-back comparisons passed`. Guardian admission was true. The workflow removed the private source checkout, plaintext dump, and temporary passphrase file.
- This supersedes the earlier BLOCKED backup status caused by the manifest root-field mismatch. The backup acceptance gate is now SATISFIED. Preserve the GPG passphrase in the password manager; it is not present in the manifest or logs. Restore only into a separate/new Supabase project first, following `docs/RESTORE_PRE_OPPORTUNITY_EXPANSION.md`; never test restore over production.
- Backup completion does not itself authorize opportunity expansion deployment. Before any production mutation, review the restore guide, confirm recoverability/credentials, and follow the existing release gates. No Supabase schema/data or production opportunity code was changed by this backup.

## 2026-11-20 — Pre-implementation handover: first-class opportunity types and category-specific retrieval
- Verified the pre-expansion full encrypted database backup is complete: runner Actions run #7 `44743162368`; immutable source snapshot and R2 encrypted database + recovery manifest both passed read-back SHA-256. Preserve this snapshot; do not overwrite/delete it.
- User-approved product scope: add opportunity type selection to the dashboard Scan filters so selected types control actual retrieval. Include Employment, Ausbildung (dual and school-based), Volunteering/Freiwilligendienst (FSJ, FÖJ, BFD, European Solidarity Corps), Internship/Praktikum, and Graduate/Trainee programmes. Explicitly EXCLUDE Werkstudent/student jobs; do not build student coursework, student profiles or student-work features.
- Keep existing engineering/job retrieval, career tracks, source allocation, application tracking and dashboard behavior backward compatible. Empty/missing opportunity_types in old requests must preserve legacy employment behavior; do not silently broaden scheduled scans.
- Implementation must add a validated opportunity_types array across dashboard → Cloudflare Search Bridge → runner workflow request → Python scan planner. Persist selected types and category/source strategy in scan metadata/telemetry. Multi-select must be supported.
- Category retrieval strategy must be separate from eligibility/matching. Do not drop a potentially relevant opportunity just because current language/education does not meet a requirement; retain it with explicit requirement/eligibility evidence. Preserve source attribution, canonical deduplication, posting freshness and no duplicate rows.
- Initial source strategy research: official BA Jobsuche covers jobs and Ausbildung and its Jobsuche supports internships; official BA education pages distinguish dual Ausbildung, school-based Ausbildung, Praktikum and dual study. FREIWILLIG JA is the official cross-provider FSJ/FÖJ/BFD portal with location/radius/activity/accommodation filters. European Youth Portal exposes EU-funded ESC volunteering opportunities and accredited organisations. IHK/Lehrstellenradar and employer career pages are relevant additional discovery sources.
- Permission boundary: existing BA bulk/API adapter is documented as disabled pending authorization; keep it disabled until authorization is independently established. FREIWILLIG JA is not an unrestricted public search API; do not scrape, reverse-engineer private endpoints or bypass protections. Use approved public interfaces, provider-approved APIs, permitted search indexing, or clearly attributed official source links until access terms are confirmed. No source should be marked integrated merely because a portal exists.
- Source strategy should be type-specific and measurable: separate keyword/query dictionaries, provider/source allow-lists, bounded query budgets, yield/freshness/failure metrics, source attribution and fallback rules for each opportunity type. Do not allocate the whole budget to BA; preserve fair interleaving and provider rate limits. Never infer visa, compensation, housing or eligibility from missing text.
- Do not add Werkstudent, student jobs, student-only holiday jobs, student coursework or a student dashboard. Internship/Praktikum remains a distinct category only when the posting is an internship placement, not a student employee role.
- Initial inspected code: `public/index.html` embeds Scan form fields; active JS is `public/frontend-v3.js`; Worker `/search` validates and dispatches `search_request`; Python `deep_search.py` validates requests and plans BA query boards; `public_source_adapters.py` has generic public adapters; source settings and permission policy in `settings.json`, `RETRIEVAL_INTEGRATIONS.md`, `SOURCE_CAPACITY_AND_PERMISSION_GUIDE.md`.
- No application code, production Worker, Supabase schema/data, GitHub Actions production scan, Hugging Face Space or public vacancy data has been changed in this pre-implementation milestone. Next: inspect exact active UI/worker/runner integration and tests; implement through dedicated PRs, run private full regression + public runner smoke + YAML/contract validation, then separately decide on deployment. Update both handovers after each significant milestone.

## 2026-11-20 — Private opportunity-type search PR #181 is open; validation pending
- Private project PR #181: https://github.com/happytiswis-sudo/engineering-career-radar/pull/181 (head `1bbe279c6978f870b83493ce2a51f08c045a0a89`). It adds Employment, Ausbildung, Volunteering/FSJ/FÖJ/BFD/ESC, Internship/Praktikum and Graduate/Trainee filters, category-specific bounded query seeds, source-strategy metadata and a deterministic classifier. Werkstudent/student work is excluded.
- The dashboard-to-Worker-to-Python request contract now includes `opportunity_types`; old requests default to Employment. Existing employment query budgets and production behavior are intended to remain unchanged.
- BA bulk search remains disabled pending written authorization. FREIWILLIG JA is not treated as an unrestricted API. Category query seeds can use the existing SerpApi adapter only when the configured API key is present; existing ATS and Arbeitnow adapters remain available.
- Private full-suite regression, browser/JS contract tests and runner smoke have NOT yet been executed for PR #181. Do not merge or deploy until these are run and pass. Production scan and public vacancy publication remain separately gated.
- The verified pre-expansion encrypted database backup remains run #7 `44743162368`; preserve its recovery snapshot and do not overwrite/delete it.

## 2026-11-20 — Final opportunity-type retrieval validation PASS (Cloro + SerpApi + source strategy)
- Private project PR #182: https://github.com/happytiswis-sudo/engineering-career-radar/pull/182, final candidate SHA `4395e63a10bbbfcbf6f8ce11df741d3bab565a7a`.
- Non-publishing full private scanner regression [44749310232](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44749310232) PASS: 513 Python tests, zero failures/errors/skips; frontend syntax/contract tests PASS; Bridge/restricted RPC/Worker syntax tests PASS; public retrieval-engine regression PASS; extension packaging and cleanup PASS.
- Public runner smoke [44749310054](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44749310054) PASS. Runner workflow validation [44748605095](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44748605095) PASS for the candidate-selector workflow; subsequent changes to that workflow were comments only.
- Opportunity type filters: employment, Ausbildung, volunteering/Freiwilligendienst (FSJ/FÖJ/BFD/ESC), internship/Praktikum, graduate/trainee. Werkstudent/student work excluded. Legacy requests default to employment.
- Category retrieval uses bounded BA query planning only if BA is authorized, SerpApi Google Jobs when its key is configured, and Cloro Google organic `site:` queries to official portals only when `CLORO_SEARCH_ENABLED` and a Cloro API key are configured. Cloro is not a jobs API; only opportunity-detail-like URLs are accepted. BA bulk adapter remains disabled pending written authorization; FREIWILLIG JA is not assumed to expose unrestricted API access.
- No production deployment, production scan, Supabase schema/data mutation, Hugging Face write or public vacancy publication has occurred. Code PR #182 remains subject to merge review; production deployment is a separate controlled release. Preserve verified backup #7 and immutable recovery snapshots.

## 2026-11-20 — Opportunity-type search deployed to Cloudflare production
- Private code PR #182 merged as `2c41877b0ecb52064845260ea18ce543affa7570`.
- Non-publishing final regression [44749310232](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44749310232) PASS: 513 Python tests, zero failures/errors/skips; frontend, Worker, Bridge and retrieval contracts PASS. Public runner smoke [44749310054](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44749310054) PASS.
- Controlled Cloudflare deployment [44749745031](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44749745031) SUCCESS. Deployment workflow revalidated dashboard/Worker contracts, confirmed deployment credentials without printing them, deployed dashboard Worker + public assets and Search Bridge, then removed private checkout.
- Cloudflare API read-back confirms `career-radar-dashboard` latest deployment `707d2f6c-92a3-48f9-a284-bbe17b2362a7` created `2026-11-20T14:03:27Z`, version `eb27b3f9-c419-464f-bb6c-2a0c0dc73f55` at 100% traffic; `career-radar-bridge` deployment `e4bbb248-4cb8-4730-a8ea-16b886a4c389` created `2026-11-20T14:03:32Z`, version `a3aea443-8880-42fa-90d9-c684f33fc2b3` at 100% traffic.
- Feature is live in the production dashboard Scan form. Categories: Employment, Ausbildung, Volunteering, Internship/Praktikum, Graduate/Trainee. Werkstudent/student work excluded. Old requests default to Employment.
- Category discovery: Cloro official-domain organic queries only when `CLORO_SEARCH_ENABLED` plus a Cloro API key are present; SerpApi category search only when `SERPAPI_API_KEY` is present; BA automated bulk remains disabled pending written authorization. FREIWILLIG JA, BFD, ESC, IHK, Lehrstellenradar and EURES remain official discovery targets, not claimed unrestricted direct APIs. Missing provider configuration must be surfaced clearly.
- No Supabase schema/data change, production scan, Hugging Face write or public vacancy publication was performed. The verified full backup #7 and immutable recovery snapshots remain untouched. Next operational step is user-facing Scan filter smoke test, then measure per-category source yield; do not run a production scan without explicit approval.

## 2026-11-20 — Hugging Face Space → Cloudflare CORS incident investigation
- User screenshot shows the Career Radar UI loaded from `https://sidmed-engineering-career-radar.static.hf.space` and a frontend `fetch` network exception labelled `Cloudflare connection/CORS failed`.
- Read-only inspection of current private main and the live deployed Worker script confirms the exact static HF origin is already present in BOTH `cloudflare/dashboard-lock-worker.js` and `cloudflare/search-worker.js` allowlists. Cloudflare live script downloads confirm the deployed dashboard and Bridge scripts both contain that origin and CORS headers. Do not add wildcard CORS or relax the allowlist.
- A live, external GitHub Actions CORS smoke test [44752329275](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44752329275) PASS against `https://career-radar-dashboard.happytiswis.workers.dev/api/bridge/health`: (1) preflight from the exact HF static origin returned 204 with allow-origin/method/header; (2) GET /health returned 200 with exact allow-origin; (3) `https://unapproved.example` preflight returned 403 with no allow-origin. Full runner private regression [44752329251](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44752329251) PASS, workflow validation PASS, runner smoke PASS.
- Added and merged runner PR #60 (`f16af720d26dba9a9b3469e7f3d708e0399cb25b`) to keep the live CORS smoke test as a permanent regression gate.
- No production code, Cloudflare deployment, Supabase data/schema, Hugging Face Space config or production scan was changed in this incident investigation. Current evidence does NOT reproduce a server-side CORS failure. The screenshot's generic frontend catch can also mask a browser network/CSP/extension issue or transient fetch failure. Next diagnostic: user hard-refreshes the HF Space, then tests the same UI from the canonical Cloudflare dashboard origin `https://career-radar-dashboard.happytiswis.workers.dev`; if HF fails but Cloudflare origin succeeds, inspect browser DevTools Console/Network for CSP/connect-src, extension filtering, DNS/TLS or an actual preflight failure. Ask for the failed request URL and console message only if still reproducible.
- Preserve all verified recovery snapshots, including backup #7; no backup was touched.

## 2026-11-21 — BA regression test workflow wiring (validation in progress)
- Public runner PR #64 (`ci/ba-private-regression-trigger-20261121`) adds a narrowly path-filtered pull_request trigger to the canonical non-publishing private scanner regression workflow and checks out the exact PR head SHA from the private source repository, preserving read-only token use and isolated workspace merge with current private main.
- Root cause confirmed in the runner workflow: it previously had push/main, workflow_call and workflow_dispatch triggers but no pull_request trigger. The legacy private Actions page in screenshots is historic; public runner is the active owner of full-private-suite.
- PR #64 workflow YAML read-back is syntactically valid under current runner-workflow-validation; validation job passed and public runner smoke passed. A private-main regression was also started by an existing broad backup-source-regression job; this does not substitute for BA PR #186 head testing.
- Runner workflow validation's reusable test job was explicitly pinned to private BA PR head `d9a146c65be8840db000cf287656e3e93131fa81` on a separate test-only branch, to validate the exact candidate without merging production code. Keep the candidate private PR unmerged until a full non-publishing suite plus BA adapter tests succeed against current main.
- Neither PR changes production deployment or starts a scan. No Supabase/HF/R2 writes. Preserve verified backup #7 (44743162368).
- Follow-up inside runner PR #65: renamed the reusable regression job from the historical `backup-source-regression` label to `ba-private-candidate-regression` while retaining the exact private candidate SHA pin. This is a clarity-only CI test update; verify the resulting full-private-suite before closing PR #65.


## 2026-11-21 — BA private regression trigger reconciled against current runner main
- Reconciliation branch `ci/ba-private-regression-trigger-reconciled-20261121` is based on current runner `main` after PR #65; the earlier PR #64 branch was one commit behind and diverged, so it is intentionally left untouched.
- Updated canonical `.github/workflows/private-scanner-regression.yml` with a narrow `pull_request` path trigger for private BA source-planning/config/adapter changes and explicit selection of `github.event.pull_request.head.sha`. The existing read-only private-source token, ephemeral integration merge against private `main`, regression suite, and cleanup remain unchanged.
- This is a non-publishing validation workflow. It cannot launch production scans, publish jobs, write Supabase/HF/R2, or deploy Cloudflare. Production remains a separate release gate.
- Validation must run on this reconciled branch before PR review/merge. Then the dedicated workflow must complete full-private-suite for exact private PR #186 head `d9a146c65be8840db000cf287656e3e93131fa81`; only that exact-head run is acceptable as regression evidence.
- Preserve verified backup #7 (run `44743162368`) and all immutable recovery snapshots; do not overwrite or delete them.


## 2026-11-21 — BA regression trigger merged and exact candidate validated
- Runner PR #67 merged to runner main as `bf9cc4ea9021f58f80435ac8862c6c1594a1ba75`. It reconciles the earlier #64 work with current main and makes the canonical private-scanner regression workflow respond to BA-related private PR changes.
- Runner PR #67 checks passed: runner workflow validation, public runner smoke, and the PR-triggered non-publishing private candidate regression.
- Exact BA candidate validation is runner Actions run [44835602074](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44835602074), job `ba-private-candidate-regression / full-private-suite`. Logs confirm private candidate SHA `d9a146c65be8840db000cf287656e3e93131fa81`, private base SHA `80a3d68d948edffb1ddfef1fdb1e4b632650a733`, and 513 Python tests with zero failures, errors or skips; frontend, Bridge, Worker, retrieval and extension contracts, package upload and cleanup all passed.
- Private PR #186 was then merged after exact-head validation as `b9d521b983a87ca896a35719197848067f78b3e5`.
- Production deployment and production scan/publication remain separate and have not been started in this milestone. Preserve verified recovery backup #7 (run `44743162368`) and all immutable snapshots.


## 2026-11-21 — Cloro production runner enablement candidate
- Runner PR #68: https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/68
- Candidate explicitly sets `CLORO_SEARCH_ENABLED=true`, passes the two existing encrypted Actions secrets, and reports key presence without printing values. A separate manual-only no-cost credential preflight workflow is added.
- Runner validation run [44837284130](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44837284130): workflow validation PASS; exact private Cloro candidate regression PASS (514 tests, zero failures/errors/skips); public runner smoke [44837284198](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44837284198) PASS.
- The Cloro credential-presence job intentionally failed because both `CLORO_API_KEY_1` and `CLORO_API_KEY_2` are missing from this public runner repository. Logs confirmed both are empty; no key values were printed. The private repository's secret store is not inherited. User must add both keys as encrypted Actions secrets in this runner repository before operational activation.
- The manual preflight `.github/workflows/cloro-credentials-preflight.yml` makes no API calls and consumes no credits. After the two secrets are added, rerun it or rerun the credential-presence job and confirm 2/2 before any live scan.
- The Cloro adapter is capped at 8 requests per deep scan and 4 per focused scan, with dual-key round-robin preference and fallback on auth/quota rejection. No monthly quota meter exists; do not claim a verified 1,000-request allowance without confirming the provider's account plan/credit rules.
- No production scan, Cloro API request, Cloudflare deployment, Supabase write, Hugging Face write or public vacancy publication occurred. Preserve verified backup #7 and immutable snapshots.


## 2026-11-21 — Cloro production runner activation merged; API credentials pending
- Runner PR #68 merged to main as `0228ad5610f01140ec73fb1cce5ff06f33f5a792`.
- The production scanner environment now sets `CLORO_SEARCH_ENABLED=true`, passes `CLORO_API_KEY_1` / `CLORO_API_KEY_2` from encrypted runner Actions secrets, and prints only sanitized presence status. Added manual workflow `.github/workflows/cloro-credentials-preflight.yml`; it performs no network/API calls and fails until both secrets are configured.
- Candidate runner validation [44837514267](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44837514267) PASS: exact private source candidate full regression 514 tests (0 failures/errors/skips), runner workflow validation PASS, public runner smoke [44837514259](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44837514259) PASS. Post-merge runner-main regression [44837598125](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44837598125) and smoke [44837598044](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44837598044) also PASS; the post-merge private suite again passed 514 tests.
- Credential-presence job reported both keys missing from the public runner repository and emitted a warning; no values were exposed. Private-repository secrets are not inherited by the runner. Until both are added, `cloro_enabled()` remains false and Cloro makes no requests. User action: add both encrypted Actions secrets in runner repository Settings → Secrets and variables → Actions, then run the no-cost preflight.
- Production workflow remains non-publishing by default. No production scan, Cloro API calls, Cloudflare deployment, Supabase mutation, Hugging Face write or public vacancy publication was made. Preserve verified backup #7 and immutable snapshots.


## 2026-11-21 — Cloro live API authentication verification authorized
- User confirmed both encrypted runner secrets are present; manual no-cost credentials preflight run #1 succeeded on runner main commit `63dc480254af1b2787dcffd120df40dd126550b0`. This proves secret presence only, not provider authentication.
- User explicitly authorized the next verification to make exactly one minimal live Google Search API request per key (maximum two total), separately for `CLORO_API_KEY_1` and `CLORO_API_KEY_2`. Live requests may consume Cloro credits. Never expose keys or response payloads in logs.
- Public runner workflow `.github/workflows/cloro-live-auth-smoke.yml` is being added as a manual-only workflow with a required explicit boolean confirmation, one request per key, no retries, no cross-account fallback, 5-result cap, short timeout, and sanitized status-only output. It is not a production scan and does not publish or write Supabase/HF/R2/Cloudflare.
- GitHub connector does not expose a workflow-dispatch action. After the workflow is merged, the operator must manually dispatch it on `main` with `confirm_live_api_calls=true`; inspect the run logs for each account's sanitized result. Do not dispatch production-scan.yml.
- Preserve verified backup #7 and all immutable recovery snapshots. No recovery snapshot was modified.


## 2026-11-21 — Cloro live-auth smoke workflow merged; live API calls pending manual dispatch
- Runner PR #70 merged to public runner main as `277d2477684386ed7c0eae19fcb51dfcb4581e7f`. It adds `.github/workflows/cloro-live-auth-smoke.yml`, a manual-only, explicit-confirmation test that makes at most one minimal Google Search request for each key independently (maximum two total), with no retry or cross-account fallback. It prints only per-account HTTP/auth status and a recognized/unrecognized response-shape marker; it never prints credentials, response bodies, result URLs or snippets.
- PR validation run [44839181515](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44839181515) PASS: Cloro secret-presence check PASS, YAML/workflow validation PASS, full private candidate regression PASS across Python, frontend, Bridge/Worker, retrieval and extension packaging/cleanup. Public runner smoke [44839181683](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44839181683) PASS.
- Private handoff PR #191 merged as `683d4f3cd5c7a26964e2f5c9c285e2443e8332d2`.
- The earlier no-cost presence-only preflight run #1 succeeded; both keys are configured in the public runner. This does not prove either key authenticates.
- **Remaining operator action:** manually run [Cloro live API authentication smoke](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/workflows/cloro-live-auth-smoke.yml) on `main` and set `confirm_live_api_calls=true`. This is the user's explicitly authorized two-request test and may consume provider credits. Expected sanitized output: `account_1: AUTH_PASS` and `account_2: AUTH_PASS`; if HTTP auth fails, the workflow reports the status code. It makes no production scan, publishing, Supabase/HF/R2/Cloudflare writes.
- The connected GitHub toolset does not expose workflow dispatch, so the assistant cannot start this manual workflow. Do not substitute production-scan.yml or run any full scan. After the user dispatches it, inspect the result and only then claim live authentication PASS/FAIL.
- Preserve verified backup #7 and all immutable recovery snapshots; none were changed.


## 2026-11-21 — Cloro first live request HTTP 400 diagnosed and request schema corrected
- User ran the bounded two-key live smoke. Both independent requests returned HTTP 400. This is a request-validation response, not an authentication rejection; the result did not establish that either key is invalid.
- Root cause found by comparing the exact sent JSON with the Cloro Google Monitor request schema and vendor migration guide: the smoke/adapter sent lowercase `country: "de"` plus unsupported `language` and `num` fields. The API schema requires uppercase ISO country code and uses `hl` for interface language and `pages` (1–10) for result depth.
- Private PR #193 merged as `e4e24745aa89a57ba6e9b14f9344da09162af276`: `cloro_search.py` now sends `country: "DE"`, `hl: "de"`, `pages: 1`; a unit test asserts the exact JSON payload; docs updated.
- Runner PR #72 merged as `405b83fea3acead477db19983b57b4aa0f51bb9e`: manual live smoke now sends the same schema. It still sends exactly one request per key, with no retry/fallback, and no response bodies/credentials logged.
- Exact candidate regression for private SHA `5f8d7d838673144539f086c4d0f5c9993b8a6671) passed in runner workflow validation run [44839877615](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44839877615): private Python suite, frontend, Bridge/Worker, retrieval regression, packaging and cleanup all PASS. Runner smoke [44839877616](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44839877616) PASS. The earlier intermediate validation attempts failed only because the test harness pinned/expected the prior candidate SHA or an assertion string differed; those test-harness issues were corrected and the final candidate run passed.
- Runner PR #73 resets the temporary candidate pin to merged private main SHA `e4e24745aa89a57ba6e9b14f9344da09162af276`; validation is pending.
- **Live key authentication remains unverified** until the user manually reruns [Cloro live API authentication smoke](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/workflows/cloro-live-auth-smoke.yml) on `main` with `confirm_live_api_calls=true`. The previous run was against old runner commit `0bc3419e2309ae5ce2f0d9ef9f98849bd8dfb10b`, so it must not be rerun from the old workflow version. The corrected run will use the fixed payload and at most two requests total. Do not start production scan.
- No production scan, publishing, Cloudflare deploy, Supabase/HF/R2 write or recovery snapshot mutation occurred. Preserve backup #7 and all immutable snapshots.


## 2026-11-21 — Cloro live authentication verified for both accounts
- User manually ran corrected workflow run #2, GitHub Actions run [44840205440](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44840205440), on runner main commit `d3bebc412f55f6225ab0f56e9e4b0fd0df7375a0`.
- Independently inspected sanitized job logs: `account_1: AUTH_PASS (HTTP 200); payload_shape=recognized`; `account_2: AUTH_PASS (HTTP 200); payload_shape=recognized`. Exactly two requests maximum, no retry/fallback. No credentials or response bodies exposed.
- Both encrypted runner Actions secrets are present and both keys authenticate successfully with the corrected Google Monitor payload. Cloro credentials are now live-verified.
- This does NOT constitute a full retrieval/yield validation; next safe step, if authorized, is a tightly bounded non-production adapter test / provider response parsing check, then observe first normal scheduled production scan without starting a manual scan or public publishing.
- No production scan, publishing, Cloudflare deploy, Supabase/HF/R2 write or recovery snapshot mutation occurred during this test. Preserve backup #7 and all immutable snapshots.


## 2026-11-21 — Dashboard source-selection visibility checked before BA + Cloro production scan
- User screenshot shows the Search Jobs form has no source/provider selection control. Inspected current private `public/frontend-v3.js`: launch payload omits `sources`; no source selector is rendered.
- Cloudflare `validateInput()` defaults omitted `sources` to `ba, ats, arbeitnow, smartrecruiters, workday, workable, jobicy, remotive, himalayas, nomado24, themuse` (with the existing fallback). Thus the UI does not currently permit restricting a run to BA + Cloro only.
- Private scanner `radar.py` adds BA dynamic boards when request profile includes `ba` and settings `discovery_ba_adapter_mode` is `enabled_by_user_request`; current `settings.json` has that exact setting. The current dashboard default includes `ba`.
- Private scanner `radar.py` independently appends bounded Cloro boards to manual scans whenever `CLORO_SEARCH_ENABLED=true` and `cloro_enabled()` sees at least one configured key. Public runner `production-scan.yml` passes `CLORO_SEARCH_ENABLED: 'true'` and both Cloro secrets. Both keys already passed live auth smoke run [44840205440](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44840205440).
- Therefore a normal dashboard launch using current defaults includes BA and Cloro, but also other configured default source families. Do not claim it is a BA+Cloro-only run. For a strict two-source isolation test, implement a visible source selector and pass selected sources through the dashboard payload/Worker validation before launching.
- User intends to launch a real scan; no scan was dispatched by the assistant. Keep production publishing disabled and preserve backup #7 / immutable recovery snapshots.


## 2026-11-21 — Dashboard source selector merged; Cloudflare rollout initiated separately
- Private source PR #197 merged at `0a6ff517e251bac17af28476be2eb916de957e6c`. It adds the Search Jobs provider selector (23 source IDs), configured defaults, select-all, selected-count feedback, explicit source submission and manual Cloro selection gating.
- Exact private candidate `3d519c8560f9c391a8db6c60c4127c5b10c5b25d` passed runner validation run `44842273835`: 518 private Python tests, 0 failures/errors/skips; frontend syntax/contracts, navigation, Applications auth/Kanban, extension Bridge/RPC/Worker, retrieval regression and extension packaging all passed. Public runner smoke run `44842273773` passed.
- Runner PR #77 merged at `896ac57889222ba864c852214ce3bcbf5df5e26d` to pin the tested candidate in the validation workflow.
- This branch appends the required `[dashboard-deploy]` trigger marker to the Cloudflare deployment workflow so that the deploy occurs only after this reviewed runner PR is merged. Deployment must independently pass the source validation, credential preflight and Cloudflare Worker/assets deployment steps. Do not start a production scan or enable public vacancy publishing as part of the UI deployment.
- No production scan or data publication has been initiated. Preserve backup #7 and all immutable recovery snapshots.


## 2026-11-21 — Source selector Cloudflare deployment completed
- Private PR #197 merged at `0a6ff517e251bac17af28476be2eb916de957e6c`. Exact candidate passed **518 private Python tests, 0 failures/errors/skips** plus frontend syntax/contracts, navigation, Applications, extension Bridge/RPC/Worker, retrieval regression and package validation in run `44842273835`; runner smoke passed.
- Runner PR #77 merged at `896ac57889222ba864c852214ce3bcbf5df5e26d` to pin the tested private candidate; PR #79 and #80 added the explicit deployment trigger; PR #81 corrected the push gate because squash commit messages did not preserve the token as expected. All runner PR validation checks passed.
- Cloudflare deploy run `44842889234` completed success. Dashboard Worker/assets version: `35850ba5-f9ca-4597-8693-f1c83de0489d`; Bridge Worker version: `30522581-9ea1-4ff9-8058-344b9df8870b`. Cloudflare credentials were present and not displayed. Existing Bridge encrypted secrets were preserved.
- The workflow reported a transient npm npx-canceled/missing-packages diagnostic, then successfully uploaded and deployed both Workers; final run conclusion was success. The public URL could not be independently opened through the available web viewer. Browser UX smoke test remains a user-facing verification item.
- No production scan, public vacancy publishing, Supabase/HF/R2 writes or recovery snapshot mutations were made. Preserve backup #7 and all immutable recovery snapshots.


## 2026-11-21 — Production shortlist persistence gate fix in review
- User requested the scanner must succeed before any shortlist persistence, the private identity-hash artifact must exist, telemetry/hash validation must remain mandatory, and no production scan may run until the fixes are verified.
- Runner PR #83: https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/83; branch `fix/production-scan-persistence-gates-20261121`. Scanner step now has `id: scan`; Supabase publisher requires successful scan plus both `private-source/public/jobs.json` and `private-source/private/retrieval-identity-hashes.json`; Hugging Face mirror requires `steps.persist-supabase.outcome == 'success'`. Added workflow contract tests.
- Current runner PR head: `49c3fa29ddc982ceca6437bb132a1c34c49b0654`. Full runner/private-source regression is NOT yet available; connector returned no PR-associated workflow runs or commit statuses. Do not merge until genuine full regression evidence is green.
- Private Cloro resilience change is in PR #199 (private repo). It isolates Cloro-only sanitized RuntimeError failures at the board boundary, bounded retry for transient 5xx/network errors, and no same-account retry for HTTP 429.
- No production scan, manual workflow dispatch, result persistence, public/private Space publication, R2 write or Cloudflare deployment was performed. Preserve backup #7 and all verified recovery snapshots unchanged.


## 2026-11-21 — Cloro resilience and Supabase persistence gate fixes merged
- Private source PR #199 merged to `main` as `941ade248e6f214bb573b8d296716d4bb28726bf`. The reviewed Cloro adapter isolates sanitized Cloro-only provider RuntimeErrors at the per-board boundary; preserves unexpected RuntimeErrors from other scanner components as fatal; retries transient HTTP 5xx/network failures once after one second; never retries HTTP 429 on the same account; rotates to the alternate configured account on authentication/quota rejection; applies board cooldown after all accounts rate-limit; and emits sanitized status/category only.
- Exact private candidate SHA `453298f4fed0404a4c9413e3dcb787deb4062c0b` passed the full read-only private regression in runner Actions run [44845207832](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44845207832): 524 Python tests (0 failures, 0 errors, 0 skips), frontend syntax/contracts, Bridge/RPC/Worker contracts, public retrieval regression, extension packaging/upload, private checkout cleanup. Runner workflow validation [44845207814](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44845207814) PASS; Supabase persistence gate tests 3/3 PASS; public runner smoke [44845207802](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44845207802) PASS (79 tests).
- Runner PR #83 merged to runner `main` as `741be58140fa89073f5bbe3a9a82b427f372e903`. The scanner step has stable `id: scan`; Supabase shortlist persistence now requires `steps.scan.outcome == 'success'`, `jobs.json` and the private retrieval identity-hash file; Hugging Face result mirroring requires successful Supabase persistence. Publisher-side telemetry and hash validation remains intact and fail-closed.
- Runner PR #83 candidate SHA `88eddfb04eb81740e863784486c8dc156dd1f648` passed its private regression run [44845207832](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44845207832), which tested private source candidate SHA `453298f4fed0404a4c9413e3dcb787deb4062c0b` against current private `main` and logged 524 tests, 0 failures/errors/skips; workflow validation [44845207814](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44845207814) and public smoke [44845207802](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44845207802) also passed.
- Both PRs were squash-merged only after exact candidate full regression, workflow gate tests and smoke checks passed. Both repositories' main branches were aligned to their PR base SHAs when the runs were triggered; post-merge main verification remains required.
- No production scan, Supabase write, HF/R2 archive write, public vacancy publication or Cloudflare deployment was started as part of this merge. Do not enable production publishing or dispatch a production scan until post-merge main validation and operational preflight. Preserve verified recovery backup #7 (run `44743162368`) and all immutable snapshots.


## 2026-11-21 — Post-merge main regression verified
- After PR #199 and #83 were merged, runner handover and private-source handover / operations reference were updated. Runner PR #83 post-merge non-publishing private regression run [44846062827](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44846062827) completed success.
- The canonical private scanner regression was explicitly re-triggered after the documentation-only handover/operations-reference updates via runner commit `df8abb651643b69e2252598acfd58495b113857f`. Post-merge main regression [44846145097](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44846145097) completed success: latest private `main` candidate `2f915bee89c4fc09d8255ec8111de97a2246b5d3`, 524 Python tests (0 failures/errors/skips), frontend, Bridge/RPC/Worker contracts, public retrieval tests, extension packaging and private cleanup all passed. Public runner smoke [44846145098](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44846145098) passed.
- This verifies merged source and runner CI only. No production scan, Supabase result write, HF/R2 publication, public vacancy publishing or Cloudflare deployment occurred. Keep production publishing disabled until separate credential/storage preflight and a deliberately controlled non-publishing dry run are reviewed. Preserve backup #7 and all immutable recovery snapshots.


## 2026-11-21 — BA + Cloro bounded non-publishing adapter smoke prepared
- User authorized proceeding with a bounded adapter verification before any dashboard production scan.
- Planned runner-only manual workflow: at most one BA Jobsuche v6 search request (one page, 10 rows, zero detail requests) and one Cloro Google Monitor query using only the first configured key (one configured key exposed to the test process; no alternate-account fallback). Both adapters execute in an isolated runner workspace; output is sanitized counts/status/response-shape only.
- The workflow must not invoke radar.py, run the full retrieval pipeline, write Supabase/HF/R2/Cloudflare, publish vacancies, or modify production data. It must require explicit workflow_dispatch confirmation and use the private source read token only to checkout the exact private main revision.
- The BA endpoint is a community-documented, unofficial interface. Stop on HTTP 401/403/429; do not bypass controls or retry. Cloro uses the already corrected payload contract; no retry/fallback in this smoke harness.
- Current production state remains unchanged. Do not start a dashboard scan until the bounded adapter smoke and review are complete. Preserve verified backup #7 and every immutable recovery snapshot unchanged.


## 2026-11-21 — Bounded BA + Cloro non-publishing adapter smoke workflow added
- Branch `test/ba-cloro-nonpublishing-smoke-20261121` adds `.github/workflows/ba-cloro-adapter-smoke.yml`, manual-only with required boolean confirmation and a selectable private source ref.
- The workflow checks out private source read-only, imports only `germany.fetch_german_jobs` and `cloro_search.fetch_cloro_jobs`, and calls each adapter directly. BA is capped at one page / 10 rows / zero detail requests. Cloro receives only `CLORO_API_KEY_1`; the harness hard-blocks a second network attempt, so neither retry nor account fallback can issue another request.
- The test validates recognized response structure and reports only HTTP category, response-shape marker, row counts and request count. It never logs keys, payload bodies, URLs, titles, employers, or snippets. It does not call the full scanner, assessment pipeline, persistence, publishing, or deployment.
- Live requests are not yet run. Merge the reviewed workflow PR first, then manually dispatch it on `main` with `confirm_live_adapter_requests=true` and `private_ref=main`. The connected GitHub actions toolset has no workflow-dispatch operation, so assistant cannot dispatch this manual workflow. Do not dispatch `production-scan.yml`.
- No production scan, Supabase/HF/R2 write, public vacancy publication, Cloudflare deploy, or recovery snapshot mutation occurred. Preserve backup #7 and all immutable snapshots.


## 2026-11-21 — BA + Cloro bounded adapter smoke workflow merged; live run pending
- Runner PR #84 merged to `main` at `cf78061e2884dd1a9b217325312b17903848bacb`; source handover PR #200 merged at `6bf2c38dcc42feea545ec9f644564fc533b1de93`.
- New manual workflow: `.github/workflows/ba-cloro-adapter-smoke.yml`. It requires `confirm_live_adapter_requests=true`, checks out private source read-only, and directly calls the two adapters. BA: one Jobsuche v6 request, page 1, max 10 rows, zero detail calls. Cloro: only `CLORO_API_KEY_1` is exposed and the harness hard-blocks a second network attempt. It validates response shapes and emits sanitized counts/status only.
- Static validation performed before merge: embedded Python parsed successfully with Python AST; workflow YAML parsed successfully. Existing private main full regression remains the last verified code regression (run `44846145097`, 524 tests, zero failures/errors/skips); no scanner source code changed in this PR.
- **Live provider test has NOT run yet.** GitHub connector does not expose workflow dispatch. Operator must manually run the workflow from runner `main`, set `confirm_live_adapter_requests=true`, and keep `private_ref=main`. This makes at most one BA request and one Cloro request; no retries, persistence, publication, or deployment. Do not dispatch `production-scan.yml`.
- No production scan, Supabase/HF/R2 write, public vacancy publication, Cloudflare deploy, or recovery snapshot mutation occurred. Preserve verified backup #7 and every immutable snapshot.


## 2026-11-21 — Live BA + Cloro bounded adapter smoke PASS (user-confirmed Actions run #1)
- User supplied screenshots of GitHub Actions workflow **BA + Cloro adapter smoke (non-publishing) #1**, manually triggered on runner `main`, commit prefix `ab76bae`; overall workflow status Success, duration 14 seconds.
- Expanded step log explicitly reports: `BA: PASS (HTTP success; response_shape=recognized; provider_rows=10; accepted_rows=10; requests=1)`; `Cloro: PASS (HTTP success; response_shape=recognized; provider_rows=9; accepted_rows=9; requests=1)`; final harness line: `PASS: bounded BA + Cloro adapter smoke; at most one network request per adapter.`
- Workflow also explicitly reports: `No scanner run, result persistence, publication, or deployment was performed.` The explicit live-request confirmation gate was skipped (expected for the successful confirmed dispatch); private checkout, Python setup, adapter step and cleanup succeeded.
- This proves one live request per provider returned HTTP success and a recognized provider response shape, with 10 BA provider rows/10 accepted adapter rows and 9 Cloro provider rows/9 accepted adapter rows. It is a bounded adapter connectivity/parsing check only; it does not prove broader geographic/role coverage, freshness, deduplication quality, CV match quality, or full-scan reliability.
- **Production dashboard scan is not automatically authorized by this smoke.** Before any real scan, confirm the user intends to persist production scan results; select BA and Cloro only in the dashboard provider picker; keep public vacancy publishing disabled. Runner persistence gates merged in PR #83 require successful scan plus jobs and identity-hash artifacts before Supabase persistence, and HF mirror only after Supabase success. No full scanner or production data write was part of this test.
- Both AI handovers updated after the live test. Preserve verified backup #7 and all immutable recovery snapshots unchanged.


## 2026-11-21 — HF Space browser connection error traced; canonical Cloudflare UI is safe route
- User screenshot from `https://sidmed-engineering-career-radar.static.hf.space` shows the generic frontend error `Cloudflare connection/CORS failed for origin ...`.
- Read-only inspection confirms the exact static HF origin is already explicitly allowed in current private `cloudflare/dashboard-lock-worker.js` and `cloudflare/search-worker.js`; Cloudflare live script downloads for both deployed Workers also contain the exact origin and CORS logic. Do not add wildcard CORS or relax the origin/header allowlists.
- Existing live CORS smoke run [44752329275](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44752329275) verified the exact HF origin against `/api/bridge/health`: preflight 204 with allow-origin/method/header, GET 200 with exact allow-origin, and unapproved origin 403 without allow-origin. This proves server-side CORS worked at that time; it does not prove the user's current browser network path.
- Current HF Space `index.html` was read via Hub filesystem and is an older UI: its Search Jobs form has no provider selector. Current private GitHub `public/index.html` / `public/frontend-v3.js` contain the 23-provider selector and explicit source payload. The HF Space is therefore stale relative to the current Cloudflare deployment/source. Prior storage guardian records the Space at 999,931,761 / 1,000,000,000 bytes (99.99%) and explicitly prohibits uploading/deleting historical Space files; do not attempt a Space sync or overwrite.
- Current frontend `api()` catches every fetch rejection and labels it as CORS, without distinguishing browser CSP/connect-src, DNS/TLS, extensions, transient network failure, or true CORS. The screenshot's generic message alone is not proof of a CORS policy rejection.
- Current Cloudflare control-plane read-back shows dashboard Worker latest deployment 100% traffic: version `823dd9f9-f972-405b-a49b-79931ac9eb12`, created `2026-11-21T00:47:32Z`; Bridge latest deployment 100% traffic: version `30522581-9ea1-4ff9-8058-344b9df8870b`, created `2026-11-21T00:18:39Z`. Live Worker script sources contain the explicit HF origin allowlist. No Cloudflare configuration was changed in this investigation.
- Safe immediate route: open the canonical Cloudflare-hosted dashboard `https://career-radar-dashboard.happytiswis.workers.dev/`. It serves the current UI and its API is on the same origin, avoiding the HF-to-Cloudflare cross-origin browser path. Use its BA + Cloro source selector; do not use the stale HF Space UI for the scan.
- Do not launch a scan until the user confirms the canonical dashboard loads and its Test connection succeeds. No production scan, Supabase/HF/R2 write, publishing, Cloudflare deployment, HF file write, or recovery snapshot mutation occurred. Preserve backup #7 and all immutable snapshots.


## 2026-11-21 — User reports canonical Worker health URL does not load
- User reports that direct navigation to `https://career-radar-dashboard.happytiswis.workers.dev/api/bridge/health` does not load. This is stronger evidence than the original frontend banner: a top-level browser navigation is not subject to CORS enforcement, so do not diagnose this as CORS alone.
- Fresh Cloudflare control-plane read-back confirms BOTH `career-radar-dashboard` and `career-radar-bridge` Worker subdomains are enabled (`enabled:true`, previews enabled). Dashboard latest deployment `823dd9f9-f972-405b-a49b-79931ac9eb12` remains at 100% traffic; Bridge latest deployment `30522581-9ea1-4ff9-8058-344b9df8870b` remains at 100% traffic. No deployment/configuration change was made.
- The dashboard Worker's live script still contains the explicit HF origin allowlist and OPTIONS handling, then proxies to the Bridge service binding. Prior CORS smoke [44752329275](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44752329275) is historical only; it does not establish present public endpoint reachability.
- The frontend still mislabels every fetch rejection as CORS. A direct-navigation failure must first be classified by the browser's exact error (e.g. DNS/TLS/timeout, Cloudflare 10xx, HTTP 502/503/404). Do not change allowlists, rotate secrets, disable security, re-enable/disable subdomains, or redeploy blindly.
- Runner PR #86 adds a separate live CORS HTTP regression test on branch `test/live-hf-origin-cors-20261121`; it is not merged and has no verified passing check yet. Do not merge on the basis of its existence.
- Next required diagnostic: obtain the exact browser result when opening the health URL (error code/page or raw response). If it loads JSON, investigate the cross-origin request/preflight and browser CSP/extensions; if it fails before HTTP, investigate public workers.dev DNS/TLS/edge reachability; if it returns 502/503, inspect Worker invocation logs and Bridge service binding/secret configuration. No production scan or data write until resolved.


## 2026-11-21 — Dashboard health check recovered; user-started production scan #44849069993 in progress
- User screenshots now show the dashboard green banner `Cloudflare health API returned success.` and direct browser navigation to `https://career-radar-dashboard.happytiswis.workers.dev/api/bridge/health` returning `{"ok":true,"configured":true}`. Connection health is now verified from the user's browser; prior direct health failure is no longer current.
- User reports scan run `44849069993`. GitHub Actions live job query confirms job `scan-score-publish` is `in_progress`; scanner step `Find jobs and compare against private master CV` (#14) is currently in progress. All setup/preflight steps 1–13 completed successfully, including Supabase/storage preflight, CV/matching engine, historical metrics load, and sanitized Cloro credential readiness.
- This is the full `production-scan.yml` workflow, not the bounded non-publishing adapter smoke. Its workflow defaults: `enable_production_publish=false` (public publication remains off unless both repo variable and explicit dispatch input are true); `enable_private_archive=true`; `enable_private_telemetry=true`; `enable_private_results=true`. Therefore private R2 archiving, aggregate Supabase telemetry, and shortlisted-job Supabase persistence/private HF mirror may occur after successful scan, subject to storage gates. Do not claim the run is non-publishing/private-write-free.
- Scanner environment explicitly sets `CLORO_SEARCH_ENABLED=true`. However the old HF Space frontend has no visible provider selector and the GitHub Actions job summary doesn't expose the dispatched `search_request` value through the available tools; BA+Cloro-only selection is NOT yet proven. Do not infer that this run isolated to BA and Cloro. Review sanitized source metrics / run summary after completion; if source IDs cannot be confirmed, treat it as a broader/default-profile scan.
- No action taken to cancel or rerun. Do not start another scan. Monitor run #44849069993 to completion and inspect source-level counts/failures, storage gates, Supabase persistence and publication outcome. Preserve backup #7 and all immutable recovery snapshots.


## 2026-11-21 — Production scan #44849069993 completed; BA/Cloro source yield reviewed
- Run completed successfully in 6m52s. Aggregate source-yield artifact `career-radar-source-yield` (artifact ID `14683783907`) downloaded and verified (`verification.verified=true`, run ID matches).
- This was a broad/default-profile scan across 17 source families, NOT an isolated BA+Cloro-only test. Therefore these are live production-scan observations, not a controlled A/B adapter test.
- BA (`bundesagentur`): 290 attempted units, 290 successful, 0 errors, 3,169 raw URLs, 2,241 unique postings. Per-unit success rate 100%.
- Cloro: 8 attempted units, 6 successful, 2 errors, 37 raw URLs / unique postings. Per-unit success rate 75%; source failure counter records `cloro: 2`. The artifact does not retain per-board error detail, so root cause of the two failures remains unknown. Prior bounded adapter smoke passed (one request, 9 provider rows, 9 accepted rows); this scan proves Cloro yields postings but not complete reliability.
- Global retrieval funnel: 27,674 raw URLs; 24,931 unique canonical URLs; 24,931 usable postings; 25,671 posting identities; 24,522 newly discovered; 1,149 historically seen; 606 cross-source duplicate URLs; 2,003 same-run duplicate postings deduplicated; 534 same-run duplicate postings merged; 0 cross-source duplicate postings merged.
- Query accounting: 570 planned / 500 attempted / 500 successful / 0 failed / 70 skipped / 0 unconfigured. Career tracks: 35 allocated, 33 with retrieval results. Scanner collected 13,386 postings and shortlisted 95; AI telemetry: 50 queued, 39 assessed, 50 terminal outcomes (verify interpretation before making stronger claims).
- Persistence/archive: private Supabase telemetry verified; shortlist finalized and verified in Supabase (13,386 collected, 95 shortlisted, 17 source metrics). Private R2 archive `history/run-44849069993.json` verified (954,944 bytes). No public publication authorized. Hugging Face private Space mirror refresh correctly blocked by Storage Guardian: Space repository usage 999,931,761 bytes against 1,000,000,000 quota; projected 1,002,976,009 bytes; stop threshold 950,000,000. No historical Space data deleted. Supabase DB admission allowed at 20.52% usage.
- Node.js 20 deprecation annotation is non-blocking. Separate warning is the capacity guard; do not delete Space history or bypass guard. Need plan a safe capacity cleanup only after inventory and verified recovery snapshot policy; never overwrite/delete immutable recovery snapshots.
- Next: investigate Cloro's two board-level failures from private scanner logs if retained (ephemeral workspace was removed, so artifact alone cannot identify boards/errors); add sanitized per-board failure classification to future aggregate telemetry. Run a controlled BA+Cloro-only validation only after dispatch path explicitly guarantees source selection; don't claim this run was isolated.


## 2026-11-21 — Run 44849069993 shortlist, Cloro, AI and storage root causes; diagnostics hardening candidate
- Read-only Supabase inspection of `career_radar_private.scan_runs` confirms the saved request was `min_score=70` (not 45), region Germany, seniority entry_junior, all 23 source families, no explicit cities/roles/tracks. Dashboard UI default is 45; do not assume this particular dispatched run used 45. Preserve the exact request in future scan diagnostics.
- Exact shortlist funnel: 13,386 collected; 1,072 reached the user-filter stage; 960 were rejected by score as first blocker (961 total score rejection counts, overlapping with other criteria); 3 first blocked by location; 3 first blocked by seniority; 4 first blocked by opportunity type; 62 candidates had multiple rejection reasons; 102 remained after user filters; freshness gate then excluded 7 older-than-90-day postings (0 confirmed expired), leaving 95. Thus 95 is explained primarily by min score 70 and upstream role/CV/geography gates, not by the final score threshold alone. `rule_screen_rejected=10,890` and `geography_rejected=2,713` are record-level counts across grouped duplicate-source records and must not be added as disjoint unique-posting counts.
- Cloro exact failures: board IDs `google-serp-7` (UAV Engineer) and `google-serp-8` (CAMO Engineer) both ended `HTTP 429` / `Cloro account rate limited`; 6/8 query units succeeded and yielded 37 unique postings. Existing scanner logs do not retain the per-key outcome split for this run. Never retry the same rate-limited account or bypass provider limits.
- AI exact metrics: queue=50, valid assessments=39, non-assessed=11, deadline not exhausted. 85 provider attempts: Inception Mercury 34 valid / 13 invalid JSON; OpenRouter 5 valid / 2 failures (one HTTP 429, one HTTP 503); NaraRouter (bynara) 0 valid / 31 HTTP 500. The 31 repeated Nara 500s show missing server-error cooldown. Scanner generated a reconciled aggregate terminal-outcome ledger, but `publish_supabase_jobs.build_diagnostics` omitted it from persisted `safe_event`, so terminal categories were not saved.
- HF storage: target Space repo measured 999,931,761 / 1,000,000,000 bytes (99.99%); incoming mirror payload 3,044,248 bytes would project to 1,002,976,009, exceeding the per-Space repository cap and the 950,000,000-byte stop threshold. Account-wide private namespace use was 999,931,761 / 100,000,000,000 bytes (1.0%); this is a separate quota. Guardian correctly blocked the Space mirror. No historical data or recovery snapshots were deleted. Supabase/R2 remain the verified persistence/archive path; do not bypass the guard or prune snapshots.
- Source PR #202 branch `fix/scan-yield-ai-cloro-diagnostics-20261121` adds per-board Cloro request/slot/result/failure diagnostics without query text or credential values; persists the aggregate AI terminal ledger and explicit score filter counts to private Supabase; keeps board-level details out of the public aggregate artifact; and cools AI providers after HTTP 5xx for the rest of the batch. Added unit tests for Cloro 429 diagnostics/privacy, persisted diagnostic fields, and AI 5xx cooldown. Regression is pending; do not merge until a genuine full private suite passes.
- Runner branch `feat/ba-cloro-isolated-scan-20261121` adds manual workflow `.github/workflows/ba-cloro-isolated-scan.yml`: exact source set `[ba, cloro]`, score 45, no AI credentials, no Supabase/HF/R2 credentials, no persistence or publication; uploads only aggregate counts and sanitized Cloro board diagnostics. Runner private-regression workflow has a marker mapping so merge can trigger full tests against the source candidate. Manual live dispatch remains pending after reviewed PR merge; GitHub connector cannot dispatch workflows.
- Preserve verified recovery backup #7 and all immutable snapshots. No new production scan, external persistence, public publication, Cloudflare/HF deployment, Space deletion, or snapshot mutation was performed during this diagnostic/code work.


## 2026-11-21 — Read-only Hugging Face Space file inventory and CI gating status
- Read-only `hf_fs ls hf://spaces/Sidmed/engineering-career-radar --recursive` returned 34 current files/directories; visible file payload sizes sum to 83,530,111 bytes (~83.5 MB). The 13 visible `history/run-*.json` snapshots sum to 79,930,361 bytes (~79.9 MB); largest visible snapshot is 16,296,558 bytes. Several visible objects are Git LFS-backed.
- This current-tree inventory is far below the measured repository storage of 999,931,761 / 1,000,000,000 bytes. Approximate gap is 916,401,650 bytes. The file listing does not expose historical Git object/ref/LFS revision accounting, so prior versions/history are the likely source but exact breakdown is unverified. Do not delete current or historical files, rewrite Git history, run garbage collection, or prune any verified recovery snapshot. A fresh private Space with a clean Git history and Supabase/R2-backed archives is a possible future migration path, but no new Space was created and no migration was started.
- Source diagnostics PR #202 remains OPEN pending a genuine full private regression. Runner PR #87 (isolated BA+Cloro workflow) and PR #88 (candidate-routing infrastructure) are merged. Runner PR #89 is open to trigger the private regression against source candidate branch; workflow run is not yet visible in the connector. If no run appears, manually dispatch `Private scanner regression and extension package validation` with `private_ref=fix/scan-yield-ai-cloro-diagnostics-20261121`, `private_base_ref=main`. Do not merge source PR #202 until full suite passes.
- After source PR #202 is merged, manually dispatch `BA + Cloro isolated full retrieval (non-publishing)` with `confirm_live_provider_requests=true`. It runs exact sources `ba` + `cloro`, min score 45, no AI credentials, no Supabase/HF/R2 credentials and no persistence/publication steps. It emits only an aggregate artifact plus sanitized Cloro board diagnostics.
- No Space file changed, no history/snapshot deleted, no production scan or data write started by this inventory/CI orchestration.


## 2026-11-21 — Cloro/AI diagnostics implementation merged after full candidate regression
- Source PR #202 merged to private `main` at `d9d3b99b2c7a6bf99afa82920993ee8679fe6af4` after runner private regression run `44851317658` tested exact candidate SHA `64b651a0474e86d7946fae75e6cedf8fc9fc1fd8` against current base: 527 Python tests, 0 failures/errors/skips; frontend syntax/contracts, extension Bridge/RPC/Worker contracts, public retrieval regression, extension packaging and private checkout cleanup all passed.
- Runner PR #87 merged isolated BA+Cloro non-publishing workflow. Runner PR #88 and #89 merged private candidate regression routing. Runner PR #90 is open to run the same full suite against exact post-merge private `main`; wait for its check before declaring post-merge regression complete.
- Manual isolated full retrieval workflow is available at `.github/workflows/ba-cloro-isolated-scan.yml`; after post-merge regression, dispatch with `confirm_live_provider_requests=true`. It uses exact sources BA + Cloro, score45, no AI credentials, no Supabase/HF/R2 credentials, no persistence/publication, and uploads aggregate-only results with private-safe per-board diagnostics.
- Hugging Face current working-tree inventory: 34 files, 83,530,111 bytes; 13 visible history snapshots sum to 79,930,361 bytes. Repository meter is 999,931,761 bytes, leaving an unverified ~916,401,650-byte gap likely in old Git/LFS history. No files or snapshots changed. Never rewrite history or prune snapshots to free quota.


## 2026-11-21 — Post-merge full regression PASS for private main
- After source PR #202 merged, runner PR #90 triggered full regression against exact private `main` SHA `53b7721aa7b9199a409c9896d104dbbcf98e5c3f` (this includes the post-merge AI handover update). Workflow run `44851473811`, full-private-suite completed success: 527 Python tests, 0 failures, 0 errors, 0 skipped; frontend syntax/contracts, extension Bridge/RPC/Worker contracts, public retrieval regression, extension packaging/upload and private checkout cleanup all succeeded.
- Runner PR #90 merged at `469e2ff79a94b29035a3c9f6d125a71df312ca94`, preserving the post-merge regression routing.
- Candidate regression before merge also passed on SHA `64b651a0474e86d7946fae75e6cedf8fc9fc1fd8` in run `44851317658` (527 tests, zero failures/errors/skips). Thus both pre-merge candidate and post-merge main regression are verified.
- Remaining manual operation: dispatch `BA + Cloro isolated full retrieval (non-publishing)` from runner Actions with `confirm_live_provider_requests=true`. It is an explicit live retrieval test, not production scan; exact sources BA+Cloro, min_score45, no AI, no Supabase/HF/R2 credentials, no persistence or public publication. Review the aggregate-only artifact to confirm both families returned postings and per-board Cloro statuses.
- Production scan #44849069993 remains the last broad scan; no additional production scan, data write, public publication, HF file mutation, or recovery snapshot mutation occurred during these fixes.


## 2026-11-21 — Isolated BA + Cloro live retrieval run #44851791276: partial provider success
- Manual non-publishing isolated workflow completed on runner main with exact source selection `ba` + `cloro`, min_score=45, Germany, entry_junior. Aggregate artifact ID `14685198999` was downloaded and inspected. No Supabase/HF/R2 persistence or public vacancy publication occurred; no raw job rows, URLs, descriptions, CV data, or credentials were included in the artifact.
- BA: 290/290 units successful, 0 errors, 3,169 raw URLs, 2,241 unique canonical URLs/postings.
- Cloro: 2/8 units successful, 6 errors, 13 raw URLs and 13 unique postings. Per-board diagnostics prove all six failed boards (`google-serp-1`, `-2`, `-4`, `-5`, `-7`, `-8`) got HTTP 429 from both credential slots (12 rate-limit responses total). Board `google-serp-6` succeeded with slot 2; `google-serp-3` succeeded with slot 1 after one transport retry. Prior HTTP 200 credential smoke only proved authentication, not sufficient quota. Do not rotate/retry around 429; check provider quota/account plan or ask Cloro support. Do not run another live Cloro test immediately while rate limits may persist.
- Combined: 2,254 usable unique postings (2,241 BA + 13 Cloro), 3,182 raw URLs, 928 same-run duplicate postings deduplicated, 503 duplicate postings merged, 0 cross-source duplicate URLs detected, 608 shortlisted. Search profile min_score=45. Filter diagnostics: rule_screen_rejected=1,591; geography_rejected=0; before_user_filters=950; after_user_filters=813; seniority rejection count=34 (first blocker 11); opportunity_type=11 (first blocker 10); score=116 (first blocker 116); seniority_excluded=138. Artifact does not include freshness gate breakdown, so do not infer why 813 became 608 without additional diagnostics. Historical novelty is unknown: private archive identity registry unavailable, `newly_discovered_vacancies=null`.
- Workflow #1 was green due an insufficient pass gate (it only required BA and Cloro each return >0 postings). This incorrectly described partial Cloro success as a complete provider pass. Runner PR #91 (`fix/isolated-scan-require-full-provider-coverage-20261121`) changes gate to require every attempted unit for both BA and Cloro succeed with zero errors and non-zero unique postings. Artifact upload occurs before the strict gate so partial outcomes remain inspectable. PR #91 is open; do not merge until appropriate CI/workflow validation passes. No new live requests were made by this change.
- Current Cloro result is a partial failure, not full pass. No production scan, persistence, publication, deployment, Space mutation, or recovery snapshot change occurred. Preserve all verified recovery snapshots.


## 2026-11-21 — Isolated test gate correction follow-up
- Artifact for run `44851791276` was inspected directly. It confirms Cloro six board failures with HTTP429 from both credential slots (12 rate-limit responses), and success only on `google-serp-3` and `google-serp-6`. BA remained 290/290 successful. Treat run as BA PASS / Cloro PARTIAL, despite the initial workflow green status.
- The aggregate artifact shows `after_user_filters=813` and final shortlist=608 (drop of 205). It did not include `freshness_gate_diagnostics`, so the exact cause of that drop cannot be proven from this artifact. Scanner code shows freshness gate is applied after specialist review; a follow-up workflow change now includes the freshness breakdown in future isolated artifacts.
- Runner PR #92 (`fix/isolated-scan-require-full-provider-coverage-v2-20261121`) corrects the workflow pass gate to require every attempted BA and Cloro unit to succeed with zero errors, preserves aggregate artifact upload before gate failure, and includes freshness diagnostics. PR #91 was closed as superseded. PR #92 is open, mergeable, awaiting validation; do not merge until workflow validation is satisfactory.
- Do not immediately repeat live Cloro calls while provider HTTP429 limits may remain active. First check account quota/plan or provider response/reset guidance. No production scan, persistence, publication, deployment, Space mutation, or recovery snapshot mutation was performed.


## 2026-11-21 — TinyFish + Firecrawl integration work authorized; secrets provisioned
- User confirmed GitHub Actions repository secrets `TINYFISH_API_KEY` and `FIRECRAWL_API_KEY` were added to `happytiswis-sudo/engineering-career-radar-runner`. Screenshot shows both names and recent timestamps; values were not viewed, retrieved, or logged.
- Planned integration (dedicated feature branches and reviewed PRs only): TinyFish Search as an optional source family; TinyFish Fetch for bounded enrichment of discovered public vacancy URLs; Firecrawl as a strictly bounded fallback only when TinyFish Fetch cannot retrieve content. No TinyFish Agent or Browser API for bulk vacancy collection.
- Provider contracts checked against current official docs: TinyFish Search GET `https://api.search.tinyfish.ai` with `X-API-Key`, `query`, optional DE/de geo targeting; results contain title/snippet/url. TinyFish Fetch POST `https://api.fetch.tinyfish.ai` with `X-API-Key`, maximum 10 URLs/request, markdown output. Firecrawl scrape POST `https://api.firecrawl.dev/v2/scrape` with Bearer key; preflight GET `/v2/team/credit-usage` exposes remainingCredits/planCredits. TinyFish Search and Fetch are documented as credit-free; Search free plan limit 30 requests/minute. Firecrawl scrape baseline is 1 credit/page; search 2 credits per 10 results. Use a hard small per-run page cap and reserve threshold; never scrape every vacancy indiscriminately.
- Planned code scope: source adapter + bounded query planner + diagnostics + tests; include source id `tinyfish` in request validation, dashboard picker and Cloudflare Worker validation/default handling; inject only the two new secrets into the production scan step; add a dedicated non-publishing provider preflight/adapter smoke workflow that does not include persistence/publication secrets. Do not change production deployment, Supabase schema, Hugging Face Space, R2, or recovery snapshots as part of this work.
- No live provider requests, production scan, persistence, publication, deployment, or snapshot mutation performed during planning. No credentials were read by the assistant.


## 2026-11-21 — TinyFish + Firecrawl runner integration candidate
- User screenshot confirmed repository Actions secrets `TINYFISH_API_KEY` and `FIRECRAWL_API_KEY` exist in `happytiswis-sudo/engineering-career-radar-runner`; values were not retrieved or exposed.
- Feature branch `feat/tinyfish-firecrawl-integration-20261121` injects the two secrets only into the production scanner process and adds a manually gated `.github/workflows/tinyfish-firecrawl-isolated.yml` for TinyFish-only bounded validation. It checks Firecrawl remaining credits via read-only API preflight, runs TinyFish-only scanner with no AI/persistence/publication secrets, uploads only sanitized aggregate metrics, and shares the production scan concurrency group to prevent concurrent credit reservations.
- Runner test `tests/test_tinyfish_firecrawl_workflow.py` verifies production secret wiring, manual/non-publishing isolation, Firecrawl preflight, strict serialization, and private candidate routing. Runner workflow validation is extended to parse the new workflow and execute the contract test.
- Companion private source candidate is `feat/tinyfish-firecrawl-retrieval-20261121`. Runner PR validation routes the private regression to that exact branch when PR title includes `[tinyfish-firecrawl-candidate]`. No API calls have yet been made. Do not manually run the new provider workflow until CI and private regression pass.
- No production scan, deployment, Supabase/HF/R2 write, vacancy publication, Space mutation, or recovery snapshot change occurred. Keep all verified recovery snapshots untouched.


## 2026-11-21 — TinyFish candidate CI correction follow-up
- Runner PR #93 initial checks exposed test-contract assumptions: immutable fallback SHA assertion now also accepts the PR-title-routed exact private feature branch while retaining the immutable fallback; outdated private-path trigger assertion was replaced with a check that the runner PR calls the private candidate regression; workflow YAML validation now checks the manual gate semantically rather than relying on PyYAML scalar formatting.
- Initial exact private candidate regression ran 534 tests with 2 failures: Firecrawl test state was asserted after its mock patch context restored globals, and the embedded frontend bundle was not synchronized with the updated dashboard JS. Both have been fixed on private feature branch; source metrics now also include sanitized TinyFetch/Firecrawl failure categories.
- Latest public runner smoke after contract-test corrections passed. Fresh runner workflow validation and private candidate regression are pending after the latest branch updates. No live provider API calls, production scan, persistence, publication, deployment, or recovery snapshot mutation occurred.


## 2026-11-21 — TinyFish + Firecrawl integration merged
- Runner PR #93 merged to runner `main` as `c53f4fd632c97b7dac05ec6301ec000d5b070aa5`. It adds `TINYFISH_API_KEY` and `FIRECRAWL_API_KEY` to the production scanner environment, a manually gated isolated TinyFish-only validation workflow, read-only Firecrawl quota preflight, serialized concurrency, aggregate-only artifact, and CI safeguards. No secret values are stored in source or handover.
- Private source PR #203 merged to source `main` as `734493b9aca85d6a32db2427bd6e2455a132db1a`. TinyFish remains explicit opt-in (source ID `tinyfish`), with role-aware search planning, TinyFish Search and selective Fetch, bounded Firecrawl fallback, quota protection, sanitized source metrics, dashboard source selector, Worker allowlist and tests.
- Exact private feature candidate `e9786c628bcf2a06ca670f6b95ab93dce4dc4534` passed full regression through runner PR #93 run `44899043564`: 534 Python tests, 0 failures/errors/skips; workflow validation and credential-presence check passed; public runner smoke passed. The private regression checked out the exact branch and reported the exact SHA.
- No live TinyFish/Firecrawl requests, production scan, Supabase/HF/R2 writes, public vacancy publication, deployment, or recovery snapshot mutation has occurred. Do not assume provider functionality is live-verified until the isolated workflow completes successfully. Next step: post-merge regression against private main, then user-authorized bounded provider validation; only then decide whether to enable TinyFish in a production search. Keep TinyFish disabled by default and Firecrawl under the configured budget.


## 2026-11-21 — TinyFish dashboard deployed to Cloudflare
- Separate deployment-trigger PR #94 merged to runner main as `d8f17dfdc92b1d7610fd2111efd46cad8404ef0f`; it adds only the repository-standard `[dashboard-deploy]` marker to the deploy workflow.
- Cloudflare deploy workflow run `44899504286` completed SUCCESS. Dashboard Worker `career-radar-dashboard` deployed version `f011565f-d7ca-4f89-84b9-63bbc59d5f40`; search Bridge Worker `career-radar-bridge` deployed version `bf1c1259-53da-4c1e-97d7-ea332f7e1d49`. Both deploy steps, source validation, Cloudflare credential check, and cleanup passed.
- Post-deploy fetch of `https://career-radar-dashboard.happytiswis.workers.dev/` returned the Career Radar workspace page. Fetch of the deployed `/frontend-v3.js` asset confirmed the source picker includes `tinyfish` / “TinyFish Search + Fetch”. The deployed dashboard is now ready to select the new source, but live provider functionality is not yet proven.
- PR #94 runner validation passed: 534 Python tests, 0 failures/errors/skips; runner validation, credential presence, and public runner smoke all succeeded.
- The isolated provider workflow `.github/workflows/tinyfish-firecrawl-isolated.yml` has not been dispatched. The connected GitHub action toolset does not expose workflow_dispatch, and no authenticated GitHub browser profile is connected. A user click is required to run the bounded live provider test at `https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/workflows/tinyfish-firecrawl-isolated.yml` with `confirm_live_provider_requests=true`. That workflow does not publish, persist to Supabase, write HF/R2, or run AI assessment; it only emits aggregate metrics. It is serialized against production scans.
- No production scan, Supabase write, HF/R2 archive write, vacancy publication, or recovery snapshot mutation occurred. Do not claim TinyFish/Firecrawl live API validation PASS until the isolated workflow succeeds. Keep TinyFish opt-in and do not enable it in scheduled/default scans.


## 2026-11-21 — TinyFish isolated provider validation failure diagnosis
- User supplied screenshot of GitHub Actions run `provider-validation`; live run is runner workflow_dispatch run [44899949742](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44899949742), head SHA `b6bf9a51b73d7c77dfc000bb2866b3fcf419fbe8`. Public runner smoke run `44899621038` on the same SHA passed.
- Job `136833551602` passed checkout of public runner and private source `main` read-only, isolated TinyFish-only request profile verification, Python 3.12 setup, Hub client install, credential-presence check, and Firecrawl quota preflight. Preflight showed TinyFish key present and Firecrawl `remainingCredits=1025`, `planCredits=1000` (provider account response; unexpected remaining > plan is not itself a failure).
- The only failing step was `Run bounded TinyFish-only scanner (no AI or persistence)`, which ran `python radar.py` and exited 1 after ~9.5 s. Workflow redirected stdout/stderr to `$RUNNER_TEMP/tinyfish-isolated-scan.log`, then emitted only generic error and deleted the private checkout. Thus actual exception is irretrievably absent from this run's logs; do not infer it is invalid credentials. The summary/upload/pass-gate steps were skipped.
- Code inspection: private source `main` contains adapter `tinyfish_search` calling TinyFish Search `GET https://api.search.tinyfish.ai` with `X-API-Key`, and Fetch `POST https://api.fetch.tinyfish.ai`; role-aware planner in `deep_search.tinyfish_boards` makes 3 focused / 6 deep boards. Adapter catches ordinary HTTP/network/schema errors at provider-call level and should surface categorized failures rather than exit; therefore likely failure may be outside that catcher (scanner setup / dependency / runtime exception), but root cause remains unconfirmed.
- Important discovery for follow-up: isolated workflow sets `SEARCH_REQUEST` with roles and source `tinyfish`, then expects output `public/jobs.json`. No production data writes are intended; workflow contains no Supabase/HF/R2/AI secrets and holds production concurrency lock. Keep TinyFish opt-in and keep Firecrawl strictly budgeted.
- Fix must improve diagnostic quality without printing raw vacancy records, URLs, snippets, CV data, credentials, or provider response bodies. In failure handler print sanitized exception class/category and write a tiny redacted diagnostic to job summary; never artifact the raw log. Retain private checkout cleanup and no-persistence guard. Ensure scanner creates requested output in isolated mode or summary gracefully identifies missing output.
- Next safe step: create dedicated runner branch from current main to make the isolated workflow produce sanitized exception diagnostics; add regression assertions in `tests/test_tinyfish_firecrawl_workflow.py`; open reviewed PR; wait for runner workflow validation and full private regression route. After merge, rerun only the isolated non-publishing provider validation, then inspect aggregate-only summary. Do not rerun live calls blindly until diagnostics improve.
- No new provider calls, production scan, AI assessment, Supabase/HF/R2 persistence, public publication, deployment, or recovery snapshot mutation occurred during this diagnosis. Preserve all verified recovery snapshots.


## 2026-11-21 — TinyFish failure diagnostics candidate
- Current isolated provider run `44899949742` failed in `python radar.py`; its actual exception was hidden because stderr/stdout were redirected to a temporary log and then deleted during cleanup. Credential presence and read-only Firecrawl quota preflight had passed.
- Candidate branch `fix/tinyfish-isolated-sanitized-diagnostics-20261121` starts from runner main `dd4645751dd775774dd10282668f52721f65a5a0`. The workflow patch will surface only a scrubbed exception class/category, no raw exception message or traceback locals, and retain raw scanner output only in runner temp for the lifetime of the job. No raw log/artifact upload, no vacancy data/URLs/CV, and cleanup remains unconditional.
- Regression will assert the diagnostic contract and unchanged isolation controls. This is a runner workflow/test-only change; no private scanner, production scan, AI, Supabase/HF/R2, deployment or snapshot mutation.

- PR #95 runner-only diagnostics change must validate current private `main`; it does not change private scanner source. The runner workflow validation routing was corrected on this branch so the PR title `sanitized TinyFish isolated scanner failure diagnostics` routes to private `main`, not the old Cloro candidate SHA. CI surfaced a stale fallback because the old Cloro candidate now conflicts with current private `cloro_search.py`; this was unrelated to the isolated diagnostic patch. A new contract test forbids reintroducing that stale fallback into this PR.

- PR #95 CI identified a test assertion that was too broad: the old Cloro fallback SHA legitimately remains in the shared routing expression for unrelated PRs. Replaced that assertion with a focused check that this diagnostics PR title maps specifically to private `main`; TinyFish candidate mapping remains intact. Latest test fix commit: `fed181fa9a01e3d2152566ac11b15a411853e215`.

- PR #95 follow-up CI showed the focused route assertion was still too literal for GitHub expression wrapping/parentheses. It has been changed to a regex that asserts the diagnostics title condition is followed by routing to `main`, while still permitting the shared fallback for unrelated PRs. Latest test fix: `ed6907dd2cb3c0c2d2fbc358a860785295f81ba7`.

- Public runner smoke run `44900607407` caught only a brittle regex escaping issue in the new route test; other workflow safeguards and 84/85 tests passed. Replaced regex parsing with direct extraction of the `private_ref` expression and assertions for the specific title, `main` target and retained TinyFish candidate target. New test commit: `7362eb5ac6235cae84676b4ae29a0aa92eb6b251`.


## 2026-11-21 — TinyFish sanitized scanner diagnostics fix merged
- Runner PR #95 merged by squash as `5886eb08a8a26ea77358899bd929c8ee92f28a58` after checks on exact PR head `7362eb5ac6235cae84676b4ae29a0aa92eb6b251): workflow validation run `44900639132` PASS (runner contract checks + full private scanner regression against current private main), public runner smoke run `44900639169` PASS. Private suite exact counts are recorded in the Actions logs and should be retrieved if needed; do not infer beyond checked success.
- Workflow now keeps the raw scanner log in runner temp only and emits only a sanitized failure category plus exit code to step summary; raw stdout/stderr, URLs, vacancy rows, CV details and credentials are never emitted or artifacted. Private source cleanup remains unconditional. No scanner/runtime behavior or production workflow was changed.
- Next: inspect post-merge main checks, then rerun the manually gated isolated TinyFish provider workflow exactly once. It remains serialized and non-publishing: TinyFish-only, no AI/Supabase/HF/R2 credentials, aggregate-only artifacts. Do not run a production scan or enable TinyFish in scheduled/default searches based only on this test. If live run passes, record real aggregate metrics; if it fails, inspect only sanitized category and fix on a new dedicated branch.
- No production scan, Supabase/HF/R2 write, vacancy publication, Cloudflare deploy, or recovery snapshot change occurred. Preserve all verified recovery snapshots.

- Post-merge runner main commit: `421e3942f150b697302ee16de5b18f454d437365`. Public runner smoke run `44900703524` PASS. Post-merge private scanner regression run `44900703522` PASS; private Python suite, frontend syntax/contracts, extension Bridge/RPC/Worker tests, public retrieval tests, extension package build/upload and cleanup completed successfully. Aggregate artifact `career-radar-chrome-extension` id `14705238067` (26,310 bytes) is the normal tested extension package; no raw vacancy records were published.

## 2026-11-21 — Follow-up provider run exposed shell quoting bug in sanitized diagnostics
- User shared the rerun log after PR #95. Credential preflight passed: TinyFish key present; Firecrawl quota endpoint reported remaining=1025, plan=1000. Scanner invocation lasted ~12 seconds and returned exit 1.
- New failure handler itself then emitted shell error `line 31: scanner_runtime_error: command not found`. Cause is confirmed from workflow source: this double-quoted `echo` contains Markdown backticks around ${failure_category}; Bash interprets the backticks as command substitution. Thus the diagnostic formatter is defective and the category field is blank. The scanner's underlying Python failure remains unknown because raw scanner output is correctly withheld.
- Next: dedicated runner branch from current main; replace the backtick-containing echo with safe `printf -- '- Sanitized category: %s\\n' "$failure_category"` (or equivalent single-quoted literal), add a regression asserting the summary formatter uses printf and has no command-substitution backticks, preserve raw output secrecy, no artifacts containing raw logs, and unconditional private checkout cleanup. Validate PR and full private regression before merge.
- Then rerun the bounded isolated provider workflow once. If it still fails, the category will be populated; extend only safe allowlisted classification or add a sanitized Python exception-class reporter. Never print exception message, raw traceback, provider body, vacancy rows/URLs/snippets, CV data or credentials.
- No production scan, AI assessment, Supabase/HF/R2 writes, vacancy publication, Cloudflare deployment, or recovery snapshot mutation occurred. Preserve verified recovery snapshots.

- Follow-up fix branch `fix/tinyfish-diagnostic-shell-quoting-20261121` created from runner main `d3db1ef84cb43676db181620c92c31193b816f05`. Confirmed cause of blank category is Bash command substitution from unescaped Markdown backticks in a double-quoted echo. Patch switches that line to single-quoted printf format plus argument; regression asserts the safe printf format and forbids the faulty echo. Scanner source is unchanged.

- PR #96 first validation showed the shared private regression router still selected an obsolete Cloro candidate for the new diagnostics-fix PR title; the runner workflow checks themselves passed. Added the PR #96 title to the explicit route-to-private-main allowlist and extended the contract test. This ensures the required private regression validates current private main, not an unrelated stale candidate.

## 2026-11-21 — TinyFish diagnostics shell formatter fix merged
- User-provided isolated workflow run showed TinyFish credential preflight passed (key presence only) and Firecrawl quota preflight passed (remaining=1025, plan=1000), but scanner process returned exit 1. The failure handler then itself failed at shell line 31 because double-quoted echo contained Markdown backticks, which Bash evaluated as command substitution (`scanner_runtime_error: command not found`). Therefore the blank category was a confirmed workflow formatting bug; the underlying scanner exception remains unknown because raw scanner output is withheld.
- Runner PR #96 merged as `8242eb049700486e12a33ea7610d365f4f7b470e`. Fix uses a single-quoted printf format string and category as a separate argument; contract test prevents reintroducing the backtick echo. Also extends private regression routing so this diagnostics PR validates current private `main`, not stale Cloro candidate.
- PR checks on exact head `375ac4680b5a837442aaccac9e493916359cf75f`: runner workflow validation `44901127403` PASS (YAML/workflow contract tests + full private scanner regression against current private main); public runner smoke `44901127394` PASS. The full private suite, frontend syntax/contracts, Bridge/RPC/Worker tests, public retrieval tests, extension packaging/upload and private checkout cleanup all succeeded.
- Post-merge main runs queued at time of handover: public smoke `44901197602`; private non-publishing regression/extension package validation `44901197561`. Verify both before claiming post-merge success.
- Next step: once post-merge main regression is green, rerun the manually gated isolated TinyFish provider workflow once. It remains TinyFish-only, serialized against production, no AI/Supabase/HF/R2 persistence/public publishing, aggregate-only artifact. If it still fails, use the populated sanitized category and improve allowlisted classification; never expose raw scanner log, provider payload, vacancy URLs/snippets, CV content or credentials. Do not start normal production scan or enable TinyFish by default until live validation passes.
- No production scan, AI assessment, Supabase/HF/R2 writes, vacancy publication, Cloudflare deployment, or recovery snapshot mutation occurred. Preserve all verified recovery snapshots.

- Post-merge verification for PR #96: public runner smoke run `44901197602` PASS; private non-publishing regression/extension package validation run `44901197561` PASS on merge SHA `8242eb049700486e12a33ea7610d365f4f7b470e`. Full private Python suite, frontend contracts, Bridge/RPC/Worker checks, public retrieval regression, extension package build/upload, and private checkout cleanup all succeeded. Artifact `career-radar-chrome-extension` was produced (26,312 bytes).
- The workflow formatter bug is now fixed and validated. The earlier scanner's underlying exit-1 cause is still unclassified. Next required operation is one manual dispatch of `tinyfish-firecrawl-isolated.yml` with `confirm_live_provider_requests=true`; GitHub integration has no workflow_dispatch action. Do not infer provider PASS from regression PASS. No production scan or publishing occurred.

## 2026-11-21 — Isolated TinyFish run #3 still fails after formatter repair
- User provided screenshots for isolated workflow run #3, run ID `44909617762` (job `136862429986`). Credential-presence and Firecrawl quota preflight succeeded; scanner step ran ~14 seconds then exited 1. Formatter now works: sanitized category correctly reports `scanner_runtime_error`; raw output remains withheld. This confirms the earlier shell-quoting defect is fixed, but the underlying Python exception is still not identified.
- Run #3 exact outcome: checkout/profile setup pass; TinyFish secret present; Firecrawl quota remaining=1025, plan=1000; bounded scanner fails; summary/artifact correctly skipped; private checkout cleanup passes. No publication or persistence.
- Next diagnostic change must keep scanner output private while recording only safe exception metadata. Wrap `runpy.run_path('radar.py', run_name='__main__')` in a tiny Python harness; catch exceptions without printing message/traceback; write only an allowlisted exception class and, for HTTPError, numeric status to a runner-temp marker. Classify common safe categories (HTTP status, URL/network, timeout, missing file/dependency, JSON, KeyError/ValueError/TypeError) in the step summary. Keep raw scanner log ephemeral and never artifact it. Add regression tests for the safe wrapper and ensure no exception string/traceback is emitted.
- Implement through a new runner-only branch and reviewed PR; require runner validation plus full private scanner regression and public smoke before merge. Then rerun isolated provider validation once. Do not touch scanner runtime source unless sanitized class/status evidence requires a targeted follow-up.
- No production scan, AI, Supabase/HF/R2 writes, vacancy publication, Cloudflare deployment, or recovery snapshot mutation. Preserve verified recovery snapshots.

- Branch `fix/tinyfish-safe-exception-diagnostics-20261121` implements safe Python exception-class/status metadata for the isolated scanner. Wrapper executes unchanged private `radar.py`, catches uncaught exceptions, writes only class name and (for HTTPError) numeric status to runner temp, and never writes exception message, traceback, locals, URLs or payload. Bash maps allowlisted classes/statuses to sanitized categories. PR router/test extended so this diagnostics PR validates private current main.

## 2026-11-21 — Safe exception metadata diagnostics merged
- PR #97 merged as `0876b124964e84385ddfe876e58ad438c454a0d5`.
- Workflow now runs the unchanged private `radar.py` under a small `runpy` wrapper. If it raises, only exception class and numeric HTTP status (when applicable) are written to a runner-temp marker; exception messages, traceback, locals, URLs and provider payloads are not written to the marker or emitted. Shell maps allowlisted classes/statuses to sanitized failure categories. Raw stdout/stderr remains ephemeral runner temp and is never artifacted; cleanup remains unconditional.
- PR exact-head checks: runner workflow validation `44910001653` PASS, including YAML/workflow contract checks and full private scanner regression against current private main; public runner smoke `44910001635` PASS.
- Post-merge main public smoke `44910065547` PASS. Post-merge full private regression `44910065580` was still running at handover update; verify before reporting complete.
- Next: verify post-merge private suite success, then rerun isolated TinyFish provider workflow once. The previous isolated run #3 `44909617762` failed with generic `scanner_runtime_error`; the next run should reveal an allowlisted exception category/class and optional HTTP status. Do not print or artifact raw output. Do not start production scan, AI, persistence, or enable TinyFish in scheduled/default searches unless the isolated provider test passes.
- No production scan, AI assessment, Supabase/HF/R2 writes, vacancy publication, Cloudflare deployment, or recovery snapshot mutation. Preserve verified recovery snapshots.

- Post-merge verification completed: private regression/extension package workflow `44910065580` PASS on merge SHA `0876b124964e84385ddfe876e58ad438c454a0d5`. Full private Python suite, frontend syntax/contracts, Bridge/RPC/Worker tests, public retrieval regression, extension packaging/upload and private checkout cleanup all succeeded. Public smoke `44910065547` PASS.
- All code and regression validation for the safe exception-metadata diagnostic fix is complete. Next operation is the manually gated isolated provider run with `confirm_live_provider_requests=true`. No GitHub Actions workflow-dispatch action is available in this integration; the operator must click Actions → TinyFish + Firecrawl isolated provider validation → Run workflow and enable the confirmation input. This is still a bounded, non-publishing run.


## 2026-11-21 — TinyFish run #4: ValueError narrowed; safe traceback-frame diagnostic candidate
- User supplied screenshots for isolated run `44910316475` (commit `136b7a1ac7aeedff0c7199d4cd14c38ce9898e4e`). Preflight succeeded (TinyFish key present; Firecrawl quota remaining=1025/plan=1000); scanner failed with sanitized category `invalid_runtime_value`, exception class `ValueError`. Private checkout cleanup succeeded; no output artifact, publication or persistence.
- Reviewed private source adapter: TinyFish board generation is bounded (focused max 3 queries; fetch budget 2). Adapter catches ValueError from request/schema parsing in its request and fetch blocks; exceptions outside those blocks can still propagate (e.g. URL parsing/row normalization). Do not assume the exact source without a frame.
- New runner-only branch `fix/tinyfish-safe-valueerror-tracepoint-20261121` adds a safe innermost traceback frame marker: basename only, function name, and line number. It does NOT include source line, absolute path, exception message, traceback text, locals, URL or payload. Output is allowlist-validated before summary. Regression assertions enforce no raw traceback/line leakage.
- Next: PR validation against current private main plus public smoke; merge only if both pass. Then request one further manually gated isolated provider run to locate exact ValueError line. Keep workflow non-publishing; do not alter private scanner until exact source line is known.


## 2026-11-21 — TinyFish run #4 ValueError; safe failure-frame tracepoint merged
- Isolated run #4 `44910316475` failed after preflight succeeded (TinyFish key present; Firecrawl remaining=1025/plan=1000). Safe diagnostics reported `ValueError` / `invalid_runtime_value`; scanner checkout cleanup passed. The exact source line remains unknown; do not assume it is query validation or malformed URL without traceback frame evidence.
- Reviewed private adapter: `tinyfish_search` validates query length before its request try block, handles provider/schema ValueErrors within request/fetch try blocks, and has other per-result operations (including URL parsing and vacancy normalization) outside those try blocks. These are candidate locations only, not proven cause.
- Runner PR #98 merged as `afb447cf13f42c797ed279cde00f18033f77c3d6`. It adds a safe innermost traceback frame marker: basename only, function name, line number. It never records source text, absolute path, exception message, traceback text, locals, URLs or payloads. Shell allowlist-validates before displaying.
- PR exact-head validation `44910691273` PASS (workflow contracts and full private scanner regression against current private main); public runner smoke `44910691265` PASS. Private suite, frontend syntax/contracts, Bridge/RPC/Worker tests, public retrieval regression, extension package/upload and checkout cleanup all passed.
- Next: verify post-merge main smoke/private regression, then manually dispatch the isolated TinyFish workflow once. The next failure should show a safe failure frame such as `public_source_adapters.py:NNN (tinyfish_search)`; use that exact line to fix private scanner source through its own feature branch and reviewed PR. Keep test non-publishing; no production scan, AI, Supabase/HF/R2 writes, publication or Cloudflare deployment until isolated provider validation passes.
- Preserve all verified recovery snapshots.

- Post-merge verification for PR #98 completed: public smoke `44910734112` PASS and private regression/package validation `44910734163` PASS on merge SHA `afb447cf13f42c797ed279cde00f18033f77c3d6`. Full private suite, frontend contracts, Bridge/RPC/Worker, public retrieval regression, extension package/upload and checkout cleanup succeeded.
- The next isolated TinyFish workflow run is still manually gated. Dispatch `.github/workflows/tinyfish-firecrawl-isolated.yml` with `confirm_live_provider_requests=true` once; the new sanitized summary should identify the innermost failure frame. Do not start production scans or enable TinyFish by default before a real isolated search succeeds.


## 2026-11-21 — TinyFish isolated run #6: telemetry scope mismatch identified
- User screenshot for run #6 shows safe failure frame `scan_telemetry.py:143 (verify_scan_telemetry)`, exception `ValueError`. Exact guard: full scan allocated no retrieval queries to any career track.
- Root cause is isolated workflow request shape, not provider credentials: the test requested two explicit role titles but supplied `tracks: []`. Empty selected_tracks is treated by `build_track_coverage_report` as a full-catalogue scan; the TinyFish-only focused provider path does not produce the normal per-track board query allocations, so the global full-scan telemetry gate correctly rejects it.
- Fix candidate in runner-only branch `fix/tinyfish-isolated-track-scope-20261121`: set the isolated request tracks explicitly to the two matching catalogue tracks `Airworthiness & Maintenance Planning` (CAMO Engineer) and `Manufacturing & Production` (Manufacturing Engineer). Add assertions in workflow preparation and regression tests that both selected tracks remain explicit. This should make `selected_tracks_only=true` and bypass only the full-catalogue allocation requirement for this explicitly scoped diagnostic run; all other telemetry reconciliation and production full-scan validation remain unchanged.
- Validate via PR #99 exact-head runner workflow validation, public smoke, and full private scanner regression. Then manually rerun isolated provider workflow. If provider test still fails, use new sanitized frame/category; do not assume TinyFish provider failure from this telemetry guard.
- No production scan, persistence, AI, publication, Cloudflare deploy or recovery snapshot mutation. Preserve verified recovery snapshots.


## 2026-11-21 — TinyFish run #6 telemetry scope fix merged
- Run #6 sanitized failure frame is `scan_telemetry.py:143 (verify_scan_telemetry)`, `ValueError`: full scan allocated no retrieval queries to any career track. This is the telemetry full-scan allocation guard, not a proven TinyFish/Firecrawl provider error.
- Root cause: isolated request named CAMO Engineer and Manufacturing Engineer but used `tracks: []`. The empty track list is interpreted as full-catalogue scope; provider-only TinyFish validation has no full per-track board allocation, so the full-scan guard correctly rejected it.
- Runner PR #99 merged as `a97ff5fd2cc7e5d65825b11993d6dea9bdd78dfa`. Isolated request now explicitly scopes `Airworthiness & Maintenance Planning` and `Manufacturing & Production`, with regression assertions. `scan_telemetry.py` and production full-scan checks were not changed or weakened.
- PR validation `44911253557` PASS, public runner smoke `44911253522` PASS, and full private candidate regression passed: private Python suite, frontend syntax/contracts, Bridge/RPC/Worker, public retrieval regression, extension package/upload, cleanup.
- Post-merge public smoke `44911315263` and private regression/package validation `44911315191` were queued at handover time. Verify these before next manual provider run.
- Next: after post-merge checks pass, manually dispatch `.github/workflows/tinyfish-firecrawl-isolated.yml` with `confirm_live_provider_requests=true`. This is still one bounded, serialized, TinyFish-only non-publishing scan. Only a successful provider result with usable postings validates TinyFish; a telemetry pass alone does not.
- No production scan, AI assessment, Supabase/HF/R2 writes, public vacancy publication, Cloudflare deployment or recovery snapshot mutation. Preserve all verified recovery snapshots.


## 2026-11-21 — TinyFish run #8: second request-source override found
- User screenshot for isolated run #8 `44911516630` still failed with `invalid_runtime_value`, `ValueError`, safe frame `scan_telemetry.py:143 (verify_scan_telemetry)`.
- PR #99 fixed `isolated-search-request.json` to include the two selected tracks, but the scanner is actually launched with a separate `SEARCH_REQUEST` environment variable in the same workflow. That environment variable still contained `"tracks":[]`, overriding the file and keeping `selected_tracks_only=false`. This explains why the previous fix had no effect on the scanner's effective request.
- New runner-only branch `fix/tinyfish-search-request-track-override-20261121` updates the sole `SEARCH_REQUEST` environment JSON to the exact two matching tracks and extends regression tests to assert both request sources and reject an empty track list in the effective env request. No changes to private scanner or telemetry validator.
- Next: PR validation, public smoke, full private regression; merge only on PASS. Then manually run isolated provider workflow once. Do not call TinyFish provider broken until telemetry gate passes and the provider is actually invoked.
- No production scan, AI, persistence, publication, Cloudflare deployment or recovery snapshot mutation. Preserve verified recovery snapshots.

- PR #100's first full validation attempt `44911729527` exposed a runner validation-routing gap: its title did not match any recognized TinyFish private-ref routing label, so the reusable private regression tried to merge an old fixed private SHA into current `main` and stopped on unrelated `AI_HANDOFF.md`/`cloro_search.py` conflicts before tests. The scanner code was not modified by this runner-only PR. Extend the routing allowlist for this exact PR title so validation targets current private `main`, then rerun the full PR checks.


## 2026-11-21 — TinyFish run #8 effective SEARCH_REQUEST override fix merged
- Isolated run #8 `44911516630` still failed at safe frame `scan_telemetry.py:143 (verify_scan_telemetry)`, `ValueError`. Diagnosis: PR #99 had populated `tracks` in `isolated-search-request.json`, but the scanner is launched using a separate `SEARCH_REQUEST` environment variable that still contained `tracks: []`. That env value overrides the generated file, so the effective profile was still interpreted as a full scan.
- Runner PR #100 merged as `bc7cc17e61d160c34c160ea5c98f0c8617718420`. It now passes the two selected catalogue tracks in both request sources and regression-tests that the environment override is populated. It also adds the PR title to runner validation routing so the reusable private regression targets current private `main` instead of an obsolete fixed private SHA.
- PR exact-head validation `44911847059` PASS; public runner smoke `44911847053` PASS. Full private regression against current private main PASS, including private Python suite, frontend contracts, Bridge/RPC/Worker, public retrieval regression, extension package/upload and cleanup.
- Post-merge smoke `44911909958` and private regression/package validation `44911909835` were queued at handover update; verify these before another provider run.
- Next: after post-merge checks pass, manually dispatch `.github/workflows/tinyfish-firecrawl-isolated.yml` once with `confirm_live_provider_requests=true`. Confirm the sanitized frame no longer fails telemetry and then inspect whether the bounded TinyFish request actually returns usable postings. A telemetry pass alone is not provider success.
- No production scan, AI assessment, Supabase/HF/R2 writes, public vacancy publication, Cloudflare deployment or recovery snapshot mutation. Preserve all verified recovery snapshots.


## 2026-11-21 — TinyFish isolated provider validation #9 PASS
- User manually triggered runner workflow run `44912166916` on runner main commit `a41fe542816e38d9d7bfbbc03de55498a9d60871`. Job `provider-validation` completed SUCCESS in 29 seconds (workflow total 33 seconds).
- Sanitized aggregate: 30 collected, 25 shortlisted; TinyFish status `healthy_with_results`; search queries 3/3 completed, 0 failed; TinyFetch enrichment 2/6; Firecrawl fallback 0/0 successful, 4 skipped. The workflow's `Require usable TinyFish results` gate passed (`PROVIDER_PASSED=true`).
- Confirms TinyFish now successfully returns usable vacancies through the isolated bounded scanner after PR #100 corrected the effective `SEARCH_REQUEST` track override. This is a real provider validation PASS, not merely telemetry passing.
- Artifact `tinyfish-firecrawl-provider-summary` ID `14709887645`, 589 bytes, aggregate-only. Raw vacancy rows/URLs/descriptions/CV/credentials were not included; ephemeral private checkout was removed. No Supabase, Hugging Face, R2, AI assessment, or public vacancy writes.
- Interpretation: TinyFish is operational and produced usable results. Enrichment remains partial (2/6); Firecrawl fallback was skipped (4) because the fallback did not run/succeed. Do not report all six enrichments complete or claim Firecrawl provider success. Next safe work: inspect the sanitized aggregate artifact and scanner code/config for the 4 skipped fallback and 4 non-enriched records, then make a separate branch/PR if a code change is justified. Keep future provider diagnostics isolated and non-publishing. Production scan/deployment remain separate and have NOT been run. Preserve verified recovery snapshots.


## 2026-11-21 — Investigation: TinyFish run #9 enrichment / Firecrawl skips
- Inspected run #9 aggregate-only artifact `14709887645` (downloaded and opened): `fetch_attempted=6`, `fetch_succeeded=2`, `fetch_failed=4`; `fetch_failure_categories={page_not_found:4}`; `firecrawl_attempted=0`, `firecrawl_succeeded=0`, `firecrawl_skipped=4`; `firecrawl_failure_categories={}`. Search was healthy: 3/3 queries, 30 valid postings. Firecrawl quota preflight had passed earlier (reported 1,025 remaining / 1,000 plan); therefore skips were not caused by absent key or quota preflight.
- Source inspection: `deep_search.py::tinyfish_boards` makes 3 focused boards for this profile, each with `fetch_budget=2`, yielding exactly 6 TinyFetch candidates. `public_source_adapters.py::tinyfish_search` selects only the first two found rows with descriptions shorter than 450 chars per board; no replacement candidates are attempted when fetch returns errors.
- In `tinyfish_search`, Firecrawl is deliberately permitted only for TinyFetch errors `timeout`, `target_unreachable`, `empty_content`, `proxy_error`, or `target_http_error` with status >=500. `page_not_found` is outside that allowlist; code increments `firecrawl_skipped` and continues. This is the expected safety behavior: don't use a second scraper to retry missing/404 pages or bypass target access controls. Firecrawl was never invoked, so run #9 does NOT validate Firecrawl scraping, only its quota preflight.
- Why only 2/6 descriptions enriched: four selected URLs were classified by TinyFetch as `page_not_found`; two returned sufficiently longer page text. The scanner does not top up the failed slots with later search results, so 4 failures remain even though up to 30 postings were discovered. Search results still remain as valid postings with snippet/search-result-only descriptions; no postings were discarded for fetch failure.
- Observability/test gaps: artifact shows the TinyFetch failure category but not a dedicated reason breakdown for Firecrawl skips; the skip reason is inferred from matching counters and allowlist code. Existing adapter tests cover transient timeout fallback, bot-blocked and 403 non-fallback, but no explicit `page_not_found` test. Add a regression test that asserts page_not_found never invokes Firecrawl, and expose safe aggregate skip-reason counters (e.g. `disallowed_tinyfetch_error:page_not_found`) in a later dedicated PR. Consider improving candidate ranking/top-up within an unchanged bounded request budget; do not simply widen fetch or Firecrawl quotas. No raw URLs were available in artifact, so exact target domains and whether provider classification reflects target HTTP 404 vs its normalized error could not be confirmed.
- No code changes, branch, PR, production scan, deployment, or production writes were made during this investigation. Verified recovery snapshots preserved.


## 2026-11-21 — TinyFish enrichment reliability candidate PR
- Public runner branch `ci/tinyfish-enrichment-private-regression-20261121` adds PR path filters for `public_source_adapters.py`, `deep_search.py`, and `tests/**`, and routes PR title marker `[tinyfish-enrichment]` to private candidate branch `fix/tinyfish-enrichment-reliability-20261121` for read-only full regression.
- The isolated TinyFish provider workflow now carries sanitized `fetch_replacement_attempted`, `fetch_replacement_succeeded`, `fetch_skip_reasons`, and `firecrawl_skip_reasons` in its aggregate-only artifact. It remains manual, bounded and non-publishing.
- The private candidate is not merged. Do not dispatch a production scan, production deployment, AI assessment or any persistence/publication workflow. Preserve verified recovery snapshots.


## 2026-11-21 — TinyFish enrichment reliability PRs merged; full regression PASS
- Public runner PR #101 merged as `3c47b9c6c8fc4a6dc12b2b9858e6f348ef420acd`. It adds PR path filters for `public_source_adapters.py`, `deep_search.py` and `tests/**`, and routes `[tinyfish-enrichment]` PRs to private branch `fix/tinyfish-enrichment-reliability-20261121` for read-only full regression.
- It also adds `fetch_replacement_attempted`, `fetch_replacement_succeeded`, `fetch_skip_reasons` and `firecrawl_skip_reasons` to the aggregate-only TinyFish provider artifact. The provider workflow remains manual, bounded and non-publishing.
- Private scanner PR #204 merged as `5883cd883fdeeba5cd1a3bea77267b3343d85854`. Full private regression run #44916018719 passed on attempts 1 and 2; attempt 2 was rerun after merge against the current private base. All Python, frontend, Bridge/RPC/Worker, public retrieval regression, extension package/upload and cleanup steps passed. Post-merge runner-main regression #44916107000 and public runner smoke #44916106977 passed; runner workflow validation #44916018817 passed.
- No live provider request was dispatched for this implementation; provider tests are mocked. No production scan, production publication, AI assessment, Supabase/HF/R2 write, Cloudflare deployment or recovery snapshot mutation. Preserve verified recovery snapshots.


## 2026-11-21 — Live TinyFish isolated provider validation #10 PASS
- Verified workflow run [#44952896092](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44952896092) on `main` commit `9128f67bb0228305e0fbd3a6da945147214a48ff`; job `provider-validation` succeeded, including the bounded TinyFish-only scanner and the explicit usable-results gate.
- Inspected artifact [tinyfish-firecrawl-provider-summary](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44952896092) (ID `14726490860`): 30 collected / 25 shortlisted, TinyFish `healthy_with_results`, 3/3 queries succeeded, 30 valid postings, 30 unique canonical URLs, zero retrieval errors.
- TinyFetch enrichment: 2/6 successful; 4 normalized `page_not_found`. Three replacement attempts with two successful replacements. Firecrawl scrape attempts 0, successes 0, skipped 4; skip reason `disallowed_tinyfetch_error:page_not_found`. This is intentional: do not use a second scraper to retry missing pages or bypass target access denials. The run proves TinyFish live retrieval but does not prove Firecrawl scrape success; its read-only quota preflight succeeded as a required workflow step.
- Isolated / non-publishing: no Supabase, Hugging Face, R2, AI assessment, public vacancy write, or raw vacancy/CV/URL artifact. Private checkout cleanup step passed. No production scan or production publishing action was run. Preserve verified recovery snapshots.
- Next engineering opportunity: improve candidate replacement/enrichment yield within existing bounded request ceilings while retaining the strict no-fallback-on-404/access-denial policy; implement only on a dedicated branch with regression tests and reviewed PR.


## 2026-11-21 — Bounded TinyFish enrichment candidate PR validation state
- Private feature PR #206 is `fix/tinyfish-enrichment-candidate-ranking-20261121`; runner routing PR #104 maps the exact title marker to this private branch and includes an immutable private fallback reference. Exact private branch SHA at last verification: `48a263df4b6cf1658ab59f0cd629f938a7f23f9c`.
- Runner reusable regression validates the private checkout branch and SHA before tests, merges current private `main` in the ephemeral runner workspace only, and removes the private checkout after completion.
- CI history exposed focused candidate failures in fetch replacement counters/queue behaviour and a global-budget test fixture; the adapter was adjusted to preserve two initial candidates, replace failed candidates only within the per-board/global budget, and keep ranking limited to URLs already returned by TinyFish Search. Diagnostic step remains in this branch to print capped failing test details, no vacancy/CV/credential data.
- Runner workflow-contract validation passed at runner SHA `2c66845675784df929221e055510a291b19ed435`; subsequent smoke runs exposed a fallback-SHA assertion mismatch, now updated in `tests/test_production_workflow_contract.py` to assert explicit `private_fallback_ref`. Latest changes still require fresh full regression, runner validation and smoke PASS; do not merge PR #206 or #104 until all required checks are green.
- No production scan, deployment, Supabase/HF/R2 persistence, AI assessment, public vacancy publication, or recovery snapshot changes were performed. Preserve verified recovery snapshots.


## 2026-11-22 — TinyFish regression CI routing and isolation (validation pending)
- Runner PR #104 remains an isolated feature branch; runner `main` baseline at start of work was `38b14c07d202d4fb568d45ac5b4caeb794dad35b`. Private candidate is validated from exact branch `fix/tinyfish-enrichment-candidate-ranking-20261121`, currently pinned to private handoff commit `c822bf13697ad95134f32ecf990fd597b28360ea`; the reusable workflow asserts this exact SHA before tests.
- Fixed the workflow diagnostic's unittest construction (`cls(name)`, not undefined `case(cls, name)`) so it emits bounded failure details rather than aborting before diagnosis.
- Fixed runner workflow-contract test path resolution by defining the repository root from `__file__`; this was the public smoke failure.
- Reusable regression concurrency is now namespaced by caller workflow and ref with `cancel-in-progress: false`, preventing independent callers from cancelling one another's queued regression jobs. The R2 guardian PR regression is skipped for the dedicated TinyFish-ranking PR, avoiding a redundant run against its stale pinned private SHA.
- Public runner smoke passed on runner commit `e1537e1956215271e59f35c2a06a8d633ea5c0d5`. Runner workflow validation passed YAML/contract checks; private full suite on that run executed 542 tests and found two candidate replacement-order failures. The private candidate was corrected afterward; latest full suite, focused tests, runner smoke, workflow-contract tests, extension/package validation are pending a clean run on the exact current heads.
- Do not merge until all required checks pass on exact latest heads. No production scan, deployment, production persistence/publication, or recovery snapshot mutation. Preserve verified recovery snapshots.


## 2026-11-22 — Regression concurrency contract coverage
- Added a runner contract test asserting that reusable full-suite calls use a caller-workflow/ref-specific concurrency group with `cancel-in-progress: false`, and that the R2 guardian does not launch a duplicate stale private regression for the TinyFish-ranking PR.
- Added after the previous handoff entry; validation must be repeated on the resulting runner branch head and exact private candidate SHA `c822bf13697ad95134f32ecf990fd597b28360ea`.
- No production workflows, deployments, provider calls, persistence/publication, or recovery snapshots were touched.


- Removed the redundant pull-request trigger from the reusable full-suite workflow. PR validation now invokes the private regression once through `runner-workflow-validation.yml`; this avoids parallel duplicate 542+ test suites while retaining the workflow's push/manual/call entry points. Cross-caller concurrency remains namespaced to prevent cancellation.


## 2026-11-22 — Final TinyFish validation evidence recorded
- Runner workflow validation run [#44959999423](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44959999423) passed on runner branch commit `402150209974bb55377ea385f9d9e81ed965b7eb`, with private candidate `c822bf13697ad95134f32ecf990fd597b28360ea` reconciled against private main `9117077d01ccef99ba8ed8f0ec855b91693ccad2`.
- Evidence: 4/4 focused TinyFish tests, 542/542 private Python tests, 89/89 runner workflow/contract tests, frontend syntax/contracts, Bridge/restricted RPC/Worker, public retrieval regression, extension package creation/upload, checkout cleanup, runner YAML validation and public runner smoke all passed. R2 guardian duplicate regression was correctly skipped for this dedicated PR.
- The private handoff has now been updated with the PASS record, producing private candidate documentation-only commit `af69343d0b9efa6a88b8501b8ac522a2989df40e`; the reusable workflow pin is updated to that exact SHA. Run the final gate again on the latest runner branch head after this pin update. No production operations or recovery snapshot changes.


- Final review tightened the private checkout provenance gate: the reusable workflow now fails if either the candidate branch name OR its SHA differs from the expected exact values (previous comparison could incorrectly pass when only one matched). The pinned private candidate is `af69343d0b9efa6a88b8501b8ac522a2989df40e`; rerun all latest-head gates after this hardening.


## 2026-11-22 — Private TinyFish candidate PR merged; runner PR revalidation required
- Private scanner PR #206 was merged with a merge commit (not squash) as `2ee04f0c420a97e7b15991fb97f38c0cd75e408b`. This preserves the exact validated feature branch commit `af69343d0b9efa6a88b8501b8ac522a2989df40e` as an ancestor of private `main`; the candidate branch still resolves to that exact SHA.
- Runner PR #104 remains open. Its previous validation passed on runner head `30a342b7a4a39a1fdf1117c0d70e9b6f3591a5a4` against the pre-merge private base. Re-run all runner checks now so the reusable workflow reconciles the newly merged private `main` in the ephemeral workspace and verifies the same exact candidate SHA.
- No production scan, deployment, provider dispatch, Supabase/HF/R2 write, AI assessment, public publication or recovery snapshot mutation. Preserve verified recovery snapshots.


## 2026-11-22 — Post-merge CI provenance fix (candidate PR)
- After PR #104 merged to runner `main` as `b2b994751852499c77728b2f166ce9726341516e`, post-merge runner smoke passed but the post-merge full private regression stopped before tests because `git branch --show-current` is empty for the detached checkout used by Actions.
- This is a workflow provenance assertion defect, not a test failure. The run verified private main at `2ee04f0c420a97e7b15991fb97f38c0cd75e408b`, but the branch-name assertion rejected the detached HEAD.
- Follow-up branch `fix/post-merge-private-provenance-detached-head-20261122` changes provenance validation to require both the checked-out HEAD SHA and fetched `origin/<expected-branch>` SHA to equal `af69343d0b9efa6a88b8501b8ac522a2989df40e`. This remains exact and safe on detached checkouts; no weakening to SHA-only or name-only matching.
- Re-run the complete post-merge private suite, runner validation and smoke after this fix. No production scan/deployment, provider dispatch, persistence/publication, or recovery snapshot mutation.


- The first follow-up workflow attempt exposed an empty `env:` mapping left behind when the obsolete branch-name environment variable was removed. Removed that empty mapping; the provenance step now uses only its explicit expected branch/SHA constants and remote-ref lookup. Revalidate YAML parsing and all checks on the updated branch head.


- Finalized the provenance gate to support both PR candidate routing and post-merge `main` runs: it now resolves the candidate ref from the workflow output, verifies checked-out HEAD against that branch/tag/immutable SHA, and additionally enforces the pinned TinyFish SHA whenever the resolved ref is the TinyFish candidate branch. This prevents a fixed candidate-only assertion from rejecting legitimate main regression runs after merge.


## 2026-11-22 — TinyFish runner PRs merged; post-merge main regression PASS
- Runner PR #104 merged as `b2b994751852499c77728b2f166ce9726341516e`. Its first post-merge main regression exposed a detached-HEAD provenance assertion issue before the suite ran; no Python test failed. Follow-up PR #106 corrected provenance resolution for both PR and main/tag/immutable-SHA contexts and was merged as `eeeca8d396af690679c09828deafd31675004241`.
- Final post-merge main validation [#44960813840](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44960813840) passed on runner main `eeeca8d396af690679c09828deafd31675004241`, checking private main `2ee04f0c420a97e7b15991fb97f38c0cd75e408b`: focused TinyFish tests 4/4, full Python suite 542/542, runner workflow contracts 89/89, frontend, Bridge/restricted RPC/Worker, public retrieval regression, extension package/upload and cleanup all passed.
- Post-merge public runner smoke [#44960813842](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44960813842) passed on the same runner main commit. Exact candidate provenance was verified for PR candidate branch `fix/tinyfish-enrichment-candidate-ranking-20261121` at `af69343d0b9efa6a88b8501b8ac522a2989df40e` and for the post-merge private `main` ref at `2ee04f0c420a97e7b15991fb97f38c0cd75e408b`.
- CI-only changes and read-only validation. No production scan, production deployment, provider dispatch, persistence/publication, AI assessment, or recovery snapshot mutation. Preserve verified recovery snapshots.


## 2026-11-22 — Track coverage / Personio regression routing merged
- Runner PR #107 merged to `main` as `59c0fb0315e3a7ff968651a62c3efcd7192bd3dc`. It adds the `[track-coverage-personio]` PR-title route so the reusable private scanner regression checks the exact candidate branch rather than silently testing private main.
- The validation PR's runner-main checks passed: workflow validation, runner smoke and credential-presence check. The reusable non-publishing private regression checked private candidate `fix/track-coverage-personio-metrics-20261122` at `1c08133019e5415917695f3d2fcd9ec1d49f256d`.
- Full Python suite: 545 tests, 0 failures, 0 errors, 0 skipped. Focused TinyFish diagnostic 4/4; frontend syntax/contracts, Bridge/restricted RPC/Worker, public retrieval regression, extension packaging/upload and private checkout cleanup passed.
- The route is only a validation mechanism. No production scan, Cloudflare production deployment, provider dispatch, Supabase/HF/R2 write, publication or recovery snapshot mutation. Preserve verified recovery snapshots.

## 2026-11-22 — Private track coverage / Personio candidate exact-head regression
- Private source PR #207: https://github.com/happytiswis-sudo/engineering-career-radar/pull/207, branch `fix/track-coverage-personio-metrics-20261122`.
- The exact latest private PR head `9dd7832bc90c164a59f6a1610372498ee723947c` was validated by the non-publishing runner workflow [#45004586690](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45004586690), job `137218959459`.
- Full private Python suite: 545 tests, 0 failures, 0 errors, 0 skipped. Focused TinyFish diagnostics, frontend syntax/contracts, Bridge/restricted RPC/Worker checks, public retrieval regression, extension packaging/upload and private checkout cleanup all passed.
- Runner workflow validation, runner smoke and credential-presence checks succeeded. The separate conditional `private-candidate-regression` job was skipped by workflow routing; the dedicated full candidate regression above did execute and pass.
- PR #207 remains open and unmerged. The technical review is a maintainer-authored COMMENT, not an independent GitHub approval. Do not misrepresent it as independent approval. No production deployment or scan was run; merge remains separate because the connected Cloudflare Workers Builds integration can deploy production on merge.
- Historical scan `44962287103` and verified recovery snapshots remain untouched. No provider dispatch, AI assessment, Supabase/HF/R2 write, or public vacancy publication.

- Follow-up documentation on the private PR #207 branch added the master specification telemetry amendment, append-only DEC-113 and operations-reference interpretation. Latest private PR head after these documentation-only commits is `740a48a30a3fc4eead681431d2b0ca131f21bdf0`; executable scanner and test files are unchanged from the validated code/handover commits. The prior full regression remains evidence for executable code, not a claim that the later documentation-only tip was rerun.


## 2026-11-22 — Cloudflare release-path verification for private PR #207
- Read-only Cloudflare verification confirms `career-radar-dashboard` is linked to private `happytiswis-sudo/engineering-career-radar` on `main`, with Workers Builds automatic builds enabled. Production path filters include Python and test files changed by private PR #207; merging that PR can therefore trigger a production dashboard deployment.
- The dashboard Workers Builds production command runs the configured Python/frontend checks and then `wrangler deploy --config wrangler.jsonc`. The Bridge Worker has no Workers Builds configuration.
- This runner's `deploy-cloudflare-dashboard.yml` is separately dispatchable with `workflow_dispatch`; it checks out private `main` and deploys both dashboard and Bridge. Its push trigger is limited to changes to the deploy workflow file in this runner repository, not private-source merges.
- No Cloudflare settings or production resources were changed during this read-only check. Keep deployment separate: after independent approval, temporarily suppress the dashboard auto-build path for the merge window, merge the private PR, dispatch and verify the explicit deployment, then restore and read back the original build filters. Do not claim deployment from a merge or CI result alone.
- Preserve scan `44962287103` and verified recovery snapshots. No production scan, provider dispatch, Supabase/HF/R2 write, AI assessment or public vacancy publication was run.


## 2026-11-22 — Runner handover PR #108 merged
- Documentation-only PR #108 was merged to runner `main` as `78d3e60531df863227845f3a2906a5202fa3b0f6` after reviewing the exact diff and confirming runner validation/full-private-suite run #45027863123 and runner smoke #45027863106 succeeded on the PR head.
- No runner executable code or workflow changed in PR #108. No Cloudflare deployment, production scan, provider dispatch, persistence/publication, AI assessment or recovery snapshot mutation occurred.
- Private source PR #207 remains open pending independent approval. Its dashboard Workers Builds production auto-build path must be held during the merge window before a separate explicit production deployment.


## 2026-11-22 — Release gate recheck and production run evidence
- Rechecked dashboard PR #209 and runner PR #111. Both remain open, documentation-only, independently awaiting approval; no approval review was recorded at this check.
- `Sidkd007` has `read` permission on this public runner repository, so GitHub does not permit that user to approve PR #111. Obtain independent approval from a collaborator with sufficient permission; do not bypass branch/review protections.
- Production credential and publishing-gate preflight run [#44962020159](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44962020159) completed successfully on 2026-11-21; preflight job #137022719253 had all steps succeed. Earlier preflight #44961321518 failed.
- Production scan run [#44962287103](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/44962287103) was dispatched and completed successfully on 2026-11-21. The workflow dispatch used blank search request and is recorded in the run's own metadata; scan safety inputs must be confirmed from event metadata/artifact before describing exact persistence modes. Preserve and inspect its aggregate artifact before conclusions.
- Do not say scan is awaiting launch. The latest observed production-scan run is #44962287103; no later run was found in the first 100 Actions runs on 2026-11-22.
- Current live Cloudflare read-back: dashboard and bridge both have query-string redaction enabled, invocation logs disabled and persistence disabled. Dashboard traces enabled at 10%; bridge traces disabled. Bridge R2 bucket, rate limiters, and expected secret bindings remain present. No Cloudflare settings were changed.
- PR #209 latest preview passed build and deployment at commit `4df62f61fdb0152d9968cc5457e5c1692a8ef10d`; PR #111 runner workflow validation and smoke passed at commit `7f5473d306f429c9050cda58db31fe0a54914b06`. These are preview/CI results, not a new production deployment.
- This session's GitHub integration does not expose workflow dispatch. No Actions dispatch or production deployment was triggered during this session.
- Workers Builds automatic-build hold remains active; original path filters are not recovered. Do not guess filters, remove the hold, or merge PR #209 before preserving production-deployment separation.
- Preserve verified recovery snapshots. No secrets, private vacancy records, or raw scan payloads were added here.

## 2026-11-22 — Production scan #44962287103 aggregate artifact reviewed
- Downloaded and inspected verified privacy-safe artifact `career-radar-source-yield` (artifact id `14729917876`, SHA-256 `03ea7e63b63b4870b1c6c873655b4b4ca11f21cb58bcc504e29fe64dbb704435`). Artifact declares `verification.verified=true` and run id matches `44962287103`.
- Retrieval funnel: 28,300 raw URLs; 25,578 unique canonical URLs; 25,578 usable postings; 26,321 retrieved vacancy identities; 25,084 newly discovered identities; 1,237 historically seen retrieved identities; 622 cross-source duplicate URLs detected; 1,982 same-run duplicate postings deduplicated; 530 same-run duplicates merged; 3 cross-source postings merged.
- Scan totals: 14,036 collected postings; 111 shortlisted; 28 AI assessed. These are distinct stages and must not be conflated.
- Coverage summary: 35 catalogue tracks / 35 reported / 35 allocated; 34 tracks with results. Planned queries 570; attempted 500; successful 500; failed 0; skipped 70; unconfigured 0. Per-track artifact rows report each track as `status: skipped` even though each had 14 or 15 successful attempted queries and most tracks returned vacancies. This is an apparent telemetry/status inconsistency; do not treat the per-track status field as correct until fixed/reconciled. Transport, Port & Intermodal Logistics returned zero vacancies.
- Source metrics: Greenhouse 10,892 canonical URLs (220/220 successful); Ashby 5,628 (124/125, one error); Lever 3,185 (99/99); Bundesagentur 2,238 canonical URLs across 290 successful calls; Workday 959; Personio 774 postings across 34 board observations but only 34 canonical URLs; Arbeitnow 1,200; Arbeitnow visa 671; Nomado24 443; Jobicy 261; Workable 328; Himalayas 167. Source-yield totals should not be summed naïvely because identity/canonical definitions vary by source.
- Diagnostic classifications: 3 missing optional credentials, 1 upstream provider unavailable, 2 rate-limited, 2 source errors, 11 source-failure signals and 1 zero-yield signal. JobSpy providers were disabled by configuration (LinkedIn, Indeed, Glassdoor, ZipRecruiter, Bayt, Naukri, BDJobs, HelloWork); The Muse was unconfigured; Personio showed cooldown; Cloro had 2 errors; Ashby had 1 error. Do not re-enable restricted platforms without explicit authorization or infer a broad provider outage from disabled sources.
- GitHub job run evidence: scan job concluded success; Supabase aggregate telemetry write, R2 archive storage/read-back, and Supabase shortlisted-results persistence passed. Hugging Face publication steps were skipped; public publication was not performed. Preflight #44962020159 passed earlier.
- The scan's safety switches were not exposed by the summarized job list. Avoid asserting all four switches were false; in fact Supabase and R2 writes occurred, so it was definitely not a zero-write scan.
- No recovery snapshots were changed. Preserve verified snapshot artifacts.

## 2026-11-23 — Independent audit verification (read-only)
- Reviewed user-supplied `GitHub_Career_Repos_Audit.docx`. Independent Actions API readback confirms private repo latest 100 runs all failed in 2–6 seconds (median 3 seconds), latest run 2026-11-14; exact cause remains unproven and exhausted Actions allowance is only a hypothesis.
- Runner latest 100 currently: 79 success, 12 skipped, 7 failed, 2 cancelled (slightly changed from 22-Nov audit snapshot). Main smoke and private-source regression passed on 2026-11-22; R2 guardian succeeded 2026-11-23.
- Current runner main `.github/workflows/ba-cloro-isolated-scan.yml` retains weak Cloro/BA gate; partial board success can pass. PR #92 remains open and must not be merged unchanged: its stricter gate writes literal `\\n` into GITHUB_OUTPUT instead of actual line breaks, risking output parsing. Correct on a dedicated branch and test before merge.
- First 100 branches in both repositories report `protected=false`; complete branch inventory and exact settings remain unverified because branch-protection API access is denied to the connector.
- No scan or provider request was launched, no production persistence/publication occurred, and no recovery snapshot was changed.

## 2026-11-23 — Post-audit sitemap milestone
- Private repository PR #210 merged as `7d91d7c6ab5e7955fa956eddc359697b1996afb8`, adding sitemap/robots to the dashboard's public shell; production deployment intentionally remains separate and the Workers Builds hold must remain intact.
- Sitemap/robots XML and directive checks passed; no private result/data URLs are listed.
- The Cloro full-coverage defect remains confirmed on runner main. PR #92 remains unsafe to merge unchanged due to literal backslash-n output escaping; fix and validate on a dedicated branch.
- No production scan/provider request, persistence/publication, or recovery snapshot mutation occurred.

## 2026-11-23 — Branch inventory count correction
- Paginated GitHub branch API readback confirms private repo has 211 branches (100 + 100 + 11), all `protected=false`; uploaded audit counted 210. Public runner has 115 branches (100 + 15), all `protected=false`.
- Branch API flags do not substitute for administrative ruleset/branch-protection configuration. Connector could not read those settings; private Settings screenshot showed no classic branch protection rules.
- Private repository lookup for `happytiswis-sudo/Con` returned 404; do not infer status or delete anything.

## 2026-11-23 — Cloro gate correction started
- Starting dedicated branch `fix/cloro-full-coverage-gate-regression-20261123` from runner main to replace inline weak BA/Cloro success logic with a fail-closed, testable coverage gate and unit regression tests. Existing PR #92 is not merged and remains unsafe due to escaped `GITHUB_OUTPUT` newlines; do not merge it unchanged. No live provider requests, production scan, persistence, publication, deployment, or snapshot operations are authorized by this code change.

## 2026-11-23 — Cloro false-green gate fixed in PR #112; validation PASS
- Implemented on dedicated branch `fix/cloro-full-coverage-gate-regression-20261123` and opened runner PR #112: https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/112.
- Replaced permissive inline gate with `scripts/ba_cloro_coverage_gate.py`. It fails closed unless both Bundesagentur and Cloro have attempted units > 0, successful_units == attempted_units, zero errors, and non-zero unique_postings. Missing, malformed, boolean, or zero-attempt metrics fail closed.
- The helper writes proper newline-delimited `GITHUB_OUTPUT` records and adds gate results/reasons to the sanitized aggregate summary. Artifact upload remains before the final job-failure gate, preserving diagnostics for incomplete provider runs.
- Added 8 regression tests covering full pass, partial Cloro 2/8 with postings, BA partial failure, missing metrics, zero attempts/results, provider errors, malformed/boolean values, and real newline output. Runner workflow validation also parses/contracts the isolated workflow and executes the tests.
- PR #112 CI exact-head results: runner workflow validation PASS; private candidate full regression PASS (private Python suite, frontend syntax/contracts, Bridge/RPC/Worker checks, public retrieval tests, extension packaging/upload); public runner smoke PASS; Cloro credential-presence check PASS. No live provider scan was run.
- PR #92 was closed as superseded by PR #112; comment explains not to merge it.
- PR #112 has no independent reviews yet. Do not merge until an independent authorized reviewer approves and all required checks remain green. No production scan, provider requests, persistence/publication, deployment, or recovery snapshot changes.

## 2026-11-23 — Current-main reconciliation and final exact-head regression PASS
- Reconciled PR #112 branch with current runner main using a two-parent merge commit `aeb2629747ddeb64fb21702aefc6ae5a76939ffb`; first parent is prior PR head `1487136b03948962a6ebcff18d17c54f3c5f9d78`, second parent is current main `ebcf35c7794be79dd4ebc10fbf15f4af10bdba6a`. No force push; fast-forward ref update only.
- Exact reconciled head `aeb2629747ddeb64fb21702aefc6ae5a76939ffb` checks: runner workflow validation PASS (including YAML contract and new coverage unit tests); private candidate full regression PASS; public runner smoke PASS; Cloro credential presence PASS. No failed steps.
- Private full regression completed Python suite, frontend syntax/contracts, Bridge/RPC/Worker checks, public retrieval regression, extension packaging/upload and cleanup.
- PR #112 remains open and unmerged. Independent review count remains zero. Wait for an independent authorized approval before merge. No live Cloro/BA requests or production scan, persistence/publication, deployment, or recovery snapshot changes.


## 2026-11-23 — PR #112 authorized merge path and strict final validation
- User explicitly authorized merging runner PR #112 without a human GitHub approval, conditional on this assistant's documented technical review, all required CI checks passing, and GitHub permitting the merge. Do not fabricate or submit an independent approval; proceed through normal merge controls if all gates pass.
- PR branch reconciled with runner main commit `569ed77279ee127a3d0df0f9a0151f8fdfc75da6` using a two-parent merge commit; branch is now based on latest main with no behind commits.
- Code review caught a validator edge case: fractional floating-point metrics could be truncated by `int()`; validator now accepts only integer values or decimal-digit strings and rejects booleans/fractional/malformed values. Regression assertion added.
- Latest exact-head workflow validation passed, including YAML/workflow contract and BA + Cloro coverage unit tests; public runner smoke passed. Full private candidate regression passed Python suite, frontend syntax/contracts, Bridge/RPC/Worker checks, public retrieval tests, extension package checks and cleanup. No live provider requests were made.
- This handover update is documentation-only and will receive its own required PR workflow validation before merge. Production deployment remains separate; do not run a live scan, write production data, publish vacancies, deploy Cloudflare, or alter verified recovery snapshots as part of this merge.


## 2026-11-23 — PR #112 merged; release remains separate
- Runner PR #112 merged successfully into runner `main` as merge commit `4b9c968e77b31944bd355e8b36e04db26c74811c`. GitHub confirms PR state closed/merged and main points to this commit.
- Merge proceeded under the user's explicit authorization without a human approval review; no review was fabricated. PR branch was current with main (0 commits behind) and GitHub reported mergeable.
- Exact pre-merge head `218965e16ebd6332eb98252084ad7750d5ac40e6`: runner workflow validation PASS (YAML/workflow contracts, Supabase and TinyFish/Firecrawl safeguards, strict BA + Cloro unit tests), Cloro credential-presence PASS, full private candidate regression PASS (Python, frontend, Bridge/RPC/Worker, public retrieval, extension packaging/upload, cleanup), and public runner smoke PASS.
- The strict gate now requires complete attempted-unit success, zero errors and non-zero postings for BOTH Bundesagentur and Cloro; malformed, missing, boolean and fractional counts fail closed. The `GITHUB_OUTPUT` newline escaping defect is fixed; sanitized aggregate diagnostics upload before the final failing gate.
- Post-merge main workflows #45235623373 (private scanner regression/extension package, non-publishing) and #45235623256 (runner smoke) were queued at the time of this update; inspect their completion before calling the post-merge main baseline green.
- No live BA/Cloro provider requests, production scan, Supabase/R2 persistence, public vacancy publication, Cloudflare deployment, or verified recovery snapshot mutation was performed. Keep production deployment and live scan as separate, explicitly authorized release steps.


## 2026-11-23 — P1/P2 governance, Actions allocation and housekeeping investigation
- Current branch inventory: private dashboard repository 211 branches; public runner repository 116 branches. GitHub branch objects report `protected=false` for all 327 sampled/current refs (main included). This flag alone is not a complete ruleset readback.
- Administrative readback limitation: GitHub connector can read repo metadata (admin permission reported) but branch-protection GET returns 403 `Resource not accessible by integration`. Public runner rulesets endpoint returns an empty list. Do not claim safeguards enabled.
- Private dashboard rulesets endpoint returns GitHub 403: “Upgrade to GitHub Pro or make this repository public to enable this feature.” This indicates rulesets are plan-gated for this private personal repo; classic branch-protection state still needs account-owner UI confirmation. No branch settings changed.
- Private dashboard Actions sample: latest 100 workflow runs all concluded failure; newest sampled run dated 2026-11-14. Representative job API records show `runner_id=0`, empty runner name, `steps=[]`, zero billable milliseconds; job-log download returns BlobNotFound/404. This is consistent with failure before a hosted runner was allocated, not an application test failure. Exact cause (billing/spending cap, plan allowance, concurrency or GitHub-side allocation) is NOT proven: billing usage API is not exposed by this connection.
- Public runner Actions remain healthy: latest 100 sampled runs 87 success, 7 failure, 5 skipped, 1 cancelled; runner smoke and private-candidate regression after PR #112 merge passed.
- Handover sizes before cleanup: runner AI_HANDOFF.md 333,307 characters / 1,618 lines; dashboard AI_HANDOFF.md 454,371 characters / 2,155 lines. Plan is to archive old entries verbatim and retain a concise operational handover; do not discard historical evidence.
- Branch cleanup audit: 82 runner branches and 163 dashboard branches match the exact head SHA of a merged PR, are not current open-PR heads, and do not match reserved backup/recovery/verified/snapshot naming patterns. This is a preliminary candidate set, NOT authorization to bulk-delete: perform reference/active-work checks and preserve all verified recovery snapshots. No branches deleted.
- Remaining manual access needed: GitHub browser sign-in is not connected to the available browser session; use the account owner's signed-in GitHub session to confirm private-repo plan/billing and configure main safeguards if the plan supports them. Do not ask for passwords in chat.


## Governance / Actions allocation investigation — 2026-11-23
- Current public runner main at audit: `ad2053af63b3e42f6acb4903c9c9cd880a7eac3a`; branch API readback reports `protected=false`. Private source main at audit: `9154df08302330b082e81b8eeeb36dbc4c72001b`; branch API readback reports `protected=false`.
- Current public runner smoke run `45236387547` passed on 2026-11-23. It executed hosted runner setup, checkout, runner verification, privacy-safe retrieval tests and cleanup steps.
- Private repository latest sampled run `43652073604` (2026-11-14) failed before steps were exposed in the connector response. The job summary alone does not prove a billing or allocation root cause; check account Actions billing, spending limits, concurrency and repository Actions settings before conclusion.
- GitHub connector exposes read-only Actions inspection and lacks branch-protection writes, billing reads, workflow dispatch, branch listing/deletion. Do not claim configuration or cleanup completed through this connector. No recovery branch/snapshot deleted and no production scan/deployment triggered.
- Never inspect legal/terms pages. Continue with a signed-in administrative browser session if available; keep any code/config changes on dedicated branches and reviewed PRs.

### Follow-up evidence — 2026-11-23
- Private source `.github/workflows/verify.yml` is an explicit tombstone: its comment says private push/PR verification was retired because the private repository Actions compute allowance is exhausted, and its only job has `if: false`. Full validation is routed through this public runner's `private-scanner-regression.yml`.
- Sampled the 12 most recent private workflow runs; every sampled job failed with `runner_id=0`, blank runner name, no steps and 1–3 seconds elapsed. This confirms pre-runner scheduling failure, consistent with exhausted private Actions compute allowance; exact account billing/usage allocation remains to be verified in account settings.
- Full regression run `45235623373` passed on 2026-11-23: 545 private Python tests (0 failures/errors/skips), frontend/Worker contracts, extension contracts, public retrieval tests, extension artifact packaging/upload and private checkout cleanup. It tested private code SHA `9b7c5f731e9c927ce6aea6be4a21c7199871f024` against runner code SHA `4b9c968e77b31944bd355e8b36e04db26c74811c`. Current private main `9154df08302330b082e81b8eeeb36dbc4c72001b` and runner main `ad2053af63b3e42f6acb4903c9c9cd880a7eac3a` are each two documentation-only AI_HANDOFF.md commits ahead of those tested code SHAs.
- Account billing/usage, spending limit and concurrency settings remain unverified because the automation browser is not authenticated; the user's ordinary browser session is not shared. No billing/settings changes or production actions were performed.

### Operator clarification — 2026-11-23
- The operator confirms private Actions compute exhaustion is already intentionally handled by the two-repository architecture: this public runner checks out private source read-only and executes regression/production workflows using public-repository hosted runners. Do NOT pursue restoring private Actions compute or make private billing verification a release blocker. The private `verify.yml` tombstone is intentional.
- Remaining governance issue: configure branch protection on both repositories' `main` branches. GitHub API currently reports protection disabled. Browser setup via TinyFish is not yet authenticated and has intermittently failed; do not claim protection enabled until API/UI read-back verifies it.
- Current successful full regression run `45235623373` validated private SHA `9b7c5f731e9c927ce6aea6be4a21c7199871f024` with 545 tests and all frontend/Worker/extension/public-runner checks passing. Production operations remain separately gated.

### Latest operator clarification — 2026-11-23 (supersedes older pending-action wording)
- The operator explicitly confirms private-repository Actions compute exhaustion is already resolved operationally by design: this public runner checks out private source read-only and executes validation/production workflows on public hosted runners. Do not pursue private Actions billing/compute restoration, and do not list it as a blocker.
- Earlier handover notes asking to inspect private billing, account spending limits, concurrency, or restore private Actions compute are historical context only and are superseded by this instruction.
- Current GitHub integration identity is `happytiswis-sudo`; repository metadata reports admin permission on both repositories. Branch-protection endpoint reads through this connector return HTTP 403 `Resource not accessible by integration`; this is a connector scope limitation, not evidence that protection is enabled. Previously verified branch API metadata reported both `main` branches unprotected.
- Handover PR #113 (runner) and private-source PR #211 are open, mergeable and documentation-only, with no submitted reviews, inline threads, or commit-status checks. Do not merge solely because GitHub reports mergeable; validate latest state and obtain required independent review/approval or explicit operator decision.
- TinyFish GitHub browser was blocked by GitHub's temporary unusual-activity restriction. Do not retry automated sign-in. No branch-protection settings were changed. Continue supported operations through GitHub connector; use the operator's normal signed-in GitHub UI only for administrative settings unavailable to the connector.
- No `main` branch was directly modified, no branch or verified recovery snapshot was deleted, and no production scan/deployment/publish was triggered in this governance pass.

## Post-merge governance handover — 2026-11-23
- The operator clarified that external collaborator review is not required for these owner-managed repositories. The operator's explicit instruction is sufficient; do not block owner-authorized documentation PRs waiting for collaborators.
- The documentation-only governance PR was self-reviewed for scope and content, then squash-merged after GitHub reported the PR clean and its available checks passed.
- Runner handover PR #113 merged as `8ff481b45ed60aacbffd374eeedd6b98b032176d`; resulting `main` head verified at the same SHA.
- Branch protection is still disabled on this repository's `main`; the GitHub connector has no branch-protection write action and its protection read endpoint returns 403. Do not claim protection is enabled until an authenticated settings change is made and read back.
- No production deployment, production scan, branch deletion, or recovery-snapshot modification was performed.

## 2026-11-23 — Phase 0 scheduled-results reliability investigation (in progress)

- Owner-approved roadmap order: Phase 0 scheduled Results reliability; Phase 1 extension reliability; Phase 2 eligibility/relevance; Phase 3 Results workbench; Phase 4 evidence-led source/ranking improvements. Do not introduce SearXNG, embeddings/Ollama, new ATS sources or higher BA concurrency without measured benefit/rate-limit evidence; no wholesale dashboard rewrite.
- Public runner main at investigation start: `05fa477c85022b35b11540a276dd6b1035bf0cbd`. Dedicated branch: `fix/phase0-scheduled-results-reliability-20261123`. Private source main: `eb11cf17a133cdf7531876c59fa6e57ae322aa97`; private matching branch exists. Never modify main or verified recovery snapshots.
- Confirmed defect in `.github/workflows/production-scan.yml`: `Persist verified scan telemetry`, the Supabase storage guardian and `Persist completed shortlist to Supabase` are gated by manual-dispatch inputs. A scheduled event supplies no such inputs. R2 archive steps separately include a schedule condition, so private archive attempts can occur while Supabase Results persistence is skipped.
- Read-only Supabase evidence: project `plzjmyytuumxckbrrzlp` is ACTIVE_HEALTHY. Latest 10 `career_radar_private.scan_runs` records all show `history_index.event=workflow_dispatch`; no scheduled event appears in this sample. Latest record `44962287103`: 111 result rows, 18 source metric rows, `storage=supabase+r2`, R2 archive store. No database rows were changed.
- Phase 0 implementation must explicitly derive scheduled/manual retention booleans and keep three independent paths: private Supabase shortlist + manifest/telemetry; private R2 archive with its own fail-closed cost/admission guard; public publication behind BOTH existing explicit gates (`CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true` and `enable_production_publish=true`). Supabase is authoritative. Hugging Face private mirror is secondary and must not block a verified Supabase result write.
- No production dispatch, scan, Supabase write, R2 write, HF upload, public publication or deployment has been performed. Current work is investigation only. Run regression, review PR, then seek/confirm deployment approval separately.

## 2026-11-23 — Phase 0 implementation candidate opened

- Implementation PR [#115](https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/115), branch `fix/phase0-scheduled-results-reliability-20261123`; private source handover PR [#213](https://github.com/happytiswis-sudo/engineering-career-radar/pull/213).
- Workflow now explicitly enables scheduled Supabase private Results/manifest and aggregate telemetry, with independent R2 archive guard; Supabase write does not depend on HF credentials; private HF mirror remains best-effort; public publication still requires both explicit gates. README retention semantics corrected.
- Added `tests/test_scheduled_private_retention.py` and updated the existing workflow-contract expectation. Initial runner-smoke attempt on earlier candidate commit failed two tests: an outdated exact description assertion and a case-sensitive new assertion. Both tests were corrected on the current branch head; current-head rerun is pending.
- Runner workflow validation job passed on the initial candidate commit. Private-source regression job also failed later in its separate public retrieval-engine regression step; this is not yet diagnosed and must be investigated before calling the full suite green. Its private Python and frontend/Worker test steps passed; extension package steps were skipped after the downstream failure.
- No production dispatch/scan, Supabase write, R2 upload, HF upload, public publication or deployment has occurred. No history/snapshot changed. Do not merge until latest-head public runner smoke and the relevant full regression evidence pass.

## 2026-11-23 — Phase 0 validated and merged

- Implementation PR [#115](https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/115) merged as `a5986dfa07d238277532d957ee69711412b0978f).
- Exact candidate head `94ae1cf2c740a311851c02dd5855965095d8f5fe` passed:
  - Public runner smoke [45269061191](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45269061191): PASS.
  - Runner workflow validation [45269061290](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45269061290): PASS.
  - Private-source regression [45269061570](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45269061570): PASS; 499 private Python tests, 0 failures, 0 errors, 0 skips; frontend v3, extension Bridge/restricted RPC/Worker, public retrieval regression, extension package/upload and cleanup steps all succeeded.
- Scheduled workflow now enables private Supabase shortlist + run manifest and aggregate telemetry explicitly on schedule events. Private R2 archival remains separately fail-closed/guarded; HF mirror remains secondary and best-effort; public publication still requires both `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true` and `inputs.enable_production_publish=true`.
- Runner README and tests updated. No production scan was dispatched. No Supabase/R2/HF data, Cloudflare Worker or verified recovery snapshot changed.
- Next acceptance gate: inspect the next scheduled weekday run and reconcile its run ID in private Supabase `scan_runs`, shortlist row count in `scan_jobs`, source-metric count, and telemetry receipt. R2 archive success is a separate guarded outcome; public publication must remain false.

## 2026-11-23 — Phase 1 extension reliability (in progress)

- Phase 0 runner workflow fix merged as `a5986dfa07d238277532d957ee69711412b0978f`; latest runner main at Phase 1 start includes post-merge handover `0a84761f01920b3a9eaad5b2eea9038e238fc459`.
- Phase 0 checks passed: public runner smoke run 45269061191, workflow validation 45269061290, private-source regression 45269061570; 499 private Python tests passed with 0 failures/errors/skips. Actual scheduled-run Supabase acceptance remains pending the next weekday schedule; no manual production scan was triggered.
- Phase 1 private source branch: `feat/extension-quick-standard-full-api-first-20261123`, based on private main `ed0891f202ce38f9c88db76e3021b1f5eebb9b53`.
- Confirmed extension defects: Connect auto-starts/resumes a full role-catalogue run; BA API harvesting is initiated by `SEARCH_PAGE_READY` and the portal search tab lifecycle; adapter fixed to pageSize=50/maxPages=2 while popup exposes 50/100/250; no Quick/Standard/Full mode control; local progress exists but restart recovery and explicit cancellation of in-flight API requests need hardening.
- Planned fix: Connect-only flow, three explicit bounded search modes, direct API-first role processing independent of BA tab, honour 50/100/250 by page size + page count, persist server checkpoints/local cursor, restore running sessions on service-worker startup, pause/resume/stop with AbortController and durable pending queue.
- Do not increase BA API concurrency or bypass site access controls. Keep 403/429 as safe pauses and retain detail-tab fallback only for incomplete API detail capture.
- No Phase 1 code, Supabase migration/data write, production scan or deployment performed yet.

## 2026-11-23 — Phase 1 extension implementation candidate prepared

- Private source candidate branch: `feat/extension-quick-standard-full-api-first-20261123`; private source implementation PR will carry the full code and test changes. Candidate includes Connect-only popup, Quick/Standard/Full modes, API-first BA harvesting without a search-tab trigger, result limit 50/100/250 pagination, durable server/local progress checkpoints, alarm-based service-worker recovery, and AbortController-backed pause/resume/stop.
- Extension version `0.1.16`; no Supabase migration required because existing extension run counters/checkpoint storage is sufficient. No increase to BA detail concurrency (remains 4); 403/429 pauses safely.
- A temporary public-runner validation PR will call the reusable private scanner regression workflow with the exact private candidate branch and current private main as base. The temporary workflow harness is test-only and must not be merged into runner main.
- Phase 1 tests are pending. No production deployment, extension-store release, scan or database write has occurred. Phase 0 next-scheduled-run acceptance remains outstanding.

## 2026-11-23 — Phase 1 validation findings (in progress)

- Exact private candidate regression run 1: Python suite failed two stale assertions (extension version and role-plan construction); both were corrected.
- Exact private candidate regression run 2: Python suite passed all 547 tests; Node extension contract then failed one stale test selector that expected `async function advanceSearch()` before its new parameter was added. The test now matches `async function advanceSearch(`; no runtime syntax error was reported.
- Candidate includes subsequent lifecycle fixes for durable API batch alarms, pause/detail waiting alarm cancellation, manual role skip cancellation and removal of automatic BA form submission.
- Re-run the reusable private-source regression against the latest private branch head; do not merge Phase 1 until every private Python, frontend, Worker, extension API, BA pagination, schema and package check passes.

## 2026-11-23 — Phase 1 lifecycle hardening before final regression

- Prior private regression passed all 547 Python tests but stopped at one stale Node assertion because `advanceSearch` gained a parameter; that selector has been corrected.
- Candidate now fails closed on missing saved plans or changed catalogue SHA, correctly completes a final API batch exactly at the selected plan boundary, clears alarms while paused/waiting on detail fallback, and cancels incomplete detail fallback on explicit role skip.
- Search content script no longer auto-submits BA search forms. Added targeted tests for exact-boundary completion and recovery safety.
- Re-run exact private branch regression; no merge until all Python/Node/Worker/extension/package checks pass.

## 2026-11-23 — Phase 1 remaining contract corrections (in progress)

- The latest private regression passed Python and stopped in Node extension contract tests on stale expectations for the old full-plan variable, portal-block event path and detail advancement signature. Updated them to the new Quick/Standard/Full API-first contract.
- Corrected the legacy ingestion-retry path to schedule the API batch worker after the current role is reprocessed successfully.
- Re-run full private regression against the latest private branch head. Do not merge while any contract check remains red.

## 2026-11-23 — Phase 1 final safety corrections before regression

- Updated remaining Node contracts to the new bounded CV-ranked plan, API pause/cancel behavior and detail-fallback completion.
- Fixed Stop to persist a server-side pause when queued discoveries remain unsaved, and made recovery verify both catalogue SHA and plan fingerprint before rebuilding a lost local plan.
- Re-run the full private regression against the latest source branch; no merge until all checks pass.

## 2026-11-23 — Phase 1 test harness correction

- Latest exact-branch regression passed all 548 Python tests (0 failures/errors/skips); the extension/Worker contract step stopped on a JavaScript test-harness ReferenceError because early assertions referenced `popupHtml` before its declaration. Corrected those assertions to use the already initialized `popup` value.
- This was a test-only declaration-order issue, not a production-code failure. Re-run the full private regression against the updated candidate; no merge until all checks pass.

## 2026-11-23 — Phase 1 UI contract correction

- Latest full run passed all 548 Python tests; Node contract caught a genuine popup markup omission: JavaScript referenced `searchMode`, but the HTML select had not been inserted because the original text replacement missed the actual markup. Added Quick / Standard / Full select and explanatory text to the popup.
- This was a real UI wiring omission and has now been corrected. Re-run the complete private regression; merge remains blocked until all checks pass.

## 2026-11-23 — Phase 1 final regression candidate

- Updated Node extension contracts to use the declared popup variable and API-first role plan/detail lifecycle after a prior ReferenceError and legacy assertions.
- Stop intent now gates each role boundary and post-fetch continuation; watchdog alarms clear on stop. Retry-ingest resumes the API batch worker. Recovery validates catalogue SHA and plan fingerprint; exact-size final batches complete correctly.
- Full private regression must be rerun on the latest branch head before merge.

## 2026-11-23 — Phase 1 API-first contract test correction

- Latest run passed all 548 Python tests and popup mode markup contract. One remaining Node test still expected publication freshness to be set on BA portal-tab navigation. The API-first adapter correctly sends `veroeffentlichtseit` in the direct BA REST query; the test now asserts that API request contract.
- This was a stale test expectation from the previous tab-driven design, not a runtime failure. Re-run complete private regression.

## 2026-11-23 — Phase 1 freshness contract correction

- Latest private regression passed the Python suite and stopped at a redundant Node freshness assertion referencing a duplicate popup variable. The contract now reuses the already loaded popup source and verifies the exact date-range field; API adapter freshness validation remains separate.
- Re-run full private regression on the latest source branch before merge.

## 2026-11-23 — Phase 1 full regression PASS

- Private candidate code SHA `7b56aacf1895912ca0faec005d906465fd87905c` passed public-runner regression run `45272532710`: 548 Python tests, 0 failures/errors/skips; Node syntax and extension/Bridge/RPC/Worker/API-first BA pagination/abort/schema contract tests all passed; Chrome extension package artifact created/uploaded.
- ZIP SHA-256: `c7b97e22637ab2effec55400792b9731b001336a844dfe7c9e9df1f1e72ed7db`, artifact ID `14866076950`. Validation artifact only, not store-published.
- Private PR #214 is mergeable/clean against current private main `ed0891f202ce38f9c88db76e3021b1f5eebb9b53`; only documentation changed after the tested code SHA. No production deployment or scan.
- Phase 0 scheduled-run Supabase acceptance remains pending the next weekday schedule. Phase 1 code may be merged separately from production rollout.

## 2026-11-23 — Phase 1 full regression PASS

- Exact private source candidate `fc424b4e61c8ba338ab9515a2d4c36c3228ba404` passed reusable private-source regression [45272612265](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45272612265).
- 548 Python tests: 0 failures/errors/skips. 103 Node tests passed. Extension/Bridge API contracts, restricted RPC, Worker syntax, BA API result-limit pagination (50/100/250), abort behavior, frontend/Worker checks and package creation all passed.
- Public runner smoke [45272612246](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45272612246): PASS. Runner workflow validation [45272612291](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45272612291): PASS.
- Extension validation artifact SHA-256: `04de1144bc64ab5c062bf2d4bb93743f395b2491929f7f2a6211673822e5f6ac`, Actions artifact retained 14 days; not a store release.
- Private implementation PR [#214](https://github.com/happytiswis-sudo/engineering-career-radar/pull/214) is ready for reviewed merge. Production Bridge Worker deployment and extension distribution remain separate release steps. Phase 0 next scheduled-run acceptance remains pending.

## 2026-11-23 — Phase 2 reconciled-current-main regression PASS

- Reconciled private candidate SHA `e35215f19b16311c2ade44eb1f722c5585c7cb65` passed runner run `45275812009` against current private main `ff697c0b14d3126ab2d34a5e9604df47e7112939`: 559 tests, 0 failures/errors/skips; sanitized AST/import diagnostic and all extension/Worker/BA/package checks passed.
- Validation artifact ID `14866582444`, SHA-256 `a815d0c2d03ad80f44cddf4f8efe1e0b75da8cdf625bb8029108b1f511965e95`; validation-only, not production release.
- Phase 2 branch is reconciled with current private main and ready for reviewed PR. No production deployment or scan.

## 2026-11-23 — Phase 0 public-publication separation hardening (validation pending)

- The prior scheduled run `45248808801` predated the Phase 0 schedule persistence fix; its event used old runner SHA `ad2053af...` and skipped Supabase preflight, telemetry, shortlist persistence and archive-index merge. Latest Supabase Results row at that point remained manual run `44962287103` (111 rows). Next scheduled run after these workflow fixes remains the acceptance gate.
- New Phase 0 correction: scheduled/private-results runs persist to private Supabase (shortlist + discoverable run manifest) and private R2 archive independently. They no longer trigger the Hugging Face Space/dashboard mirror upload.
- Hugging Face mirror and public dashboard/vacancy publication now require BOTH `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true'` and explicit `enable_production_publish: true`. Its capacity preflight and read-back verification are also behind that explicit authorization. A private Results write cannot implicitly publish to the Space.
- This removes ambiguity while HF Space visibility could not be verified through the connected Hub metadata endpoint. Supabase remains authoritative; R2 is private archive; public mirror is separately authorized.
- Regression tests updated to assert the separation. Validation pending; no production scan or deployment performed.

## 2026-11-23 — Phase 0 publication-gate test corrections

- First runner validation reached and passed all 499 private-source tests, but two runner workflow contract tests still asserted the previous private-HF-mirror naming/gating. Updated those assertions to require the public mirror's explicit production flag and to prove schedule/private-results alone cannot trigger it.
- No workflow code rollback; the intended workflow now gates both HF capacity preflight and upload on the explicit repository authorization variable plus the manual dispatch boolean.
- Re-run the complete runner and private-source regression before merge.

## 2026-11-23 — Phase 0 strict private/public separation regression PASS

- Branch `fix/phase0-explicit-public-publication-gate-20261123` passed runner workflow validation run `45277276754`, public runner smoke `45277276856`, and private-source regression `45277276770` (499 tests, 0 failures/errors/skips).
- Tests now prove scheduled/private Supabase persistence cannot trigger the HF mirror; the HF capacity guard, upload and read-back are gated by both `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH == 'true'` and `enable_production_publish: true`.
- Phase 0 schedule acceptance remains pending the next scheduled scan on this merged workflow. No manual production scan or publication was triggered by this PR.

## 2026-11-23 — Phase 0–3 release status after Phase 3 deployment

- **Phase 0:** Runner PR #124 merged private Supabase Results + manifest persistence and private R2 archiving separately from Hugging Face/public publication. HF capacity preflight, upload and read-back require both `CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true` and explicit manual `enable_production_publish: true`. Contract regression #45277276770 passed 499 tests. Scheduled acceptance remains pending the next weekday scan at 07:30 UTC; run #45248808801 predates the fix.
- **Phase 1:** Private PR #214 merged Connect-only, Quick/Standard/Full API-first extension retrieval, durable progress/recovery and cancellation. 548 Python + 103 Node tests passed; extension ZIP is validation-only, not store-published.
- **Phase 2:** Private PR #218 merged degree/seniority eligibility corrections; reconciled regression #45275812009 passed 559 tests, 0 failures/errors/skips, including direct positive/negative cases and real-description adjudication.
- **Phase 3:** Private PR #220 merged as `f677ec1d3b748415454c608c58ac1504c1080415`; 559 Python + 104 Node tests passed. Supabase migration version `20261123223518` applied and privilege checks confirm no anon/authenticated access to private workbench tables/RPCs; service_role access only.
- **Phase 3 deploy:** Runner PR #126 merged as `706e03894fd010afed1ba53bf23b673e88b979ec`. Cloudflare deploy run [45281286280](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45281286280) succeeded. Cloudflare API confirms dashboard deployment `1c231080-e2b6-485a-b3e0-9bebd0e72c69` / version `6b9c404a-4813-4d68-9999-8704cea1498f` and Bridge deployment `3a2aee37-14b0-4052-8dd8-c5bdefb469b2` / version `dc7c2803-53ce-4b26-bb95-87f2ef51530f`, both 100%.
- **Phase 4:** Intentionally deferred until post-Phase-0 yield data is measured; benchmark BM25/fuzzy before embeddings/Ollama, verify each ATS endpoint and usable yield, and keep BA concurrency unchanged absent rate-limit evidence.
- Security advisor: new private RLS/no-policy INFO findings are expected for service-role-only private schema; leaked-password protection WARN is pre-existing and was not changed.
- Preserve all recovery snapshots. No manual production scan or public publication was triggered.


## 2026-11-23 — Production scans changed to manual-only
- User decision: no automatic production scans. The only normal start path is the dashboard **⌕ Search jobs** tab, which dispatches `.github/workflows/production-scan.yml` through the Cloudflare bridge. A GitHub Actions manual dispatch remains available for operator diagnostics.
- Removed the weekday `schedule` trigger and all schedule-event-only execution branches from `production-scan.yml`. Kept `workflow_dispatch` and all existing dashboard request inputs/dispatch semantics intact.
- Added a regression assertion that production-scan.yml has exactly one trigger (`workflow_dispatch`) and contains no scheduled-event branches.
- Unrelated scheduled maintenance workflows (R2 admission guardian and n8n health check) are not job scans and were not changed. No database, archive, public publication, production deployment, or recovery snapshot was touched.
- Runner PR [#128](https://github.com/happytiswis-sudo/engineering-career-radar-runner/pull/128) merged to `main` as `cd809f197a81e6d841c8a3ce6d15dec08af74e9c` on 2026-11-23.
- Passing hosted checks on final implementation head `a0786a363197ce186c8f5efea6967d239099443e`: workflow validation run `45284084893` PASS; public runner smoke `45284084771` PASS (105 tests); full private-source regression `45284084695` PASS. Earlier attempts caught stale tests that required a schedule; those tests were updated to assert manual-only behavior before the final green run.
- Source documentation PR [#222](https://github.com/happytiswis-sudo/engineering-career-radar/pull/222) merged as `72b9d9a7c325e5418c85b82bcfc22b81fe7deedd`.
- Verified on runner `main`: production-scan.yml contains `workflow_dispatch` only, no `schedule` trigger, and zero schedule-event execution branches. The dashboard dispatch contract was left intact. No production scan, production deployment, Supabase/R2/HF mutation, or recovery-snapshot change occurred.


## 2026-11-24 — Private-source audit remediation candidate (in progress)
- Private source candidate branch: `feat/audit-p0-p1-remediation-20261124`. The current private main at review start was `e6911b385eacf06627eeaaf66622c8e0793cf009`; runner main at review start was `b8a2ba3cf2df52f49a428f6ab17abdb7cfc881bb`.
- Candidate changes currently include explicit EU-27/EEA/UK/Europe/custom geographic scopes, separate fit/desirability/priority dimensions, extension server-side status/score filtering and new Supabase RPC migration, scan-history data-quality reconciliation, BA structured evidence and external apply links, and per-vacancy CV/cover-letter/application-email prompt generation.
- Initial runner regression [45295928831](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45295928831) reconciled the candidate with private main without merge conflicts, but failed the private Python suite (564 tests; 2 failing test methods: `test_feature_pipeline_contract.WholePipelineContractTests.test_extended_agents_are_persisted` and `test_r2_history_guard_contract.R2HistoryGuardianContractTests.test_active_frontend_loads_archive_index_and_details_with_cv_auth`). The targeted diagnostic tests had zero failures. Do not claim regression PASS.
- Subsequent candidate edits synchronized the frontend source and embedded HTML byte-for-byte and adjusted a brittle region test. These later commits have not yet been validated by a full regression.
- Direct Supabase schema read confirmed `career_radar_private.extension_discoveries.id` is bigint, `run_id` is uuid, and `scan_runs.run_id` / `scan_jobs.run_id` are text. The candidate extension-filter SQL currently assumes UUID for `p_run_id`; this mismatch must be corrected before migration. Do not apply candidate migrations to production until reviewed and tested.
- No PR has been opened, no candidate migration applied, no production scan or deployment performed, and no data/archive/recovery snapshot modified.
- Next steps: fix SQL type and verify all referenced columns/function signatures against production schema; investigate the two test failures with exact diagnostics; run complete current-main-reconciled regression; review SQL grants/RLS and score semantics; open reviewed PR only after tests pass. Deploy Workers and apply migrations only as separate approved release steps.


## 2026-11-24 — SQL schema read-back correction
- Verified Supabase `extension_discoveries.run_id` is UUID and the existing extension list RPC takes `p_run_id uuid`; the new extension discovery v2 RPC's UUID argument is correct. `scan_runs.run_id` and `scan_jobs.run_id` are text, and separate scan history/finalization RPCs use text. Do not conflate these different tables' run-ID types.


## 2026-11-24 — External audit remediation validation and release gate (in progress)
- Public runner main at intake: `b8a2ba3cf2df52f49a428f6ab17abdb7cfc881bb`.
- Validation PR #135 branch `fix/audit-remediation-clean-20261124`, head `eed03cedba54cba73b28013992c1de4863bb4710`; run #45398057560 completed successfully. The private candidate regression job and runner-control validation passed; this is code validation only, not a production deployment.
- Corresponding private PR #229 is merged to private main at `6c211b08dae172b282ec80bc653a097661e27e61`. Source changes cover ranking/geography separation, EU scopes, scan-history quality, extension discovery/assessment status, v3 application prompt actions and three additive Supabase migrations.
- The live Supabase migration ledger ends at `20261123223518`; migrations `20261124110000`, `20261124120000`, and `20261124130000` remain unapplied. Deployment workflow must remain separate until these are reviewed/applied and RPC grants verified.
- Cloudflare dashboard and Bridge Workers are present; query-string redaction remains enabled and persistent invocation logs remain disabled. Preserve all bindings/secrets and privacy settings during deployment.
- No production scan, publication, archive mutation, or verified recovery snapshot mutation is authorized in this remediation deployment.
- User prohibits opening or reading tool/site terms. Do not access terms pages or make unsupported compliance conclusions.


### 2026-11-24 — Supabase migration application verified
- Applied private PR #229's three additive migrations to Supabase project plzjmyytuumxckbrrzlp in order; live ledger now records 20261124130203, 20261124130204 and 20261124130206 for discovery filters, scan-history quality and extension detail-assessment transitions.
- Verified service_role-only grants for the new discovery and detail RPCs and the scan finalization/history RPCs; anon/authenticated execution is false.
- The detail transition queued 2,906 eligible full-detail extension discoveries. Post-migration inventory: 2,912 pending (six were already pending), 1,851 needs_detail, 0 assessed, 4,763 total. No assessment run was launched.
- Exact private candidate SHA c006a37166ba4854fce4b76f37a2f1ee4edcd075 passed runner validation run #45398057560: 581 Python tests, 0 failures/errors; frontend/Worker, extension/RPC and runner-control checks passed. Private main merged at 6c211b08dae172b282ec80bc653a097661e27e61.
- Current deploy workflow .github/workflows/deploy-cloudflare-dashboard.yml deploys both career-radar-dashboard and career-radar-bridge. Production deployment remains a separate gate and has not yet been run.


## 2026-11-24 — Pre-deployment release gate (current status supersedes earlier pending notes)
- Private source main `6c211b08dae172b282ec80bc653a097661e27e61` has a Git tree identical to the candidate SHA validated by runner run #45398057560 (`c006a37166ba4854fce4b76f37a2f1ee4edcd075`): 581 Python tests, 0 failures/errors, plus frontend/Worker, extension/RPC and runner-control checks.
- Supabase project `plzjmyytuumxckbrrzlp` is ACTIVE_HEALTHY. Migrations 20261124130203, 20261124130204 and 20261124130206 applied and verified. New discovery-list and scan-history RPCs smoke-tested; latest history correctly reports degraded after source failures. Privileged RPCs are service_role-only.
- Extension inventory: 4,763 total; 2,912 claimable/queued; 1,851 needs_detail; 74 partial-detail; 1,777 too-short (categories overlap); 0 assessed. No AI assessment was dispatched.
- Cloudflare binding names read back without exposing secret values. Dashboard: ASSETS, BRIDGE, DASHBOARD_API_KEY. Bridge: ARCHIVE_CI_TOKEN, ARCHIVES R2, CV_GITHUB_TOKEN, CV_PASSWORD, DASHBOARD_API_KEY, EXTENSION_PAIRING_PROVISION_SECRET, GENERAL_LIMITER, GITHUB_TOKEN, HF_SPACE_ID, HF_TOKEN, STRICT_LIMITER, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL. Preserve every secret and binding.
- Both Workers have query-string redaction enabled, non-persistent logs and invocation logs disabled. Dashboard traces are 10% and non-persistent; Bridge traces disabled.
- Rollback anchors: dashboard active version `6b9c404a-4813-4d68-9999-8704cea1498f` (prior `baff4ebb-6f3a-4ee6-9bfd-c027e7e9fbdd`); Bridge active version `dc7c2803-53ce-4b26-bb95-87f2ef51530f` (prior `99d55cd5-5c12-4119-a05f-cebad67433b8`).
- Canonical public runner deploy workflow `.github/workflows/deploy-cloudflare-dashboard.yml` deploys both Workers from private main. It validates code, preflights CLOUDFLARE_API_TOKEN/CLOUDFLARE_ACCOUNT_ID without exposing values, then runs Wrangler. Do not start a production scan.


## 2026-11-24 — Production deployment completed and smoke-tested
- Runner PR #138 merged to main at `5d205be35b85115dc907cc1bd892b0e3bd3f62d0`. Production deployment run #45400758065 completed SUCCESS and deployed both Workers from private source main.
- Dashboard Worker deployment `789ab3d3-30b7-4047-b340-5fdb4cf5a2cf`, version `38de7324-fa65-476c-8705-88ba39f45907`, 100% traffic; rollback version `6b9c404a-4813-4d68-9999-8704cea1498f`.
- Bridge Worker deployment `d9d5c41f-69da-4897-9e12-9c85744d76c7`, version `310400aa-46e7-4445-b863-bda87f081f4e`, 100% traffic; rollback version `dc7c2803-53ce-4b26-bb95-87f2ef51530f`.
- Post-deploy read-back confirms dashboard/Bridge bindings preserved; no secret values were read. Both redact query strings, persist no logs, and have invocation logs disabled. Dashboard traces remain 10% non-persistent; Bridge traces disabled.
- Browser smoke test: dashboard root loaded; Test connection returned `Cloudflare health API returned success.` and Connected. Results loaded 111 rows; Scan history loaded 28 runs and 36 workflow executions; Applications loaded 2 Supabase records. Extension results page rendered and correctly required Master CV/Roles password; none supplied. No records mutated.
- Supabase migrations applied and RPC grants verified. Extension inventory remains 4,763 total; 2,912 queued/claimable, 1,851 needs_detail, 0 assessed. No production scan or assessment batch started.
- PR-only deploy preflight validates source and Cloudflare credential presence without deploying; only merge/push to main triggers actual deployment.
- Verified recovery snapshots, R2 archives and production history were not modified. No tool/site terms pages were accessed.
- Follow-up audit items remain separate work: compact CV evidence payload; multilingual technical synonym/ESCO layer; regional alias/geocoding; source registry/coverage matrix and health UI; unknown-vs-no-gap states; threshold consolidation; stale workflow/legacy UI cleanup; richer application detail; search-form simplification; session-level password UX. Do not invoke all 2,880 prompt variants or auto-dispatch the 2,912 queued assessments. Keep deterministic eligibility gates authoritative.


## 2026-11-24 — Supabase advisor read-back after production deployment
- Supabase health advisor returned no lints.
- Security advisor reports 11 INFO RLS-enabled/no-policy findings, all in `career_radar_private`. Verified anon/authenticated have no schema USAGE or table SELECT; service_role has both. This is deny-by-default and must not be weakened to silence the linter.
- One security WARN remains: Supabase Auth leaked-password protection disabled. No supported connector action exposes this setting, so it was not changed. Reassess via supported project Auth settings after confirming Supabase Auth flows; this is separate from the custom CV/Roles Worker password.
- Performance advisor reports 66 unindexed foreign keys, 3 auth RLS init-plan findings, 143 unused indexes and 5 duplicate indexes. These are project-wide; no unindexed-FK finding targets `career_radar_private`. Unused-index findings include `scan_jobs` and `extension_discoveries`; keep indexes until real workload evidence justifies removal. Do not drop shared/public automation indexes blindly.
- No additional schema changes were made from advisor output; production deployment and smoke-test status remains unchanged.


## 2026-11-24 — P1/P2 backlog intake; deployed release frozen
- User requested remaining P1/P2 audit work via dedicated feature branches, reviewed PRs, exact-SHA regression, and separate deployment. Never commit experiments on main, never overwrite/delete verified recovery snapshots, and never trigger production scans during this work.
- Baseline private source main `8fd1f6d044b4f9ce03ebeff2288cdfa874018fca`, runner main `f7be3511848a3822aa98a0881a6fc48dac7947e7`. Compared with deployed source `997f3d2f2933e15cf5d63807952d1fb4e3fda17a` and runner `5d205be35b85115dc907cc1bd892b0e3bd3f62d0`: only handover files changed; runtime trees are identical to deployed production.
- Validated supplied registry: 2,880 unique prompt variants, 12 archetypes × 15 domains × 4 locales × 4 seniority bands. JSON is compact component manifest; CSV expands all prompts. Runtime integration should reconstruct variants dynamically, route relevant checks only, deterministic-first, one consolidated model call maximum except borderline adjudication. Do not call all variants or trust illustrative costs as vendor pricing.
- Existing runtime already has EU scopes, fit/location separation, scan quality status, extension server-side filters, v3 application prompts, BA extension schema/Retry-After tests and unknown-gap wording. Do not reimplement these. Audit current code before every task.
- Prioritize P1: compact CV profile/version cache/token telemetry; multilingual synonym/ESCO-ready evidence ontology; collision-safe location parsing/geocoding; source registry/coverage/health; richer deterministic dedupe; role/opportunity taxonomy; score/assessment semantics; extension heartbeat/expiry/resume and bounded dry-run assessment backfill. BA per-host pacing only after checking scanner-side path; no retries/bypass for 401/403.
- P2: source health drawer and search plan; richer application detail/checklist/follow-up status; search form simplification/sticky action; session-level editor unlock; scanner modularization and stale workflow/UI cleanup only after reference graph proves safe; concise searchable handovers/ADRs.
- Audit raised a hosted-runner policy question. User forbids reading terms pages; do not open them or claim compliance. Keep production scans manual-only.
- No runtime code, database, Worker, production scan, archive, Hugging Face artifact, or verified recovery snapshot changed during intake. Feature work must use separate branches/PRs and exact-SHA runner validation; deploy only after merge in a separate release gate.


## 2026-11-24 — P1 milestone 1 validation complete
- Private source PR #235 merged to main at `34b4024b1cadff17f73e0a78d0921d4883bebdd1`; production is not yet deployed. Runtime tree is ready for a separate deployment after remaining P1 work or a dedicated release gate.
- Validation-only runner PR #142 closed without merge after run #45405353072 passed: 589 Python tests, 0 failures/errors; frontend; extension/Bridge/restricted-RPC/Worker contracts; public retrieval regression; Chrome extension package build/upload. Public runner smoke test passed. No deployment or production scan was triggered.
- P1 feature integrates compact 2,880-variant registry routing into one AI request (5–8 relevant checks), evidence-linked <=2,200-character CV profile, scan-local versioned cache key, provider token telemetry, and Results specialist-lens UI. Deterministic 54-check engine and hard eligibility gates remain authoritative.
- CSV/JSON prompt mismatch found and resolved in runtime: the expanded CSV's activation paragraph is authoritative; all 2,880 CSV prompts reconstruct exactly after correcting the abbreviated JSON suffix and specialist-name punctuation. Shared prompt dimensions are deduplicated per vacancy to control token budget.
- No Supabase migration, Cloudflare deployment, production scan, R2/HF archive mutation or recovery snapshot change. Next P1 task: measured BA host governor, then multilingual skill ontology and collision-safe regional location normalization.


## 2026-11-24 — P1 milestone 2 validation complete: BA host governor
- Private source PR #237 merged to main at `348ba7094a8239a1d20c20a88d0b2020c4708bb2`. No production deployment or BA scan was triggered.
- Exact private branch run #45406823726 passed 596 Python tests, zero failures/errors; frontend contracts; extension/Bridge/restricted-RPC/Worker contracts; public retrieval regression; Chrome extension package build/upload (SHA-256 `2d373b7b404dcc2eff9e1dce8aed9e0d25a7f44beefb77ffd117321dc5192fdc`). Validation-only runner PR #144 closed without merge.
- Scanner-side BA v6/v4 search/detail now share host pacing, Retry-After, bounded jittered retry, no 401/403 retry, circuit breaker and host metrics. Production before/after 429/403 rate measurement awaits an authorized manual scan; do not start one autonomously.
- Stable deployed release remains untouched. No database migration, Cloudflare deploy, archive mutation or verified recovery snapshot change.


## 2026-11-24 — P1 milestone 3 validation complete: multilingual ontology
- Private PR #239 merged to main at `0fbb281ea85988430c9c58737ae90213fdec7991`. No production deployment or scan triggered.
- Exact private branch run #45408182000 passed 604 Python tests, zero failures/errors; frontend; extension/Bridge/restricted-RPC/Worker contracts; public retrieval regression; Chrome extension package uploaded. Validation-only PR #146 closed without merge.
- New ontology covers 14 internal engineering skill concepts and four locales (en-GB/de-DE/fr-FR/nl-NL), exact evidence phrase matching, accent normalization, idempotent alias expansion, ESCO-ready but unmapped metadata and CV profile concept IDs. No fabricated ESCO mappings or extra production requests.
- Stable deployed release remains untouched. No DB migration, Cloudflare deployment, archive mutation or recovery snapshot change.


## 2026-11-24 — P1 milestone 4 validation complete: location normalization
- Private PR #241 merged to main at `d569c4a357c49f3a6525850e867416630b342286`. No production deployment or scan triggered.
- Exact private branch run #45410727950 passed 611 Python tests, zero failures/errors; frontend; extension/Bridge/restricted-RPC/Worker contracts; public retrieval regression; Chrome extension package build/upload (artifact ID `14927284978`). Validation-only runner PR #148 closed without merge.
- Location parsing now has collision-safe city/state aliases, foreign-country precedence, UK/Ukraine and USA/Busan protection, and source-provided BA coordinate extraction. The established West filter remains configured clusters only; NRW/Bavaria are Germany-wide but not West. UI and README clarify.
- Stable deployed release remains untouched. No DB migration, Cloudflare deployment, archive mutation or recovery snapshot change.


## 2026-11-24 — Clean paired validation branch for P1 cross-source dedupe

- Private candidate: `feat/p1-cross-source-dedupe-clean-20261124`, based on private main `be8a34844e52b4365fa49dfeac4f0485f9bfbeff`.
- Runner validation branch: `ci/validate-cross-source-dedupe-clean-20261124`, based on runner main `739be3ead219c2937e8584c46edf0c120928c661`.
- An earlier reused branch was closed without merge after review found unrelated source changes. This clean branch is the only candidate for validation.
- Candidate validation must resolve the exact private feature-branch SHA, compare against current private main, perform a clean ephemeral merge and run the full non-publishing regression suite. No production scan, publishing, data write or Cloudflare deployment.
- Preserve all recovery snapshots and archives. Do not access tool/site terms pages; production scans remain manual-only.


### 2026-11-24 — Cross-source dedupe candidate validation prepared

- Clean runner validation branch now routes commit marker `[cross-source-dedupe-clean]` to private candidate `feat/p1-cross-source-dedupe-clean-20261124`; this mapping is additive and leaves all existing routes unchanged.
- Runner PR merge will trigger the existing non-publishing private full regression against the exact candidate branch. The workflow must report candidate SHA and base reconciliation. No scan or publishing step is enabled.
- Source implementation includes conservative SimHash matching, same-provider separation, posting-date guard and source/application link preservation. The candidate has not yet passed full CI; do not call PASS.
- No production deployment, database write, scan, publication or recovery-snapshot change.


## 2026-11-24 — Final exact-SHA rerun for cross-source dedupe

- Private candidate branch is `feat/p1-cross-source-dedupe-clean-20261124`. It received final safeguards after the first validation attempt started: same-provider feed-family normalization, source-adapter-based merge metrics, and BA `externeUrl` preservation.
- The earlier run #45478463216 was started before those final changes and must not be used as acceptance for the final candidate.
- This runner branch adds only a harmless workflow comment to trigger the existing push-path validation; the commit marker routes to the same private candidate branch. The workflow remains non-publishing.
- Exact private head SHA, clean merge-base reconciliation and all full-suite checks must be confirmed from the resulting run before PR #245 can be marked ready or merged.
- No production scan, publishing, data write, deployment or recovery-snapshot mutation.


## 2026-11-24 — Re-run after one test-fixture-only correction

- Prior final-candidate run #45478864757 checked out the candidate, reconciled it with main, and executed 623 Python tests; one new application-link fixture assertion errored because it still referenced `application_url` after the fixture correctly switched to BA `externeUrl`.
- The assertion has been corrected on private candidate branch `feat/p1-cross-source-dedupe-clean-20261124`; no production implementation defect was indicated.
- This runner branch adds a harmless workflow comment so a new main push with marker `[cross-source-dedupe-clean]` starts the exact private candidate regression again. Do not accept the earlier failed run.
- No production scan, data write, publishing, deployment or recovery-snapshot mutation.


## 2026-11-24 — Third exact-SHA regression required after concurrency hardening

- Previous exact candidate run #45479139981 passed 623 Python tests, frontend contracts, extension/Bridge/RPC/Worker checks, 105 public retrieval tests and extension packaging. It is not acceptance for the new final candidate because a post-run review added atomic identity grouping and ambiguous-match retention.
- Private candidate remains `feat/p1-cross-source-dedupe-clean-20261124`; new source changes serialize shared index/group updates across source workers and keep multi-group ambiguous matches separate.
- This branch adds only a harmless workflow comment; commit marker `[cross-source-dedupe-clean]` routes to the exact private candidate. No publishing or production scan is enabled.
- No production deployment, database write, archive mutation or recovery-snapshot change.


## 2026-11-24 — Final exact-SHA P1 F15 regression PASS

- Private PR #245 merged as `dea29762406f8902adfc9f7ee36b3102c65f6bad`; candidate branch `feat/p1-cross-source-dedupe-clean-20261124`, tested SHA `0307b06cf124a8429ce0227d94883bb3f6b5b8c0`.
- Final runner regression #301 / run `45479938845`: 624 Python tests passed (0 failures/errors); frontend contracts passed; extension, Bridge, restricted RPC and Worker checks passed; public retrieval suite passed 105 tests; Chrome extension artifact `14961607502` uploaded.
- Artifact SHA-256: `902565859bfa79c8411302211c807e330aed7b7c112ccfcf12f66424dfab59dd`.
- Runner workflow remained non-publishing. The run checked out the exact private candidate, reconciled the current base in an ephemeral workspace, removed the private checkout, and packaged the extension. No production scan, Supabase/R2/HF write, public publication, Cloudflare deployment or recovery snapshot mutation.
- Runner PRs #152, #153, #154 and #155 are validation-routing/handover changes only and were merged to make the exact candidate runs reproducible. The previous failed run #45478864757 was fixture-only; it is superseded by run #45479938845.
- Production release remains separate and unchanged. Continue using GitHub Actions only for non-publishing regression and deployment workflows; keep production scan workflow manual-only.


## 2026-11-24 — P1 F14 regional source registry validation route prepared

- Private candidate branch: `feat/p1-regional-source-registry-20261124`, created directly from private main.
- Added one explicit non-publishing regression route for commit marker `[regional-source-registry]`; it resolves the exact private candidate branch and retains the existing ephemeral merge/full-suite behavior.
- No production scan, publication, Supabase/R2/HF write, Cloudflare deployment, secrets change or recovery-snapshot mutation.
- Do not accept this candidate until a fresh full regression validates its exact head SHA.


## 2026-11-24 — Re-run F14 after employer metadata coverage refinement

- Earlier run #302 / `45482044587` passed the prior candidate (634 Python tests; frontend/extension/Worker contracts; 105 public retrieval tests; extension artifact uploaded). It is not acceptance for the latest candidate SHA.
- Private branch `feat/p1-regional-source-registry-20261124` now additionally consumes declared `germany_first`, country/location aliases and source category tags from the existing additional-board registry.
- Re-run the full exact-SHA private regression. The commit marker `[regional-source-registry]` selects the candidate through the existing non-publishing path.
- No production scan, database write, publication, Cloudflare deployment, secrets change or recovery-snapshot mutation.


## 2026-11-24 — Final F14 fixture-only exact-SHA regression

- Run #303 / `45482639796` was triggered after employer-country and category metadata changes. A subsequent fixture-only correction switches the category test to a query-discovery adapter, isolating role affinity from the The Muse US/Canada geographic constraint.
- Private candidate branch `feat/p1-regional-source-registry-20261124` has advanced again. Run #303 is not acceptance for the current candidate SHA.
- This branch adds only a harmless workflow comment to trigger the existing full non-publishing private regression. Exact candidate checkout, ephemeral merge, full suites and package checks remain unchanged.
- No production scan, publication, data write, deployment or recovery-snapshot mutation.


## 2026-11-24 — F14 malformed-history guard requires final exact regression

- The final source registry candidate now safely treats malformed historical numeric metrics as unknown/zero rather than allowing corrupt private telemetry to abort scan planning. A focused regression covers malformed raw counts, freshness, yield, error and attempt values.
- This advances the private branch beyond the candidate currently being validated by run #304. Run #304 is not acceptance for this final head.
- This branch adds only a harmless trigger comment for the existing exact-ref, non-publishing full regression.
- No production scan, data write, deployment, publication, archive or recovery-snapshot mutation.


## 2026-11-24 — F14 candidate handover commit requires exact-SHA regression #306

- The private candidate's AI handover was updated after run #305 started, which advanced the candidate branch head. Run #305 remains useful test evidence for the pre-handover SHA but cannot accept the latest branch head.
- Trigger a new exact-SHA full non-publishing regression against current private branch `feat/p1-regional-source-registry-20261124`, including its final malformed-history metric guard and handover update.
- The existing workflow's exact candidate checkout, ephemeral base merge, full Python/frontend/extension/public retrieval tests and package validation remain unchanged.
- No production scan, data writes, deployment, publication, secret changes or recovery-snapshot mutation.


## 2026-11-24 — F14 final exact-SHA validation completed

- Final run #306 (`45483913150`) completed successfully against private candidate SHA `b4fd69f56111351bd647c0ffecff4dab709839f7`, base `f02a4d87abcc996c8bed108f08f10960a1aef568`.
- 637 Python tests passed; 0 failures/errors/skips. Frontend contracts passed; Extension Bridge, restricted RPC and Worker checks passed; public retrieval suite passed 105 tests.
- Chrome extension package artifact `14963541380` uploaded; SHA-256 `e05ef9f5d3c69e1ca8aeecb7dba69c71a9322984b583fc1bbe5352973e145502`.
- Validation workflow routing PRs #157, #158, #159, #161 and #162 were validation-only. No production scan, data write, deployment or publication occurred.
- Private F14 implementation merged via PR #247 as `2c61437c26fc22b07b2e309fa42334b5b20fb9f0`.
- Do not deploy this code as part of validation. Production release remains a separate, explicit operation.


## 2026-11-24 — F14 worldwide-remote ranking regression follow-up

- Post-merge review found that country-specific non-remote ATS boards with declared country metadata could receive a positive regional score under `world_remote` because the country-match branch was evaluated after the remote-feed branch.
- Private fix branch `fix/f14-world-remote-source-ranking-20261124` now explicitly ranks remote feeds above non-remote sources and keeps Bundesagentur lower still; all selected boards remain in the queue.
- Added a regression covering remote feed vs country-specific ATS vs Germany-only BA ordering.
- This runner route is validation-only and selects the exact private fix branch for a fresh full regression. No production scan, data write, deployment, publication or recovery-snapshot mutation.


## 2026-11-24 — F16 source-health archive UI exact-SHA validation route

- Add a commit-message route for the dedicated private candidate `feat/p1-f16-source-health-20261124`.
- Candidate scope: archive source-health field retention and v3 archive-detail UI; exact JS/CSS embedding parity and contract tests are required.
- Run the existing non-publishing full private regression with exact candidate checkout and ephemeral merge against current private main.
- No production scan, data write, deployment, publication, secrets change or recovery-snapshot mutation.


## 2026-11-24 — F16 LinkedIn access evidence refinement requires exact-SHA rerun

- After run #308 started, the private F16 candidate was refined to display the LinkedIn experiment's separate operator-authorization flag, live-adapter-enabled flag and actual valid-posting evidence. The UI explicitly warns that configuration flags do not prove platform permission.
- This advances the private candidate SHA. Run #308 is baseline evidence only and must not accept the latest candidate.
- Add a second commit marker route to the same exact private F16 branch and run a fresh full non-publishing regression.
- No production scan, data write, deployment, publication, secret change or recovery-snapshot mutation.


## 2026-11-24 — F16 exact embedded asset parity correction requires run #310

- Run #308 (`45485869415`) failed only `test_active_frontend_loads_archive_index_and_details_with_cv_auth`: embedded `public/index.html` JS had wrapper newlines and was not byte-identical to `public/frontend-v3.js`.
- Private candidate corrected the inline script to exact file bytes and recorded the cause in its handover.
- Run #309 is not acceptance for the latest private candidate SHA. This validation-only route triggers a fresh exact-SHA full non-publishing regression #310.
- No production scan, data write, deployment, publication, secret change or recovery-snapshot mutation.


## 2026-11-24 — F16 exact CSS asset parity correction requires run #311

- Run #310 (`45486346106`) passed the Python suite but failed the frontend v3 contract because the embedded stylesheet had wrapper newlines and did not exactly equal `public/frontend-v3.css`.
- Private candidate now embeds exact CSS file bytes, matching the already-corrected JS embedding. No functional CSS change was introduced by this correction.
- Trigger a fresh exact-SHA full non-publishing regression against the latest private F16 branch. Run #310 is not acceptance for this updated candidate.
- No production scan, data writes, deployment, publication, secrets change or recovery-snapshot mutation.


## 2026-11-24 — F14 worldwide-remote ranking validation #307

- Runner PR #164 merged at `078a05f755a11f992b1fe8e50ed149fddc3256e4`; public runner smoke run `45484906460` and workflow validation run `45484906529` completed successfully.
- Exact private candidate validation: run #307 / `45484933548`, candidate `fix/f14-world-remote-source-ranking-20261124` at SHA `8cf7633a7a1b9c0e11dca15df4184d80b5525558`; ephemeral base `8fcd32c247b843f01438f97e250381d510d6a5ca`.
- 638 private Python tests passed (0 failures/errors/skips); frontend, Extension Bridge/restricted RPC/Worker contracts and 105 public retrieval tests passed; Chrome extension artifact `14963698349` uploaded (ZIP SHA-256 `435a15128994388a9eb1e25702c41063831729ff92f4ffa835010769d447c21e`); private checkout cleanup passed.
- Run #307 was non-publishing. It did not scan production, write Supabase/R2/HF, deploy Cloudflare, publish vacancies or mutate recovery snapshots.
- After run #307, private `main` advanced to `62f8fdde0013af38a7d7f5e8941b70616072ce09`; revalidate the isolated candidate against the latest base before merging. Do not infer that #307 tested this later base.


## 2026-11-24 — F14 worldwide-remote exact-candidate revalidation #313

- Runner validation run #313 / `45488332931` completed SUCCESS. Exact private candidate branch `fix/f14-world-remote-source-ranking-20261124` was verified at SHA `455739ad190089b8cc4535c6e3db3af49096e0a3`; private `main` base was `62f8fdde0013af38a7d7f5e8941b70616072ce09`; merge base `8fcd32c247b843f01438f97e250381d510d6a5ca`.
- Candidate and latest private base were reconciled only in the ephemeral runner workspace; no branch push occurred.
- Full private Python suite: 638 tests, 0 failures, 0 errors, 0 skipped. Frontend syntax/contracts passed; Extension Bridge/restricted RPC/Worker checks passed; public retrieval regression passed 105 tests; Chrome extension packaging/upload and private checkout cleanup passed.
- Chrome extension artifact ID `14963164971`, size 29,384 bytes, SHA-256 `032a78fcc178b59b6c59f2fefb04a75159bb6022fa75d354821c75b545c81d30`.
- The validation was non-publishing. No production scan, Supabase write/migration, Cloudflare deployment, Hugging Face publication, R2/archive mutation or recovery-snapshot change.
- The private fix is under reviewed PR #250. Merge only after review of the minimal `source_registry.py` ordering change and its regression test; production deployment remains a separate approval/release step.


### Follow-up — F14 handover and merge status

- Private PR #250 has since been reviewed and merged as `f0f3b97fa47c6dca2eaddd8b8393066c38d20a27`; private handover PR #251 merged as `830e98f9ed230758359ac43986a73f8825ddaad4`.
- Runner handover PR #169 validation run #428 / `45490816663` completed SUCCESS: `validate`, Cloro credential-presence and full private-suite jobs passed. The separate `private-candidate-regression` job was skipped by workflow routing; the full-suite job itself passed.
- Run #428 validated the runner handover PR workflow, not a new private source candidate; run #313 remains the source-fix exact-SHA acceptance run.
- No production deployment or scan was triggered; recovery snapshots remain untouched.


## 2026-11-24 — Final audit implementation plan and release boundary
- User approved five separately reviewed stages: P0 reliability/ranking/EU scope; P0/P1 extension retrieval/assessment; P1 specialist-agent router/multilingual matching; application prompts/dashboard integration; P2 UX/maintainability.
- Private specification branch `docs/final-audit-implementation-spec-20261124` adds `docs/CAREER_RADAR_FINAL_IMPLEMENTATION_SPEC_2026-11-24.md` with per-stage acceptance criteria and exact-SHA test requirements. The private AI handover carries the same milestone.
- F14 worldwide-remote source ordering is already merged and exact-candidate validated by run #313; it is not outstanding work. Preserve this behavior in later ranking tests.
- Current runner main at planning start: `e1038bf41125c573f39b92b5af5db5451797978a`; private main at planning start: `830e98f9ed230758359ac43986a73f8825ddaad4`.
- Runner remains the non-publishing validation plane. Each stage must validate the exact private candidate SHA against refreshed private main; keep private checkout ephemeral and read-only. CI success is not deployment or production data validation.
- No production scan, production deployment, publication, Supabase write/migration, Cloudflare setting change, Hugging Face mutation, R2 archive mutation or recovery snapshot change was performed for this milestone.
- Next: review/merge private specification PR; then validate each stage independently. Deployment requires its own explicit release gate, credential preflight, rollback plan and read-back verification.


## 2026-11-24 — Stage 1 geographic baseline and exact candidate pending
- Private Stage 1 regression PR #253 targets `feat/stage1-eu-geography-regression-20261124` at candidate SHA `16a1b08f703bb10b919c0c5f51387959423d5482`.
- Current private source already implements EU-27/EEA/UK/custom-Europe in request planning and geographic gating; new tests lock scope separation and collision behavior. The full Stage 1 ranking/scan-quality audit remains open.
- Exact-candidate validation must use public runner `private-scanner-regression.yml`, with candidate ref and base `main`; record exact private candidate/base SHAs and all test/job results. No production operations.
- No production scan, deployment, persistence/publication, Supabase/R2/HF mutation or recovery-snapshot change.


## Stage 1 exact-candidate validation routing — 2026-11-24
- Reviewed runner PR #173; merged as `8aea3ba15f7c4210315726cf45d8d0d629c84e6d` with commit marker `[stage1-exact-candidate]`.
- The marker maps the runner push-triggered private regression to private branch `feat/stage1-eu-geography-regression-20261124`. The private candidate head at the time of routing was `fcc60979b2048f3a7396d94d1181f97d2132bc0f`, based on private main `830e98f9ed230758359ac43986a73f8825ddaad4`.
- Workflow still performs ephemeral read-only private checkout and full suite; no production scan, publication, deployment or private write is enabled.
- GitHub connector's `fetch_commit_workflow_runs` wrapper filters to pull-request-triggered runs and returned no runs for the push merge SHA. The exact push-triggered run ID/result must be independently read from Actions before claiming PASS. Do not infer success from the merge.
- Private Stage 1 remains incomplete: funnel reconciler helper exists but is not integrated into scanner/dashboard status; score-dimension and sort-precedence audit remains open. Do not start Stage 2 until those gates and exact-candidate regression pass.


### Stage 1 candidate revision correction — 2026-11-24
- Private candidate head was corrected after the first marker-triggered runner merge: latest SHA `fa851256c9b83efe0a707d10b74ae995ce059b00` (base `830e98f9ed230758359ac43986a73f8825ddaad4`). The earlier marker may have validated a prior head and is not valid evidence for this latest SHA.
- Re-trigger only after the final implementation/integration commit is stable. The existing marker maps to the same private branch; the workflow's checkout assertion records the resolved SHA in logs.
- Connector workflow-run enumeration filters to pull-request-triggered runs, so the push-triggered run after merge `8aea3ba15f7c4210315726cf45d8d0d629c84e6d` could not be inspected through that action. Do not claim a pass until the actual Actions run ID/jobs/logs are reviewed.
- Stage 1 remains open; do not begin Stage 2 yet.


### Latest Stage 1 candidate head — 2026-11-24
- Private branch `feat/stage1-eu-geography-regression-20261124` now points to `6fbfe34a83b26bd8f39ec809e9da35f2519c349e` (base `830e98f9ed230758359ac43986a73f8825ddaad4`). This supersedes the earlier candidate SHA in the prior note.
- Exact full-suite evidence is still absent. The marker merge happened before the latest candidate hardening; rerun after the candidate and remaining Stage 1 integration work are final. Workflow-run listing via the available connector is PR-only and combined status returned no checks for the runner push commit.


## Stage 1 final-candidate execution preparation — 2026-11-24
- Private candidate work extends the existing mainline scan-quality implementation rather than adding a second reconciler. Main already contains `20261124120000_career_radar_scan_history_quality_status.sql` and finalization logic comparing shortlist counts with persisted `scan_jobs`; keep it read-only in CI.
- Candidate adds qualification outcome counts at scanner output and validates the partition in `scan_telemetry.verify_scan_telemetry`; `publish_supabase_jobs.build_diagnostics` carries the aggregate into the existing private diagnostics JSON. No migration/write/production operation.
- Scoring changes bound fit dimensions to 48+30+17, preserve geography/junior/entry/AI confidence separately, and report advert skill evidence coverage and AI-reported confidence separately. Selected sort precedence and stable tie-breaks are regression-tested.
- Final exact candidate SHA will be taken from the private feature branch after code/test freeze. Use the `[stage1-final-score-funnel]` marker route (once merged) to invoke the full non-publishing private suite; record exact candidate/base/workflow SHAs, run ID, every job outcome and artifacts. No deployment.


### Stage 1 exact regression attempt — 2026-11-24
- Run `45497463976` validated private SHA `6c9f4863266259f189eaf48352af48920e2a3853` and base `830e98f9ed230758359ac43986a73f8825ddaad4`; clean ephemeral merge. Full private Python suite: 649 tests, 1 failure, 0 errors, 0 skipped. Only failing test: `R2HistoryGuardianContractTests.test_active_frontend_loads_archive_index_and_details_with_cv_auth`; it detected that embedded JS in `public/index.html` did not match `public/frontend-v3.js`.
- Private candidate corrected by synchronizing the embedded frontend. New exact candidate SHA: `be0da4c450334b6f2ffc19a7974f8cf226fc7ceb`. Run #45497463976 does not validate this SHA. Trigger a fresh full regression before any merge.
- Next runner marker is `[stage1-final-score-funnel]`; existing routing maps it to the private Stage 1 feature branch. Keep the test path non-publishing and inspect every job before recording PASS.


### Stage 1 full regression result and superseding candidate — 2026-11-24
- Run `45497904380` succeeded on exact private candidate `be0da4c450334b6f2ffc19a7974f8cf226fc7ceb`, base `830e98f9ed230758359ac43986a73f8825ddaad4`, merge base same. Python: 649 tests, 0 failures/errors/skips; frontend syntax/contracts, extension Bridge/restricted RPC/Worker syntax, public retrieval 105 tests, extension packaging/upload and checkout cleanup all PASS. Artifact ID `14969378027`, artifact digest `8716f8dd1bb8d8b52bbb6b57823c8a96db1980d1dd62d486beaa90ade8e9b10a`, local zip SHA-256 `1ee5b992af1f83b39e7f4e29f2c4908f1903fed18be5144d6a9cf5b65c489651`.
- Post-pass diff review discovered default Results sort still called undefined `newestFirst` and coverage UI displayed weighted coverage under an unweighted label. Both fixed and regression assertion added; embedded frontend resynchronized.
- New candidate SHA `1d5f19b03e0716f34aa62c598e0e40edfabf3b66`; the prior run cannot validate it. Re-trigger full suite with existing `[stage1-final-score-funnel]` marker and inspect all jobs before merge.


## Stage 1 final exact-candidate PASS and merge — 2026-11-24
- Private PR #253 merged to private main as `2fbff2813aaab735d11ffda0524173b9d925590a`.
- Exact candidate SHA `1d5f19b03e0716f34aa62c598e0e40edfabf3b66`; base/merge base `830e98f9ed230758359ac43986a73f8825ddaad4`.
- Runner run #45498672617: SUCCESS. 649 Python tests, 0 failures/errors/skips; frontend syntax/contracts PASS; Extension Bridge/restricted RPC/Worker syntax PASS; public retrieval 105 tests PASS; extension package/upload PASS; private checkout cleanup PASS.
- Runner workflow commit `ae3a31ad787d5403a9edd966bc513e36c579351f`; workflow file SHA `d4176a7698b8b2ae3205e883bdf45537d1ce00ab`. Artifact ID `14970546531`; uploaded digest `44b1170658720677455d84c95043fb552a6809ba2e3df5e8d93d69a4417038f5`; package SHA-256 `a8e8576ff03ff931d3914e7388a638ada9d3bef57dfa876c4c960780e10b1d85`.
- Stage 1 complete. Stage 2 is authorized to start on a separate branch from new main. Keep production release separate and preserve recovery snapshots.


## Stage 2 kickoff — non-publishing validation plan (2026-11-24)
- Stage 1 merged and exact-candidate validated. Private main at Stage 2 start: `23caab3a0073b2655bc7e017696482f552003405`; runner main: `b42ce426b3868948849f547d1cdbdffbacee5864`.
- Stage 2 acceptance: structured BA fields and URLs preserved; bounded pagination/retry/host pacing; saved and unassessed records visible; assessment states reconciled; heartbeat/expiry and resumable bounded batches; no-claim/terminal reasons explicit; retrieval separate from assessment.
- Validate only exact private feature branch via ephemeral read-only checkout. No live provider crawl, production backfill, Supabase production write/migration, deployment, publication, archive mutation or recovery snapshot change.


## Stage 2 validation audit finding — 2026-11-24 (before implementation)
- Private source main at Stage 2 kickoff: `c1fc6621c5dba2f7416c5e3447eebdac339313b1`; Stage 2 feature branch: `feat/stage2-extension-retrieval-assessment-20261124`.
- Existing BA API pagination/retry/pacing, full-detail capture, bounded assessment worker and 30-minute claim expiry are already present. Preserve them.
- Verified claimability defect: the SQL assessment claim RPC accepts any description >=400 characters and does not require `detail_completeness='full'`; readiness count also omits unassessed/null-status rows that the RPC treats as pending. This can claim partial records and make UI claimable counts disagree with the worker.
- Verified diagnostics gap: when claim returns no rows, worker output has aggregate counters but no explicit no-claim reason/status snapshot. Planned fix uses existing service-role discovery status RPC, returning counts only; no job text or IDs.
- Stage 2 will add a forward-only migration and tests; do not apply it to production or run the assessment workflow. Exact-candidate regression remains read-only/non-publishing.


## Stage 2 validation handover — 2026-11-24
- Current runner main at handover: `c769224546f153e5933367f78a9d127b1e017941`; private source baseline: `c1fc6621c5dba2f7416c5e3447eebdac339313b1`.
- Private Stage 2 candidate branch: `feat/stage2-extension-retrieval-assessment-20261124`. It contains a forward-only full-detail claim guard, claim/readiness count alignment, completion validation, and aggregate-only no-claim reason diagnostics. Exact candidate SHA is to be refreshed after the private handover commit and must be validated explicitly.
- Existing BA pagination/retry/per-host pacing, structured field capture, bounded assessment batch loop, checkpoint recovery and 30-minute stale-claim expiry are preserved; regression must cover them rather than reimplement them.
- Validation must use the private scanner regression workflow with an ephemeral read-only private checkout and exact candidate/base SHA assertions. It must not run a provider crawl, assessment backfill, production scan, Supabase production write/migration, deployment, publication or archive operation.
- The current workflow has no Stage 2 candidate marker route. Add a narrowly scoped route only if needed for push-triggered exact-candidate validation; do not change production workflow behavior. Inspect every job and artifact before recording PASS.
- Production publishing remains disabled. CI/merge does not authorize Cloudflare deployment, Supabase migration, Hugging Face/R2 publication, production scans or recovery-snapshot mutation.


## Stage 2 runner route merged and exact-candidate regression PASS — 2026-11-24
- Runner PR #179 merged to runner main as `2bb59a1056a07259bbc8db3a3db8ecbec2b949bb`. It adds the exact push-marker route `[stage2-full-detail-claim-guard]` to the existing non-publishing private regression workflow.
- Post-merge run #45502544647 completed SUCCESS on exact private candidate branch `feat/stage2-extension-retrieval-assessment-20261124`, candidate SHA `d8559e5cc4c11c22992f031e84d47ef1b5d17802`, base `main` resolved to `c1fc6621c5dba2f7416c5e3447eebdac339313b1`. Isolated integration merge was clean; no merge commit was pushed to the private candidate branch.
- 656 private Python tests: 0 failures, 0 errors, 0 skipped. Frontend syntax/contracts PASS. Extension Bridge, restricted RPC and Worker syntax PASS. Public retrieval regression: 105 tests PASS. Chrome extension artifact upload PASS (artifact ID `14972380864`, digest `dd490a85f09f96138a4d2ed7145f4d2ba218601b89382f678afc840ce28858e0`, zip SHA-256 `39636a7a4e2fd8e54588bb998b6c0c5b2f13c9494727332ab220347f6fc994d1`). Private checkout cleanup PASS.
- Private PR #255 subsequently merged as `1a811c5c764446bced4ed3a2c483511203f65a9a` after exact-candidate regression. The migration was not applied and no deployment/publication was performed.
- Cloudflare build configuration's production path include remains the explicit `__PR207_RELEASE_HOLD__/**` sentinel; the Stage 2 changed paths are excluded from production auto-build. The PR's Cloudflare check was Preview-only.
- Production scans, provider crawls, assessment backfills, Supabase production writes/migrations, Cloudflare deployment, Hugging Face/R2 publication, archive changes, secrets and recovery snapshots remain untouched.


## Stage 3 agent-router validation route — HISTORICAL / SUPERSEDED
- This earlier in-progress note is retained here only as an audit-history marker. Stage 3 was subsequently merged in private PR #258, and provider compatibility was merged in private PR #260. Final exact-SHA validation and post-merge verification are recorded in the `Stage 3 agent-router and provider compatibility — FINAL / VALIDATED` section at the end of this handover. Do not treat the former candidate/route checklist below as outstanding work.


## Sanitized private regression diagnostics — 2026-11-24
- Added a failure-only diagnostic step to the non-publishing private regression workflow. It reruns the suite only after a failure and emits test ID, exception class, source basename and line number; it deliberately suppresses exception messages, test stdout/stderr, vacancy data, CV content and credentials.
- This supports diagnosing exact-candidate regression failures without exposing private test payloads in the public runner logs. No production workflow, source checkout permissions, scan, publication, deployment or credentials were changed.


## Diagnostic parser correction — 2026-11-24
- Corrected the failure-only private regression diagnostic to parse unittest's stored traceback strings rather than treating them as traceback objects. Output remains limited to test ID, exception class, source basename and line number; exception messages and test stdout/stderr remain suppressed.




## Stage 3 agent-router and provider compatibility — FINAL / VALIDATED (2026-11-24)
- Main Stage 3 implementation merged in private PR #258 as `96eee77b94468d4bcac476f45355b2d43e044f0b`. Exact candidate `61003416f39f2506aedaeb4e6358082ce0690820` against base `32af9ab2b6ccca54729eee05631c902e1685821c` passed runner #45508167578: 686 private Python tests, 0 failures/errors/skips; frontend, Extension Bridge/restricted RPC/Worker, 105 public retrieval tests, extension package and cleanup all passed. Artifact ID `14973838037`, SHA-256 `b3973560e81443901cad8cddf285b1c96bb1ae6a8e0ff5f736c2c26256e8cae7`, 29,382 bytes.
- Provider compatibility follow-up merged in private PR #260 as `e458863706725199266793845a51c83a6a775dea` (merge parent `6f7443f82e744cd6f5aed07cd9ff940e93c84250`). Exact candidate `c37cc0763f6944e34a6c12df5229690e61113ba0` passed initial runner #45509206939 against base `d23f9d94f17bdb9e562e783744a16ead48dda01c`, then passed required latest-base runner #45509462247 against `6f7443f82e744cd6f5aed07cd9ff940e93c84250`, which matches the actual merge parent. The latest-base run passed all 686 private Python tests (0 failures/errors/skips), frontend, Extension Bridge/restricted RPC/Worker, 105 public retrieval tests, extension package/upload and cleanup. Artifact ID `14974857162`, SHA-256 `da48586bbe143ea4a021e16df5a244d791a24e3c043e33d291dd27f051846603`, 29,382 bytes.
- Provider correction: normalize provider name safely before provider-specific JSON-mode selection and classify malformed assessment JSON case-insensitively, preserving backup-provider eligibility and correct failure telemetry.
- The exact regression runs were read-only and ephemeral; current private main was integrated only in the runner workspace. No production scan/provider request, Supabase production write/migration, Cloudflare production deployment, Hugging Face/R2 publication, archive mutation, secret change or verified recovery-snapshot modification occurred.
- Cloudflare `career-radar-dashboard` latest production deployment remains `2026-11-24T13:11:18.354674Z`, before the Stage 3 and provider correction merges. No production deployment followed either merge. Production release remains separate.
- Post-merge verification: private main `47d1cc2a21125ab0f1e35950dbecb6ee89886221` was run as both candidate and base in runner #45509945449 and #45509958298; both full workflows passed all private Python, frontend, Extension Bridge/restricted RPC/Worker, 105 public retrieval, package/upload and cleanup steps. First post-merge artifact ID `14975023656`, SHA-256 `b7c906479a7cf3b7ab50d3dfab527755801a62af7dee9770a158ef573c7864ad`, 29,382 bytes.
- Stage 3 code is merged and validated. Next milestone: fresh Stage 4 audit against the approved five-stage specification; do not infer later-stage scope from Stage 3 notes.



## Production scan #37 — preserved baseline and retrieval diagnosis (2026-11-25)

- **Immutable baseline run:** [runner workflow #37 / run 45515114028](https://github.com/happytiswis-sudo/engineering-career-radar-runner/actions/runs/45515114028), completed SUCCESS in 10m 9s. Runner main SHA: `ad081f04dc20e31ef489cd6b7f89a0b8d3f2c6c1`; private scanner main SHA checked out by that run: `1f63fe2da1f781ea258ff4008d710ab613b7a36d`. Preserve the run and artifact; do not delete, replace, rerun over, or overwrite this baseline.
- **Aggregate artifact:** `career-radar-source-yield`, artifact ID `14978166719`, SHA-256 `d322fa6bde708938f26c0e88150484502cb170f01c4a21665dd23fc069d500f0`, 2,752 bytes, expires 2027-02-23. It is an aggregate-only GitHub Actions artifact; no Supabase/R2/HF scan-results write occurred. It is the canonical baseline record.
- **Funnel:** 27,583 raw URLs; 25,014 global unique canonical URLs; 25,014 usable postings; 25,781 retrieved vacancy identities; 24,569 newly discovered; 1,212 historically seen; 667 cross-source duplicate URLs; 1,827 same-run duplicate postings deduplicated; 238 duplicate postings merged; 13,721 collected postings; 514 shortlisted. Qualification: 629 assessed, 0 explicitly eligible, 629 review-required, 1 hard-excluded. AI assessed 6.
- **Track coverage:** 35/35 catalogue tracks reported; 280 queries planned, 210 attempted and successful, 0 failed, 0 explicitly skipped, 70 unobserved, 0 unconfigured. Every track had 8 planned, 6 attempted/successful and 2 unobserved. 24 tracks had returned vacancies; 11 returned zero. Zero-yield tracks: Energy, Infrastructure & Inspection; Energy, Water & Public Utilities Operations; Engineering Data & Digital Improvement; Facilities, Industrial Operations & Compliance; Food, Packaging & Consumer Production; Industrial Technical & Technician Opportunities; Materials, Laboratory & Metrology; Renewables, Utilities & Sustainability; Supply Chain, Planning & Procurement; Technical Sales, Applications & Commercial Engineering; Transport, Port & Intermodal Logistics.
- **Interpretation:** the 11 zero-result tracks are not proven to have no vacancies. The uniform 6-of-8 attempted pattern across all 35 tracks plus 70 unobserved outcomes indicates an allocation/outcome-observability gap that must be reconciled. The aggregate artifact deliberately excludes per-query/board identity and query strings, so it cannot identify which exact two planned provider tasks per track lacked terminal outcomes. Do not relabel unobserved as failed or skipped; do not increase provider budgets merely to make the counter reach 280/280.
- **Source-family yield:** Greenhouse 10,824; Ashby 5,774 (124/125 attempted units successful, 1 error); Lever 3,154; Bundesagentur 1,558 unique canonical URLs from 2,105 raw; Arbeitnow 1,200; Arbeitnow visa 684; Workday 1,018; Personio 800 usable postings (33 unique employer-board URLs); Workable 328 unique URLs from 495 raw; Jobicy 256 unique from 512 raw; Nomado24 469; Himalayas 93; SmartRecruiters 54; Cloro 37 (6/8 successful, 2 errors); Pinpoint 34; Remotive 15 unique from 30 raw. LinkedIn alerts yielded no URLs. The Muse was not configured because its optional API key was absent.
- **Sanitized provider classifications:** diagnostic counters report 3 missing optional credentials, 1 upstream-unavailable signal, 2 rate-limit signals, 2 source-error signals, 3 source-failure signals and 1 zero-posting-yield signal. These are classification counters, not a one-to-one incident ledger. Source-failure counts additionally identify Personio cooldown (1), The Muse unconfigured (1), Cloro (2) and Ashby (1). Cloro's two failed tasks and Ashby's one failed unit are reflected in source yield. Exact board/query/provider response detail is not in the public aggregate artifact; do not invent HTTP status codes or attribute a specific zero-yield track to a provider.
- **Persistence boundary:** Supabase preflight and all Supabase telemetry/results writes were skipped; R2 archive writes were skipped; Hugging Face archive/mirror publication was skipped. The run read historical HF data for retrieval planning and created only the aggregate GitHub Actions artifact. GitHub artifact retention is intentional and must remain intact.
- **Next engineering investigation (no production scan authorized):** inspect the exact planned-track task list and terminal-outcome emission for every provider represented in `track_query_boards`; reconcile planned identities with `board_outcomes` matching keys; determine whether the 70 are genuinely unexecuted or missing instrumentation. Add a private, redacted diagnostic that maps track × provider to planned/attempted/succeeded/failed/skipped/unobserved counts without exposing query text, board slugs, vacancy records, CV data or credentials. Add fixtures proving each provider path emits terminal outcomes, including successful-empty and provider-error cases. Separately inspect why the 11 zero-result tracks received no vacancies despite the large global funnel; distinguish provider coverage, search-term relevance, geography, deduplication and downstream eligibility filters. Keep any fix on a dedicated branch and reviewed PR; run full regression before merge.
- **Provider follow-up priorities:** explain Cloro's 2/8 failures and Ashby's 1/125 error from sanitized failure categories; determine the Personio cooldown's scope; decide whether The Muse is worth configuring; identify the other optional-credential classifications without exposing secret names/values. Do not assume missing credentials caused the 11 zero-result tracks.
- **Release gate:** no subsequent production scan, provider call, Supabase write, R2 write, Hugging Face publication, Cloudflare deployment, secret change, archive mutation or recovery-snapshot change is authorized by this investigation. The next production scan requires separate explicit user authorization after code-level diagnosis and regression.



### Code-level explanation of the 70 unobserved track outcomes (investigation addendum)
- The uniform 70 is strongly explained by a telemetry-plan mismatch, not 70 provider failures: `radar.py` assigns `track_query_plan` to all `workday`, `nomado24` and `himalayas` boards. Track coverage expands each map into one planned row per track. Workday explicitly emits `workday_query_outcomes`; JobSpy emits `query_outcomes`. Nomado24 and Himalayas do not emit matching per-track terminal outcome records.
- Adapter inspection confirms the semantic mismatch: Nomado24 iterates its own board query terms but returns only a posting list, without query-level outcomes; Himalayas performs two broad cursor reads and a fixed set of provider search filters, not the synthetic per-track query phrases assigned by the scanner. The track report matches outcomes on exact `type|slug|city|query`; the generic board-level outcome has an empty query and cannot satisfy the per-track rows.
- The missing count is exactly 70 = 35 catalogue tracks × 2 providers (Nomado24 and Himalayas). This is a high-confidence code-level explanation for the 70 unobserved counters. It does NOT mean either provider failed: this run retrieved 469 Nomado24 postings and 93 Himalayas postings. Nor does it mean the 70 catalog track searches were actually executed as planned.
- Required fix: stop creating synthetic per-track query plans for bulk/feed adapters unless they truly execute each exact track phrase and emit a matching terminal outcome. Either (a) instrument the provider's actual query/filter units with explicit query outcomes and a valid track mapping, or (b) report those providers as aggregate source yield only and exclude them from track-query planned counts. Add regression fixtures for both adapters and exact planned/outcome reconciliation. Do not patch main or run another production scan to prove this.
- This correction explains the telemetry gap, not the 11 zero-result tracks. Those tracks require a separate evidence-based analysis; do not attribute their zero yield to Nomado24/Himalayas or to the unobserved counters without per-track source evidence.


### Private scanner provider-track diagnostics validation — 2026-11-25
- Private candidate branch: `fix/provider-track-diagnostics-20261125` in `happytiswis-sudo/engineering-career-radar`.
- Runner workflow #325 (run ID 45595597283) was a non-publishing full-suite validation attempt. It failed during test import and reported 4 failures plus 2 errors across 667 discovered tests; downstream frontend/extension stages were skipped.
- Root causes identified from sanitized runner logs: indentation in the private adapter test module, legacy track-coverage assertions expecting raw `query_details`, a partial-success status mismatch, Nomado cursor-loop regression, and a stale Cloro isolation assertion. These have been corrected on the private candidate branch.
- The sanitized diagnostic helper itself failed because it used `re.findall`/`re.match` without importing `re`; the runner workflow branch `fix/private-regression-diagnostic-import-20261125` now fixes that and adds a narrow pull-request trigger for handover/workflow changes. The candidate title marker `[provider-track-diagnostics]` selects the exact private candidate branch.
- No production scan, deploy, publication, Supabase/R2 writes or recovery snapshot changes were performed.


### Provider-track candidate regression dispatch — 2026-11-25
- Runner PR #196 merged as `f41a0c4c51a6d0e0ddb06443e14ee3ddbba8b3f7`.
- The non-publishing private regression workflow now has a narrow pull-request trigger for runner handover/workflow changes, imports `re` in its sanitized diagnostics, and maps the `[provider-track-diagnostics]` title marker to private branch `fix/provider-track-diagnostics-20261125`.
- A runner handover-only PR with that title marker is being opened to trigger the exact private candidate's full regression suite. No production scan or deploy is involved.


### Provider-track regression retry — 2026-11-25
- Runner PR #197 triggered non-publishing private workflow #328, run ID 45596259032, against the exact private candidate branch.
- The retry reduced the full-suite failures from 4 failures + 2 errors to 1 failure + 1 error across 667 tests.
- Sanitized diagnostics isolated the remaining issues to: (1) one final indentation defect in `tests/test_public_source_adapters.py`; (2) a privacy-contract assertion in `tests/test_track_coverage_report.py` expecting the prior label rather than the new aggregate-only label.
- Both have now been corrected on the private candidate branch. The full suite must be rerun before merge.


### Provider-track regression retry #2 — 2026-11-25
- Runner PR #197 workflow #329 (run ID 45596422492) validated the exact private candidate and discovered 697 tests; only one assertion failed.
- Sanitized diagnostic: `test_public_source_adapters.PublicSourceAdaptersTests.test_himalayas_records_provider_units_without_track_claims`, assertion at line 486. The adapter stopped on a short first page despite a valid `nextCursor`.
- Corrected the adapter to follow an explicit continuation cursor even when the current page contains fewer than the requested page size. This is the provider's actual continuation contract and preserves truthful page-unit counts.
- Re-run the full suite on the latest private candidate head before merging either implementation PR.


### Full regression result and latest candidate update — 2026-11-25
- Runner workflow #330, run ID 45596592603, completed SUCCESS for private candidate SHA `cbe713b3593002bc4b674b2cf0ed14ee35a96728`: 697 Python tests passed; frontend syntax/contracts passed; extension Bridge/Worker contracts passed; public retrieval-engine regression passed; Chrome extension package was created and uploaded as a non-production artifact.
- The private candidate was then improved with the exact scan #37 source-plan decomposition: six Workday boards × 35 catalogue terms = 210 real track-query units; Nomado24 also runs the 35 catalogue terms but previously lacked outcomes; Himalayas broad pages/filters were falsely assigned track cells. Latest branch keeps Nomado24 track mapping/outcomes and removes Himalayas synthetic track attribution.
- The same review found the static Workday title regex rejected 67 of 185 titles in the 11 zero-result catalogue tracks; exact catalogue-title acceptance and fixtures for all 11 tracks are now on the private branch.
- Workflow #330 does NOT validate these post-run additions. Trigger a fresh exact-head regression before merging PR #266. No production scan/deploy/write/publication occurred.


### Provider-track regression retry #3 — 2026-11-25
- Runner workflow #331, run ID 45597639040, validated the expanded Nomado track-attribution changes and the 11-track title/query fixtures. The full Python suite reported one test-module import error.
- Sanitized diagnostic: `unittest.loader._FailedTest.test_source_upgrade_v2`, `IndentationError` at loader.py line 339. The new query-generation fixture used four-space method indentation in a legacy test class whose methods use one-space indentation.
- Corrected the new test method to match the existing class indentation. No production code change is implicated by this import error. Rerun the exact latest private candidate head.


### Exact-head full regression PASS — 2026-11-25
- Runner workflow #332, run ID 45597818540, completed SUCCESS against private candidate head `83aeccc6d45fc9c7a469dedd58306f30ff1e8a12`.
- Passed: full private Python suite; frontend syntax/contracts; extension Bridge, restricted RPC and Worker syntax; public retrieval-engine regression; tested extension package creation/upload; cleanup.
- The candidate includes the corrected scan #37 decomposition (six Workday boards × 35 catalogue terms, plus 35 real Nomado24 track queries; Himalayas provider-scope only), all-11-track catalogue query-generation fixtures, and all-11-track Workday title-gate fixtures.
- No production scan, deployment, Supabase/R2 write, HF publication, or recovery-snapshot change occurred. PR #266 remains open until final PR review/merge.


### Final refreshed-head regression dispatch — 2026-11-25
- Private PR #266 has refreshed exact head SHA `e75e9fb3ce88fcfcf53398af5aab8a615be4b30c`; base `main` is `3dc341ea9d61cbef760c9a490563b0e39bd817f4`, with zero commits behind.
- Previous workflow #332 (run ID 45597818540) passed all stages against the preceding code head `83aeccc6d45fc9c7a469dedd58306f30ff1e8a12`.
- Trigger a fresh exact-head non-publishing regression against PR #266's current head `e75e9fb3ce88fcfcf53398af5aab8a615be4b30c` before merging. The change since #332 includes only the refreshed private handover/operations/decision-log records.
- Keep production scan, Cloudflare deployment, Supabase/R2 writes and Hugging Face publication out of this workflow.


### Final cooldown attribution review — 2026-11-25
- Runner workflow #334 (run ID 45598631382) completed SUCCESS against private head `e75e9fb3ce88fcfcf53398af5aab8a615be4b30c`, passing full Python, frontend, extension Bridge/Worker, public retrieval-engine, packaging/upload and cleanup stages.
- A subsequent code review found a cooldown accounting edge case: Workday/Nomado24 track maps were not converted to explicit skipped outcomes when a board was held by cooldown. The private candidate now expands each held `track_query_plan` entry into a `skipped` outcome and has a focused regression test.
- The cooldown correction post-dates #334. Trigger a new exact-head non-publishing regression after the PR head and this handover are refreshed; do not merge based solely on #334.


### Cooldown correction exact-head regression gate — 2026-11-25
- Latest private candidate head is `931ed57f76e54bc339fb9e635e76ae3d1630c3ad` (PR #266, base main `3dc341ea9d61cbef760c9a490563b0e39bd817f4`, zero commits behind).
- Runner #334 (run ID 45598631382) passed every regression stage for the previous candidate head `e75e9fb3ce88fcfcf53398af5aab8a615be4b30c`.
- The only post-#334 code change is the cooldown-skipped track-query expansion helper plus its unit test, with private handover updates. Run the full non-publishing workflow against exact head `931ed57f76e54bc339fb9e635e76ae3d1630c3ad` before merge.


### Exact-head provider-track regression PASS — 2026-11-25
- Runner #338 (run ID 45599372877) completed SUCCESS against private PR #266 head `931ed57f76e54bc339fb9e635e76ae3d1630c3ad`.
- All stages passed: private Python suite, frontend syntax/contracts, extension Bridge/restricted RPC/Worker tests, public retrieval-engine regression, Chrome extension package creation/upload, cleanup.
- This run includes the cooldown skipped-track correction, which now records each track/query from cooldown-held Workday/Nomado boards as explicitly skipped instead of unobserved.
- Private PR #266 is ready for merge; no production scan, deployment, Supabase/R2 write or HF publication was performed by the validation workflow.


### Provider-track diagnostics merged — 2026-11-25
- Private implementation PR #266 merged to scanner `main` as `4560abb8bb3689c7ec6d9eee8fcc66f62acc1988`.
- Private post-merge handover PR #267 merged as `c8956da3c3374d5c937e6d61ce53166457d8850d`.
- Runner handover PR #197 merged as `1e6b80f16ac99e5c6abe56049b33d6c2374e2371`.
- Exact-head non-publishing runner #338 (run ID 45599372877) passed all regression stages against private code SHA `931ed57f76e54bc339fb9e635e76ae3d1630c3ad`, including the cooldown skipped-track correction.
- Deployment is a separate manual action using `.github/workflows/deploy-cloudflare-dashboard.yml`. It requires `CLOUDFLARE_API_TOKEN` secret and `CLOUDFLARE_ACCOUNT_ID` Actions variable. The workflow checks presence without printing values, then deploys dashboard Worker/assets and the Search Bridge Worker. No production scan is part of that workflow.
- No production scan was run during code validation or merge. Preserve this separation.


### Cloudflare production deployment verified — 2026-11-25
- Workflow `deploy-cloudflare-dashboard.yml` run ID `45600445145` completed SUCCESS from runner `main`.
- Cloudflare credential preflight passed without exposing values.
- `career-radar-dashboard` deployed successfully; current version `70f30710-0010-4030-bd5c-60f4e9e5fc6b`, 100% traffic.
- `career-radar-bridge` deployed successfully; current version `11218a2c-f498-4262-bc2a-2d90c1d92186`, 100% traffic.
- Cloudflare API deployment records confirmed both current 100% deployments.
- No production scan, Supabase/R2 write, or Hugging Face publication was triggered. A production scan remains a separate explicit authorization gate.


### Provider × track telemetry persistence regression routing — 2026-11-25
- Added a narrow runner pull-request trigger for metadata updates plus a title marker `[provider-track-telemetry-persistence]` that resolves the private checkout to `feat/persist-provider-track-funnels-20261125`.
- The workflow still runs only the non-publishing private scanner regression/package validation. It does not dispatch a production scan, deploy Cloudflare, write Supabase/R2, or publish to Hugging Face.
- Exact private branch head must pass all existing stages before the implementation PR is merged.
- Keep any production scan as a separate explicit release gate.


### Exact-head validation trigger for telemetry persistence PR #270 — 2026-11-25
- PR #270 implementation head: `f21e5b18cf3bdc6d87b29310c6fd09d68c4f809b`.
- Runner #343 (run ID 45603312511) passed the full suite, but its log confirms it validated private `main` at `94d09fdf7d26f09ca5ce2eaa34757a9607b13a1d`, not PR #270. It is not an acceptable merge gate for #270.
- This handover-only runner PR is titled with marker `[provider-track-telemetry-persistence]` to route the private checkout to `feat/persist-provider-track-funnels-20261125`. The workflow must assert the exact private head SHA and run every existing regression/package/cleanup stage.
- Keep private PR #270 open and unmerged until that exact-head run completes SUCCESS. This workflow is non-publishing only; no production scan, deployment, Supabase/R2 write or Hugging Face publication.


### Corrected exact-head regression for private PR #270 — 2026-11-25
- Final review removed duplicate provider telemetry dictionary entries in private commit `42755ee5e8b59a89358841a7a4c0668e15ffbeed`.
- Previous run #344 passed the prior candidate head `f21e5b18cf3bdc6d87b29310c6fd09d68c4f809b`; it is not the final merge gate after this cleanup.
- PR #201 synchronize event must rerun the non-publishing full suite against the current branch head `feat/persist-provider-track-funnels-20261125` and assert the exact updated SHA `42755ee5e8b59a89358841a7a4c0668e15ffbeed`.
- Keep private PR #270 open until every full-private-suite stage succeeds on this corrected exact head. No production scan, deployment, Supabase/R2 write or Hugging Face publication.


### Corrected exact-head regression PASS — run #345 — 2026-11-25
- Exact private candidate SHA: `42755ee5e8b59a89358841a7a4c0668e15ffbeed`; current private base: `94d09fdf7d26f09ca5ce2eaa34757a9607b13a1d`. The runner reconciled the candidate in an ephemeral workspace and confirmed a clean integration diff; no branch was pushed by that merge step.
- Runner workflow run ID `45607235467` completed SUCCESS. Full private Python suite: 105 tests passed; frontend syntax/contracts, Extension Bridge/restricted RPC/Worker, public retrieval-engine regression, extension package creation/upload, private checkout cleanup and post-job cleanup all passed.
- Chrome extension artifact was uploaded successfully (artifact ID `15017558293`; SHA-256 `44609df0d57a41974b2bd2afaaccdbb2e92469ceca2144b1d260155badc3b916`).
- This PASS is for the corrected exact head above and supersedes the earlier #344 result for merge-gate purposes. No production scan, live provider request, Cloudflare production deployment, Supabase/R2 write or Hugging Face publication was performed.


### Exact-head regression route for scan #38 telemetry reconciliation — 2026-11-25
- Private scanner PR #271 branch: fix/scan38-provider-track-telemetry-20261125.
- This runner PR adds only a title-marker route `[scan38-telemetry-reconciliation]` to check out that exact private candidate. It must run the complete existing non-publishing private Python, frontend, extension, public retrieval, package and cleanup stages.
- Keep private PR #271 open until the run succeeds against the exact branch head and the aggregate artifact privacy checks pass.
- This workflow does not run a production scan, deploy Cloudflare, write Supabase/R2, or publish to Hugging Face. Scan #38 (45608496646) remains immutable baseline; no recovery snapshot may be overwritten or deleted.


### Scan #38 telemetry correction validation and merge — 2026-11-25
- Runner PR #202 merged as e0c7239a0c19baa675788448540f7a4043e27038. It adds exact candidate routing marker [scan38-telemetry-reconciliation] to private branch fix/scan38-provider-track-telemetry-20261125.
- Exact non-publishing regression run #347 (45623134467) checked out private candidate SHA 30c7a6f43e165149eb9d284202faaa792743d550 and reconciled against private main 520d9dfcf8c42763d2124ccf0b1fc55a32841c36. Full private suite passed 704 tests, 0 failures/errors/skips; frontend, Extension Bridge/restricted RPC/Worker, public retrieval tests, Chrome extension packaging/upload and cleanup all passed. Artifact ID 15028185684, SHA-256 50926b7804c90fdd520ae641ab1423a388e3df86c23eb98aef16e659829f5889.
- Private scanner PR #271 merged as f6802e814a5f988954c50085fafed77efd488c73. This corrects query-level source-yield counters and explicitly exports safe provider × track aggregates.
- Scan #38 (45608496646) remains the immutable production baseline. No production scan, Cloudflare deployment, Supabase/R2 write or Hugging Face publication was triggered by this validation/merge. Production deployment remains on hold pending the separate seven-track query-breadth investigation and a future evidence-backed release decision.


### Exact-head regression route for bilingual zero-yield track terms — 2026-11-25
- Private scanner PR #273 branch: feat/bilingual-zero-yield-track-terms-20261125.
- This runner PR adds only the title-marker route `[bilingual-track-term-rotation]` to check out the exact private candidate for full non-publishing regression.
- The candidate adds bilingual catalogue-title terms to seven zero-yield tracks while preserving one query per track per provider; no live provider request or production scan is included.
- Keep PR #273 open until exact-head full suite and public data-safety checks pass. Production deployment remains on hold; scan #38 and recovery snapshots remain immutable.


### Bilingual catalogue-term rotation merged — 2026-11-25
- Search breadth PR #273 merged to private main as 9cc358987c89cfb09448c8e6204ad57224d52b96. It adds English catalogue-title terms to the seven historically empty tracks while retaining German aliases. Focused mode remains one query per track per provider; planned query budget remains unchanged (35 Nomado24 + 210 Workday = 245).
- Exact non-publishing runner regression #350 / 45624214489 verified private candidate branch feat/bilingual-zero-yield-track-terms-20261125 at exact SHA c7f0aef4b5cfce07abb06d49d945e1624d311ccf, reconciled against private main c977254436b73ab63a1e149c6531dd24986baa66. Full private suite passed 705 tests (0 failures/errors/skips); frontend contracts, extension Bridge/RPC/Worker, public retrieval-engine tests, package/upload and cleanup all passed. Artifact ID 15026797848; SHA-256 3c8ae3d2b1b656b4fe560bcfa34b231ba3666ab6389196dfdf8c71b24cc95fd3.
- Runner routing PR #204 merged as b4372c3fc490b753873a4728f2d1fc27d17124f5. Runner workflow validation #482 completed SUCCESS.
- The seven-track fix is validated offline only. No live provider requests or production scan were run to prove improved market yield. A future production scan must be separately authorized and compared with immutable scan #38. Deployment remains on hold; no Supabase/R2 write, Hugging Face publication or recovery snapshot mutation.


### Scan #39 AI, shortlist funnel, novelty and Personio diagnostics candidate — 2026-11-25
- Private scanner candidate branch: `fix/scan39-ai-telemetry-personio-20261125`.
- Candidate work is code-only and must be validated by the full non-publishing private regression route `[scan39-ai-coverage-telemetry-personio]` against the exact branch head.
- Changes include documented NaraRouter alias defaults (`auto/naraya.ai` / `auto/bynara`), Inception Mercury default `mercury-2.5`, validated OpenAI-compatible completion envelopes, and queue token reservations based on estimated prompt tokens rather than the maximum input ceiling for every request.
- Assessment accounting remains one terminal result per queued item; controlled fallback/cooldown behavior is retained. No provider is contacted by offline regression.
- Personio XML adapter now records raw rows, processed rows, valid postings, invalid/duplicate IDs, missing titles and truncation, making the observed XML-to-accepted-posting drop explainable.
- Shortlist funnel now counts unique vacancy identities at rule, geography, qualification and assessment stages, with fail-closed reconciliation; novelty comparison uses the same normalized employer/title/canonical-URL identity basis (Personio requisition IDs only for generic URLs) for retrieval and shortlist history.
- No production scan, provider request, Cloudflare deployment, Supabase/R2 write, Hugging Face publication or recovery snapshot mutation is permitted by this candidate. Production remains HOLD pending exact-head regression and review.


### Scan #39 exact-head regression refresh — 2026-11-25
- Private scanner PR #279 current candidate head: `undefined` on branch `fix/scan39-ai-telemetry-personio-20261125`.
- Runner PR #209 routes title marker `[scan39-ai-coverage-telemetry-personio]` to this candidate. Any candidate branch update requires a new exact-head regression; do not treat earlier run #366 as current-head validation.
- Run #366 / 45638786149 checked an earlier candidate head and failed on three stale provider-contract assertions (Mercury model alias, byNara model alias and Inception JSON-mode expectation). Those tests are being aligned to the provider contracts and the latest shortlist-stage accounting changes are included in the next candidate head.
- The runner remains strictly non-publishing. Production scan, live provider requests, deployment, Supabase/R2 writes and Hugging Face publication are prohibited; scan #38 and verified recovery snapshots remain immutable.


### Scan #39 candidate head advanced — 2026-11-25
- Scanner PR #279 latest head is `4a0b0fbe9722a9e4c77b8607661101b49ff6cc28`; runner workflow exact-head pin was advanced to the same SHA in commit `3092021a9aea152fb565dd31d7dcee20e8b2c993`.
- Latest code includes the full post-detail qualification stage in the shortlist funnel. Earlier run #366 failed only on outdated provider-alias/JSON-mode expectations and is not a pass for this candidate.
- Await the new exact-head full non-publishing run. Production remains HOLD; no live scan, provider request, deployment, Supabase/R2 write, HF publication or snapshot mutation.


### Scan #39 exact candidate head refresh — 2026-11-25
- Scanner PR #279 head advanced to `6d864f8563e2075cf79ac24a6fee7efe0083dac3` after its AI handover, operations reference and decision log were updated. Runner workflow now pins that exact SHA (workflow commit `4b8abdb1464692ac81e145bf7a4c52f70cd41edf`).
- The previous candidate regression run is stale; require a fresh full non-publishing run against this exact SHA. Production remains HOLD.
