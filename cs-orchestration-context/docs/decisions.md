# Decisions

## Decision 1: Helpdesk-agnostic core
The core orchestration layer must not depend directly on Freshdesk.
Freshdesk will be implemented as an adapter behind a common Helpdesk interface.

Reason: Freshdesk is current system, but the company may change Helpdesk system later.

## Decision 2: Start with mock and dry-run mode
First milestone should not update production systems by default.

Reason: integration payloads need to be visible and tested before real API writes.

Current status:
- local development supports mock and dry-run modes
- Render deployment should start with `DRY_RUN=true`
- `DRY_RUN=false` is used only for intentional Freshdesk note creation

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

## 2026-06-05: Render deployment with production hardening

Decision:
- Deploy as a Render Web Service, not a Static Site.
- Use Render environment variables for all secrets.
- Use `APP_ENV=production` for public deployment.
- Require `INBOUND_API_KEY` in production.
- Disable public `/docs`, `/redoc`, `/openapi.json`, `/`, and `/config/status` in production.
- Keep `/health` public for Render health checks.
- Hide debug request payloads in production errors.

Reason:
The public URL must be reachable by Freshdesk, but should not expose local debugging surfaces or secrets.

## 2026-06-05: Freshdesk private-note write-back

Decision:
- `POST /freshdesk/recent-orders` is the first channel-specific endpoint.
- It returns/builds a common `HelpdeskUpdate`.
- When `DRY_RUN=false`, the Freshdesk adapter posts a private note to `/api/v2/tickets/{ticket_id}/notes`.
- The Freshdesk note includes a clickable Sales Order link when `order_link` exists.

Reason:
Freshdesk needs agent-visible context inside the ticket, not only a JSON response.
The core workflow should remain helpdesk-agnostic while Freshdesk presentation details stay in the adapter.

## 2026-06-05: Exact contact match before partial fallback

Decision:
- If phone and email are both provided, try exact contact match first.
- If no exact match is found, fallback to phone-only then email-only.
- Mark partial matches clearly in metadata and private note text.
- Do not use `filter_mode=any` with both phone and email in the current Freshdesk fallback path.

Reason:
Agents need to know whether a result matched all provided contact data or only part of it.
The live OMS API returned HTTP 400 for the phone+email+`filter_mode=any` fallback combination, so simpler single-field fallback searches are safer.
