from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Sequence

from fds.client import FdsClient
from fds.models._model import ModelSource, RetrievableModel, FromConfigBaseModel
from fds.models.ground_station import GroundStation
from fds.models.orbit_extrapolation.requests import MeasurementsRequestGpsNmea, MeasurementsRequestGpsPv, \
    MeasurementsRequestOptical, MeasurementsRequestRadar
from fds.utils.dates import get_datetime, datetime_to_iso_string
from fds.utils.frames import Frame
from fds.utils.log import log_and_raise
from fds.utils.nmea import RmcSentence


class Telemetry(FromConfigBaseModel, RetrievableModel, ABC):
    FDS_TYPE = FdsClient.Models.TELEMETRY

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {}

    @classmethod
    def retrieve_generic_by_id(cls, client_id: str, nametag: str = None):
        obj_data = FdsClient.get_client().retrieve_model(cls.FDS_TYPE, client_id)
        obj_type = None
        if not isinstance(obj_data, dict):
            obj_data = obj_data.to_dict()
        if 'latitudeStandardDeviation' in obj_data:
            obj_type = TelemetryGpsNmeaRaw
            if 'dates' in obj_data:
                obj_type = TelemetryGpsNmea
        elif 'positionStandardDeviation' in obj_data:
            obj_type = TelemetryGpsPv
        elif 'rangeStandardDeviation' in obj_data:
            obj_type = TelemetryRadar
        elif 'azimuthStandardDeviation' in obj_data:
            obj_type = TelemetryOptical
        else:
            msg = f"Unknown telemetry type for telemetry with client_id {client_id}."
            log_and_raise(ValueError, msg)
        new_obj = obj_type(**obj_type.api_retrieve_map(obj_data), nametag=nametag)
        new_obj._client_id = client_id
        new_obj._model_source = ModelSource.CLIENT
        new_obj._client_retrieved_object_data.update(obj_data)
        return new_obj


class TelemetryNmea(Telemetry, ABC):
    @abstractmethod
    def __init__(
            self,
            standard_deviation_ground_speed: float,
            standard_deviation_latitude: float,
            standard_deviation_longitude: float,
            standard_deviation_altitude: float, nametag: str
    ):
        super().__init__(nametag)

        self._standard_deviation = MeasurementsRequestGpsNmea.StandardDeviation(
            standard_deviation_ground_speed,
            standard_deviation_latitude,
            standard_deviation_longitude,
            standard_deviation_altitude)

    @property
    def standard_deviation(self) -> MeasurementsRequestGpsNmea.StandardDeviation:
        return self._standard_deviation

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'standard_deviation_altitude': obj_data['altitudeStandardDeviation'],
            'standard_deviation_ground_speed': obj_data['groundSpeedStandardDeviation'],
            'standard_deviation_latitude': obj_data['latitudeStandardDeviation'],
            'standard_deviation_longitude': obj_data['longitudeStandardDeviation']
        }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'altitude_standard_deviation': self.standard_deviation.altitude,
                'ground_speed_standard_deviation': self.standard_deviation.ground_speed,
                'latitude_standard_deviation': self.standard_deviation.latitude,
                'longitude_standard_deviation': self.standard_deviation.longitude
            }
        )
        return d


class TelemetryGpsNmea(TelemetryNmea):
    FDS_TYPE = FdsClient.Models.TELEMETRY_GPS_NMEA

    def __init__(
            self,
            measurements: Sequence[Sequence[float]],
            dates: Sequence[str] | Sequence[datetime],
            standard_deviation_ground_speed: float,
            standard_deviation_latitude: float,
            standard_deviation_longitude: float,
            standard_deviation_altitude: float,
            nametag: str = None
    ):
        """
        Args:
            measurements (Sequence[Sequence[float]]): Gps NMEA data as a list of lists of floats. Components must be
                latitude, longitude, norm of velocity in ECF frame, altitude,
                geoid (optional). Units: [deg], [deg], [m/s], [m], [m].
            dates (Sequence[str] | Sequence[datetime]): list of dates in UTC format.
            standard_deviation_ground_speed (float): Ground speed standard deviation (Unit: m/s)
            standard_deviation_latitude (float): Latitude standard deviation (Unit: deg)
            standard_deviation_longitude (float): Longitude standard deviation (Unit: deg)
            standard_deviation_altitude (float): Altitude standard deviation (Unit: m)
            nametag (str): Defaults to None.
        """

        super().__init__(standard_deviation_ground_speed, standard_deviation_latitude, standard_deviation_longitude,
                         standard_deviation_altitude, nametag)
        for m in measurements:
            if len(m) not in (4, 5):
                msg = "Wrong dimension of NMEA measurements, it should be 4 or 5 (if geoid is included)."
                log_and_raise(ValueError, msg)

        self._measurements = measurements
        self._dates = [get_datetime(d) for d in dates]

    @property
    def dates(self) -> Sequence[datetime]:
        return self._dates

    @property
    def start_date(self) -> datetime:
        return self.dates[0]

    @property
    def end_date(self) -> datetime:
        return self.dates[-1]

    @property
    def measurements(self) -> Sequence[Sequence[float]]:
        return self._measurements

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update({'measurements': obj_data['measurements'],
                  'dates': obj_data['dates'], })
        return d

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'measurements': self.measurements,
                'dates': [datetime_to_iso_string(d) for d in self.dates]
            }
        )
        return d

    @classmethod
    def import_from_config_file(cls, config_filepath: str | Path,
                                measurements: Sequence[Sequence[float]] = None, dates: Sequence[str] = None):
        kwargs = {'measurements': measurements, 'dates': dates}
        for k, v in kwargs.items():
            if v is None:
                msg = f"The argument '{k}' is required!"
                log_and_raise(ValueError, msg)
        return super().import_from_config_file(config_filepath, measurements=measurements, dates=dates)


class TelemetryGpsNmeaRaw(TelemetryNmea):
    FDS_TYPE = FdsClient.Models.TELEMETRY_GPS_NMEA_RAW

    def __init__(
            self,
            nmea_sentences: Sequence[str],
            standard_deviation_ground_speed: float,
            standard_deviation_latitude: float,
            standard_deviation_longitude: float,
            standard_deviation_altitude: float,
            nametag: str = None
    ):
        """
        Args:
            nmea_sentences (Sequence[str]): Gps NMEA sentences as a list of strings in the correct NMEA format.
            standard_deviation_ground_speed (float): Ground speed standard deviation (Unit: m/s)
            standard_deviation_latitude (float): Latitude standard deviation (Unit: deg)
            standard_deviation_longitude (float): Longitude standard deviation (Unit: deg)
            standard_deviation_altitude (float): Altitude standard deviation (Unit: m)
            nametag (str): Defaults to None.
        """
        # Check that nmea_sentences is a list of strings not empty
        if not all(isinstance(s, str) for s in nmea_sentences):
            msg = f"The argument 'nmea_sentences' must be a list of strings, not a {type(nmea_sentences)}."
            log_and_raise(ValueError, msg)

        super().__init__(standard_deviation_ground_speed, standard_deviation_latitude, standard_deviation_longitude,
                         standard_deviation_altitude, nametag)
        self._nmea_sentences = list(nmea_sentences)
        self._start_date = self.get_start_date()
        self._end_date = self.get_end_date()

    @property
    def nmea_sentences(self) -> list[str]:
        return self._nmea_sentences

    @property
    def start_date(self) -> datetime:
        return self._start_date

    @property
    def end_date(self) -> datetime:
        return self._end_date

    def get_start_date(self) -> datetime:
        if self.nmea_sentences[0].startswith("$GPGGA"):
            start_index = 1
        else:
            start_index = 0
        return RmcSentence.parse_datetime(self.nmea_sentences[start_index].split(","))

    def get_end_date(self) -> datetime:
        return RmcSentence.parse_datetime(self.nmea_sentences[-1].split(","))

    @classmethod
    def import_from_config_file(cls, config_filepath: str | Path,
                                nmea_sentences: Sequence[str] = None):
        if nmea_sentences is None:
            msg = "The argument 'nmea_sentences' is required!"
            log_and_raise(ValueError, msg)
        return super().import_from_config_file(config_filepath, nmea_sentences=nmea_sentences)

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update({'nmea_sentences': obj_data['nmeaSentences'], })
        return d

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'nmeaSentences': self.nmea_sentences
            }
        )
        return d


class TelemetryGpsPv(Telemetry):
    FDS_TYPE = FdsClient.Models.TELEMETRY_GPS_PV

    def __init__(
            self,
            dates: Sequence[str] | Sequence[datetime],
            frame: str | Frame,
            measurements: Sequence[Sequence[float]],
            standard_deviation_position: float,
            standard_deviation_velocity: float,
            nametag: str = None
    ):
        """
        Args:
            dates (Sequence[str] | Sequence[datetime]): list of dates in UTC format.
            frame (str | Frame): The reference frame of the measurements.
            measurements (Sequence[Sequence[float]]): Gps PV data as a list of lists of floats. Components must be
                x, y, z, vx, vy, vz. Units: [m], [m], [m], [m/s], [m/s], [m/s].
            standard_deviation_position (float): Position standard deviation (Unit: m)
            standard_deviation_velocity (float): Velocity standard deviation (Unit: m/s)
            nametag (str): Defaults to None.
        """
        super().__init__(nametag)

        self._dates = [get_datetime(d) for d in dates]
        self._measurements = measurements
        self._frame = Frame.from_input(frame)
        self._standard_deviation = MeasurementsRequestGpsPv.StandardDeviation(
            standard_deviation_position,
            standard_deviation_velocity)

    @property
    def dates(self) -> Sequence[datetime]:
        return self._dates

    @property
    def start_date(self) -> datetime:
        return self.dates[0]

    @property
    def end_date(self) -> datetime:
        return self.dates[-1]

    @property
    def measurements(self) -> Sequence[Sequence[float]]:
        return self._measurements

    @property
    def frame(self):
        return self._frame

    @property
    def standard_deviation(self) -> MeasurementsRequestGpsPv.StandardDeviation:
        return self._standard_deviation

    @classmethod
    def import_from_config_file(cls, config_filepath: str | Path,
                                frame: Frame = None,
                                dates: Sequence[str] = None,
                                measurements: Sequence[Sequence[float]] = None):
        kwargs = {'measurements': measurements, 'dates': dates, 'frame': frame}
        for k, v in kwargs.items():
            if v is None:
                msg = f"The argument '{k}' is required!"
                log_and_raise(ValueError, msg)
        return super().import_from_config_file(config_filepath, **kwargs)

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'standard_deviation_position': obj_data['positionStandardDeviation'],
            'standard_deviation_velocity': obj_data['velocityStandardDeviation'],
            'dates': obj_data['dates'],
            'frame': obj_data['frame'],
            'measurements': obj_data['measurements'],
        }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'position_standard_deviation': self.standard_deviation.position,
                'velocity_standard_deviation': self.standard_deviation.velocity,
                'dates': [datetime_to_iso_string(d) for d in self.dates],
                'frame': self.frame.value_or_alias,
                'measurements': self.measurements
            }
        )
        return d


class TelemetryGroundBased(Telemetry, ABC):

    @abstractmethod
    def __init__(
            self,
            dates: Sequence[datetime] | Sequence[str],
            measurements: Sequence[Sequence[float]],
            ground_station: GroundStation,
            nametag: str
    ):
        super().__init__(nametag)

        self._dates = [get_datetime(d) for d in dates]
        self._measurements = measurements
        self._ground_station = ground_station

    @property
    def dates(self) -> Sequence[datetime]:
        return self._dates

    @property
    def start_date(self) -> datetime:
        return self.dates[0]

    @property
    def end_date(self) -> datetime:
        return self.dates[-1]

    @property
    def measurements(self) -> Sequence[Sequence[float]]:
        return self._measurements

    @property
    def ground_station(self) -> GroundStation:
        return self._ground_station

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'dates': obj_data['dates'],
            'measurements': obj_data['measurements'],
            'ground_station': GroundStation.retrieve_by_id(obj_data['groundStationId'])
        }

    def api_create_map(self, force_save: bool = False) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'dates': [datetime_to_iso_string(d) for d in self.dates],
                'measurements': self.measurements,
                'groundStationId': self.ground_station.save(force_save).client_id
            }
        )
        return d


class TelemetryOptical(TelemetryGroundBased):
    FDS_TYPE = FdsClient.Models.TELEMETRY_OPTICAL

    def __init__(
            self,
            dates: Sequence[datetime] | Sequence[str],
            measurements: Sequence[Sequence[float]],
            ground_station: GroundStation,
            standard_deviation_azimuth: float,
            standard_deviation_elevation: float,
            nametag: str = None
    ):
        """
        Args:
            dates (Sequence[str] | Sequence[datetime]): list of dates in UTC format.
            measurements (Sequence[Sequence[float]]): Optical data as a list of lists of floats. Components must be
                azimuth, elevation, range. Units: [deg], [deg], [m].
            ground_station (GroundStation): GroundStation object.
            standard_deviation_azimuth (float): (Unit: deg)
            standard_deviation_elevation (float): (Unit: deg)
            nametag (str): Defaults to None.
        """
        super().__init__(dates, measurements, ground_station, nametag)

        self._standard_deviation = MeasurementsRequestOptical.StandardDeviation(
            standard_deviation_azimuth,
            standard_deviation_elevation)

    @property
    def standard_deviation(self) -> MeasurementsRequestOptical.StandardDeviation:
        return self._standard_deviation

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update({'standard_deviation_azimuth': obj_data['azimuthStandardDeviation'],
                  'standard_deviation_elevation': obj_data['elevationStandardDeviation'], })
        return d

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
    def import_from_config_file(cls, config_filepath: str | Path,
                                ground_station: GroundStation = None,
                                dates: Sequence[str] = None,
                                measurements: Sequence[Sequence[float]] = None):
        kwargs = {'measurements': measurements, 'dates': dates, 'ground_station': ground_station}
        for k, v in kwargs.items():
            if v is None:
                msg = f"The argument '{k}' is required!"
                log_and_raise(ValueError, msg)
        return super().import_from_config_file(config_filepath, **kwargs)


class TelemetryRadar(TelemetryGroundBased):
    FDS_TYPE = FdsClient.Models.TELEMETRY_RADAR

    def __init__(
            self,
            dates: Sequence[datetime] | Sequence[str],
            measurements: Sequence[Sequence[float]],
            ground_station: GroundStation,
            two_way_measurement: bool,
            standard_deviation_range: float,
            standard_deviation_range_rate: float,
            standard_deviation_azimuth: float,
            standard_deviation_elevation: float,
            nametag: str = None
    ):
        """
        Args:
            dates (Sequence[str] | Sequence[datetime]): list of dates in UTC format.
            measurements (Sequence[Sequence[float]]): Radar data as a list of lists of floats. Components must be
                range, range rate, azimuth, elevation. Units: [m], [m/s], [deg], [deg].
            ground_station (GroundStation): GroundStation object.
            two_way_measurement (bool): True if the measurement is two-way.
            standard_deviation_range (float): (Unit: m)
            standard_deviation_range_rate (float): (Unit: m/s)
            standard_deviation_azimuth (float): (Unit: deg)
            standard_deviation_elevation (float): (Unit: deg)
            nametag (str): Defaults to None.
        """
        super().__init__(dates, measurements, ground_station, nametag)

        self._standard_deviation = MeasurementsRequestRadar.StandardDeviation(
            standard_deviation_range,
            standard_deviation_range_rate,
            standard_deviation_azimuth,
            standard_deviation_elevation)
        self._two_way_measurement = two_way_measurement

    @property
    def standard_deviation(self) -> MeasurementsRequestRadar.StandardDeviation:
        return self._standard_deviation

    @property
    def two_way_measurement(self) -> bool:
        return self._two_way_measurement

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update({'standard_deviation_azimuth': obj_data['azimuthStandardDeviation'],
                  'standard_deviation_elevation': obj_data['elevationStandardDeviation'],
                  'standard_deviation_range': obj_data['rangeStandardDeviation'],
                  'standard_deviation_range_rate': obj_data['rangeRateStandardDeviation'],
                  'two_way_measurement': obj_data['twoWayMeasurement'], })
        return d

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'azimuth_standard_deviation': self.standard_deviation.azimuth,
                'elevation_standard_deviation': self.standard_deviation.elevation,
                'range_standard_deviation': self.standard_deviation.range,
                'range_rate_standard_deviation': self.standard_deviation.range_rate,
                'two_way_measurement': self.two_way_measurement
            }
        )
        return d

    @classmethod
    def import_from_config_file(cls, config_filepath: str | Path,
                                ground_station: GroundStation = None,
                                dates: Sequence[str] = None,
                                measurements: Sequence[Sequence[float]] = None):
        kwargs = {'measurements': measurements, 'dates': dates, 'ground_station': ground_station}
        for k, v in kwargs.items():
            if v is None:
                msg = f"The argument '{k}' is required!"
                log_and_raise(ValueError, msg)
        return super().import_from_config_file(config_filepath, **kwargs)
