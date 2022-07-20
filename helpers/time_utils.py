from datetime import datetime
from typing import Union

ONE_MINUTE = 60
ONE_HOUR = 3600
ONE_DAY = 24 * ONE_HOUR
ONE_YEAR = 1 * 365 * ONE_DAY


def days_to_seconds(amount_days: Union[int, float]) -> int:
    return int(amount_days * ONE_DAY)


def hours_to_seconds(amount_hours: Union[int, float]) -> int:
    return int(amount_hours * 3600.0)


def minutes_to_seconds(amount_minutes: Union[int, float]) -> int:
    return int(amount_minutes * 60.0)


def to_utc_date(timestamp: int) -> str:
    return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def to_timestamp(date: datetime) -> int:
    print(date.timestamp())
    return int(date.timestamp())


def seconds_to_minutes(duration: int) -> Union[int, float]:
    return duration / ONE_MINUTE


def seconds_to_days(duration: int) -> Union[int, float]:
    return duration / ONE_DAY


def seconds_to_hours(duration: int) -> Union[int, float]:
    return duration / ONE_HOUR
