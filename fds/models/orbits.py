from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

import numpy as np

from fds.client import FdsClient
from fds.models._model import TimestampedRetrievableModel, ModelSource
from fds.utils import orbital_mechanics as om
from fds.utils.dates import datetime_to_iso_string
from fds.utils.enum import EnumFromInput
from fds.utils.frames import Frame
from fds.utils.geometry import convert_to_numpy_array_and_check_shape
from fds.utils.log import log_and_raise


class OrbitType(EnumFromInput):
    KEPLERIAN = "KEPLERIAN"
    CARTESIAN = "CARTESIAN"
    EQUINOCTIAL = "EQUINOCTIAL"
    CIRCULAR = "CIRCULAR"


class OrbitMeanOsculatingType(EnumFromInput):
    MEAN = "MEAN"
    OSCULATING = "OSC"


class PositionAngleType(EnumFromInput):
    MEAN = "MEAN"
    TRUE = "TRUE"


class Orbit(TimestampedRetrievableModel, ABC):
    FDS_TYPE = FdsClient.Models.ORBIT

    @abstractmethod
    def __init__(
            self,
            kind: str | OrbitMeanOsculatingType,
            date: str | datetime,
            frame: str | Frame,
            nametag: str = None
    ):
        super().__init__(date, nametag)
        self._kind = OrbitMeanOsculatingType.from_input(kind)
        self._frame = Frame.from_input(frame)

    @property
    def kind(self) -> OrbitMeanOsculatingType:
        return self._kind

    @property
    def frame(self) -> Frame:
        return self._frame

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'date': obj_data['date'],
            'frame': obj_data['frame']
        }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'date': datetime_to_iso_string(self.date),
                'frame': self.frame.value
            }
        )
        return d

    @classmethod
    def retrieve_generic_by_id(cls, client_id: str, nametag: str = None):
        obj_data = FdsClient.get_client().retrieve_model(cls.FDS_TYPE, client_id)
        if not isinstance(obj_data, dict):
            obj_data = obj_data.to_dict()
        if 'semiMajorAxis' in obj_data:
            obj_type = KeplerianOrbit
        else:
            msg = f"Object '{cls.FDS_TYPE}' cannot be converted to SDK object"
            log_and_raise(ValueError, msg)
        new_obj = obj_type(**obj_type.api_retrieve_map(obj_data), nametag=nametag)
        new_obj._client_id = client_id
        new_obj._model_source = ModelSource.CLIENT
        new_obj._client_retrieved_object_data.update(obj_data)
        return new_obj


class KeplerianOrbit(Orbit):
    FDS_TYPE = FdsClient.Models.KEPLERIAN_ORBIT

    def __init__(
            self,
            semi_major_axis: float,
            anomaly: float,
            argument_of_perigee: float,
            eccentricity: float,
            inclination: float,
            raan: float,
            anomaly_kind: str | PositionAngleType,
            kind: str | OrbitMeanOsculatingType,
            date: str | datetime,
            frame: str | Frame = Frame.GCRF,
            nametag: str = None):
        """
        Args:
            semi_major_axis (float): (Unit: km)
            anomaly (float): (Unit: deg) Mean or True anomaly, depending on anomaly_kind
            argument_of_perigee (float): (Unit: deg)
            eccentricity (float): (Unit: adimensional)
            inclination (float): (Unit: deg)
            raan (float): (Unit: deg)
            anomaly_kind (str | AnomalyKind): Anomaly kind (MEAN or TRUE)
            kind (str | OrbitMeanOsculatingType): Orbit kind
            date (str): Date in UTC format
            nametag (str, optional): Defaults to None.
      """
        super().__init__(date=date, kind=kind, frame=frame, nametag=nametag)

        self._anomaly_kind = PositionAngleType.from_input(anomaly_kind)
        if self._anomaly_kind == PositionAngleType.TRUE:
            self._orbital_elements = om.OrbitalElements(SMA=semi_major_axis, ECC=eccentricity, INC=inclination,
                                                        AOP=argument_of_perigee, RAAN=raan, TA=anomaly)
        else:
            self._orbital_elements = om.OrbitalElements.with_mean_anomaly(SMA=semi_major_axis, ECC=eccentricity,
                                                                          INC=inclination, AOP=argument_of_perigee,
                                                                          RAAN=raan, MA=anomaly)

        self._kind = OrbitMeanOsculatingType.from_input(kind)

    @property
    def orbital_elements(self) -> om.OrbitalElements:
        return self._orbital_elements

    @property
    def keplerian_period(self) -> float:
        return om.keplerian_period(self.orbital_elements.SMA)

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'kind': obj_data['meanOscType'],
                'semi_major_axis': obj_data['semiMajorAxis'],
                'inclination': obj_data['inclination'],
                'eccentricity': obj_data['eccentricity'],
                'raan': obj_data['raan'],
                'argument_of_perigee': obj_data['argumentOfPerigee'],
                'anomaly': obj_data['anomaly'],
                'anomaly_kind': obj_data['positionAngleType']
            }
        )
        return d

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()

        d.update(
            {
                'meanOscType': self.kind.value,
                'semi_major_axis': self.orbital_elements.SMA,
                'anomaly': self.orbital_elements.TA,
                'argumentOfPerigee': self.orbital_elements.AOP,
                'date': datetime_to_iso_string(self.date),
                'eccentricity': self.orbital_elements.ECC,
                'inclination': self.orbital_elements.INC,
                'raan': self.orbital_elements.RAAN,
                'positionAngleType': PositionAngleType.TRUE,
            }
        )
        return d


class CartesianState(Orbit):
    FDS_TYPE = FdsClient.Models.CARTESIAN_ORBIT

    def __init__(
            self,
            position_x: float,
            position_y: float,
            position_z: float,
            velocity_x: float,
            velocity_y: float,
            velocity_z: float,
            date: str | datetime,
            frame: str | Frame,
            nametag: str = None):
        """
        Args:
            position_x (float): (Unit: km)
            position_y (float): (Unit: km)
            position_z (float): (Unit: km)
            velocity_x (float): (Unit: km/s)
            velocity_y (float): (Unit: km/s)
            velocity_z (float): (Unit: km/s)
            date (str): Date in UTC format
            nametag (str, optional): Defaults to None.
        """
        super().__init__(date=date, kind=OrbitMeanOsculatingType.OSCULATING, frame=frame, nametag=nametag)
        self._position_x = position_x
        self._position_y = position_y
        self._position_z = position_z
        self._velocity_x = velocity_x
        self._velocity_y = velocity_y
        self._velocity_z = velocity_z

    @property
    def position(self) -> np.ndarray:
        return np.array([self._position_x, self._position_y, self._position_z])

    @property
    def velocity(self) -> np.ndarray:
        return np.array([self._velocity_x, self._velocity_y, self._velocity_z])

    @property
    def position_x(self) -> float:
        return self._position_x

    @property
    def position_y(self) -> float:
        return self._position_y

    @property
    def position_z(self) -> float:
        return self._position_z

    @property
    def velocity_x(self) -> float:
        return self._velocity_x

    @property
    def velocity_y(self) -> float:
        return self._velocity_y

    @property
    def velocity_z(self) -> float:
        return self._velocity_z

    @property
    def state(self) -> np.ndarray:
        return np.array([self.position_x, self.position_y, self.position_z, self.velocity_x, self.velocity_y,
                         self.velocity_z])

    @classmethod
    def from_state(cls, state: np.ndarray, date: str | datetime, frame: str | Frame, nametag: str = None):
        """
        Args:
            state (np.ndarray): State vector with shape (6,), for position and velocity (Unit: km and km/s)
            date (str): Date in UTC format
            frame (str | Frame): Frame
            nametag (str, optional): Defaults to None.
        """
        convert_to_numpy_array_and_check_shape(state, (6,))
        return cls(
            position_x=float(state[0]),
            position_y=float(state[1]),
            position_z=float(state[2]),
            velocity_x=float(state[3]),
            velocity_y=float(state[4]),
            velocity_z=float(state[5]),
            date=date,
            frame=frame,
            nametag=nametag
        )

    @classmethod
    def from_position_velocity(cls, position: Sequence[float] | np.ndarray, velocity: Sequence[float] | np.ndarray,
                               date: str | datetime, frame: str | Frame, nametag: str = None):
        """
        Args:
            position (Sequence[float]): Position (Unit: km)
            velocity (Sequence[float]): Velocity (Unit: km/s)
            date (str): Date in UTC format
            frame (str | Frame): Frame
            nametag (str, optional): Defaults to None.
        """
        position = convert_to_numpy_array_and_check_shape(position, (3,))
        velocity = convert_to_numpy_array_and_check_shape(velocity, (3,))
        array = np.concatenate((position, velocity))
        return cls.from_state(array, date, frame, nametag)

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'position_x': obj_data['positionX'],
                'position_y': obj_data['positionY'],
                'position_z': obj_data['positionZ'],
                'velocity_x': obj_data['velocityX'],
                'velocity_y': obj_data['velocityY'],
                'velocity_z': obj_data['velocityZ'],
            }
        )
        return d

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'positionX': float(self.position[0]),
                'positionY': float(self.position[1]),
                'positionZ': float(self.position[2]),
                'velocityX': float(self.velocity[0]),
                'velocityY': float(self.velocity[1]),
                'velocityZ': float(self.velocity[2]),
            }
        )
        return d
