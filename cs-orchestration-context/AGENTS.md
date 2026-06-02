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

## Current priority
First milestone:
Helpdesk request -> OMS lookup -> normalize order data -> create support summary -> update Helpdesk ticket.

Initial use case:
Find last X orders by customer phone/email and return:
- order information
- fulfillment status
- shipment/tracking status
- ETA if available
- useful support summary for the agent

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

## Suggested implementation style
- Use a small web API first.
- Keep API clients stateless where possible.
- Use typed internal models for normalized data.
- Make workflows explicit and testable.
- Log enough to debug integrations, but never log secrets or full customer PII unnecessarily.

## Definition of done for first milestone
- Local app can receive a mock Helpdesk webhook.
- App can search mock OMS data by phone or email.
- App normalizes OMS response into internal order model.
- App builds a Helpdesk update payload.
- App supports dry-run mode that prints the outgoing Helpdesk update.
- Tests cover at least one OMS response and one Helpdesk update payload.
- README documents env vars and local run commands.
