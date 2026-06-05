# Project Context

## Business
The company is a US retail / dropshipping business selling tires and parts.

Customer communication comes from multiple channels:
- phone calls
- web chat
- email
- marketplaces such as Walmart and eBay

Freshdesk is currently used as the centralized storage for support communication.
ChannelReply connects Walmart/eBay communication to Freshdesk.
Freshcaller is used as the phone UI and is integrated with Freshdesk.
Twilio is currently used for basic IVR and forwarding calls to agents.

## Internal systems
The company has internal APIs that expose:
- sales order history
- current order status
- fulfillment status
- shipment/tracking status
- return/replacement order creation
- product/SKU details and attributes

## Main problem
Support agents need fast, structured and reliable information from OMS and product systems inside the support workflow.

The system should reduce manual lookup work and prepare enough context for agents or automated replies.

## Long-term goal
Resolve a major part of customer requests without human involvement.

For high-confidence cases, the system should be able to send replies automatically through:
- email
- SMS
- marketplace communication channels
- programmable voice for phone calls

## First step
The first public API layer is now implemented.

Current implemented use case:
Freshdesk sends ticket id, customer phone/email, and optional order number to the Render-hosted orchestration API.
The service calls the Order Business API, normalizes recent order and shipment data, then writes a Freshdesk private note.

Current production endpoint:

```text
POST /freshdesk/recent-orders
```

Current deployment state:
- hosted as a Render Web Service
- `/health` is public
- `/docs`, `/redoc`, `/openapi.json`, `/`, and `/config/status` are disabled in production mode
- inbound requests are protected by `X-API-Key`
- outgoing Freshdesk writes use `FRESHDESK_API_KEY`

Current WISMO/recent-order behavior:
- default Freshdesk recent-orders lookup asks OMS for 3 records
- phone/email exact match is attempted first when both values are provided
- if no exact contact match exists, fallback searches phone-only then email-only
- partial matches are clearly marked in metadata and private note text
- Sales Order links are included in Freshdesk private notes when available
