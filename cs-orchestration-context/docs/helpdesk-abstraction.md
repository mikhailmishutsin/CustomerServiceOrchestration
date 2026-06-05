# Helpdesk Abstraction

## Goal
Avoid hard dependency on Freshdesk inside core workflows.

The orchestration layer should depend on a common Helpdesk interface.
Freshdesk-specific endpoints, field names and payload formats should be isolated in the Freshdesk adapter.

## Common operations

```text
get_ticket(ticket_id)
update_ticket_fields(ticket_id, fields)
add_private_note(ticket_id, text)
add_public_reply(ticket_id, text)
set_ticket_type(ticket_id, type)
set_priority(ticket_id, priority)
assign_ticket(ticket_id, group_id, agent_id)
```

## Freshdesk adapter responsibilities
- Map common field names to Freshdesk custom field names.
- Build Freshdesk API payloads.
- Handle Freshdesk authentication.
- Handle Freshdesk API errors and rate limits.
- Hide Freshdesk-specific behavior from workflow services.

Current implementation:
- `FreshdeskAdapter.apply_update(update)` posts private notes to Freshdesk.
- Endpoint used: `POST {FRESHDESK_BASE_URL}/api/v2/tickets/{ticket_id}/notes`.
- Authentication uses `FRESHDESK_API_KEY` as Freshdesk Basic auth username and `X` as password.
- Payload uses Freshdesk `body` plus `private=true`.
- The adapter converts plain-text notes into HTML and appends a clickable Sales Order link when `custom_fields.order_link` exists.
- The adapter uses a Freshdesk-specific HTML renderer when structured `metadata.matched_orders` is available.
- The rendered Freshdesk note shows the latest order first, then detailed tracking for the latest order, then other recent orders.
- The latest order is not duplicated inside the other recent orders section.
- Sales Order links are rendered near the latest order.
- FedEx tracking numbers are clickable when `tracking_url` is available.
- Freshdesk response metadata is attached under `metadata.freshdesk`.

## Common field examples

```text
order_summary -> Freshdesk custom field configured for OMS/support response
order_link -> Freshdesk custom field configured for latest order link
private_note -> Freshdesk private note endpoint
```

Exact Freshdesk field names should be configured, not hardcoded in business workflows.

## Current Freshdesk endpoint

The first channel-specific route is:

```text
POST /freshdesk/recent-orders
```

It accepts:

```json
{
  "ticket_id": "112",
  "customer_phone": "+15551234567",
  "customer_email": "customer@example.com",
  "order_number": ""
}
```

It builds a common `HelpdeskUpdate`.
When `DRY_RUN=false`, the adapter creates a Freshdesk private note.
