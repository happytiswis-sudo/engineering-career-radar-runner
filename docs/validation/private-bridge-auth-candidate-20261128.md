# Private Bridge authentication candidate validation

- Private source repository: `happytiswis-sudo/engineering-career-radar`
- Candidate branch: `fix/private-bridge-routes-require-cv-password-20261128`
- Candidate commit: `8a5e8c658c4da89fbaed0ec8b01ccac69bf1c5ab`
- Related private PR: #291
- Scope: require the Master CV password for private Supabase/application/scan endpoints and scan-management operations; update the active dashboard API calls to send `X-CV-Password`.
- Required validation: run the private full Python suite and runner workflow validation against this exact branch. No deployment is authorized by this validation record.
- Production safety: no destructive POST requests, production scans, Supabase mutations, R2 mutations, Hugging Face publication, or recovery-snapshot changes are part of this validation.

- Retargeted to runner `main` after PR #220 merged; this synchronize event triggers validation against the same-named private candidate branch.

- Candidate source and test fixtures were synchronized after the first run identified two test-contract assertions; the next run must execute the full 733-test suite on this exact commit.

- Updated two existing UI contract tests to expect the new Master CV authentication on scan/history calls; the prior failures were stale assertions, not product runtime failures. Re-run all 733 tests on this exact commit.

- Updated the existing frontend contract assertions to expect Master CV authentication on the private API calls. The latest Python suite passed 733/733; the frontend contract gate then identified stale assertions, now updated. Fresh exact-head run required.

- Candidate now also fixes Hugging Face Space URL construction by including `/spaces/` for the canonical owner/repo ID; the Space catalogue was verified as valid JSON with 784 roles across 34 tracks.

- Updated the existing dashboard navigation contract to expect CV-authenticated scan, status, run, history and job calls and to verify the proxy forwards the password header. Re-run the full gates on this exact commit.

- Updated the existing public-data and R2-history contract tests to assert the corrected `/spaces/{owner}/{repo}/resolve/main/` helper rather than the old model-style URL. Re-run the 734-test suite and all downstream frontend/Bridge/retrieval gates.
