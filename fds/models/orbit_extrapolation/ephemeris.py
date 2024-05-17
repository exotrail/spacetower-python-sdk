from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

import numpy as np

from fds.models.orbits import KeplerianOrbit, CartesianState
from fds.models.quaternion import Quaternion
from fds.utils.dates import get_datetime
from fds.utils.frames import Frame
from fds.utils.geometry import convert_to_numpy_array_and_check_shape


class Ephemeris(ABC):
    def __init__(self, dates: Sequence[datetime]):
        self._dates = dates

    @property
    def dates(self) -> Sequence[datetime]:
        return self._dates

    @property
    def _ref_lenght(self) -> int:
        return len(self._dates)

    @classmethod
    @abstractmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'Ephemeris':
        pass

    @abstractmethod
    def export_table_data(self) -> list[dict]:
        pass


class PowerEphemeris(Ephemeris):
    def __init__(self, dates: Sequence[datetime], battery_charge: Sequence[float],
                 solar_array_collected_power: Sequence[float], thruster_power_consumption: Sequence[float],
                 thruster_warm_up_power_consumption: Sequence[float]):
        super().__init__(dates)
        self._battery_charge = convert_to_numpy_array_and_check_shape(
            battery_charge, (self._ref_lenght,))
        self._solar_array_collected_power = convert_to_numpy_array_and_check_shape(
            solar_array_collected_power,
            (self._ref_lenght,))
        self._thruster_power_consumption = convert_to_numpy_array_and_check_shape(
            thruster_power_consumption,
            (self._ref_lenght,))
        self._thruster_warm_up_power_consumption = convert_to_numpy_array_and_check_shape(
            thruster_warm_up_power_consumption, (self._ref_lenght,))

    @property
    def battery_charge(self) -> np.ndarray:
        return self._battery_charge

    @property
    def solar_array_collected_power(self) -> np.ndarray:
        return self._solar_array_collected_power

    @property
    def thruster_power_consumption(self) -> np.ndarray:
        return self._thruster_power_consumption

    @property
    def thruster_warm_up_power_consumption(self) -> np.ndarray:
        return self._thruster_warm_up_power_consumption

    def export_table_data(self) -> list[dict]:
        return [
            {
                'date': date,
                'battery_charge': bc,
                'solar_array_collected_power': cp,
                'thruster_power_consumption': pc,
                'thruster_warm_up_power_consumption': wpc
            }
            for date, bc, cp, pc, wpc in zip(
                self.dates,
                self.battery_charge,
                self.solar_array_collected_power,
                self.thruster_power_consumption,
                self.thruster_warm_up_power_consumption
            )
        ]

    @classmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'PowerEphemeris':
        lines = obj_data['lines']
        dates = []
        battery_charge = []
        solar_array_collected_power = []
        thruster_power_consumption = []
        thruster_warm_up_power_consumption = []

        for line in lines:
            dates.append(get_datetime(line['date']))
            battery_charge.append(line['charge'])
            solar_array_collected_power.append(line['solarArrayCollectedPower'])
            thruster_power_consumption.append(line['thrusterPowerConsumption'])
            thruster_warm_up_power_consumption.append(line['thrusterWarmupPowerConsumption'])

        return cls(
            dates=dates,
            battery_charge=battery_charge,
            solar_array_collected_power=solar_array_collected_power,
            thruster_power_consumption=thruster_power_consumption,
            thruster_warm_up_power_consumption=thruster_warm_up_power_consumption
        )


class KeplerianEphemeris(Ephemeris):
    def __init__(
            self,
            dates: Sequence[datetime],
            orbits: Sequence[KeplerianOrbit],
    ):
        super().__init__(dates)
        self._orbits = orbits

    @property
    def orbits(self) -> Sequence[KeplerianOrbit]:
        return self._orbits

    def export_table_data(self) -> list[dict]:
        return [
            {
                'date': date,
                'semi_major_axis': o.orbital_elements.SMA,
                'eccentricity': o.orbital_elements.ECC,
                'inclination': o.orbital_elements.INC,
                'raan': o.orbital_elements.RAAN,
                'argument_of_perigee': o.orbital_elements.AOP,
                'true_anomaly': o.orbital_elements.TA,
            }
            for date, o in zip(self.dates, self.orbits)
        ]

    @classmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'KeplerianEphemeris':
        lines = obj_data['lines']
        dates = []
        orbits = []
        for line in lines:
            dates.append(get_datetime(line['orbit']['date']))
            orbits.append(KeplerianOrbit.retrieve_by_id(line['orbit']['id']))
        return cls(
            dates=dates,
            orbits=orbits
        )


class CartesianEphemeris(Ephemeris):
    def __init__(
            self,
            dates: Sequence[datetime],
            states: Sequence[CartesianState],
    ):
        super().__init__(dates)
        self._states = states

    @property
    def states(self) -> Sequence[CartesianState]:
        return self._states

    @property
    def frame(self) -> Frame:
        return self.states[0].frame

    def export_table_data(self) -> list[dict]:
        return [
            {
                'date': date,
                'position_x': s.position_x,
                'position_y': s.position_y,
                'position_z': s.position_z,
                'velocity_x': s.velocity_x,
                'velocity_y': s.velocity_y,
                'velocity_z': s.velocity_z,
            }
            for date, s in zip(self.dates, self.states)
        ]

    @classmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'CartesianEphemeris':
        lines = obj_data['lines']
        dates = []
        states = []
        for line in lines:
            dates.append(get_datetime(line['orbit']['date']))
            states.append(CartesianState.retrieve_by_id(line['orbit']['id']))
        return cls(
            dates=dates,
            states=states,
        )


class PropulsionEphemeris(Ephemeris):
    def __init__(
            self,
            dates: Sequence[datetime],
            instant_consumption: Sequence[float],
            total_consumption: Sequence[float],
            thrust_direction_azimuth: Sequence[float],
            thrust_direction_elevation: Sequence[float],
            propellant_mass: Sequence[float],
            current_wet_mass: Sequence[float],
    ):
        super().__init__(dates)
        self._instant_consumption = convert_to_numpy_array_and_check_shape(
            instant_consumption, (self._ref_lenght,))
        self._total_consumption = convert_to_numpy_array_and_check_shape(
            total_consumption, (self._ref_lenght,))

        thrust_direction_azimuth = [np.nan if tda == 'NaN' else tda for tda in thrust_direction_azimuth]
        thrust_direction_elevation = [np.nan if tde == 'NaN' else tde for tde in thrust_direction_elevation]

        self._thrust_direction_azimuth = convert_to_numpy_array_and_check_shape(
            thrust_direction_azimuth, (self._ref_lenght,))
        self._thrust_direction_elevation = convert_to_numpy_array_and_check_shape(
            thrust_direction_elevation,
            (self._ref_lenght,))
        self._propellant_mass = convert_to_numpy_array_and_check_shape(
            propellant_mass, (self._ref_lenght,))
        self._current_wet_mass = convert_to_numpy_array_and_check_shape(
            current_wet_mass, (self._ref_lenght,))

    @property
    def instant_consumption(self) -> np.ndarray:
        return self._instant_consumption

    @property
    def total_consumption(self) -> np.ndarray:
        return self._total_consumption

    @property
    def thrust_direction_azimuth(self) -> np.ndarray:
        return self._thrust_direction_azimuth

    @property
    def thrust_direction_elevation(self) -> np.ndarray:
        return self._thrust_direction_elevation

    @property
    def propellant_mass(self) -> np.ndarray:
        return self._propellant_mass

    @property
    def current_wet_mass(self) -> np.ndarray:
        return self._current_wet_mass

    def export_table_data(self) -> list[dict]:
        return [
            {
                'date': date,
                'instant_consumption': ic,
                'total_consumption': tc,
                'thrust_direction_azimuth': tda,
                'thrust_direction_elevation': tde,
                'propellant_mass': pm,
                'current_wet_mass': cwm,
            }
            for date, ic, tc, tda, tde, pm, cwm in zip(
                self.dates,
                self.instant_consumption,
                self.total_consumption,
                self.thrust_direction_azimuth,
                self.thrust_direction_elevation,
                self.propellant_mass,
                self.current_wet_mass
            )
        ]

    @classmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'PropulsionEphemeris':
        lines = obj_data['lines']
        dates = []
        instant_consumption = []
        total_consumption = []
        thrust_direction_azimuth = []
        thrust_direction_elevation = []
        propellant_mass = []
        current_wet_mass = []

        for line in lines:
            dates.append(get_datetime(line['date']))
            instant_consumption.append(line['instantConsumption'])
            total_consumption.append(line['totalConsumption'])
            thrust_direction_azimuth.append(line['thrustDirectionAlpha'])
            thrust_direction_elevation.append(line['thrustDirectionDelta'])
            propellant_mass.append(line['remainingPropellant'])
            current_wet_mass.append(line['currentMass'])

        return cls(
            dates=dates,
            instant_consumption=instant_consumption,
            total_consumption=total_consumption,
            thrust_direction_azimuth=thrust_direction_azimuth,
            thrust_direction_elevation=thrust_direction_elevation,
            propellant_mass=propellant_mass,
            current_wet_mass=current_wet_mass
        )


class EulerAnglesEphemeris(Ephemeris):
    def __init__(
            self,
            dates: Sequence[datetime],
            roll: Sequence[float],
            pitch: Sequence[float],
            yaw: Sequence[float],
            frame_1: str,
            frame_2: str,
    ):
        super().__init__(dates)
        self._roll = convert_to_numpy_array_and_check_shape(roll, (self._ref_lenght,))
        self._pitch = convert_to_numpy_array_and_check_shape(pitch, (self._ref_lenght,))
        self._yaw = convert_to_numpy_array_and_check_shape(yaw, (self._ref_lenght,))
        self._frame_1 = frame_1
        self._frame_2 = frame_2

    @property
    def roll(self) -> np.ndarray:
        return self._roll

    @property
    def pitch(self) -> np.ndarray:
        return self._pitch

    @property
    def yaw(self) -> np.ndarray:
        return self._yaw

    @property
    def frame_1(self) -> str:
        return self._frame_1

    @property
    def frame_2(self) -> str:
        return self._frame_2

    def export_table_data(self) -> list[dict]:
        return [
            {
                'date': date,
                'roll': r,
                'pitch': p,
                'yaw': y,
            }
            for date, r, p, y in zip(self.dates, self.roll, self.pitch, self.yaw)
        ]

    @classmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'EulerAnglesEphemeris':
        lines = obj_data['lines']
        dates = []
        roll = []
        pitch = []
        yaw = []

        for line in lines:
            dates.append(get_datetime(line['date']))
            roll.append(line['roll'])
            pitch.append(line['pitch'])
            yaw.append(line['yaw'])

        return cls(
            dates=dates,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            frame_1=Frame.ECI.value,
            frame_2=Frame.TNW.value
        )


class QuaternionEphemeris(Ephemeris):
    def __init__(
            self,
            dates: Sequence[datetime],
            quaternions: Sequence[Quaternion],
            frame_1: str,
            frame_2: str,
    ):
        super().__init__(dates)
        self._quaternions = quaternions
        self._frame_1 = frame_1
        self._frame_2 = frame_2

    @property
    def quaternions(self) -> Sequence[Quaternion]:
        return self._quaternions

    @property
    def frame_1(self) -> str:
        return self._frame_1

    @property
    def frame_2(self) -> str:
        return self._frame_2

    def export_table_data(self) -> list[dict]:
        return [
            {
                'date': date,
                'q_real': q.real,
                'q_i': q.i,
                'q_j': q.j,
                'q_k': q.k,
            }
            for date, q in zip(self.dates, self.quaternions)
        ]

    @classmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'QuaternionEphemeris':
        lines = obj_data['lines']
        dates = []
        quaternions = []
        for line in lines:
            dates.append(get_datetime(line['date']))
            quaternions.append(
                Quaternion(
                    real=line['q0'],
                    i=line['q1'],
                    j=line['q2'],
                    k=line['q3'],
                    date=dates[-1]
                )
            )
        return cls(
            dates=dates,
            quaternions=quaternions,
            frame_1=Frame.ECI.value,
            frame_2="Spacecraft Body Frame"
        )
