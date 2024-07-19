from abc import abstractmethod, ABC
from datetime import datetime

from fds.models.ground_station import GroundStation
from fds.utils.enum import EnumFromInput
from fds.utils.log import log_and_raise


class EventWithDuration(ABC):
    """
    Base class for all events with a time duration.
    """
    class EventKind(EnumFromInput):
        """
        This class enumerates all the event types categorized as "events with duration".
        """
        STATION_ENTER = "STATION_ENTER"
        STATION_EXIT = "STATION_EXIT"
        ECLIPSE_ENTER = "ECLIPSE_ENTER"
        ECLIPSE_EXIT = "ECLIPSE_EXIT"
        SUN_IN_FOV_START = "SUN_IN_FOV_START"
        SUN_IN_FOV_END = "SUN_IN_FOV_END"

    @abstractmethod
    def __init__(
            self,
            start_date: datetime = None,
            end_date: datetime = None
    ):
        if start_date is None and end_date is None:
            msg = "Either 'start_date' or 'end_date' is a needed input!"
            log_and_raise(ValueError, msg)

        if start_date is not None and end_date is not None and start_date > end_date:
            msg = f"Start date ({start_date}) is after end date ({end_date})."
            log_and_raise(ValueError, msg)

        self._start_date = start_date
        self._end_date = end_date

    @property
    def start_date(self) -> datetime | None:
        """
        The start date of the event
        """
        return self._start_date

    @start_date.setter
    def start_date(self, start_date: datetime):
        if self.end_date is not None and start_date > self.end_date:
            msg = f"Start date {start_date} is after end date {self.end_date}"
            log_and_raise(ValueError, msg)

    @property
    def end_date(self) -> datetime | None:
        """
        The end date of the event.
        """
        return self._end_date

    @end_date.setter
    def end_date(self, end_date: datetime):
        if self.start_date is not None and end_date < self.start_date:
            msg = f"End date {end_date} is before start date {self.start_date}"
            log_and_raise(ValueError, msg)
        self._end_date = end_date

    @property
    def duration_sec(self) -> float | None:
        """
        The duration of the event, expressed in seconds.
        """
        if self.start_date is None or self.end_date is None:
            return None
        return (self.end_date - self.start_date).total_seconds()


class EclipseEvent(EventWithDuration):
    """
    This class is used to represent eclipse (enter and exit) events.
    """
    def __init__(
            self,
            start_date: datetime = None,
            end_date: datetime = None
    ):
        super().__init__(start_date, end_date)


class SensorEvent(EventWithDuration):
    """
    This class is used to represent all the event with duration related to the sensors.
    """
    class EventKind(EnumFromInput):
        """
        Enumerates the sensors events currently handled.
        """
        SUN_IN_FOV = "SUN_IN_FOV"

    def __init__(
            self,
            kind: EventKind,
            start_date: datetime = None,
            end_date: datetime = None
    ):
        super().__init__(start_date, end_date)
        self._kind = self.EventKind.from_input(kind)

    @property
    def kind(self) -> EventKind:
        """
        The type of sensor event with duration this instance is representing.
        """
        return self._kind


class OrbitalEvent:
    """
    This class is used to represent all the occurring event related to orbital mechanics.
    """
    class EventKind(EnumFromInput):
        """
        Enumerates all the types of orbital event.
        """
        APOGEE = "APOGEE"
        PERIGEE = "PERIGEE"
        ASCENDING_NODE = "ASCENDING_NODE"
        DESCENDING_NODE = "DESCENDING_NODE"
        ORBITAL_LOCAL_TIME_6AM = "ORBITAL_LOCAL_TIME_6AM"
        ORBITAL_LOCAL_TIME_NOON = "ORBITAL_LOCAL_TIME_NOON"
        ORBITAL_LOCAL_TIME_6PM = "ORBITAL_LOCAL_TIME_6PM"
        ORBITAL_LOCAL_TIME_MIDNIGHT = "ORBITAL_LOCAL_TIME_MIDNIGHT"

    def __init__(
            self,
            kind: EventKind | str,
            date: datetime = None,
    ):
        self._kind = self.EventKind.from_input(kind)
        self._date = date

    @property
    def kind(self) -> EventKind:
        """
        What type of orbital event this instance represents.
        """
        return self._kind

    @property
    def date(self) -> datetime:
        """
        The date of the orbital event.
        """
        return self._date


class StationVisibilityEvent(EventWithDuration):
    """
    This class is used to represents the station visibility events with duration.
    """
    def __init__(
            self,
            ground_station: GroundStation,
            start_date: datetime = None,
            end_date: datetime = None
    ):
        super().__init__(start_date, end_date)
        self._ground_station = ground_station

    @property
    def ground_station(self) -> GroundStation:
        """
        The ground station this event is associated to.
        """
        return self._ground_station
