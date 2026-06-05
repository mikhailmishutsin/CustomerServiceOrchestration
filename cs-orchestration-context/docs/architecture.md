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
        +--> Order Business API
        |       +--> search_orders
        |       +--> get_order_details
        +--> FedEx API fallback
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

### Order Business API client
Responsible only for communication with the Order Business API.

Should expose methods like:
- search orders by phone/email
- search orders by customer name or order reference when available
- apply supported filters such as order status, fulfillment status and marketplace
- get order details
- get fulfillment/shipment status
- create return order
- create replacement order

Order search and order details use the same Order Business API base URL and service user.
The client should still expose separate methods because `search_orders` and `get_order_details` are different operations.

### FedEx tracking client
Responsible only for fallback FedEx shipment tracking calls.

Important rule:
- If Order Business API `expand=true` already returns embedded `tracking_status`, do not call the FedEx API.
- Use the FedEx API only when embedded tracking status is missing and a FedEx tracking status URL/reference is available.
- The FedEx API has its own base URL and service user.

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

## Credential and endpoint boundaries

The orchestration layer should treat each external capability as a separate integration boundary:

```text
ORDER_BUSINESS_API_BASE_URL    + ORDER_BUSINESS_API_USER/PASSWORD + ORDER_BUSINESS_API_SECRET_KEY
FEDEX_API_BASE_URL             + FEDEX_API_USER/PASSWORD + FEDEX_API_SECRET_KEY
FRESHDESK_BASE_URL             + FRESHDESK_USER/API_KEY
```

Do not assume the FedEx API uses the same URL or service user as the Order Business API.
Do not share service users between integrations unless the external system explicitly requires it.
Each client should receive only the credentials it needs for its own endpoint.
Login/password authorize the service user; `secret_key` remains a separate URL-level credential.
