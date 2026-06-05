import httpx

from cs_orchestration.config.settings import ServiceCredentials, ServiceEndpoint
from cs_orchestration.integrations.oms.real_client import (
    OrderBusinessApiClient,
    OrderBusinessApiError,
)


def test_search_orders_calls_order_business_api_with_expand_and_secret_key() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"success": True, "orders": []})

    client = OrderBusinessApiClient(
        ServiceEndpoint(
            base_url="https://orders.example.test/orders_business_apis",
            credentials=ServiceCredentials(
                username="svc-user",
                password="svc-password",
                secret_key="svc-secret-key",
            ),
        ),
        transport=httpx.MockTransport(handler),
    )

    response = client.search_orders(
        customer_phone="5551234567",
        customer_email="customer@example.com",
        expand=True,
        limit=5,
    )

    assert response["success"] is True
    assert captured_request is not None
    assert captured_request.url.path.endswith("/orders_business_apis/search_orders")
    assert captured_request.url.params["customer_phone"] == "5551234567"
    assert captured_request.url.params["customer_email"] == "customer@example.com"
    assert captured_request.url.params["expand"] == "true"
    assert captured_request.url.params["max_records"] == "5"
    assert captured_request.url.params["secret_key"] == "svc-secret-key"
    assert captured_request.headers["Authorization"].startswith("Basic ")
    assert "filter_mode" not in captured_request.url.params
    assert client.last_request_debug is not None
    assert client.last_request_debug["operation"] == "search_orders"
    assert client.last_request_debug["query"]["secret_key"] == "[redacted]"
    assert "svc-secret-key" not in client.last_request_debug["url"]
    assert "svc-password" not in client.last_request_debug["url"]


def test_get_order_details_calls_order_business_api() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"order_number": "wlm-000000000000000"})

    client = OrderBusinessApiClient(
        ServiceEndpoint(
            base_url="https://orders.example.test/orders_business_apis/",
            credentials=ServiceCredentials(
                username="svc-user",
                password="svc-password",
                secret_key="svc-secret-key",
            ),
        ),
        transport=httpx.MockTransport(handler),
    )

    response = client.get_order_details(
        order_number="wlm-000000000000000",
        expand=True,
    )

    assert response["order_number"] == "wlm-000000000000000"
    assert captured_request is not None
    assert captured_request.url.path.endswith("/orders_business_apis/get_order_details")
    assert captured_request.url.params["order_number"] == "wlm-000000000000000"
    assert captured_request.url.params["expand"] == "true"
    assert captured_request.url.params["secret_key"] == "svc-secret-key"
    assert client.last_request_debug is not None
    assert client.last_request_debug["operation"] == "get_order_details"


def test_query_user_secret_auth_mode_sends_username_when_configured() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"success": True, "orders": []})

    client = OrderBusinessApiClient(
        ServiceEndpoint(
            base_url="https://orders.example.test",
            credentials=ServiceCredentials(username="svc-user", secret_key="svc-secret"),
            auth_mode="query_user_secret",
            user_param="username",
            secret_param="secret_key",
        ),
        transport=httpx.MockTransport(handler),
    )

    client.search_orders(customer_phone="5551234567")

    assert captured_request is not None
    assert captured_request.url.params["username"] == "svc-user"
    assert captured_request.url.params["secret_key"] == "svc-secret"
    assert client.last_request_debug is not None
    assert client.last_request_debug["query"]["username"] == "[redacted]"
    assert client.last_request_debug["query"]["secret_key"] == "[redacted]"


def test_http_status_error_does_not_expose_secret_in_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"Location": "https://www.example.test/"},
            request=request,
        )

    client = OrderBusinessApiClient(
        ServiceEndpoint(
            base_url="https://orders.example.test",
            credentials=ServiceCredentials(
                username="svc-user",
                password="svc-password",
                secret_key="very-secret-value",
            ),
        ),
        transport=httpx.MockTransport(handler),
    )

    try:
        client.search_orders(customer_phone="5551234567")
    except OrderBusinessApiError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected OrderBusinessApiError")

    assert "302" in message
    assert "https://www.example.test/" in message
    assert "very-secret-value" not in message
