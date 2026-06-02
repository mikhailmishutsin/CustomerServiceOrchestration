# Workflows

## Workflow 1: Enrich Helpdesk ticket with recent orders

### Trigger
Helpdesk sends a webhook or API request when a ticket is created or updated.

### Steps
1. Receive ticket context.
2. Extract customer phone, email, full name, and order reference if available.
3. Build OMS search request.
4. Decide `filter_mode`:
   - omit when only one criterion is used or default API behavior is desired;
   - use `all` when all provided criteria must match;
   - use `any` when broad matching is needed, for example phone OR email OR name.
5. Prefer `expand=true` for order-status enrichment because it can return order details and tracking status in one response.
6. Call OMS `search_orders`.
7. Sort orders from newest to oldest by `order_date` if needed.
8. For each selected order:
   - if `orders[].details` exists, use it for line and shipment data;
   - if `orders[].details` is missing, call `get_order_details` with `expand=true` when shipment data is required.
9. If expanded details still do not include `tracking_status`, use `tracking_status_urls` as fallback.
10. Normalize orders and shipments.
11. Build short support summary.
12. Build full private note.
13. Update Helpdesk ticket through the helpdesk adapter.

### Success result
Agent can see recent order and shipment status directly in the ticket.

### No match result
Add or return a clear message:

```text
No matching orders found by provided phone/email/name/order reference.
```

### Multiple orders result
Show last X orders, newest first.
Clearly mark the latest order.

## Workflow 2: Get specific order details

### Trigger
Agent, automation, or customer request provides a specific order number.

### Steps
1. Call `get_order_details`.
2. Use `expand=true` when shipment status and ETA are needed.
3. Parse order lines and purchase order lines.
4. Extract carrier, tracking number, supplier, warehouse, fulfillment status.
5. Extract embedded `tracking_status` when available.
6. If no embedded status exists, optionally call the tracking status URL.
7. Normalize response.
8. Return common order details model.

### Important note
`get_order_details` without expand is not enough for final shipment status/ETA. It gives tracking references and URLs, but not necessarily the actual current carrier status.

## Workflow 3: Future automatic response

Not part of the first milestone.

Possible future steps:
1. Classify customer intent.
2. Check if data confidence is high.
3. Generate or select approved response template.
4. Send reply through correct channel.
5. Log automation decision.
6. Escalate to human agent if confidence is low.

## Workflow 4: Future IVR order status

Not part of the first milestone.

Possible future steps:
1. Customer calls phone number.
2. Twilio asks for order number or detects caller phone.
3. Orchestration API searches OMS.
4. If verified, returns order/shipment status.
5. Twilio reads status using programmable voice.
6. If not verified or ambiguous, forward to human agent.
