# Engineering Career Radar — Public Execution Runner

This repository is the **public GitHub Actions execution plane** for the private Career Radar source repository. It exists so standard GitHub-hosted runner jobs execute from a public repository rather than consuming the private repository's included Actions compute allowance.

## Repository boundary

| Repository | Responsibility | Data classification |
|---|---|---|
| [engineering-career-radar](https://github.com/happytiswis-sudo/engineering-career-radar) | Authoritative scanner, matching/agent code, master CV, dashboard source, migrations, private history contracts | **Private — source of truth** |
| [engineering-career-radar-runner](https://github.com/happytiswis-sudo/engineering-career-radar-runner) | Workflow orchestration, regression runner, public-safe tests and operational runbooks | Public — no user data or credential values |

The public runner checks out the private repository into an ephemeral private-source directory using PRIVATE_SOURCE_READ_TOKEN (fine-grained token, only the private source repository, **Contents: Read-only**). The token is never written to source or persisted in the checkout. The workflow removes the private checkout at the end of the job.

**Never copy** the master CV, private user/application data, private Space history, provider responses containing personal data, credentials, or raw scan output into this public repository, public Actions artifacts, or public logs.

## Current workflows

| Workflow | Trigger | Purpose | Writes production data? |
|---|---|---|---|
| runner-smoke.yml | Push / PR / manual | Proves public hosted-runner execution and tests public retrieval-intelligence code | No |
| private-scanner-regression.yml | Push to main when runner/scan control files change; manual | Checks out private source read-only and runs the full Python, frontend contract and public retrieval suites | No |
| production-scan.yml | Weekday schedule / manual | Runs the private scanner and matching engine from the public hosted runner | **No by default**; publication is gated |

### Production scan safety gate

The production scan always checks out the private source repository's current main branch and logs only its commit SHA. It does not accept an arbitrary ref input. Detailed scanner output is redirected to the ephemeral runner temp directory; public step summaries contain aggregate counts only, never posting titles, employer names, vacancy URLs, descriptions, CV content or credentials. No scan-result artifacts are uploaded to this public repository.

A scan can be run in **dry-run mode** while the repository variable CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH is absent or anything other than the literal string true. In that mode it performs retrieval and matching, writes no results to Supabase, R2 or Hugging Face, and does not publish a dashboard snapshot. Local output is destroyed with the ephemeral runner.

Production publication is enabled only after:
1. All required secrets and variables below have been configured in this public runner repository.
2. The dry-run scan and regression suite have been reviewed.
3. The operator deliberately sets CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true.

When enabled, the workflow validates required publishing credentials before scanning, then persists the completed results/aggregate telemetry to Supabase, uploads and SHA-256 verifies the private R2 archive, and publishes the allowlisted dashboard bundle to the private Hugging Face Space. R2/HF/Supabase are external write operations; do not enable the gate until the credentials are verified.

## Required Actions secrets

Create these under **Settings → Secrets and variables → Actions → Repository secrets** in this repository. Secret values cannot be read back or transferred automatically from the private repository; copy them from their original secure source. Never paste values into issues, PRs, documentation, or chat.

| Secret | Purpose |
|---|---|
| PRIVATE_SOURCE_READ_TOKEN | Fine-grained read-only checkout of the private source repository |
| HF_TOKEN | Read/write access to the private Career Radar Hugging Face Space |
| SUPABASE_URL | Career Radar Supabase project URL |
| SUPABASE_SERVICE_ROLE_KEY | Server-side Supabase RPC access; never expose to browser |
| DASHBOARD_API_KEY | Authenticates the Cloudflare archive bridge |
| ARCHIVE_CI_TOKEN | Authenticates private R2 archive upload/read-back through the bridge |

The following provider credentials are optional and should be copied only if configured and still valid in the private repository. Their absence must not be represented as a successful provider call:

- SERPAPI_API_KEY, SERPER_API_KEY, CLORO_API_KEY_1, CLORO_API_KEY_2, SEARXNG_API_TOKEN
- OPENROUTER_API_KEY, INCEPTION_API_KEY, NARAROUTER_API_KEY, HIMALAYAS_API_KEY, THE_MUSE_API_KEY

Use short expirations for fine-grained tokens and renew them before expiry. The token must have no write, Actions, administration, or account permissions.

## Required / relevant Actions variables

Configure under **Settings → Secrets and variables → Actions → Repository variables**. Use the values already approved for the private source repository; do not guess:

- Required for private Space reads/writes: HF_SPACE_ID (currently documented as Sidmed/engineering-career-radar).
- Publication gate: CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH — leave unset until explicitly approved; set to literal true only after preflight.
- Optional bridge: CARE_RADAR_BRIDGE_URL (default: https://career-radar-bridge.happytiswis.workers.dev).
- Search configuration: JOBSPY_AUTHORIZED_SITES, LINKEDIN_RETRIEVAL_AUTHORIZED, JOBSPY_LINKEDIN_MODE, JOBSPY_LINKEDIN_FETCH_DESCRIPTION, JOBSPY_SCHEDULED_ENABLED, JOBSPY_RESULTS_PER_QUERY, JOBSPY_LINKEDIN_MAX_QUERIES_PER_RUN, JOBSPY_LINKEDIN_QUERY_DELAY_SECONDS, JOBSPY_LINKEDIN_RATE_LIMIT_COOLDOWN_HOURS, JOBSPY_LINKEDIN_RESET_PAUSE.
- Optional search configuration: SEARXNG_BASE_URL, NARAROUTER_PROVIDER, NARAROUTER_MODEL.

Copy values from the private repository's current Variables page and validate them against the current source workflow. A selected JobSpy platform is not authorization; retain each platform's independent permission gate. Do not use proxies, logins, CAPTCHA solving or access-control bypasses.

## Operating procedure

1. Confirm the latest private-scanner-regression run is green.
2. Dispatch production-scan.yml manually with no search_request for the configured broad profile, or provide a validated dashboard search JSON.
3. Keep publication disabled for the first dry run. Review aggregate source yield, unique canonical URL funnel, usable posting counts, source errors, career-track coverage and runtime. Do not infer live performance from unit tests.
4. If dry-run output is healthy, verify required secrets/variables and Supabase/R2/HF access. Only then set CAREER_RADAR_ENABLE_PRODUCTION_PUBLISH=true and run a controlled publication.
5. Verify the run ID in Supabase, retrieval_funnel.newly_discovered_vacancies_basis=private_hash_identity_registry, R2 SHA-256 read-back, and private Space jobs.json plus search-history.json.
6. Confirm the dashboard reads the newly published run. Do not claim the >20,000 unique URL objective without a measured production run.

## Current engineering status

- PR #105 merged in the private source repository: retrieval yield diagnostics, conservative adaptive allocation, source health recommendations, canonical URL funnel and hash-only vacancy identity reconciliation.
- The private full-suite validation has passed on this public runner: 402 Python tests, frontend contract checks and 7 public retrieval regression tests. A later run must be retained as the evidence for each subsequent change.
- The private repository's own Actions allowance is exhausted. Do not dispatch production workflows from the private repository.
- Production orchestration PR #2 is merged into this repository's main branch as 54d88531df2f7683060a2ad2119e64577b04b6fd. The new production-scan.yml is available for manual/scheduled execution, but a post-migration dry-run has not yet been performed.
- The private-source migration PR #116 remains open pending regression. The first post-merge regression run proved the private Python suite passes (402 tests) but exposed a stale frontend contract assertion: the capacity control is rendered dynamically by `public/index.html`, so the test was checking the wrong representation. That assertion has been corrected on PR #116. The same PR also restores the three original retrieval-identity publisher tests that were accidentally displaced while adding workflow URL coverage; both URL tests are now additive. A fresh hosted regression is still required before merge. The regression workflow temporarily targets the private migration branch; after it passes and PR #116 merges, restore the regression default to private main and rerun.
- The public runner now includes a static contract test for private checkout, explicit publication gates, public-log redaction and artifact prohibition. Its public runner smoke test passes; the full private regression is not yet green.
- Production publishing remains disabled. Publishing secrets/variables have not been verified in this repository; no production scan, R2/Supabase/HF publication, Cloudflare redeployment or dashboard smoke is claimed.

## Privacy / incident response

If a private CV, job data, token, or raw scan log is accidentally committed or emitted to a public log/artifact, stop publication, remove the exposed content from public history where possible, rotate the affected credential immediately, and review GitHub audit logs. Deleting a commit does not revoke a leaked secret. Keep private source checkout, raw logs, and transient results on the ephemeral hosted runner only.
