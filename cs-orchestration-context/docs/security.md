# Security and Privacy

## Secrets
Never commit secrets.

Use environment variables for:
- OMS API keys
- Freshdesk API keys
- Twilio credentials
- any webhook signing secrets

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

## Automation safety
Before sending automatic customer-facing replies, require:
- clear intent
- high confidence
- verified customer/order match
- approved response template or reviewed generation rules
- logging of automation decision
