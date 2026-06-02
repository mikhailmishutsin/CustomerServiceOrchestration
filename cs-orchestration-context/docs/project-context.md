# Project Context

## Business
The company is a US retail / dropshipping business selling tires and parts.

Customer communication comes from multiple channels:
- phone calls
- web chat
- email
- marketplaces such as Walmart and eBay

Freshdesk is currently used as the centralized storage for support communication.
ChannelReply connects Walmart/eBay communication to Freshdesk.
Freshcaller is used as the phone UI and is integrated with Freshdesk.
Twilio is currently used for basic IVR and forwarding calls to agents.

## Internal systems
The company has internal APIs that expose:
- sales order history
- current order status
- fulfillment status
- shipment/tracking status
- return/replacement order creation
- product/SKU details and attributes

## Main problem
Support agents need fast, structured and reliable information from OMS and product systems inside the support workflow.

The system should reduce manual lookup work and prepare enough context for agents or automated replies.

## Long-term goal
Resolve a major part of customer requests without human involvement.

For high-confidence cases, the system should be able to send replies automatically through:
- email
- SMS
- marketplace communication channels
- programmable voice for phone calls

## First step
Build an API layer that receives requests from the Helpdesk system, calls OMS, post-processes the response and sends useful information back to Helpdesk.

Initial use case:
Find last X orders by customer phone/email and return order information, shipping status and ETA.
