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
    """
    This class serves as the baseline for all ephemeris classes and regroups features common to all of them.
    """
    def __init__(self, dates: Sequence[datetime]):
        self._dates = dates

    @property
    def dates(self) -> Sequence[datetime]:
        """
        All the dates at which a line of the ephemeris have been computed.
        """
        return self._dates

    @property
    def _ref_length(self) -> int:
        return len(self._dates)

    @classmethod
    @abstractmethod
    def create_from_api_dict(cls, obj_data: dict) -> 'Ephemeris':
        """
        :meta private:
        """
        pass

    @abstractmethod
    def export_table_data(self) -> list[dict]:
        """
        :meta private:
        """
        pass


class PowerEphemeris(Ephemeris):
    """
    Ephemeris of the state of the battery.
    """
    def __init__(self, dates: Sequence[datetime], battery_charge: Sequence[float],
                 solar_array_collected_power: Sequence[float], thruster_power_consumption: Sequence[float],
                 thruster_warm_up_power_consumption: Sequence[float]):
        super().__init__(dates)
        self._battery_charge = convert_to_numpy_array_and_check_shape(
            battery_charge, (self._ref_length,))
        self._solar_array_collected_power = convert_to_numpy_array_and_check_shape(
            solar_array_collected_power,
            (self._ref_length,))
        self._thruster_power_consumption = convert_to_numpy_array_and_check_shape(
            thruster_power_consumption,
            (self._ref_length,))
        self._thruster_warm_up_power_consumption = convert_to_numpy_array_and_check_shape(
            thruster_warm_up_power_consumption, (self._ref_length,))

    @property
    def battery_charge(self) -> np.ndarray:
        """
        Array of all the computed states of the battery.
        """
        return self._battery_charge

    @property
    def solar_array_collected_power(self) -> np.ndarray:
        """
        Array of all the computed power collected by the solar arrays.
        """
        return self._solar_array_collected_power

    @property
    def thruster_power_consumption(self) -> np.ndarray:
        """
        Array of all the computed power consumed by the thruster.
        """
        return self._thruster_power_consumption

    @property
    def thruster_warm_up_power_consumption(self) -> np.ndarray:
        """
        Array of all the computed power consumed by the thruster warming up.
        """
        return self._thruster_warm_up_power_consumption

    def export_table_data(self) -> list[dict]:
        """
        Exports the ephemeris as a list of dicts, each of which representing a whole ephemeris line.
        """
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
        """
        :meta private:
        """
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
    """
    Ephemeris of the satellite position on orbit, expressed with keplerian parameters.
    """
    def __init__(
            self,
            dates: Sequence[datetime],
            orbits: Sequence[KeplerianOrbit],
    ):
        super().__init__(dates)
        self._orbits = orbits

    @property
    def orbits(self) -> Sequence[KeplerianOrbit]:
        """
        Array of all the computed keplerian orbits.
        """
        return self._orbits

    def export_table_data(self) -> list[dict]:
        """
        Exports the ephemeris as a list of dicts, each of which representing a whole ephemeris line.
        """
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
        """
        :meta private:
        """
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
    """
    Ephemeris of the satellite position on orbit, expressed with cartesian parameters.
    """
    def __init__(
            self,
            dates: Sequence[datetime],
            states: Sequence[CartesianState],
    ):
        super().__init__(dates)
        self._states = states

    @property
    def states(self) -> Sequence[CartesianState]:
        """
        Array of all the computed cartesian states of the satellite.
        """
        return self._states

    @property
    def frame(self) -> Frame:
        """
        The frame in which the cartesian positions and velocities are expressed in.
        """
        return self.states[0].frame

    def export_table_data(self) -> list[dict]:
        """
        Exports the ephemeris as a list of dicts, each of which representing a whole ephemeris line.
        """
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
        """
        :meta private:
        """
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
    """
    Ephemeris of the thrust parameters.
    """
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
            instant_consumption, (self._ref_length,))
        self._total_consumption = convert_to_numpy_array_and_check_shape(
            total_consumption, (self._ref_length,))

        thrust_direction_azimuth = [np.nan if tda == 'NaN' else tda for tda in thrust_direction_azimuth]
        thrust_direction_elevation = [np.nan if tde == 'NaN' else tde for tde in thrust_direction_elevation]

        self._thrust_direction_azimuth = convert_to_numpy_array_and_check_shape(
            thrust_direction_azimuth, (self._ref_length,))
        self._thrust_direction_elevation = convert_to_numpy_array_and_check_shape(
            thrust_direction_elevation,
            (self._ref_length,))
        self._propellant_mass = convert_to_numpy_array_and_check_shape(
            propellant_mass, (self._ref_length,))
        self._current_wet_mass = convert_to_numpy_array_and_check_shape(
            current_wet_mass, (self._ref_length,))

    @property
    def instant_consumption(self) -> np.ndarray:
        """
        Array of the instantaneous mass flow of the thruster at the date of the ephemeris line.
        """
        return self._instant_consumption

    @property
    def total_consumption(self) -> np.ndarray:
        """
        Array of the total propellant mass consumed by the thruster at each instant of the ephemeris.
        """
        return self._total_consumption

    @property
    def thrust_direction_azimuth(self) -> np.ndarray:
        """
        Array of the azimuth angle of the propulsion axis, expressed in the satellite frame, at each computed date of
        the ephemeris.
        """
        return self._thrust_direction_azimuth

    @property
    def thrust_direction_elevation(self) -> np.ndarray:
        """
        Array of the elevation angle of the propulsion axis, expressed in the satellite frame, at each computed date of
        the ephemeris.
        """
        return self._thrust_direction_elevation

    @property
    def propellant_mass(self) -> np.ndarray:
        """
        Array of the mass of propellant left in the tanks at each computed date of the ephemeris.
        """
        return self._propellant_mass

    @property
    def current_wet_mass(self) -> np.ndarray:
        """
        Array of the total mass of the satellite at each computed date of the ephemeris.
        """
        return self._current_wet_mass

    def export_table_data(self) -> list[dict]:
        """
        Exports the ephemeris as a list of dicts, each of which representing a whole ephemeris line.
        """
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
        """
        :meta private:
        """
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
    """
    Ephemeris of the attitude of the satellite expressed with Euler angles.
    """
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
        self._roll = convert_to_numpy_array_and_check_shape(roll, (self._ref_length,))
        self._pitch = convert_to_numpy_array_and_check_shape(pitch, (self._ref_length,))
        self._yaw = convert_to_numpy_array_and_check_shape(yaw, (self._ref_length,))
        self._frame_1 = frame_1
        self._frame_2 = frame_2

    @property
    def roll(self) -> np.ndarray:
        """
        Array of the roll angle values computed during the orbit extrapolation.
        """
        return self._roll

    @property
    def pitch(self) -> np.ndarray:
        """
        Array of the pitch angle values computed during the orbit extrapolation.
        """
        return self._pitch

    @property
    def yaw(self) -> np.ndarray:
        """
        Array of the yaw angle values computed during the orbit extrapolation.
        """
        return self._yaw

    @property
    def frame_1(self) -> str:
        """
        The name of the reference frame from which the attitude of the satellite is computed.
        """
        return self._frame_1

    @property
    def frame_2(self) -> str:
        """
        The name of the frame of the satellite.
        """
        return self._frame_2

    def export_table_data(self) -> list[dict]:
        """
        Exports the ephemeris as a list of dicts, each of which representing a whole ephemeris line.
        """
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
        """
        :meta private:
        """
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
    """
    Ephemeris of the attitude of the satellite expressed with quaternion.
    """
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
        """
        Sequence of the quaternions describing the attitude of the satellite at each date of the computation.
        """
        return self._quaternions

    @property
    def frame_1(self) -> str:
        """
        The name of the reference frame from which the attitude of the satellite is computed.
        """
        return self._frame_1

    @property
    def frame_2(self) -> str:
        """
        The name of the frame of the satellite.
        """
        return self._frame_2

    def export_table_data(self) -> list[dict]:
        """
        Exports the ephemeris as a list of dicts, each of which representing a whole ephemeris line.
        """
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
        """
        :meta private:
        """
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
