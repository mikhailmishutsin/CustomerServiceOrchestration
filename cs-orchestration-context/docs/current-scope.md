# Current Scope

## In scope for first milestone

### Main flow
Find last X orders by customer phone/email/name/order reference and send a support summary back to Helpdesk.

### Input
A request from Helpdesk containing ticket and customer context.

Minimum useful fields:
- ticket id
- customer phone
- customer email
- customer name if available
- order reference if available
- ticket subject
- ticket description
- source/channel

### Processing
The orchestration layer should:
1. Receive Helpdesk request.
2. Extract customer identifiers.
3. Call Order Business API `search_orders` with optional `filter_mode` and `expand=true`.
4. Get last X matching orders.
5. If expanded details are present, use them directly.
6. If expanded details are missing, call Order Business API `get_order_details`, preferably with `expand=true`.
7. If embedded tracking status is missing, use the FedEx API fallback only when a tracking reference/URL is available.
8. Normalize raw OMS response.
9. Prepare order/shipment summary.
10. Build Helpdesk update payload.
11. In dry-run mode, return the payload without sending it.
12. In real mode, update Helpdesk.

### Integration boundaries
First milestone should already design for separate URLs and service users:

- Order Business API for order search and order details
- FedEx API for tracking fallback
- Helpdesk/Freshdesk

The first implementation can still use mock mode, but real mode should not assume the FedEx API uses the same URL or service user as the Order Business API.

### Output to Helpdesk
At minimum:
- private note for agent with found order data
- custom field with short order summary if configured
- optional order link if one clear latest order exists

## Out of scope for first milestone
- automatic public replies to customers
- AI-generated final customer response
- return/replacement order creation
- product fitment checks
- full IVR automation
- complex routing engine
- SLA/prioritization automation

These can be added after the first stable integration flow.
