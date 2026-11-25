# Scan #38 crossover — runner handover addendum
**Date:** 2026-11-25  
**Current scanner candidate:** `1e03cf40aca15156ffc4227acd2d65a752cfe1e9`  
**Acceptance criteria:** USER-APPROVED  
**Runner PR:** #207  
**Status:** Current exact-head regression required; production HOLD.

The user explicitly approved the numerical acceptance criteria recorded in the scanner PR addendum on 2026-11-25. Approved decision gates: exactly 245 planned logical query units (210 Workday + 35 Nomado24), 49 treatment + 196 unchanged controls, 245/245 terminal-outcome reconciliation, 28 byte-for-byte unchanged controls, exact registered crossover/counterbalance, at least 20% aggregate uplift in deduplicated eligible posting identities per treatment query unit, candidate non-inferior/better on at least 5/7 tracks, no more than one track regressing by >25%, at least 30 distinct eligible posting identities per arm, and control yield drift >30% makes the result inconclusive. These are operational thresholds, not statistical significance claims.

Approval of thresholds is not approval to start a production round. Each round still requires separate explicit authorization. Independent maintainer review and exact-head non-publishing regression remain release gates.

The scanner PR #276 current candidate is `1e03cf40aca15156ffc4227acd2d65a752cfe1e9` on `feat/scan38-crossover-instrumentation-20261125`. Runner PR #207 marker `[scan38-crossover-manifest]` routes to that branch. The next validation must assert the exact resolved scanner SHA and run the full private Python, frontend, extension Bridge/RPC/Worker, public retrieval, packaging, and cleanup checks. Previous 719/719 private and 108/108 public regression results apply to earlier scanner code SHA `6b278be9494420bb76211684cb1d28463e355a4a`, not the current candidate.

Use only `.github/workflows/private-scanner-regression.yml`. Do not invoke production-scan or deployment workflows. No live provider calls, production scan, Cloudflare deployment, Supabase/R2 writes, Hugging Face publication, scan #38 mutation, or recovery-snapshot mutation. Scan #38 and verified recovery snapshots remain immutable. Production HOLD.
