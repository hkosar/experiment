# Provider result captures

Empty by design — the owner session has not run.

During the session, save each raw provider result JSON here as
`<candidate>/<poc>/<step>.json`, e.g. `n8n/POC1/send-assignment.json`.
These feed `harness/receipt_conformance.py`, which computes what each provider
can and cannot supply against the D-EC_ receipt shape.

**No secret, token, or credential belongs in any file in this directory.**
Redact before saving; a capture that needs a secret to be meaningful should be
recorded as an observation instead.
