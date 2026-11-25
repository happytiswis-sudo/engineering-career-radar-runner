# Scan #38 crossover — runner handover addendum
**Date:** 2026-11-25  
**Exact scanner candidate:** `1e03cf40aca15156ffc4227acd2d65a752cfe1e9`  
**Acceptance criteria:** USER-APPROVED  
**Runner PR:** #207  
**Status:** Exact-head regression pending; independent maintainer review pending; production HOLD.

The user explicitly approved the numerical acceptance criteria on 2026-11-25. Hard gates: exactly 245 planned logical query units (210 Workday + 35 Nomado24), 49 treatment + 196 unchanged controls, 245/245 terminal-outcome reconciliation, six Workday boards plus one Nomado24 board, 28 byte-for-byte unchanged controls, and exact crossover/counterbalance. Yield gates: at least 20% aggregate uplift in deduplicated eligible posting identities per treatment query unit; candidate non-inferior/better on at least 5/7 tracks; no more than one track regressing by >25%; at least 30 distinct eligible posting identities per arm; control yield drift >30% makes the result inconclusive. These are operational thresholds, not statistical significance claims.

Approval of thresholds is not approval to start a production round. Each round still requires separate explicit authorization. The scanner candidate has received internal code-path review only; independent maintainer review remains outstanding. Operator-authored comments are not independent approval.

Scanner PR #276 candidate SHA is exactly `1e03cf40aca15156ffc4227acd2d65a752cfe1e9` on branch `feat/scan38-crossover-instrumentation-20261125`. Runner PR #207 marker `[scan38-crossover-manifest]` routes to that branch. The runner workflow now fails closed unless the checked-out scanner HEAD equals that exact SHA. It must run the full private Python, frontend, extension Bridge/RPC/Worker, public retrieval, packaging, and cleanup checks. Previous 719/719 private and 108/108 public PASS results apply to earlier scanner SHA `6b278be9494420bb76211684cb1d28463e355a4a`, not this target.

A discrepancy was found in the scanner branch's own review addendum at the target SHA: it still references `df6103a674ce2b7746f11e694baf5fc79cd2b84b` and says acceptance is pending. The runner handover and PR body record the correct target SHA and user approval. Do not alter the requested scanner target while validating it; any scanner branch update changes the SHA and requires a new exact-head run.

Use only `.github/workflows/private-scanner-regression.yml`. Do not invoke production-scan or deployment workflows. No live provider calls, production scan, Cloudflare deployment, Supabase/R2 writes, Hugging Face publication, scan #38 mutation, or recovery-snapshot mutation. Scan #38 and verified recovery snapshots remain immutable. Production HOLD.


## Dispatch mechanics correction — 2026-11-25
The workflow job condition now explicitly permits `workflow_dispatch`; before this correction, manual dispatch would have skipped the job. The remaining manual action is to run `.github/workflows/private-scanner-regression.yml` on branch `docs/scan38-crossover-instrumentation-handoff-20261125` with `private_ref=1e03cf40aca15156ffc4227acd2d65a752cfe1e9` and `private_base_ref=main`. The workflow asserts the exact scanner SHA and performs only non-publishing validation. This session's GitHub connector has no workflow-dispatch action. Do not merge or authorize round one until exact-head run succeeds and independent maintainer review is received.
