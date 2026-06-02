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

## Common field examples

```text
order_summary -> Freshdesk custom field configured for OMS/support response
order_link -> Freshdesk custom field configured for latest order link
private_note -> Freshdesk private note endpoint
```

Exact Freshdesk field names should be configured, not hardcoded in business workflows.
