# Decisions

## Decision 1: Helpdesk-agnostic core
The core orchestration layer must not depend directly on Freshdesk.
Freshdesk will be implemented as an adapter behind a common Helpdesk interface.

Reason: Freshdesk is current system, but the company may change Helpdesk system later.

## Decision 2: Start with mock and dry-run mode
First milestone should not update production systems by default.

Reason: integration payloads need to be visible and tested before real API writes.

## Decision 3: First use case is recent orders lookup
The first workflow is: find last X orders by customer phone/email, summarize order and shipment status, update Helpdesk.

Reason: this gives immediate value to support agents and creates the foundation for later automation.

## Decision 4: AI automation is later
AI-generated customer responses and fully automatic resolution are not part of the first milestone.

Reason: data enrichment and reliable integrations must work first.

## 2026-06-02: OMS expand mode and filter mode

`search_orders` now supports:
- `filter_mode=all|any` for combining criteria;
- optional filters: `order_status`, `order_status_fulfillment`, `marketplace`;
- `expand=true`, which may include `orders[].details` and embedded carrier tracking status.

Decision:
- Use `expand=true` by default for support enrichment flows where shipment status/ETA is required.
- Omit `filter_mode` from URL when not intentionally set.
- Prefer embedded `tracking_status` from expanded OMS responses.
- Fall back to `tracking_status_urls` only when embedded tracking status is missing.
- Never expose or log unredacted `secret_key` from OMS or tracking URLs.
