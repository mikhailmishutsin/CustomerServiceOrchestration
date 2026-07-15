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

## Freshdesk recent orders endpoint

### Purpose
Freshdesk calls this endpoint to enrich a ticket with recent order history and, when `DRY_RUN=false`, create a Freshdesk private note.

### Endpoint

```text
POST /freshdesk/recent-orders
```

### Authentication
When `INBOUND_API_KEY` is configured, callers must send:

```text
X-API-Key: value-from-INBOUND_API_KEY
```

Production mode requires `INBOUND_API_KEY`.

### Request body

```json
{
  "ticket_id": "112",
  "customer_phone": "+15551234567",
  "customer_email": "customer@example.com",
  "order_number": ""
}
```

Fields:
- `ticket_id` is required.
- `customer_phone` is optional but recommended.
- `customer_email` is optional but recommended.
- `order_number` is optional.

At least one lookup value is required:
- `customer_phone`
- `customer_email`
- `order_number`

### Behavior
- Default Freshdesk recent-orders lookup asks OMS for 3 records.
- Phone numbers are normalized before OMS lookup. Example: `+1 (555) 123-4567` becomes `5551234567`.
- If phone and email are both provided, the service tries exact contact match first.
- If exact contact match finds nothing, the service falls back to phone-only then email-only searches.
- Partial contact matches are flagged in metadata and private note text.
- `DRY_RUN=true` returns the Helpdesk update payload but does not create a Freshdesk note.
- `DRY_RUN=false` creates a Freshdesk private note.

### Response body

The response is a common `HelpdeskUpdate`.

```json
{
  "ticket_id": "112",
  "private_note": "Found 1 order(s) in the last 30 days...",
  "public_reply": null,
  "custom_fields": {
    "order_summary": "Latest order WLM-123 placed Jun 01, 2026, 10:15 AM CDT | Delivery status: Delivered.",
    "order_link": "https://ds.utires.com/order_management/#order=WLM-123",
    "delivery_status": "Delivered",
    "delivery_eta": "Jun 03, 2026, 9:00 AM - 5:00 PM CDT",
    "order_date": "Jun 01, 2026, 10:15 AM CDT"
  },
  "tags": ["oms-enriched"],
  "metadata": {
    "dry_run": false,
    "operation": "recent_orders_by_contact_or_reference",
    "oms_max_records": 3,
    "matched_by": "contact_exact",
    "match_quality": "exact_contact_match",
    "exact_contact_match_found": true,
    "order_count": 1,
    "freshdesk": {
      "note_id": 98765,
      "ticket_id": 112,
      "private": true,
      "status_code": 201
    }
  }
}
```

Partial match example:

```json
{
  "metadata": {
    "matched_by": "contact_partial_phone",
    "match_quality": "partial_contact_match",
    "exact_contact_match_found": false,
    "contact_match_details": {
      "matched_on": ["customer_phone"],
      "mismatched_on": ["customer_email"]
    },
    "warnings": [
      "Partial contact match only: matched on phone, did not match on email."
    ]
  }
}
```

### Freshdesk note formatting
The Freshdesk adapter posts:

```text
POST {FRESHDESK_BASE_URL}/api/v2/tickets/{ticket_id}/notes
```

Payload:

```json
{
  "body": "<div>...</div>",
  "private": true
}
```

The note body includes a clickable Sales Order link when `custom_fields.order_link` exists.
When structured matched order snapshots exist, the Freshdesk note uses a richer HTML layout:
- latest order section
- clickable Sales Order link near the latest order
- detailed tracking section for latest order only
- clickable FedEx tracking links when `tracking_url` exists
- other recent orders table that excludes the latest order

## OMS order search

### Purpose
Find recent orders by customer/order identifiers. This endpoint can now also return expanded order details and tracking status.

### Endpoint and credentials
In the application code, this operation is called `search_orders`. The current
OMS HTTP endpoint is:

```text
GET {ORDER_BUSINESS_API_BASE_URL}/search
```

`search_orders` and `get_order_details` are logical operation names; they are
not both HTTP path names.

Expected configuration shape:

```text
ORDER_BUSINESS_API_BASE_URL
ORDER_BUSINESS_API_USER
ORDER_BUSINESS_API_PASSWORD
ORDER_BUSINESS_API_SECRET_KEY
```

Order search and `get_order_details` use the same Order Business API base URL and service user.
The login/password authorize access to the system; `secret_key` is still appended to the request URL.

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
/search?customer_phone=5551234567&filter_mode=any&expand=true&secret_key=***
```

Implementation note:
The current Freshdesk partial-match fallback does not call OMS with both phone and email plus `filter_mode=any`, because the live OMS API returned HTTP 400 for that combination.
Instead it uses simple fallback searches:

```text
1. phone + email with filter_mode=all
2. phone only
3. email only
```

Example with filters:

```text
/search?customer_email=customer@example.com&customer_full_name=John%20Customer&customer_phone=5551234567&order_status=Processing&order_status_fulfillment=Delivered&marketplace=utires.com&expand=true&secret_key=***
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
- The current deployed workflow does not yet call `details_url` or `get_order_details` automatically when details are missing; that fallback is the next integration stage.
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

### Endpoint and credentials
`get_order_details` is an operation on the Order Business API.

Expected configuration shape:

```text
ORDER_BUSINESS_API_BASE_URL
ORDER_BUSINESS_API_USER
ORDER_BUSINESS_API_PASSWORD
ORDER_BUSINESS_API_SECRET_KEY
```

Order search and `get_order_details` use the same Order Business API base URL and service user.
The login/password authorize access to the system; `secret_key` is still appended to the request URL.

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
2. Fetched separately from `tracking_status_urls` when expand is false or embedded status is missing (planned fallback).

The current deployed flow uses embedded OMS status only. The separate tracking fallback will be added with the FedEx client.

### Endpoint and credentials
Fallback tracking should be configured as the FedEx API integration.

Expected configuration shape:

```text
FEDEX_API_BASE_URL
FEDEX_API_USER
FEDEX_API_PASSWORD
FEDEX_API_SECRET_KEY
```

The FedEx API client must not be called when embedded `tracking_status` is already available from Order Business API `expand=true`.

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
      "tracking_url": "https://www.fedex.com/fedextrack/?trknbr=999999999999",
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
