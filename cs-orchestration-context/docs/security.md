# Security and Privacy

## Secrets
Never commit secrets.

Use environment variables for:
- inbound API authentication
- Order Business API URL and credentials
- FedEx API URL and credentials
- Freshdesk API keys
- Twilio credentials
- any webhook signing secrets

Use separate service users for separate external services when available.
For example, do not reuse the Order Business API user for FedEx tracking unless the external system requires it.
Treat service-user passwords and URL `secret_key` values as separate secrets.

## PII
The system will process customer PII:
- names
- phone numbers
- emails
- shipping addresses
- order data

Rules:
- Do not log full customer PII unless needed for debugging.
- Mask phone/email in logs where possible.
- Do not store raw external payloads long-term unless there is a clear reason.
- Sanitize examples before committing them.

## External API calls
- Start with mock mode.
- Use dry-run mode for Helpdesk updates.
- Add retries carefully.
- Avoid duplicate customer messages.

## Inbound API authentication
- External callers should send `X-API-Key`.
- Configure the shared secret in `INBOUND_API_KEY`.
- If `INBOUND_API_KEY` is not configured, inbound API auth is inactive.
- When `APP_ENV=production`, `INBOUND_API_KEY` is required at startup.
- Store `INBOUND_API_KEY` in Render environment variables, not in GitHub.

## Production exposure
When deployed publicly:
- Keep `APP_ENV=production`.
- Keep `EXPOSE_DOCS=false`.
- Keep `EXPOSE_DEBUG_ERRORS=false`.
- Keep `/health` public for Render.
- Do not expose `/docs`, `/redoc`, `/openapi.json`, `/`, or `/config/status`.

Production error responses must not include:
- OMS request URLs
- Freshdesk request payloads
- `secret_key`
- API keys
- full debug payloads

## Freshdesk write-back safety
- Start deployed smoke tests with `DRY_RUN=true`.
- Switch to `DRY_RUN=false` only when intentionally creating Freshdesk notes.
- Use safe test tickets before wiring broad Freshdesk automation.
- Avoid duplicate notes by being careful with Freshdesk automation triggers and retries.
- Freshdesk API key is used only for outgoing calls from the orchestration service to Freshdesk.
- `INBOUND_API_KEY` is a separate shared secret for callers reaching the orchestration API.

## Automation safety
Before sending automatic customer-facing replies, require:
- clear intent
- high confidence
- verified customer/order match
- approved response template or reviewed generation rules
- logging of automation decision
