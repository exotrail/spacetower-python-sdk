import datetime
from typing import Sequence, Self

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
    return convert_date_to_utc(date_utc)


def convert_date_to_utc(date: datetime.datetime):
    if date.tzinfo is None:
        date = date.replace(tzinfo=datetime.UTC)
    elif date.tzinfo != datetime.UTC:
        date = date.astimezone(datetime.UTC)
    return date


def datetime_to_iso_string(date: datetime.datetime | None):
    if date is None:
        return None
    if not isinstance(date, datetime.datetime):
        msg = f"Invalid date type {type(date)} for {date}. Please use datetime.datetime."
        log_and_raise(ValueError, msg)
    return convert_date_to_utc(date).strftime(STUDIO_DATE_FORMAT)


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


class DateRange:
    def __init__(self, start: str | datetime.datetime, end: str | datetime.datetime):
        self._start = get_datetime(start)
        self._end = get_datetime(end)
        if self.start > self.end:
            msg = f"Start date {self.start} is after end date {self.end}"
            log_and_raise(ValueError, msg)

    def __repr__(self):
        return f"{self.start} to {self.end} ({self.duration})"

    def __str__(self):
        return f"{self.start} to {self.end} ({self.duration})"

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def start(self) -> datetime.datetime:
        return self._start

    @property
    def end(self) -> datetime.datetime:
        return self._end

    @property
    def duration(self) -> datetime.timedelta:
        return self.end - self.start

    @property
    def duration_seconds(self) -> float:
        return self.duration.total_seconds()

    @property
    def start_string(self) -> str:
        return datetime_to_iso_string(self.start)

    @property
    def end_string(self) -> str:
        return datetime_to_iso_string(self.end)

    @property
    def mid_date(self) -> datetime.datetime:
        return self.start + (self.end - self.start) / 2

    def contains(self, date: datetime.datetime, include_start=True, include_end=True) -> bool:
        if include_start and include_end:
            return self.start <= date <= self.end
        if include_start:
            return self.start <= date < self.end
        if include_end:
            return self.start < date <= self.end
        return self.start < date < self.end

    def is_overlapping(self, other) -> bool:
        return self.start < other.end and other.start < self.end

    def get_overlap(self, other) -> Self | None:
        if not self.is_overlapping(other):
            return None
        return DateRange(max(self.start, other.start), min(self.end, other.end))

    def is_adjacent(self, other) -> bool:
        return self.start == other.end or other.start == self.end

    def is_adjacent_or_overlapping(self, other) -> bool:
        return self.is_adjacent(other) or self.is_overlapping(other)

    def is_inside(self, other) -> bool:
        return other.start <= self.start and self.end <= other.end

    def is_containing(self, other) -> bool:
        return other.is_inside(self)

    def is_before(self, other) -> bool:
        return self.end < other.start

    def get_union(self, other) -> Self | None:
        if not self.is_overlapping(other):
            msg = f"Date ranges {self} and {other} do not overlap. Cannot compute union."
            log_and_raise(ValueError, msg)
        return DateRange(min(self.start, other.start), max(self.end, other.end))

    def get_intersection(self, other) -> Self | None:
        if not self.is_overlapping(other):
            msg = f"Date ranges {self} and {other} do not overlap. Cannot compute intersection."
            log_and_raise(ValueError, msg)
        return DateRange(max(self.start, other.start), min(self.end, other.end))

    def to_dict(self):
        return {
            "start": datetime_to_iso_string(self.start),
            "end": datetime_to_iso_string(self.end)
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | datetime.datetime]) -> Self:
        """
        Create a DateRange object from a dictionary with 'start' and 'end' keys.
        """
        if 'start' not in data or 'end' not in data:
            msg = f"Invalid input {data} for DateRange. Must have 'start' and 'end' keys."
            log_and_raise(ValueError, msg)
        if not isinstance(data['start'], (str, datetime.datetime)) or not isinstance(data['end'],
                                                                                     (str, datetime.datetime)):
            msg = f"Invalid input {data} for DateRange. 'start' and 'end' must be strings or datetime objects."
            log_and_raise(ValueError, msg)
        return cls(data['start'], data['end'])

    @classmethod
    def from_list(cls, data: list[str | datetime.datetime]) -> Self:
        """
        Create a DateRange object from a list of two strings or datetime objects.
        """
        if len(data) != 2:
            msg = f"Invalid input {data} for DateRange. Must be a list of two strings or datetime objects."
            log_and_raise(ValueError, msg)
        return cls(data[0], data[1])

    @classmethod
    def from_input(cls, data: Self | dict[str, str | datetime.datetime] | list[str | datetime.datetime]) -> Self:
        """
        Create a DateRange object from a variety of input formats (DateRange, dict, list).
        """
        if isinstance(data, cls):
            return data
        if isinstance(data, list):
            return cls.from_list(data)
        if isinstance(data, dict):
            return cls.from_dict(data)
        msg = (f"Invalid input {data} for DateRange. Must be a list of two strings or datetime objects, or a dict with "
               f"'start' and 'end'.")
        log_and_raise(ValueError, msg)

    @classmethod
    def from_start_and_duration(cls, start: datetime.datetime, duration: float) -> Self:
        """
        Create a DateRange object from a start date and a duration in seconds.
        """
        return cls(start, start + datetime.timedelta(seconds=duration))

    @classmethod
    def from_end_and_duration(cls, end: datetime.datetime, duration: float) -> Self:
        """
        Create a DateRange object from an end date and a duration in seconds.
        """
        return cls(end - datetime.timedelta(seconds=duration), end)

    @classmethod
    def from_start_to_now(cls, start: datetime.datetime) -> Self:
        """
        Create a DateRange object from a start date to the current date and time.
        """
        return cls(start, datetime.datetime.now(datetime.UTC))

    @classmethod
    def from_now_to_end(cls, end: datetime.datetime) -> Self:
        """
        Create a DateRange object from the current date and time to an end date.
        """
        return cls(datetime.datetime.now(datetime.UTC), end)

    @classmethod
    def from_midpoint_and_duration(cls, midpoint: datetime.datetime, duration: float) -> Self:
        """
        Create a DateRange object from a midpoint date and a duration in seconds.
        """
        return cls(midpoint - datetime.timedelta(seconds=duration / 2),
                   midpoint + datetime.timedelta(seconds=duration / 2))
