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

Runner smoke workflow is installed at `.github/workflows/runner-smoke.yml` and runs on pushes to `main`.

## Full private-suite validation

A manual-only workflow is provided at `.github/workflows/private-scanner-regression.yml`. It checks out the private repository into an ephemeral runner workspace, runs the full private Python and frontend contract suites, runs this repository's retrieval-engine tests, and removes the private checkout. It does not publish scan results or deploy anything.

Before running it, create a fine-grained GitHub token restricted to **`happytiswis-sudo/engineering-career-radar` only**, with **Contents: Read-only** and no other permissions. Add it to this public repository as the Actions secret `PRIVATE_SOURCE_READ_TOKEN`. Do not use a classic PAT, do not grant write access, and do not expose this secret to pull-request workflows. The workflow is manual-only and only runs when dispatched from `main`.

The token is not stored in this repository and cannot be added by the repository connector. Until the secret exists, the full private suite remains gated; the public smoke and retrieval-engine tests do not require it.
