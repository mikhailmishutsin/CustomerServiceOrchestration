import json
from pathlib import Path

from cs_orchestration.integrations.oms.mapper import normalize_search_orders_response


FIXTURE = Path("cs-orchestration-context/examples/oms-search-orders-response.json")


def test_normalizes_embedded_expand_tracking_status() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    orders = normalize_search_orders_response(payload)

    assert len(orders) == 1
    assert orders[0].order_number == "wlm-000000000000000"
    assert orders[0].fulfillment_status == "Shipped"
    assert orders[0].shipments[0].carrier == "FedEx"
    assert orders[0].shipments[0].tracking_status == "Delivered"
    assert orders[0].shipments[0].actual_pickup_date == "2026-05-13T00:00:00+00:00"
    assert orders[0].shipments[0].tracking_status_source == "embedded_expand"


def test_redacts_secret_key_from_details_url() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    orders = normalize_search_orders_response(payload)

    redacted_url = orders[0].details_ref.raw_details_url_redacted
    assert "secret_key=***" in redacted_url
    assert "secret_key=abc" not in redacted_url


def test_normalizes_status_for_master_and_child_tracking_numbers() -> None:
    payload = {
        "orders": [
            {
                "order_number": "wm-123",
                "order_date": "2026-06-04T10:54:14.000Z",
                "marketplace": "United Tires Walmart",
                "order_status": "Done",
                "order_status_fulfillment": "Shipped",
                "details": {
                    "order_number": "wm-123",
                    "order_date": "2026-06-04T10:54:14.000Z",
                    "marketplace": "United Tires Walmart",
                    "order_status": "Done",
                    "order_status_fulfillment": "Shipped",
                    "shipping_information": {"to": {}},
                    "lines": [
                        {
                            "purchase_order_lines": [
                                {
                                    "shipping_information": {
                                        "tracking_information": {
                                            "carrier": "FedEx",
                                            "child_tracking_numbers": [
                                                "381813584158",
                                                "381813584294",
                                                "381813584629",
                                            ],
                                            "master_tracking_number": "381813582501",
                                            "tracking_status": {
                                                "381813582501": {
                                                    "status": "In transit",
                                                    "description": "On the way",
                                                    "status_code": "IT",
                                                    "first_scan_date": "2026-06-04T22:50:12-04:00",
                                                    "estimated_delivery_window_ends": "2026-06-06T00:00:00+00:00",
                                                    "tracking_number": "381813582501",
                                                },
                                                "381813584158": {
                                                    "status": "In transit",
                                                    "description": "On the way",
                                                    "status_code": "IT",
                                                    "first_scan_date": "2026-06-04T22:50:12-04:00",
                                                    "estimated_delivery_window_ends": "2026-06-06T00:00:00+00:00",
                                                    "tracking_number": "381813584158",
                                                },
                                                "381813584294": {
                                                    "status": "In transit",
                                                    "description": "On the way",
                                                    "status_code": "IT",
                                                    "first_scan_date": "2026-06-04T22:50:12-04:00",
                                                    "estimated_delivery_window_ends": "2026-06-06T00:00:00+00:00",
                                                    "tracking_number": "381813584294",
                                                },
                                                "381813584629": {
                                                    "status": "In transit",
                                                    "description": "On the way",
                                                    "status_code": "IT",
                                                    "first_scan_date": "2026-06-04T22:50:12-04:00",
                                                    "estimated_delivery_window_ends": "2026-06-06T00:00:00+00:00",
                                                    "tracking_number": "381813584629",
                                                },
                                            },
                                        }
                                    }
                                }
                            ]
                        }
                    ],
                },
            }
        ]
    }

    orders = normalize_search_orders_response(payload)

    assert len(orders) == 1
    assert len(orders[0].shipments) == 4
    tracking_numbers = {shipment.tracking_number for shipment in orders[0].shipments}
    assert tracking_numbers == {
        "381813582501",
        "381813584158",
        "381813584294",
        "381813584629",
    }
    master_shipment = next(
        shipment
        for shipment in orders[0].shipments
        if shipment.tracking_number == "381813582501"
    )
    child_shipment = next(
        shipment
        for shipment in orders[0].shipments
        if shipment.tracking_number == "381813584158"
    )
    assert master_shipment.child_tracking_numbers == [
        "381813584158",
        "381813584294",
        "381813584629",
    ]
    assert child_shipment.child_tracking_numbers == []
    assert all(
        shipment.tracking_status == "In transit"
        and shipment.tracking_status_source == "embedded_expand"
        for shipment in orders[0].shipments
    )
