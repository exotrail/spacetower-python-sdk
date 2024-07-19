from abc import ABC, abstractmethod
from enum import Enum

import leo_station_keeping


class _ToleranceType(str, Enum):
    SMA = "SMA"
    ALONG_TRACK = "ALONG_TRACK"


class Tolerance(ABC):
    @abstractmethod
    def __init__(self, value: float):
        """
        Args:
            value (float): The value of the tolerance (in km).
        """
        self._value = value

    @property
    def value(self):
        return self._value

    @abstractmethod
    def to_microservice_format(self):
        pass


class SemiMajorAxisTolerance(Tolerance):
    def __init__(self, value: float):
        """
        Args:
            value (float): The value of the tolerance on the mean semi-major axis (in km).
        """
        super().__init__(value)

    def to_microservice_format(self) -> leo_station_keeping.SmaTolerance:
        return leo_station_keeping.SmaTolerance(sma_tolerance=self.value * 1e3, type=_ToleranceType.SMA)


class AlongTrackTolerance(Tolerance):
    def __init__(self, value: float):
        """
        Args:
            value (float): The value of the along-track tolerance (in km).
        """
        super().__init__(value)

    def to_microservice_format(self) -> leo_station_keeping.AlongTrackTolerance:
        return leo_station_keeping.AlongTrackTolerance(along_track_tolerance=self.value * 1e3,
                                                       type=_ToleranceType.ALONG_TRACK)
