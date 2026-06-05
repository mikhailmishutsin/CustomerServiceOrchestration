# Current Scope

## Implemented scope

### Main deployed flow
Find recent orders by Freshdesk ticket/customer data and create a Freshdesk private note.

### Input
A request from Freshdesk containing ticket and customer context.

Minimum useful fields:
- ticket id
- customer phone
- customer email
- optional order reference/order number

### Processing
The orchestration layer should:
1. Receive Freshdesk request at `POST /freshdesk/recent-orders`.
2. Validate inbound `X-API-Key` when configured.
3. Extract ticket id, phone, email, and optional order number.
4. Normalize US phone numbers for OMS lookup by removing punctuation and leading `1`.
5. When both phone and email exist, call OMS first with exact contact match semantics.
6. If exact match finds nothing, fallback to phone-only then email-only partial matching.
7. Call Order Business API `search_orders` with `expand=true`.
8. Ask OMS for 3 records by default for the Freshdesk recent-orders endpoint.
9. Normalize raw OMS response.
10. Format human-friendly order dates, ETA windows, and first scan dates.
11. Build Helpdesk update payload.
12. In dry-run mode, return the payload without sending it.
13. In real mode, create a Freshdesk private note.

### Integration boundaries
First milestone should already design for separate URLs and service users:

- Order Business API for order search and order details
- FedEx API for tracking fallback
- Helpdesk/Freshdesk

Real mode does not assume the FedEx API uses the same URL or service user as the Order Business API.

### Output to Helpdesk
At minimum:
- private note for agent with found order data
- short order summary in structured response/custom fields
- delivery status and ETA
- order date
- safe Sales Order link in structured data and Freshdesk note
- partial-match warning when phone/email do not both match

## Current production posture
- Render Web Service is used for public deployment.
- `APP_ENV=production` requires `INBOUND_API_KEY`.
- Public docs/debug UI are disabled in production.
- Debug request payloads are hidden in production errors.
- `/health` stays public for Render health checks.

## Out of scope for current milestone
- automatic public replies to customers
- AI-generated final customer response
- return/replacement order creation
- product fitment checks
- full IVR automation
- complex routing engine
- SLA/prioritization automation

These can be added after the first stable integration flow.
