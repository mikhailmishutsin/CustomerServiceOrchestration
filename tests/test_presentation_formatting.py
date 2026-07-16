from cs_orchestration.domain.models import Shipment
from cs_orchestration.presentation.formatting import (
    display_delivery_status,
    display_eta,
    format_datetime,
)


def test_formats_datetimes_and_eta_in_support_time_zone() -> None:
    shipment = Shipment(
        tracking_status="In transit",
        eta_start="2026-06-09T09:50:00-04:00",
        eta_end="2026-06-09T17:00:00-04:00",
    )

    assert format_datetime("2026-06-09T09:50:00-04:00") == "Jun 09, 2026, 8:50 AM CDT"
    assert display_eta(shipment) == "Jun 09, 2026, 8:50 AM - 4:00 PM CDT"
    assert display_delivery_status(shipment) == "In transit"


def test_preserves_nonstandard_datetime_value_for_agent_visibility() -> None:
    assert format_datetime("date supplied by OMS") == "date supplied by OMS"


def test_uses_central_standard_time_outside_daylight_saving_time() -> None:
    assert format_datetime("2026-12-09T14:50:00+00:00") == "Dec 09, 2026, 8:50 AM CST"


def test_formats_order_level_deadlines_in_central_time() -> None:
    assert format_datetime("2026-07-15T17:00:00+00:00") == "Jul 15, 2026, 12:00 PM CDT"
    assert format_datetime("2026-07-18T17:30:00+00:00") == "Jul 18, 2026, 12:30 PM CDT"
