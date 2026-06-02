# Data Model

These models are internal normalized models. They should stay stable even if Freshdesk or OMS payloads change.

## Customer

Fields:
- name
- email
- phone
- marketplace_customer_id later

## Order

Fields:
- order_number
- order_date
- marketplace
- order_status
- fulfillment_status
- customer
- shipping_address
- order_lines
- shipments
- details_ref
- totals

## Order Line

Fields:
- sku
- product_name
- quantity
- price
- tax_amount
- tax_percent
- fulfillment_status
- purchase_order_lines

## Purchase Order Line

Fields:
- purchase_order_line_id
- purchase_order_number
- quantity
- fulfillment_status
- supplier_name
- supplier_warehouse
- supplier_price
- shipment_reference

## Shipment

Fields:
- carrier
- tracking_number
- child_tracking_numbers
- tracking_status
- tracking_description
- raw_status_code
- eta_start
- eta_end
- ship_date
- actual_pickup_date
- first_scan_date
- delivered_at optional
- tracking_status_source

`tracking_status_source` values:
- `embedded_expand` when status came from `expand=true` OMS response
- `tracking_api` when status came from separate tracking API call
- `not_available` when only tracking number/URL exists

## Details Ref

Fields:
- order_number
- raw_details_url_redacted
- safe_agent_url optional

Rules:
- Never store or expose unredacted `secret_key`.
- If Helpdesk needs an order link, create a safe internal agent link, not the raw API URL.

## Support Summary

Fields:
- short_summary
- private_note
- latest_order_link
- confidence
- warnings

## Helpdesk Update

Fields:
- ticket_id
- private_note
- public_reply optional future
- custom_fields
- tags optional
- priority optional
- type optional
