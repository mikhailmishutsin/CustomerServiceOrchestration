# CS Orchestration Layer

API/orchestration layer for Customer Service automation.

## Purpose
This service connects the Helpdesk system with internal business systems such as OMS, product/SKU APIs, Twilio and telephony tools.

The first implementation target is Freshdesk, but the core design should not depend on Freshdesk directly. Freshdesk must be treated as one adapter behind a common Helpdesk interface.

## First milestone
Build a minimal flow:

```text
Helpdesk ticket/request
-> orchestration API
-> OMS lookup by customer phone/email
-> normalize order and shipment data
-> prepare agent-facing summary
-> push update back to Helpdesk
```

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
Create `.env` locally based on `.env.example`.

```bash
APP_ENV=local
DRY_RUN=true
OMS_API_BASE_URL=
OMS_API_KEY=
HELPDESK_PROVIDER=freshdesk
FRESHDESK_BASE_URL=
FRESHDESK_API_KEY=
```

## Suggested first Codex task

```text
Read AGENTS.md and docs/*.md.
Create the initial app structure for the orchestration layer.
Implement the first flow in mock/dry-run mode only:
POST /webhooks/helpdesk/ticket-created
-> parse request
-> lookup mock OMS orders by phone/email
-> normalize orders
-> build Helpdesk update payload
-> return dry-run response.
Add tests for normalizer and payload builder.
```
