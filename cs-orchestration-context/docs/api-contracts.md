# API Contracts

This file describes external API behavior and the normalized contracts used by the orchestration layer.
External payloads should be isolated inside adapters/clients. Business logic should use normalized internal models.

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

## OMS `search_orders`

### Purpose
Find recent orders by customer/order identifiers. This endpoint can now also return expanded order details and tracking status.

### Supported search criteria
Current known criteria:

- `customer_phone`
- `customer_email`
- `customer_full_name`
- `order_number` if supported by API/client

### Optional filters
Known filter fields:

- `order_status`
  - `New`
  - `Processing`
  - `Done`
  - `Cancelled`
  - `On Hold`
- `order_status_fulfillment`
  - `New Order`
  - `Shipped`
  - `Delivered`
  - `Done`
  - `Cancelled`
- `marketplace`
  - example: `utires.com`

### Filter mode
`filter_mode` controls how multiple search criteria are applied.

- `all` means all provided criteria must match.
- `any` means an order may match at least one provided criterion.
- If `filter_mode` is not provided in the request URL, the parameter should be omitted from the generated URL.

Example with `any`:

```text
/search_orders?customer_phone=5551234567&filter_mode=any&expand=true&secret_key=***
```

Example with filters:

```text
/search_orders?customer_email=customer@example.com&customer_full_name=John%20Customer&customer_phone=5551234567&order_status=Processing&order_status_fulfillment=Delivered&marketplace=utires.com&expand=true&secret_key=***
```

### Expand mode
`expand=true` means the OMS response may include detailed order data inside each `orders[].details` object.

When `expand=true`, the OMS may also call the shipping carrier API internally and include shipment status under:

```text
orders[].details.lines[].purchase_order_lines[].shipping_information.tracking_information.tracking_status
```

If `expand` is not enabled, search results may contain only high-level order fields and `details_url`.

### Important parser rules

- `orders[]` is the top-level result list.
- `orders[].details` may exist only when `expand=true`.
- If `orders[].details` exists, prefer it for line-level and shipment data.
- If `orders[].details` does not exist, call `details_url` or `get_order_details` to fetch line/tracking data.
- Sort orders by `order_date` descending before selecting latest order unless the client explicitly guarantees sort order.
- Never expose `secret_key` from URLs in customer-facing text, logs, notes, or custom fields.
- Store raw URLs only in redacted/debug-safe form.

See example:

```text
examples/oms-search-orders-response-expanded-sanitized.json
```

## OMS `get_order_details`

### Purpose
Fetch full order details, lines, purchase order lines, supplier info, carrier info, tracking numbers, and optionally tracking status.

### Expand mode
`get_order_details` supports `expand=true`.

Without expand:

```text
/get_order_details?order_number=ebay-00-00000-00000&secret_key=***
```

With expand:

```text
/get_order_details?order_number=ebay-00-00000-00000&expand=true&secret_key=***
```

When `expand=false` or omitted, response usually contains:

- line data
- purchase order lines
- carrier
- master tracking number
- `tracking_status_urls`

When `expand=true`, response may also contain:

- `tracking_status`
- `actual_pickup_date`
- `first_scan_date`
- `ship_date`
- `estimated_delivery_window_begins`
- `estimated_delivery_window_ends`
- carrier status and status code

See examples:

```text
examples/oms-get-order-details-response-not-expanded-sanitized.json
examples/oms-get-order-details-response-expanded-sanitized.json
```

## Shipment tracking data

Tracking status can come from two places:

1. Already embedded in OMS response when `expand=true`.
2. Fetched separately from `tracking_status_urls` when expand is false or embedded status is missing.

Parser should support both.

Important fields:

- `carrier`
- `master_tracking_number`
- `tracking_status[tracking_number].status`
- `tracking_status[tracking_number].description`
- `tracking_status[tracking_number].status_code`
- `tracking_status[tracking_number].actual_pickup_date`
- `tracking_status[tracking_number].first_scan_date`
- `tracking_status[tracking_number].ship_date`
- `tracking_status[tracking_number].estimated_delivery_window_begins`
- `tracking_status[tracking_number].estimated_delivery_window_ends`

## Normalized order model

```json
{
  "order_number": "WLM-123456",
  "order_date": "2026-06-01T12:00:00Z",
  "marketplace": "walmart_main",
  "order_status": "Done",
  "fulfillment_status": "Shipped",
  "customer": {
    "name": "John Customer",
    "email": "customer@example.com",
    "phone": "+15555555555"
  },
  "shipping_address": {
    "line1": "123 Main St",
    "line2": "",
    "city": "Austin",
    "state": "TX",
    "postal_code": "78701",
    "country": "US"
  },
  "order_lines": [
    {
      "sku": "u-xxxxxxxx",
      "product_name": "New 255/65R18 Michelin Primacy A/S 111H",
      "quantity": 1,
      "price": 217.28,
      "fulfillment_status": "Shipped"
    }
  ],
  "shipments": [
    {
      "carrier": "FedEx",
      "tracking_number": "999999999999",
      "tracking_status": "Delivered",
      "tracking_description": "Delivered",
      "raw_status_code": "DL",
      "eta_start": null,
      "eta_end": "2026-05-15T00:00:00+00:00",
      "ship_date": "2026-05-13T00:00:00+00:00",
      "actual_pickup_date": "2026-05-13T00:00:00+00:00",
      "first_scan_date": "2026-05-15T13:34:05-04:00"
    }
  ],
  "details_ref": {
    "order_number": "WLM-123456",
    "safe_agent_url": null,
    "raw_details_url_redacted": "https://ds.example.com/orders_business_apis/get_order_details?order_number=WLM-123456&secret_key=***&expand=true"
  }
}
```

## Helpdesk update payload

The common orchestration output should not be Freshdesk-specific.

```json
{
  "ticket_id": "12345",
  "private_note": "Found 1 recent order. Latest order WLM-123456: Shipped, FedEx Delivered.",
  "custom_fields": {
    "order_summary": "Latest order WLM-123456: Shipped, FedEx Delivered.",
    "order_link": "https://agent.example.com/order/WLM-123456"
  },
  "metadata": {
    "source": "orchestration-layer",
    "dry_run": true
  }
}
```

Freshdesk adapter should convert this common payload into Freshdesk API format.
