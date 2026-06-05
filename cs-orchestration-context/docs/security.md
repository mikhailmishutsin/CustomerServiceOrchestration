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

## Automation safety
Before sending automatic customer-facing replies, require:
- clear intent
- high confidence
- verified customer/order match
- approved response template or reviewed generation rules
- logging of automation decision
