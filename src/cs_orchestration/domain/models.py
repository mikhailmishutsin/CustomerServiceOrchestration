from typing import Any, Literal

from pydantic import BaseModel, Field


class Customer(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    marketplace_customer_id: str | None = None


class TicketContext(BaseModel):
    subject: str | None = None
    description: str | None = None
    source: str | None = None
    channel: str | None = None


class HelpdeskRequest(BaseModel):
    ticket_id: str
    customer: Customer
    ticket: TicketContext


class FreshdeskRecentOrdersRequest(BaseModel):
    ticket_id: str
    customer_phone: str | None = None
    customer_email: str | None = None
    order_number: str | None = None


class LookupCriteria(BaseModel):
    order_reference: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    customer_name: str | None = None


class EnrichmentRequest(BaseModel):
    source_system: str
    source_record_id: str | None = None
    request_type: str | None = None
    case_type: str | None = None
    max_records: int | None = None
    lookup: LookupCriteria = Field(default_factory=LookupCriteria)
    ticket: TicketContext = Field(default_factory=TicketContext)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShippingAddress(BaseModel):
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = "US"


class PurchaseOrderLine(BaseModel):
    purchase_order_line_id: str | None = None
    purchase_order_number: str | None = None
    quantity: int | None = None
    fulfillment_status: str | None = None
    supplier_name: str | None = None
    supplier_warehouse: str | None = None
    supplier_price: float | None = None
    shipment_reference: str | None = None


class OrderLine(BaseModel):
    sku: str | None = None
    product_name: str | None = None
    quantity: int | None = None
    price: float | None = None
    tax_amount: float | None = None
    tax_percent: float | None = None
    fulfillment_status: str | None = None
    purchase_order_lines: list[PurchaseOrderLine] = Field(default_factory=list)


TrackingStatusSource = Literal["embedded_expand", "tracking_api", "not_available"]


class Shipment(BaseModel):
    carrier: str | None = None
    tracking_number: str | None = None
    child_tracking_numbers: list[str] = Field(default_factory=list)
    tracking_status: str | None = None
    tracking_description: str | None = None
    raw_status_code: str | None = None
    eta_start: str | None = None
    eta_end: str | None = None
    ship_date: str | None = None
    actual_pickup_date: str | None = None
    first_scan_date: str | None = None
    delivered_at: str | None = None
    tracking_status_source: TrackingStatusSource = "not_available"


class DetailsRef(BaseModel):
    order_number: str | None = None
    raw_details_url_redacted: str | None = None
    safe_agent_url: str | None = None


class Order(BaseModel):
    order_number: str
    order_date: str | None = None
    ship_by: str | None = None
    deliver_by: str | None = None
    marketplace: str | None = None
    order_status: str | None = None
    fulfillment_status: str | None = None
    customer: Customer = Field(default_factory=Customer)
    shipping_address: ShippingAddress = Field(default_factory=ShippingAddress)
    order_lines: list[OrderLine] = Field(default_factory=list)
    shipments: list[Shipment] = Field(default_factory=list)
    details_ref: DetailsRef | None = None
    totals: dict[str, Any] = Field(default_factory=dict)


class SupportSummary(BaseModel):
    short_summary: str
    private_note: str
    latest_order_link: str | None = None
    latest_delivery_status: str | None = None
    latest_delivery_eta: str | None = None
    latest_order_date: str | None = None
    confidence: str
    warnings: list[str] = Field(default_factory=list)


class HelpdeskUpdate(BaseModel):
    ticket_id: str
    private_note: str
    public_reply: str | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    priority: str | None = None
    type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnrichmentResult(BaseModel):
    order_summary: str
    private_note: str
    order_link: str | None = None
    delivery_status: str | None = None
    delivery_eta: str | None = None
    order_date: str | None = None


class ShipmentSnapshot(BaseModel):
    carrier: str | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None
    child_tracking_numbers: list[str] = Field(default_factory=list)
    tracking_status: str | None = None
    tracking_details: str | None = None
    eta: str | None = None
    actual_pickup_date: str | None = None
    delivered_at: str | None = None


class OrderSnapshot(BaseModel):
    order_reference: str
    order_date: str | None = None
    ship_by: str | None = None
    deliver_by: str | None = None
    marketplace: str | None = None
    customer: Customer = Field(default_factory=Customer)
    order_link: str | None = None
    shipments: list[ShipmentSnapshot] = Field(default_factory=list)


class EnrichmentResponse(BaseModel):
    source_system: str
    source_record_id: str | None = None
    request_type: str | None = None
    case_type: str | None = None
    normalized_case_type: str | None = None
    match_status: str
    matched_order_count: int
    matched_orders: list[OrderSnapshot] = Field(default_factory=list)
    result: EnrichmentResult
    metadata: dict[str, Any] = Field(default_factory=dict)
