# CustomerServiceOrchestration
Orchestration Layer for Customer Service department

## Current milestone

This repo includes a working Customer Service orchestration service:

- receives Freshdesk recent-order requests
- calls the Order Business API in real mode or sanitized fixtures in mock mode
- normalizes recent order and shipment data
- prefers embedded `tracking_status` from `expand=true`
- creates Freshdesk private notes when `DRY_RUN=false`
- runs locally and as a Render Web Service

## Local setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
```

Run the API locally:

```bash
python -m uvicorn cs_orchestration.main:app --reload --host 127.0.0.1 --port 8001
```

Then open:

```text
http://127.0.0.1:8001/docs
```

## Current API

```text
GET /
POST /enrich-ticket
POST /enrichment/resolve
POST /orders/latest-by-contact
POST /orders/recent-by-contact
POST /freshdesk/recent-orders
GET /health
GET /config/status
```

`POST /enrich-ticket` currently uses mock OMS data from:

```text
cs-orchestration-context/examples/oms-search-orders-response.json
```

## Integration configuration

Real integrations should be configured as separate endpoint/user pairs:

```text
ORDER_BUSINESS_API_BASE_URL
ORDER_BUSINESS_API_USER
ORDER_BUSINESS_API_PASSWORD
ORDER_BUSINESS_API_SECRET_KEY

FEDEX_API_BASE_URL
FEDEX_API_USER
FEDEX_API_PASSWORD
FEDEX_API_SECRET_KEY

FRESHDESK_BASE_URL
FRESHDESK_API_KEY

INBOUND_API_KEY
APP_ENV
DRY_RUN
EXPOSE_DOCS
EXPOSE_DEBUG_ERRORS
INTEGRATION_MODE
```

The Order Business API is used for both order search and order details.
The FedEx API is a fallback only. If Order Business API `expand=true` returns embedded `tracking_status`, the app should use that value and skip the separate FedEx call.

`GET /config/status` reports whether credentials are configured, but never returns credential values.

Default API authentication assumes:

- login/password are sent as HTTP Basic auth
- `secret_key` is sent as a query parameter at the end of the URL

If the API needs only the URL secret key, configure:

```text
ORDER_BUSINESS_API_AUTH_MODE="query_secret"
```

If the API needs username and secret key in the query string instead of Basic auth, configure:

```text
ORDER_BUSINESS_API_AUTH_MODE="query_user_secret"
ORDER_BUSINESS_API_USER_PARAM="user"
ORDER_BUSINESS_API_SECRET_PARAM="secret_key"
```

Supported auth modes are:

```text
none
query_secret
query_user_secret
basic
basic_query_secret
bearer
```

## Render deployment

This repo includes a `render.yaml` blueprint for a first public deployment.

Render should run:

```bash
python -m uvicorn cs_orchestration.main:app --host 0.0.0.0 --port $PORT
```

Recommended production settings:

```text
APP_ENV=production
INTEGRATION_MODE=real
DRY_RUN=true
EXPOSE_DOCS=false
EXPOSE_DEBUG_ERRORS=false
```

Security notes:

- `INBOUND_API_KEY` is required when `APP_ENV=production`.
- Public `/docs`, `/redoc`, `/openapi.json`, `/`, and `/config/status` are disabled in production.
- `/health` stays public for Render health checks.
- Secrets belong in Render environment variables, not in GitHub.
- Start with `DRY_RUN=true`; switch to `DRY_RUN=false` only after a safe Freshdesk test.

Freshdesk should call the deployed URL with:

```text
POST https://your-render-service.onrender.com/freshdesk/recent-orders
X-API-Key: value-from-INBOUND_API_KEY
```

Example body:

```json
{
  "ticket_id": "12345",
  "customer_phone": "+15551234567",
  "customer_email": "customer@example.com",
  "order_number": ""
}
```

`POST /freshdesk/recent-orders` defaults to the last 3 recent OMS records.
When phone and email are both provided, the workflow tries exact contact match first.
If exact match fails, it falls back to phone-only then email-only and marks the result as a partial match.
