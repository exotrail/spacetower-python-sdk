from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import numpy as np

from fds.client import FdsClient
from fds.models._model import RetrievableModel, FromConfigBaseModel
from fds.models.ground_station import GroundStation
from fds.utils import geometry as geom
from fds.utils.dates import get_datetime, datetime_to_iso_string
from fds.utils.enum import EnumFromInput
from fds.utils.frames import Frame
from fds.utils.log import log_and_raise


class EventsRequest(RetrievableModel, ABC):

    @abstractmethod
    def __init__(self, start_date: str | datetime, nametag: str = None):
        super().__init__(nametag)
        self._start_date = get_datetime(start_date)

    @property
    def start_date(self) -> datetime:
        return self._start_date

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'start_date': datetime_to_iso_string(self.start_date)
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {'start_date': obj_data.get('startDate')}


class EventsRequestOrbital(EventsRequest):
    FDS_TYPE = FdsClient.Models.EVENT_REQUEST_ORBITAL

    class EventKind(EnumFromInput):
        NODE = "NODE"
        ECLIPSE = "ECLIPSE"
        ORBITAL_6AMPM = "ORBITAL_6AMPM"
        ORBITAL_NOON_MIDNIGHT = "ORBITAL_NOON_MIDNIGHT"
        APSIDE = "APSIDE"

    def __init__(
            self,
            event_kinds: Sequence[str | EventKind],
            start_date: str | datetime = None,
            nametag: str = None
    ):
        """
        Args:
            event_kinds (Sequence[str | EventKind]): Sequence of EventKind objects.
            start_date (str): (Unit: UTC) Defaults to None.
            nametag (str, optional): Defaults to None.
        """
        super().__init__(start_date, nametag)

        self._event_kinds = [self.EventKind.from_input(ev) for ev in event_kinds]

    @property
    def event_kinds(self) -> Sequence[EventKind]:
        return self._event_kinds

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'events_type': [ev.value for ev in self.event_kinds]
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'event_kinds': obj_data['eventsType']
            })
        return d


class EventsRequestSensor(EventsRequest):
    FDS_TYPE = FdsClient.Models.EVENT_REQUEST_SENSOR

    class EventKind(EnumFromInput):
        SUN_IN_FOV = "SUN_IN_FOV"

    def __init__(
            self,
            event_kinds: Sequence[str | EventKind],
            ephemerides_step: float,
            sensor_axis_in_spacecraft_frame: Sequence[float | int],
            sensor_field_of_view_half_angle: float,
            start_date: str | datetime = None,
            nametag: str = None
    ):
        """
        Args:
            event_kinds (Sequence[str | EventKind]): Sequence of EventKind objects.
            ephemerides_step (float): (Unit: s) Step of output ephemerides.
            sensor_axis_in_spacecraft_frame (Sequence[float | int]): Sequence of 3 elements.
            sensor_field_of_view_half_angle (float): (Unit: deg) Half angle defining the conical field of view.
            start_date (str): (Unit: UTC) Defaults to None.
            nametag (str, optional): Defaults to None.
        """

        super().__init__(start_date, nametag)

        self._event_kinds = [self.EventKind.from_input(ev) for ev in event_kinds]
        self._ephemerides_step = ephemerides_step
        self._sensor_axis_in_spacecraft_frame = (
            geom.convert_to_numpy_array_and_check_shape(sensor_axis_in_spacecraft_frame, (3,)))
        self._sensor_field_of_view_half_angle = sensor_field_of_view_half_angle

    @property
    def event_kinds(self) -> Sequence[EventKind]:
        return self._event_kinds

    @property
    def ephemerides_step(self) -> float:
        return self._ephemerides_step

    @property
    def sensor_axis_in_spacecraft_frame(self) -> np.ndarray:
        return self._sensor_axis_in_spacecraft_frame

    @property
    def sensor_field_of_view_half_angle(self) -> float:
        return self._sensor_field_of_view_half_angle

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'events_type': [ev.value for ev in self.event_kinds],
                'ephemerides_step': self.ephemerides_step,
                'sensor_axis_in_spacecraft_frame': self.sensor_axis_in_spacecraft_frame.tolist(),
                'sensor_field_of_view_half_angle': self.sensor_field_of_view_half_angle
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'event_kinds': obj_data['eventsType'],
                'ephemerides_step': obj_data['ephemeridesStep'],
                'sensor_axis_in_spacecraft_frame': obj_data['sensorAxisInSpacecraftFrame'],
                'sensor_field_of_view_half_angle': obj_data['sensorFieldOfViewHalfAngle']
            })
        return d


class EventsRequestStationVisibility(EventsRequest):
    FDS_TYPE = FdsClient.Models.EVENT_REQUEST_STATION_VISIBILITY

    def __init__(
            self,
            ground_stations: Sequence[GroundStation],
            start_date: str | datetime = None,
            nametag: str = None
    ):
        """
        Args:
            ground_stations (Sequence[GroundStation]): Sequence of GroundStation objects.
            start_date (str): (Unit: UTC) Defaults to None.
            nametag (str, optional): Defaults to None.
        """
        super().__init__(start_date, nametag)

        self._ground_stations = ground_stations

    @property
    def ground_stations(self) -> Sequence[GroundStation]:
        return self._ground_stations

    def api_create_map(self, force_save: bool = False) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'ground_station_ids': [gs.save(force_save).client_id for gs in self.ground_stations]
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'ground_stations': [GroundStation.retrieve_by_id(gs_id) for gs_id in
                                    obj_data.get('groundStationIDs')]
            })
        return d


class OrbitDataMessageRequest(FromConfigBaseModel, RetrievableModel, ABC):
    @abstractmethod
    def __init__(self, nametag: str = None):
        super().__init__(nametag)


class OemRequest(OrbitDataMessageRequest):
    FDS_TYPE = FdsClient.Models.OEM_REQUEST

    def __init__(
            self,
            creator: str,
            ephemerides_step: float,
            frame: str | Frame,
            object_id: str,
            object_name: str,
            write_acceleration: bool = False,
            write_covariance: bool = False,
            nametag: str = None
    ):
        """
        Args:
            creator (str): Name of the creator.
            ephemerides_step (float): (Unit: s)
            frame (str | CssdsFrame): Frame of the output ephemerides.
            object_id (str): Object ID.
            object_name (str): Object name.
            write_acceleration (bool): True if the acceleration must be written. Defaults to False.
            write_covariance (bool): True if the covariance must be written. Defaults to False.
            nametag (str, optional): Defaults to None.
        """
        super().__init__(nametag)
        self._creator = creator
        self._ephemerides_step = ephemerides_step
        self._frame = self._check_available_frames(Frame.from_input(frame))

        self._object_id = object_id
        self._object_name = object_name
        self._write_acceleration = write_acceleration
        self._write_covariance = write_covariance

    @property
    def creator(self) -> str:
        return self._creator

    @property
    def ephemerides_step(self) -> float:
        return self._ephemerides_step

    @property
    def frame(self) -> Frame:
        return self._frame

    @property
    def object_id(self) -> str:
        return self._object_id

    @property
    def object_name(self) -> str:
        return self._object_name

    @property
    def write_acceleration(self) -> bool:
        return self._write_acceleration

    @property
    def write_covariance(self) -> bool:
        return self._write_covariance

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'creator': obj_data['creator'],
            'ephemerides_step': obj_data['ephemeridesStep'],
            'frame': obj_data['frame'],
            'object_id': obj_data['objectId'],
            'object_name': obj_data['objectName'],
            'write_acceleration': obj_data['writeAcceleration'],
            'write_covariance': obj_data['writeCovariance']
        }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'creator': self.creator,
                'ephemerides_step': self.ephemerides_step,
                'frame': self.frame.value_or_alias,
                'object_id': self.object_id,
                'object_name': self.object_name,
                'write_acceleration': self.write_acceleration,
                'write_covariance': self.write_covariance
            }
        )
        return d

    @staticmethod
    def _check_available_frames(frame: Frame) -> Frame:
        if frame not in [Frame.J2000, Frame.ITRF, Frame.ECF, Frame.EME2000, Frame.TEME, Frame.GCRF, Frame.ECI,
                         Frame.CIRF]:
            msg = f"Frame {frame.value} is not available for OEM request."
            log_and_raise(ValueError, msg)
        return frame


class MeasurementsRequest(RetrievableModel, ABC):
    @dataclass
    class StandardDeviation:
        pass

    @abstractmethod
    def __init__(
            self,
            generation_step: float,
            nametag: str
    ):
        super().__init__(nametag)
        self._generation_step = generation_step

    @property
    def generation_step(self) -> float:
        return self._generation_step

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'generation_step': self.generation_step
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {'generation_step': obj_data['generationStep']}


class MeasurementsRequestStation(MeasurementsRequest, ABC):
    @dataclass
    class StandardDeviation:
        azimuth: float
        elevation: float

    @abstractmethod
    def __init__(
            self,
            ground_station: GroundStation,
            generation_step: float,
            nametag: str
    ):
        super().__init__(generation_step, nametag)
        self._ground_station = ground_station

    @property
    def ground_station(self) -> GroundStation:
        return self._ground_station

    def api_create_map(self, force_save: bool = False) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'ground_station_id': self.ground_station.save(force_save).client_id
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'ground_station': GroundStation.retrieve_by_id(obj_data['groundStationId'])
            }
        )
        return d


class MeasurementsRequestOptical(MeasurementsRequestStation):
    FDS_TYPE = FdsClient.Models.MEASUREMENT_REQUEST_OPTICAL

    def __init__(
            self,
            azimuth_standard_deviation: float,
            elevation_standard_deviation: float,
            ground_station: GroundStation,
            generation_step: float,
            nametag: str = None
    ):
        """
        Args:
            azimuth_standard_deviation (float): (Unit: deg)
            elevation_standard_deviation (float): (Unit: deg)
            ground_station (GroundStation): GroundStation object.
            generation_step (float): (Unit: s)
            nametag (str, optional): Defaults to None.
        """
        super().__init__(ground_station, generation_step, nametag)

        self._standard_deviation = (self.StandardDeviation(azimuth=azimuth_standard_deviation,
                                                           elevation=elevation_standard_deviation))

    @property
    def standard_deviation(self) -> MeasurementsRequestStation.StandardDeviation:
        return self._standard_deviation

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'azimuth_standard_deviation': self.standard_deviation.azimuth,
                'elevation_standard_deviation': self.standard_deviation.elevation
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'azimuth_standard_deviation': obj_data['azimuthStandardDeviation'],
                'elevation_standard_deviation': obj_data['elevationStandardDeviation']
            }
        )
        return d


class MeasurementsRequestRadar(MeasurementsRequestStation):
    FDS_TYPE = FdsClient.Models.MEASUREMENT_REQUEST_RADAR

    @dataclass
    class StandardDeviation:
        range: float
        range_rate: float
        azimuth: float
        elevation: float

    def __init__(
            self,
            azimuth_standard_deviation: float,
            elevation_standard_deviation: float,
            ground_station: GroundStation,
            generation_step: float,
            two_way_measurement: bool,
            range_standard_deviation: float,
            range_rate_standard_deviation: float,
            nametag: str = None
    ):
        """
        Args:
            azimuth_standard_deviation (float): (Unit: deg)
            elevation_standard_deviation (float): (Unit: deg)
            ground_station (GroundStation): GroundStation object.
            generation_step (float): (Unit: s)
            two_way_measurement (bool): True if the measurement is two-way.
            range_standard_deviation (float): (Unit: m)
            range_rate_standard_deviation (float): (Unit: m/s)
            nametag (str, optional): Defaults to None.
        """
        super().__init__(ground_station, generation_step, nametag)

        self._two_way_measurement = two_way_measurement
        self._standard_deviation = self.StandardDeviation(range=range_standard_deviation,
                                                          range_rate=range_rate_standard_deviation,
                                                          azimuth=azimuth_standard_deviation,
                                                          elevation=elevation_standard_deviation)

    @property
    def two_way_measurement(self) -> bool:
        return self._two_way_measurement

    @property
    def standard_deviation(self) -> StandardDeviation:
        return self._standard_deviation

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'two_way_measurement': self.two_way_measurement,
                'azimuth_standard_deviation': self.standard_deviation.azimuth,
                'elevation_standard_deviation': self.standard_deviation.elevation,
                'range_standard_deviation': self.standard_deviation.range,
                'range_rate_standard_deviation': self.standard_deviation.range_rate
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'two_way_measurement': obj_data['twoWayMeasurement'],
                'azimuth_standard_deviation': obj_data['azimuthStandardDeviation'],
                'elevation_standard_deviation': obj_data['elevationStandardDeviation'],
                'range_standard_deviation': obj_data['rangeStandardDeviation'],
                'range_rate_standard_deviation': obj_data['rangeRateStandardDeviation']
            }
        )
        return d


class MeasurementsRequestGpsPv(MeasurementsRequest):
    FDS_TYPE = FdsClient.Models.MEASUREMENT_REQUEST_GPS_PV

    @dataclass
    class StandardDeviation:
        position: float
        velocity: float

    def __init__(
            self,
            standard_deviation_position: float,
            standard_deviation_velocity: float,
            generation_step: float,
            frame: Frame | str,
            nametag: str = None
    ):
        """
        Args:
            standard_deviation_position (float): (Unit: m)
            standard_deviation_velocity (float): (Unit: m/s)
            generation_step (float): (Unit: s)
            frame (str | Frame): The frame in which the measurements are expressed.
            nametag (str, optional): Defaults to None.
        """
        super().__init__(generation_step, nametag)

        self._frame = Frame.from_input(frame)
        self._standard_deviation = self.StandardDeviation(standard_deviation_position,
                                                          standard_deviation_velocity)

    @property
    def standard_deviation(self) -> StandardDeviation:
        return self._standard_deviation

    @property
    def frame(self) -> Frame:
        return self._frame

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'position_standard_deviation': self.standard_deviation.position,
                'velocity_standard_deviation': self.standard_deviation.velocity,
                'frame': self.frame.value_or_alias
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'standard_deviation_position': obj_data['positionStandardDeviation'],
                'standard_deviation_velocity': obj_data['velocityStandardDeviation'],
                'frame': obj_data['frame']
            }
        )
        return d


class MeasurementsRequestGpsNmea(MeasurementsRequest):
    FDS_TYPE = FdsClient.Models.MEASUREMENT_REQUEST_GPS_NMEA

    @dataclass
    class StandardDeviation:
        ground_speed: float
        latitude: float
        longitude: float
        altitude: float

    def __init__(
            self,
            standard_deviation_ground_speed: float,
            standard_deviation_latitude: float,
            standard_deviation_longitude: float,
            standard_deviation_altitude: float,
            generation_step: float,
            nametag: str = None
    ):
        """
        Args:
            standard_deviation_ground_speed (float): (Unit: m/s)
            standard_deviation_latitude (float): (Unit: deg)
            standard_deviation_longitude (float): (Unit: deg)
            standard_deviation_altitude (float): (Unit: m)
            generation_step (float): (Unit: s)
            nametag (str, optional): Defaults to None.
        """
        super().__init__(generation_step, nametag)

        self._standard_deviation = self.StandardDeviation(standard_deviation_ground_speed,
                                                          standard_deviation_latitude,
                                                          standard_deviation_longitude,
                                                          standard_deviation_altitude)

    @property
    def standard_deviation(self) -> StandardDeviation:
        return self._standard_deviation

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'ground_speed_standard_deviation': self.standard_deviation.ground_speed,
                'latitude_standard_deviation': self.standard_deviation.latitude,
                'longitude_standard_deviation': self.standard_deviation.longitude,
                'altitude_standard_deviation': self.standard_deviation.altitude
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'standard_deviation_ground_speed': obj_data['groundSpeedStandardDeviation'],
                'standard_deviation_latitude': obj_data['latitudeStandardDeviation'],
                'standard_deviation_longitude': obj_data['longitudeStandardDeviation'],
                'standard_deviation_altitude': obj_data['altitudeStandardDeviation']
            }
        )
        return d


class EphemeridesRequest(RetrievableModel):
    FDS_TYPE = FdsClient.Models.EPHEMERIDES_REQUEST

    class EphemerisType(EnumFromInput):
        CARTESIAN = "CARTESIAN"
        KEPLERIAN = "KEPLERIAN"
        POWER = "POWER"
        PROPULSION = "PROPULSION"
        ATTITUDE_QUATERNIONS = "ATTITUDE_QUATERNIONS"
        ATTITUDE_EULER_ANGLES = "ATTITUDE_EULER_ANGLES"

        @classmethod
        def substitute_map(cls):
            return {
                'POWER': 'BATTERY',
                'PROPULSION': 'THRUST',
                'ATTITUDE_QUATERNIONS': 'QUATERNION',
                'ATTITUDE_EULER_ANGLES': 'EULER_ANGLES'
            }

        @classmethod
        def substitute_map_reverse(cls):
            d = cls.substitute_map()
            return {v: k for k, v in d.items()}

    def __init__(
            self,
            ephemeris_types: Sequence[str | EphemerisType],
            step: float,
            nametag: str = None
    ):
        """
        Args:

            ephemeris_types (Sequence[str | EphemerisType]): Sequence of EphemerisType objects. Must not contain
                duplicates.
            step (float): (Unit: s). Note: this will override the OrbitDataMessageRequest.generation_step if CARTESIAN
                ephemeris type is requested.
            nametag (str, optional): Defaults to None.
        """

        super().__init__(nametag)
        self._ephemeris_types = [self.EphemerisType.from_input(et) for et in ephemeris_types]
        self._step = step

    @property
    def ephemeris_types(self) -> Sequence[EphemerisType]:
        return self._ephemeris_types

    @property
    def step(self) -> float:
        return self._step

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        ephemeris_types = [self.EphemerisType.substitute_map().get(et.value, et.value) for et in self.ephemeris_types]
        d.update(
            {
                'ephemeris_types': ephemeris_types,
                'step': self.step
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        ephem_types = [cls.EphemerisType.substitute_map_reverse().get(et, et) for et in obj_data['ephemerisTypes']]
        return {
            'ephemeris_types': ephem_types,
            'step': obj_data['step']
        }
