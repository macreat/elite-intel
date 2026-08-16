from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class InvalidCalendarTimezone(ValueError):
    pass


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def local_calendar_range(start_date: date, end_date: date, timezone_name: str) -> tuple[datetime, datetime]:
    try:
        local_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise InvalidCalendarTimezone(timezone_name) from exc

    start = datetime.combine(start_date, time.min, tzinfo=local_timezone)
    end = datetime.combine(end_date, time.max, tzinfo=local_timezone)
    return as_utc(start), as_utc(end)


def parse_transaction_boundary(value: str | None, timezone_name: str, *, end_of_day: bool) -> datetime | None:
    if value is None:
        return None

    try:
        selected_date = date.fromisoformat(value)
    except ValueError:
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid transaction date filter: {value}") from exc
        return as_utc(timestamp)

    start, end = local_calendar_range(selected_date, selected_date, timezone_name)
    return end if end_of_day else start
