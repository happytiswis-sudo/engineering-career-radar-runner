# Engineering Career Radar — Public Runner Trial

This repository is a controlled trial to verify GitHub-hosted Actions runner availability.

## Security boundary

- This public repository contains only reviewed, non-personal source code, tests, and runner configuration.
- The master CV, personal Roles, search requests, scan results, API credentials, Supabase credentials, Cloudflare credentials, and private history remain outside this repository.
- Pull-request workflows must not receive private credentials or retrieve private user data.
- The initial workflow is a runner smoke test only. It does not scan jobs, access the private repository, publish results, or deploy the dashboard.

## Trial stages

1. Prove that a standard GitHub-hosted Ubuntu runner can execute this workflow.
2. Audit and whitelist scanner source and tests before transferring any code.
3. Add private-data retrieval only for trusted runs after secret permissions and cleanup controls are verified.
4. Run a non-publishing scan and compare its output with the existing production path.
5. Enable production publishing only after the full test and data-integrity checks pass.

The existing private dashboard and its data remain the production source of truth until the trial is explicitly validated.
