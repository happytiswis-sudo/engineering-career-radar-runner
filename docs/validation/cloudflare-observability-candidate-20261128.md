# Cloudflare observability candidate — 28 November 2026

- Private source branch: `fix/cloudflare-observability-20261128`
- Exact candidate SHA: `b1341c54c0ecc32a8d78bce7ded15fbe4d8ac6a0`
- Scope: persist privacy-safe console logs for Dashboard and Bridge Workers; keep invocation logs disabled and query-string redaction enabled; add structured Dashboard proxy errors; remove raw upstream details from persisted Bridge error events.
- Validation: run the full private Python suite, frontend contracts, Bridge/security checks, public retrieval tests, extension package validation and runner workflow validation against this exact private SHA.
- Deployment: prohibited from this validation PR. Production deployment requires a separate reviewed release PR after all gates pass.
