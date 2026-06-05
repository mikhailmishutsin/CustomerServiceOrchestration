from typing import Any
from urllib.parse import urljoin

import httpx

from cs_orchestration.config.settings import ServiceEndpoint
from cs_orchestration.integrations.oms.base import FilterMode


class OrderBusinessApiError(RuntimeError):
    pass


class OrderBusinessApiClient:
    def __init__(
        self,
        endpoint: ServiceEndpoint,
        *,
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if endpoint.base_url is None:
            raise ValueError("ORDER_BUSINESS_API_BASE_URL is not configured.")
        self.endpoint = endpoint
        self.timeout = timeout
        self.transport = transport
        self.last_request_debug: dict[str, Any] | None = None

    def search_orders(
        self,
        *,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        customer_full_name: str | None = None,
        order_number: str | None = None,
        filter_mode: FilterMode | None = None,
        order_status: str | None = None,
        order_status_fulfillment: str | None = None,
        marketplace: str | None = None,
        expand: bool = True,
        limit: int = 5,
    ) -> dict[str, Any]:
        params = self._clean_params(
            {
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "customer_full_name": customer_full_name,
                "order_number": order_number,
                "filter_mode": filter_mode,
                "order_status": order_status,
                "order_status_fulfillment": order_status_fulfillment,
                "marketplace": marketplace,
                "expand": _bool_param(expand),
                "max_records": limit,
            }
        )
        return self._get("search_orders", params)

    def get_order_details(
        self,
        *,
        order_number: str,
        expand: bool = True,
    ) -> dict[str, Any]:
        params = self._clean_params(
            {
                "order_number": order_number,
                "expand": _bool_param(expand),
            }
        )
        return self._get("get_order_details", params)

    def _get(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {**params, **self._auth_query_params()}
        headers = self._auth_headers()
        auth = self._basic_auth()
        url = urljoin(f"{self.endpoint.base_url.rstrip('/')}/", operation)
        self.last_request_debug = self._build_request_debug(
            operation=operation,
            url=url,
            params=request_params,
        )

        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            try:
                response = client.get(
                    url,
                    params=request_params,
                    headers=headers,
                    auth=auth,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise OrderBusinessApiError(_status_error_message(exc.response)) from None
            except httpx.HTTPError as exc:
                raise OrderBusinessApiError(
                    f"Order Business API request failed: {exc.__class__.__name__}"
                ) from None

    def _auth_query_params(self) -> dict[str, str]:
        credentials = self.endpoint.credentials
        if self.endpoint.auth_mode in ("query_secret", "basic_query_secret"):
            if credentials.secret_key is None:
                raise ValueError("ORDER_BUSINESS_API_SECRET_KEY is not configured.")
            return {self.endpoint.secret_param: credentials.secret_key}
        if self.endpoint.auth_mode == "query_user_secret":
            if credentials.username is None:
                raise ValueError("ORDER_BUSINESS_API_USER is not configured.")
            if credentials.secret_key is None:
                raise ValueError("ORDER_BUSINESS_API_SECRET_KEY is not configured.")
            return {
                self.endpoint.user_param: credentials.username,
                self.endpoint.secret_param: credentials.secret_key,
            }
        return {}

    def _auth_headers(self) -> dict[str, str]:
        credentials = self.endpoint.credentials
        if self.endpoint.auth_mode == "bearer":
            if credentials.secret_key is None:
                raise ValueError("ORDER_BUSINESS_API_SECRET_KEY is not configured.")
            return {"Authorization": f"Bearer {credentials.secret_key}"}
        return {}

    def _basic_auth(self) -> tuple[str, str] | None:
        credentials = self.endpoint.credentials
        if self.endpoint.auth_mode not in ("basic", "basic_query_secret"):
            return None
        if credentials.username is None:
            raise ValueError("ORDER_BUSINESS_API_USER is not configured.")
        if credentials.password is None:
            raise ValueError("ORDER_BUSINESS_API_PASSWORD is not configured.")
        return (credentials.username, credentials.password)

    @staticmethod
    def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in params.items() if value not in (None, "")}

    def _build_request_debug(
        self,
        *,
        operation: str,
        url: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        redacted_params = _redact_params(params, self.endpoint)
        return {
            "service": "order_business_api",
            "operation": operation,
            "method": "GET",
            "url": str(httpx.URL(url, params=redacted_params)),
            "query": redacted_params,
            "auth_mode": self.endpoint.auth_mode,
        }


def _bool_param(value: bool) -> str:
    return "true" if value else "false"


def _status_error_message(response: httpx.Response) -> str:
    message = f"Order Business API returned HTTP {response.status_code}."
    location = response.headers.get("location")
    if location:
        message = f"{message} Redirect location: {location}"
    return message


def _redact_params(params: dict[str, Any], endpoint: ServiceEndpoint) -> dict[str, Any]:
    redacted = dict(params)
    redacted_keys = {endpoint.secret_param}
    if endpoint.auth_mode == "query_user_secret":
        redacted_keys.add(endpoint.user_param)

    for key in redacted_keys:
        if key in redacted:
            redacted[key] = "[redacted]"
    return redacted
