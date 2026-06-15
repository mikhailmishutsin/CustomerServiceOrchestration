# CS Orchestration Layer

API/orchestration layer for Customer Service automation.

## Purpose
This service connects the Helpdesk system with internal business systems such as OMS, product/SKU APIs, Twilio and telephony tools.

The first implementation target is Freshdesk, but the core design should not depend on Freshdesk directly. Freshdesk must be treated as one adapter behind a common Helpdesk interface.

## Current milestone status
The first Freshdesk/OMS orchestration milestone is implemented and deployed.

Current production-style flow:

```text
Freshdesk ticket/request
-> Render-hosted orchestration API
-> Order Business API lookup by phone/email/order number
-> normalize order and shipment data
-> prepare agent-facing summary
-> create Freshdesk private note
```

The local app still provides Swagger and a debug UI for development.
Production mode hides those public surfaces.

## Planned integrations
- Helpdesk: Freshdesk first, replaceable later
- OMS API: order, fulfillment, shipment, return/replacement data
- Product/SKU API: product details and attributes
- Twilio: IVR, programmable voice, SMS
- Freshcaller: current telephony UI
- ChannelReply: Walmart/eBay communication bridge

## Recommended local structure

```text
AGENTS.md
README.md
docs/
examples/
src/
tests/
.env.example
.cursor/rules/project.md
```

## Local development principles
- Start with mocks.
- Use dry-run for Helpdesk updates.
- Do not call production APIs until clients and payloads are tested.
- Keep secrets only in `.env`.
- Commit examples only after sanitizing customer data.

## Environment variables
Create `.env` locally based on root `.env.example`.
For Render, configure the same values in the Render Environment Variables dashboard.

```bash
APP_ENV=local
DRY_RUN=true
INTEGRATION_MODE=mock
INBOUND_API_KEY=
ORDER_BUSINESS_API_BASE_URL=
ORDER_BUSINESS_API_USER=
ORDER_BUSINESS_API_PASSWORD=
ORDER_BUSINESS_API_SECRET_KEY=
FRESHDESK_BASE_URL=
FRESHDESK_API_KEY=
```

## Current public integration endpoint

```text
POST /freshdesk/recent-orders
```

Required header when inbound auth is configured:

```text
X-API-Key: value-from-INBOUND_API_KEY
```

Request body:

```json
{
  "ticket_id": "12345",
  "customer_phone": "+15551234567",
  "customer_email": "customer@example.com",
  "order_number": ""
}
```

## Suggested next Codex task pattern

```text
Read cs-orchestration-context/AGENTS.md and docs/*.md first.
Then implement only the requested feature, preserving the existing Freshdesk/OMS deployed flow.
Run tests before finishing and push to GitHub if Render needs to deploy the change.
```

## Context docs

- `docs/project-context.md`
- `docs/current-scope.md`
- `docs/api-contracts.md`
- `docs/workflows.md`
- `docs/security.md`
- `docs/decisions.md`
- `docs/backlog.md`
