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
