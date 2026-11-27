# Private Bridge authentication candidate validation

- Private source repository: `happytiswis-sudo/engineering-career-radar`
- Candidate branch: `fix/private-bridge-routes-require-cv-password-20261128`
- Candidate commit: `c1965b35bc8fc8b9ebfc3eb46c18cc51f36e5108`
- Related private PR: #291
- Scope: require the Master CV password for private Supabase/application/scan endpoints and scan-management operations; update the active dashboard API calls to send `X-CV-Password`.
- Required validation: run the private full Python suite and runner workflow validation against this exact branch. No deployment is authorized by this validation record.
- Production safety: no destructive POST requests, production scans, Supabase mutations, R2 mutations, Hugging Face publication, or recovery-snapshot changes are part of this validation.
