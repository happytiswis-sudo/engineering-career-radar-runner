# Cloudflare observability candidate — 28 November 2026

- Private source branch: `fix/cloudflare-observability-20261128`
- Exact candidate SHA: `50bcc611d4f494bc3c3a0dfbbe125dd0a2d2c165`
- Scope: persist privacy-safe console logs for Dashboard and Bridge Workers; keep invocation logs disabled and query-string redaction enabled; add structured Dashboard proxy errors; remove raw upstream details from persisted Bridge error events.
- Validation: run the full private Python suite, frontend contracts, Bridge/security checks, public retrieval tests, extension package validation and runner workflow validation against this exact private SHA.
- Deployment: prohibited from this validation PR. Production deployment requires a separate reviewed release PR after all gates pass.
