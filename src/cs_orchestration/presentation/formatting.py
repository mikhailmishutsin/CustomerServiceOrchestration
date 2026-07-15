from datetime import UTC, datetime
from zoneinfo import ZoneInfo


AGENT_TIME_ZONE = ZoneInfo("America/Chicago")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def format_datetime(value: str | None) -> str | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        return value
    localized = parsed.astimezone(AGENT_TIME_ZONE)
    return (
        f"{localized.strftime('%b %d, %Y')}, "
        f"{_format_time(localized)} {_timezone_label(localized)}"
    )


def format_datetime_range(start: str | None, end: str | None) -> str | None:
    start_datetime = parse_datetime(start)
    end_datetime = parse_datetime(end)
    if start_datetime:
        start_datetime = start_datetime.astimezone(AGENT_TIME_ZONE)
    if end_datetime:
        end_datetime = end_datetime.astimezone(AGENT_TIME_ZONE)
    if start_datetime and end_datetime:
        if (
            _timezone_label(start_datetime) == _timezone_label(end_datetime)
            and start_datetime.date() == end_datetime.date()
        ):
            return (
                f"{start_datetime.strftime('%b %d, %Y')}, "
                f"{_format_time(start_datetime)} - {_format_time(end_datetime)} "
                f"{_timezone_label(end_datetime)}"
            )
        return f"{format_datetime(start)} to {format_datetime(end)}"
    if end_datetime:
        return format_datetime(end)
    if start_datetime:
        return format_datetime(start)
    return None


def display_delivery_status(shipment: object | None) -> str | None:
    if shipment is None:
        return None
    return getattr(shipment, "tracking_status", None) or getattr(
        shipment, "tracking_description", None
    )


def display_eta(shipment: object | None) -> str | None:
    if shipment is None:
        return None
    return format_datetime_range(
        getattr(shipment, "eta_start", None),
        getattr(shipment, "eta_end", None),
    )


def _format_time(value: datetime) -> str:
    hour = value.strftime("%I").lstrip("0") or "0"
    return f"{hour}:{value.strftime('%M')} {value.strftime('%p')}"


def _timezone_label(value: datetime) -> str:
    if value.tzinfo == AGENT_TIME_ZONE:
        return value.tzname() or "CT"
    offset = value.utcoffset()
    if offset is None:
        return value.tzname() or "CT"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"
