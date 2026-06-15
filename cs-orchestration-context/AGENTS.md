# AGENTS.md

## Project
We are building an orchestration layer for a Customer Service system for a US tire retail / dropshipping company.

The service connects customer-support tools with internal systems:
- Helpdesk system: currently Freshdesk, but this must stay replaceable
- OMS API: order, customer, fulfillment, shipment, return and replacement data
- SKU/Product API: product details, attributes and compatibility-related data
- Twilio: IVR, programmable voice, SMS and call routing
- Freshcaller: current telephony UI integrated with Freshdesk
- ChannelReply: marketplace communication bridge for Walmart and eBay

## Main goal
Build a scalable API/orchestration layer that receives requests from support channels, enriches them with data from internal systems, prepares routing decisions and pushes structured updates back to the helpdesk or communication channel.

Long-term goal: resolve a major part of customer requests without human involvement when confidence is high enough.

## Important design principle
Do not build the core system around Freshdesk.

Use a common helpdesk abstraction layer and put Freshdesk-specific code into a separate adapter.

Expected structure:
- common/domain logic
- integration clients
- helpdesk abstraction
- Freshdesk adapter
- OMS adapter
- product/SKU adapter
- workflow/orchestration services

## Current implementation status
The first milestone is implemented and deployed publicly on Render.

Implemented flow:
Freshdesk request -> Render API -> Order Business API lookup -> normalized order/shipment data -> Freshdesk private note.

Current primary use case:
Find the last 3 recent orders by Freshdesk ticket/customer data and write an agent-facing private note back to the Freshdesk ticket.

The request can include:
- Freshdesk ticket id
- customer phone
- customer email
- optional order number

The response/note includes:
- order information
- marketplace
- customer information
- fulfillment status
- shipment/tracking status
- ETA if available
- first FedEx scan date if available
- safe Sales Order link for agents
- exact/partial contact match warning when relevant

Current public production endpoint:
- `POST /freshdesk/recent-orders`

Current deployment:
- Render web service
- production mode disables public `/docs`, `/redoc`, `/openapi.json`, `/`, and `/config/status`
- `/health` remains public
- inbound calls require `X-API-Key` when `INBOUND_API_KEY` is configured, and production requires it

## Engineering rules
- Do not hardcode API keys or secrets.
- Use environment variables for credentials.
- Keep real external API calls behind clients/adapters.
- Keep business workflows separate from low-level API clients.
- Start with mock mode and dry-run mode before real updates.
- Add tests for parsers, mappers and payload builders.
- Prefer simple readable code over complex abstractions.
- All API payload examples must be sanitized.
- Do not commit `.env` files.
- Keep `DRY_RUN=true` for deployment smoke tests; use `DRY_RUN=false` only when writing Freshdesk notes intentionally.
- Do not expose debug request payloads in production.
- If both phone and email are provided, try exact contact match first; if not found, fallback to phone-only then email-only partial matching.

## Suggested implementation style
- Use a small web API first.
- Keep API clients stateless where possible.
- Use typed internal models for normalized data.
- Make workflows explicit and testable.
- Log enough to debug integrations, but never log secrets or full customer PII unnecessarily.

## Definition of done for future feature threads
- Read this file plus `docs/project-context.md`, `docs/current-scope.md`, `docs/api-contracts.md`, `docs/workflows.md`, `docs/security.md`, `docs/decisions.md`, and `docs/backlog.md`.
- Preserve the existing Freshdesk/OMS flow unless the user explicitly changes it.
- Add focused tests for every workflow or adapter change.
- Keep new integrations behind adapters/clients.
- Push changes to GitHub when the user needs Render to deploy them.
