# API Contracts

This file describes expected contracts at the orchestration layer level.
Exact external API payloads may differ and should be isolated inside adapters/clients.

## Helpdesk request input

Expected normalized input:

```json
{
  "ticket_id": "12345",
  "customer": {
    "name": "John Customer",
    "email": "customer@example.com",
    "phone": "+15555555555"
  },
  "ticket": {
    "subject": "Where is my order?",
    "description": "I need an update on delivery",
    "source": "email",
    "channel": "freshdesk"
  }
}
```

## OMS order search request

Supported search identifiers:
- customer phone
- customer email
- order number
- marketplace order reference later

Initial request example:

```json
{
  "customer_phone": "+15555555555",
  "customer_email": "customer@example.com",
  "limit": 5
}
```

## Normalized order model

```json
{
  "order_number": "WLM-123456",
  "order_date": "2026-06-01",
  "marketplace": "Walmart",
  "order_status": "Confirmed",
  "fulfillment_status": "Shipped",
  "customer": {
    "name": "John Customer",
    "email": "customer@example.com",
    "phone": "+15555555555"
  },
  "shipping_address": {
    "line1": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "postal_code": "78701",
    "country": "US"
  },
  "shipments": [
    {
      "carrier": "FedEx",
      "tracking_number": "1234567890",
      "tracking_status": "In transit",
      "eta": "2026-06-04",
      "delivered_at": null
    }
  ],
  "details_url": "https://example.com/order/123456"
}
```

## Helpdesk update payload

The common orchestration output should not be Freshdesk-specific.

```json
{
  "ticket_id": "12345",
  "private_note": "Found 1 recent order...",
  "custom_fields": {
    "order_summary": "Latest order WLM-123456: Shipped, FedEx In transit, ETA 2026-06-04",
    "order_link": "https://example.com/order/123456"
  },
  "metadata": {
    "source": "orchestration-layer",
    "dry_run": true
  }
}
```

Freshdesk adapter should convert this common payload into Freshdesk API format.
