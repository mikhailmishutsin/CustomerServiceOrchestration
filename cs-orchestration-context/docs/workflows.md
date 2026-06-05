# Workflows

## Workflow 1: Freshdesk recent orders private note

### Trigger
Freshdesk sends an API request for a ticket that needs recent order context.

Current endpoint:

```text
POST /freshdesk/recent-orders
```

### Steps
1. Receive ticket id, customer phone, customer email, and optional order number.
2. Validate inbound `X-API-Key` when configured.
3. Normalize phone for OMS search.
4. If both phone and email exist, try exact contact search first:
   phone + email with `filter_mode=all`.
5. If exact contact search finds nothing, fallback to partial matching:
   phone-only search, then email-only search.
6. If order number exists and contact lookup does not find orders, search by order reference.
7. Prefer `expand=true` for order-status enrichment because it can return order details and tracking status in one response.
8. Call OMS `search_orders` with `max_records=3` for the Freshdesk recent-orders endpoint.
9. Sort orders from newest to oldest by `order_date` if needed.
10. For each selected order:
   - if `orders[].details` exists, use it for line and shipment data;
   - if `orders[].details` is missing, call `get_order_details` with `expand=true` when shipment data is required.
11. If expanded details still do not include `tracking_status`, use `tracking_status_urls` as fallback.
12. Normalize orders and shipments.
13. Format order dates, ETA windows, first scan dates, and delivery dates in agent-friendly form.
14. Build short support summary.
15. Build full private note.
16. Add partial-match warning if phone/email exact match was not found.
17. Add Sales Order link when available.
18. In `DRY_RUN=true`, return the Helpdesk update payload without writing to Freshdesk.
19. In `DRY_RUN=false`, create a Freshdesk private note.

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
For ambiguous multiple matches, ask the agent/customer for the last 4 digits of the order number.

### Partial contact match result
When both phone and email are provided but no exact contact match is found, the note should clearly say:

```text
No exact match was found for the provided contact data.
Partial match found: matched on phone, did not match on email.
```

Metadata should include:

```text
match_quality=partial_contact_match
exact_contact_match_found=false
contact_match_details.matched_on
contact_match_details.mismatched_on
```

### Important implementation note
Do not use `filter_mode=any` with both phone and email for the current Freshdesk partial-match fallback.
The live OMS API returned HTTP 400 for that combination.
Use phone-only and email-only fallback searches instead.

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
