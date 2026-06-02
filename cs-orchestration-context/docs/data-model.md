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
- details_url

## Order Line

Fields:
- sku
- product_name
- quantity
- fulfillment_status
- shipment_reference

## Shipment

Fields:
- carrier
- tracking_number
- tracking_status
- eta
- shipped_at
- delivered_at
- raw_status_code optional

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
