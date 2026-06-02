# Workflows

## Workflow 1: Enrich Helpdesk ticket with recent orders

### Trigger
Helpdesk sends a webhook or API request when a ticket is created or updated.

### Steps
1. Receive ticket context.
2. Extract customer phone and email.
3. Validate that at least one search identifier exists.
4. Search OMS for recent orders.
5. Sort orders from newest to oldest if OMS does not guarantee sorting.
6. Normalize orders.
7. Build short support summary.
8. Build full private note.
9. Update Helpdesk ticket.

### Success result
Agent can see recent order status directly in the ticket.

### No match result
Add or return a clear message:

```text
No matching orders found by provided phone/email.
```

### Multiple orders result
Show last X orders, newest first.
Clearly mark the latest order.

## Workflow 2: Future automatic response

Not part of the first milestone.

Possible future steps:
1. Classify customer intent.
2. Check if data confidence is high.
3. Generate or select approved response template.
4. Send reply through correct channel.
5. Log automation decision.
6. Escalate to human agent if confidence is low.

## Workflow 3: Future IVR order status

Not part of the first milestone.

Possible future steps:
1. Customer calls phone number.
2. Twilio asks for order number or detects caller phone.
3. Orchestration API searches OMS.
4. If verified, returns order/shipment status.
5. Twilio reads status using programmable voice.
6. If not verified or ambiguous, forward to human agent.
