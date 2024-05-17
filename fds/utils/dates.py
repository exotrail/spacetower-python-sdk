import datetime
from typing import Sequence

from fds.constants import STUDIO_DATE_FORMAT
from fds.utils.log import log_and_raise


def get_datetime(date_utc: str | datetime.datetime | None) -> datetime.datetime | None:
    """
    This function always returns a datetime object with UTC timezone (if the input is not None).
    In both cases, the timezone is checked. If it is not UTC, an exception is raised.
    """
    if date_utc is None:
        return None

    if isinstance(date_utc, str):
        date_utc = datetime.datetime.fromisoformat(date_utc)

    if not isinstance(date_utc, datetime.datetime):
        msg = f"Invalid date type {type(date_utc)} for {date_utc}"
        log_and_raise(ValueError, msg)
    return check_datetime_time_zone_is_utc(date_utc)


def check_datetime_time_zone_is_utc(date: datetime.datetime):
    if date.tzinfo is None:
        msg = f"Time zone information is missing from {date}"
        log_and_raise(ValueError, msg)
    elif date.tzinfo != datetime.timezone.utc:
        msg = f"Time zone information is not UTC in {date}"
        log_and_raise(ValueError, msg)
    return date


def datetime_to_iso_string(date: datetime.datetime | None):
    if date is None:
        return None
    if not isinstance(date, datetime.datetime):
        msg = f"Invalid date type {type(date)} for {date}. Please use datetime.datetime."
        log_and_raise(ValueError, msg)
    return check_datetime_time_zone_is_utc(date).strftime(STUDIO_DATE_FORMAT)


def filter_sequence_with_minimum_time_step(
        initial_sequence: Sequence,
        dates: list[datetime.datetime],
        minimum_step_in_seconds: float
) -> Sequence:
    if len(initial_sequence) == 0:
        return initial_sequence

    # Make sure the sequence is sorted
    if not all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1)):
        msg = "The dates are not sorted."
        log_and_raise(ValueError, msg)

    filtered_sequence = [initial_sequence[0]]
    j = 0
    for i, date in enumerate(dates):
        step = (date - dates[j]).total_seconds()
        if step >= minimum_step_in_seconds:
            filtered_sequence.append(initial_sequence[i])
            j = i
    return filtered_sequence
