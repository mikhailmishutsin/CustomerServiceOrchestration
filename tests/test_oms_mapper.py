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
    assert orders[0].shipments[0].tracking_status_source == "embedded_expand"


def test_redacts_secret_key_from_details_url() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    orders = normalize_search_orders_response(payload)

    redacted_url = orders[0].details_ref.raw_details_url_redacted
    assert "secret_key=***" in redacted_url
    assert "secret_key=abc" not in redacted_url
