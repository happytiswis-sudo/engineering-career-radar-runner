# Private Bridge authentication candidate validation

- Private source repository: `happytiswis-sudo/engineering-career-radar`
- Candidate branch: `fix/private-bridge-routes-require-cv-password-20261128`
- Candidate commit: `d8a5ee857bcee7fd70eac3da6d8fd7ecb154d1b9`
- Related private PR: #291
- Scope: require the Master CV password for private Supabase/application/scan endpoints and scan-management operations; update the active dashboard API calls to send `X-CV-Password`.
- Required validation: run the private full Python suite and runner workflow validation against this exact branch. No deployment is authorized by this validation record.
- Production safety: no destructive POST requests, production scans, Supabase mutations, R2 mutations, Hugging Face publication, or recovery-snapshot changes are part of this validation.

- Retargeted to runner `main` after PR #220 merged; this synchronize event triggers validation against the same-named private candidate branch.

- Candidate source and test fixtures were synchronized after the first run identified two test-contract assertions; the next run must execute the full 733-test suite on this exact commit.
