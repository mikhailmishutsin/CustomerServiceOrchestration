# Current Scope

## In scope for first milestone

### Main flow
Find last X orders by customer phone/email and send a support summary back to Helpdesk.

### Input
A request from Helpdesk containing ticket and customer context.

Minimum useful fields:
- ticket id
- customer phone
- customer email
- customer name if available
- ticket subject
- ticket description
- source/channel

### Processing
The orchestration layer should:
1. Receive Helpdesk request.
2. Extract customer identifiers.
3. Call OMS search API.
4. Get last X matching orders.
5. Normalize raw OMS response.
6. Prepare order/shipment summary.
7. Build Helpdesk update payload.
8. In dry-run mode, return the payload without sending it.
9. In real mode, update Helpdesk.

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
