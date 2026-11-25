# Scan #38 crossover — runner handover addendum
**Date:** 2026-11-25  
**Scanner candidate:** `df6103a674ce2b7746f11e694baf5fc79cd2b84b`  
**Runner PR:** #207  
**Status:** Exact candidate pin updated; rerun required.

The private scanner PR now includes an append-only review/acceptance addendum. It documents provider integration, exact query-unit budget, crossover/control invariants, the non-publishing validation evidence, and proposed numerical acceptance thresholds. Those thresholds remain pending explicit approval.

Runner PR #207 marker `[scan38-crossover-manifest]` routes to `feat/scan38-crossover-instrumentation-20261125`. The exact private candidate SHA is `df6103a674ce2b7746f11e694baf5fc79cd2b84b`. The next run must assert this SHA and run the full private Python, frontend, extension Bridge/RPC/Worker, public retrieval, packaging, and cleanup checks. Any further scanner commit invalidates the result.

Use only `.github/workflows/private-scanner-regression.yml`. Do not invoke production-scan or deployment workflows. No live provider calls, production scan, Cloudflare deployment, Supabase/R2 writes, Hugging Face publication, scan #38 mutation, or recovery-snapshot mutation. Scan #38 and verified recovery snapshots remain immutable. Production HOLD.
