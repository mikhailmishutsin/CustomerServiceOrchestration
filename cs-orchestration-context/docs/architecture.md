# Architecture

## Core idea
The orchestration layer should sit between Customer Service tools and internal systems.

It should not be tightly coupled to Freshdesk.
Freshdesk is only the first Helpdesk implementation.

## High-level flow

```text
Support Channel / Helpdesk
        |
        v
Orchestration API
        |
        +--> OMS API
        +--> Product/SKU API
        +--> Twilio / Voice APIs
        |
        v
Helpdesk / Customer Channel update
```

## Main components

### Orchestration API
Receives events and requests from Helpdesk, Twilio or other systems.

Examples:
- ticket created
- ticket updated
- web chat started
- phone IVR lookup
- agent action

### Workflow services
Business-level flows. These services coordinate clients and adapters.

Examples:
- enrich ticket with recent orders
- classify ticket type
- prepare routing decision
- prepare customer reply
- create return/replacement flow

### OMS client
Responsible only for communication with OMS API.

Should expose methods like:
- search orders by phone/email
- get order details
- get fulfillment/shipment status
- create return order
- create replacement order

### Product/SKU client
Responsible only for product API communication.

Should expose methods like:
- get SKU details
- get product attributes
- get compatibility/fitment data if available

### Helpdesk abstraction
Common interface that the orchestration layer uses.

Example methods:
- get ticket
- update ticket fields
- add private note
- add public reply
- set ticket type
- set priority
- assign group/agent

### Freshdesk adapter
Freshdesk-specific implementation of the Helpdesk abstraction.

All Freshdesk-specific field names, endpoints and payload shapes should stay here.

### Normalization layer
Converts raw external API responses into stable internal models.

Examples:
- Customer
- Order
- OrderLine
- Shipment
- TrackingStatus
- SupportSummary

## Important rule
Core workflows should use normalized models and common interfaces, not raw Freshdesk or OMS payloads.
