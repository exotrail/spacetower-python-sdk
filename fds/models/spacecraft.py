from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from typing_extensions import Self

from fds.client import FdsClient
from fds.models._model import ModelSource, RetrievableModel, FromConfigBaseModel
from fds.utils import geometry as geom
from fds.utils.enum import EnumFromInput
from fds.utils.log import log_and_raise
from fds.utils.orbital_mechanics import compute_delta_v_with_rocket_equation


class Battery(FromConfigBaseModel, RetrievableModel):
    FDS_TYPE = FdsClient.Models.BATTERY

    def __init__(
            self,
            depth_of_discharge: float,
            nominal_capacity: float,
            minimum_charge_for_firing: float,
            initial_charge: float,
            nametag: str = None
    ):
        """
        Args:
            depth_of_discharge (float): (Unit: %, 0<x<1)
            nominal_capacity (float): (Unit: W)
            minimum_charge_for_firing (float): (Unit: %, 0<x<1)
            initial_charge (float): (Unit: %, 0<x<1)
            nametag (str, optional): Defaults to None.

        """
        super().__init__(nametag)

        self._depth_of_discharge = depth_of_discharge
        self._nominal_capacity = nominal_capacity
        self._minimum_charge_for_firing = minimum_charge_for_firing
        self._initial_charge = initial_charge

    @property
    def depth_of_discharge(self) -> float:
        return self._depth_of_discharge

    @property
    def nominal_capacity(self) -> float:
        return self._nominal_capacity

    @property
    def minimum_charge_for_firing(self) -> float:
        return self._minimum_charge_for_firing

    @property
    def initial_charge(self) -> float:
        return self._initial_charge

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {'depth_of_discharge': obj_data['depthOfDischarge'],
                'initial_charge': obj_data['initialCharge'],
                'nominal_capacity': obj_data['nominalCapacity'],
                'minimum_charge_for_firing': obj_data['minimumChargeForFiring']}

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update({
            'depthOfDischarge': self.depth_of_discharge,
            'initialCharge': self.initial_charge,
            'nominalCapacity': self.nominal_capacity,
            'minimumChargeForFiring': self.minimum_charge_for_firing
        })
        return d


class SolarArray(FromConfigBaseModel, RetrievableModel):
    FDS_TYPE = FdsClient.Models.SOLAR_ARRAY

    class Kind(EnumFromInput):
        BODY = "BODY"
        DEPLOYABLE_FIXED = "DEPLOYABLE_FIXED"
        DEPLOYABLE_ROTATING = "DEPLOYABLE_ROTATING"
        NONE = "NONE"

    class InitialisationKind(EnumFromInput):
        MAXIMUM_POWER = "MAXIMUM_POWER"
        SURFACE = "SURFACE"
        SURFACE_AND_POWER = "SURFACE_AND_POWER"

    class SatelliteFace(EnumFromInput):
        PLUS_X = "PLUS_X"
        MINUS_X = "MINUS_X"
        PLUS_Y = "PLUS_Y"
        MINUS_Y = "MINUS_Y"
        PLUS_Z = "PLUS_Z"
        MINUS_Z = "MINUS_Z"

    def __init__(
            self, kind: str | Kind,
            initialisation_kind: InitialisationKind | str,
            efficiency: float,
            normal_in_satellite_frame: tuple[float, float, float],
            maximum_power: float = None,
            surface: float = None,
            axis_in_satellite_frame: tuple[float, float, float] = None,
            satellite_faces: Sequence[str | SatelliteFace] = None,
            nametag: str = None
    ):
        """
        Args:
            kind (str | Kind): Kind of solar array
            initialisation_kind (InitialisationKind | str): Initialisation kind
            efficiency (float): (Unit: %, 0<x<1)
            normal_in_satellite_frame (tuple): (Unit: unit vector)
            maximum_power (float, optional): (Unit: W). Defaults to None.
            surface (float, optional): (Unit: m^2). Defaults to None.
            axis_in_satellite_frame (tuple, optional): (Unit: unit vector). Defaults to None.
            satellite_faces (Sequence[str | SatelliteFace], optional): Satellite faces. Defaults to None.
            nametag (str, optional): Defaults to None.
        """
        super().__init__(nametag)
        self._kind = self.Kind.from_input(kind)
        self._initialisation_kind = self.InitialisationKind.from_input(initialisation_kind)
        self._efficiency = efficiency
        normal_in_satellite_frame = geom.convert_to_numpy_array_and_check_shape(normal_in_satellite_frame, (3,))
        self._normal_in_satellite_frame = normal_in_satellite_frame
        self._maximum_power = maximum_power
        if axis_in_satellite_frame is not None:
            axis_in_satellite_frame = geom.convert_to_numpy_array_and_check_shape(axis_in_satellite_frame, (3,))
        self._axis_in_satellite_frame = axis_in_satellite_frame
        self._surface = surface
        self._satellite_faces = [self.SatelliteFace.from_input(s) for s in
                                 satellite_faces] if satellite_faces is not None else satellite_faces

    @property
    def kind(self) -> Kind:
        return self._kind

    @property
    def initialisation_kind(self) -> InitialisationKind:
        return self._initialisation_kind

    @property
    def efficiency(self) -> float:
        return self._efficiency

    @property
    def normal_in_satellite_frame(self) -> np.ndarray:
        return self._normal_in_satellite_frame

    @property
    def maximum_power(self) -> float:
        return self._maximum_power

    @property
    def axis_in_satellite_frame(self) -> np.ndarray:
        return self._axis_in_satellite_frame

    @property
    def surface(self) -> float:
        return self._surface

    @property
    def satellite_faces(self) -> Sequence[SatelliteFace]:
        return self._satellite_faces

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {'kind': obj_data['solarArrayType'][17:],
                'initialisation_kind': obj_data['solarArrayDefinitionType'],
                'efficiency': obj_data['solarArrayEfficiency'],
                'normal_in_satellite_frame': obj_data['solarArrayNormalInSatelliteFrame'],
                'axis_in_satellite_frame': obj_data.get('solarArrayAxisInSatelliteFrame'),
                'satellite_faces': obj_data.get('satelliteFaces'),
                'maximum_power': obj_data.get('maximumPower'),
                'surface': obj_data.get('surface')}

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        axis_in_sat_frame = self.axis_in_satellite_frame.tolist() \
            if self.axis_in_satellite_frame is not None else None
        normal_in_sat_frame = self.normal_in_satellite_frame.tolist() \
            if self.normal_in_satellite_frame is not None else None
        d.update({'solar_array_type': 'SOLAR_ARRAY_TYPE_' + self.kind.value,
                  'solar_array_definition_type': self.initialisation_kind.value,
                  'solar_array_efficiency': self.efficiency,
                  'maximum_power': self.maximum_power,
                  'surface': self.surface,
                  'solar_array_axis_in_satellite_frame': axis_in_sat_frame,
                  'solar_array_normal_in_satellite_frame': normal_in_sat_frame,
                  'satellite_faces':
                      [s.value for s in self.satellite_faces]
                      if self.satellite_faces is not None else
                      self.satellite_faces})
        return d


class Thruster(FromConfigBaseModel, RetrievableModel, ABC):
    FDS_TYPE = FdsClient.Models.THRUSTER

    @abstractmethod
    def __init__(
            self,
            impulse: float,
            maximum_thrust_duration: float,
            propellant_mass: float,
            thrust: float,
            axis_in_satellite_frame: tuple[float, float, float],
            isp: float,
            wet_mass: float,
            warm_up_duration: float,
            nametag: str = None
    ):
        super().__init__(nametag)

        self._impulse = impulse
        self._maximum_thrust_duration = maximum_thrust_duration
        self._propellant_mass = propellant_mass
        self._thrust = thrust
        self._axis_in_satellite_frame = geom.convert_to_numpy_array_and_check_shape(axis_in_satellite_frame, (3,))
        self._isp = isp
        self._warm_up_duration = warm_up_duration
        self._wet_mass = wet_mass

    @property
    def impulse(self) -> float:
        return self._impulse

    @property
    def maximum_thrust_duration(self) -> float:
        return self._maximum_thrust_duration

    @property
    def propellant_mass(self) -> float:
        return self._propellant_mass

    @property
    def thrust(self) -> float:
        return self._thrust

    @thrust.setter
    def thrust(self, value: float):
        self._thrust = value
        self._client_id = None

    @property
    def axis_in_satellite_frame(self) -> np.ndarray:
        return self._axis_in_satellite_frame

    @property
    def isp(self) -> float:
        return self._isp

    @property
    def dry_mass(self) -> float:
        return self.wet_mass - self.propellant_mass

    @property
    def wet_mass(self) -> float:
        return self._wet_mass

    @property
    def warm_up_duration(self) -> float:
        return self._warm_up_duration

    @classmethod
    def retrieve_generic_by_id(cls, client_id: str, nametag: str = None):
        obj_data = FdsClient.get_client().retrieve_model(cls.FDS_TYPE, client_id)
        if not isinstance(obj_data, dict):
            obj_data = obj_data.to_dict()
        if 'thrusterPower' in obj_data:
            obj_type = ThrusterElectrical
        else:
            obj_type = ThrusterChemical
        new_obj = obj_type(**obj_type.api_retrieve_map(obj_data), nametag=nametag)
        new_obj._client_id = client_id
        new_obj._model_source = ModelSource.CLIENT
        new_obj._client_retrieved_object_data.update(obj_data)
        return new_obj

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'impulse': obj_data['impulse'],
            'maximum_thrust_duration': obj_data['maximumThrustDuration'],
            'propellant_mass': obj_data['propellantMass'],
            'thrust': obj_data['thrust'],
            'axis_in_satellite_frame': obj_data['thrusterAxisInSatelliteFrame'],
            'isp': obj_data['thrusterIsp'],
            'wet_mass': obj_data['thrusterTotalMass'],
            'warm_up_duration': obj_data['warmUpDuration']
        }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update({'impulse': self.impulse,
                  'maximumThrustDuration': self.maximum_thrust_duration,
                  'propellantMass': self.propellant_mass, 'thrust': self.thrust,
                  'thrusterAxisInSatelliteFrame': self.axis_in_satellite_frame.tolist(),
                  'thrusterIsp': self.isp,
                  'thrusterTotalMass': self.wet_mass,
                  'warmUpDuration': self.warm_up_duration})
        return d


class ThrusterElectrical(Thruster):
    FDS_TYPE = FdsClient.Models.THRUSTER_ELECTRICAL

    def __init__(
            self,
            impulse: float,
            maximum_thrust_duration: float,
            propellant_mass: float,
            thrust: float,
            axis_in_satellite_frame: tuple[float, float, float],
            isp: float,
            wet_mass: float,
            warm_up_duration: float,
            power: float,
            stand_by_power: float,
            warm_up_power: float,
            nametag: str = None
    ):
        """
        Args:
            impulse (float): (Unit: Ns)
            maximum_thrust_duration (float): (Unit: s)
            propellant_mass (float): (Unit: kg)
            thrust (float): (Unit: N)
            axis_in_satellite_frame (tuple): (Unit: unit vector)
            isp (float): (Unit: s)
            wet_mass (float): (Unit: kg)
            warm_up_duration (float): (Unit: s)
            power (float): (Unit: W)
            stand_by_power (float): (Unit: W)
            warm_up_power (float): (Unit: W)
            nametag (str, optional): Defaults to None.
        """
        super().__init__(impulse, maximum_thrust_duration, propellant_mass, thrust, axis_in_satellite_frame, isp,
                         wet_mass, warm_up_duration, nametag)

        self._power = power
        self._stand_by_power = stand_by_power
        self._warm_up_power = warm_up_power

    @property
    def power(self) -> float:
        return self._power

    @power.setter
    def power(self, value: float):
        self._power = value
        self._client_id = None

    @property
    def stand_by_power(self) -> float:
        return self._stand_by_power

    @stand_by_power.setter
    def stand_by_power(self, value: float):
        self._stand_by_power = value
        self._client_id = None

    @property
    def warm_up_power(self) -> float:
        return self._warm_up_power

    @warm_up_power.setter
    def warm_up_power(self, value: float):
        self._warm_up_power = value
        self._client_id = None

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'stand_by_power': obj_data['standByPower'],
                'power': obj_data['thrusterPower'],
                'warm_up_power': obj_data['warmUpPower']
            }
        )
        return d

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'thrusterPower': self.power,
                'standByPower': self.stand_by_power,
                'warmUpPower': self.warm_up_power
            }
        )
        return d


class ThrusterChemical(Thruster):
    FDS_TYPE = FdsClient.Models.THRUSTER_CHEMICAL

    def __init__(
            self,
            impulse: float,
            maximum_thrust_duration: float,
            propellant_mass: float,
            thrust: float,
            axis_in_satellite_frame: tuple[float, float, float],
            isp: float,
            wet_mass: float,
            warm_up_duration: float,
            nametag: str = None
    ):
        """
        Args:
            impulse (float): (Unit: Ns)
            maximum_thrust_duration (float): (Unit: s)
            propellant_mass (float): (Unit: kg)
            thrust (float): (Unit: N)
            axis_in_satellite_frame (tuple): (Unit: unit vector)
            isp (float): (Unit: s)
            wet_mass (float): (Unit: kg)
            warm_up_duration (float): (Unit: s)
            nametag (str, optional): Defaults to None.
        """
        super().__init__(impulse, maximum_thrust_duration, propellant_mass, thrust, axis_in_satellite_frame, isp,
                         wet_mass, warm_up_duration, nametag)


class Spacecraft(RetrievableModel, ABC):
    FDS_TYPE = FdsClient.Models.SPACECRAFT

    @abstractmethod
    def __init__(
            self,
            platform_mass: float,
            drag_coefficient: float,
            reflectivity_coefficient: float,
            nametag: str = None
    ):
        super().__init__(nametag)

        self._platform_mass = platform_mass
        self._drag_coefficient = drag_coefficient
        self._reflectivity_coefficient = reflectivity_coefficient

    @property
    def platform_mass(self) -> float:
        return self._platform_mass

    @property
    def drag_coefficient(self) -> float:
        return self._drag_coefficient

    @property
    def reflectivity_coefficient(self) -> float:
        return self._reflectivity_coefficient

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {'platform_mass': obj_data['platformMass'],
                'drag_coefficient': obj_data['dragCoefficient'],
                'reflectivity_coefficient': obj_data['reflectionCoefficient']}

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'platformMass': self.platform_mass,
                'dragCoefficient': self.drag_coefficient,
                'reflectionCoefficient': self.reflectivity_coefficient
            }
        )
        return d

    @classmethod
    def retrieve_generic_by_id(cls, client_id: str, nametag: str = None):
        obj_data = FdsClient.get_client().retrieve_model(cls.FDS_TYPE, client_id)
        if not isinstance(obj_data, dict):
            obj_data = obj_data.to_dict()
        if 'spacecraftLengthX' in obj_data:
            obj_type = SpacecraftBox
        else:
            obj_type = SpacecraftSphere
        new_obj = obj_type(**obj_type.api_retrieve_map(obj_data), nametag=nametag)
        new_obj._client_id = client_id
        new_obj._model_source = ModelSource.CLIENT
        new_obj._client_retrieved_object_data.update(obj_data)
        return new_obj


class SpacecraftBox(Spacecraft, FromConfigBaseModel):
    FDS_TYPE = FdsClient.Models.SPACECRAFT_BOX
    _PROPULSION_KINDS = {ThrusterElectrical.FDS_TYPE: ThrusterElectrical,
                         ThrusterChemical.FDS_TYPE: ThrusterChemical}

    @dataclass
    class LengthContainer:
        x: float
        y: float
        z: float

    def __init__(
            self,
            battery: Battery,
            thruster: ThrusterElectrical | ThrusterChemical,
            solar_array: SolarArray,
            platform_mass: float,
            drag_coefficient: float,
            max_angular_acceleration: float,
            max_angular_velocity: float,
            length_x: float,
            length_y: float,
            length_z: float,
            reflectivity_coefficient: float = None,
            nametag: str = None
    ):
        """
        Args:
            battery (Battery): Battery object
            thruster (ThrusterElectrical | ThrusterChemical): Thruster object
            solar_array (SolarArray): SolarArray object
            platform_mass (float): Total mass of the spacecraft (wet mass) (Unit: kg).
            drag_coefficient (float): Drag coefficient (adimensional)
            max_angular_acceleration (float): (Unit: deg/s²)
            max_angular_velocity (float): (Unit: deg/s)
            length_x (float): (Unit: m)
            length_y (float): (Unit: m)
            length_z (float): (Unit: m)
            reflectivity_coefficient (float, optional): Reflection coefficient (adimensional)
            nametag (str, optional): Defaults to None.
        """
        super().__init__(platform_mass, drag_coefficient, reflectivity_coefficient, nametag)

        # If elements are not in the server, they are saved before using them (always with random client_id)
        self._battery = battery
        self._thruster = thruster
        self._solar_array = solar_array

        self._max_angular_acceleration = max_angular_acceleration
        self._max_angular_velocity = max_angular_velocity
        self._length = self.LengthContainer(length_x, length_y, length_z)

    @property
    def battery(self) -> Battery:
        return self._battery

    @property
    def thruster(self) -> ThrusterElectrical | ThrusterChemical:
        return self._thruster

    @property
    def solar_array(self) -> SolarArray:
        return self._solar_array

    @property
    def length(self) -> LengthContainer:
        return self._length

    @property
    def propulsion_kind(self) -> str:
        return self.thruster.FDS_TYPE[9:]

    @property
    def max_angular_velocity(self) -> float:
        return self._max_angular_velocity

    @property
    def max_angular_acceleration(self) -> float:
        return self._max_angular_acceleration

    @property
    def propellant_mass(self) -> float:
        return self.thruster.propellant_mass

    @propellant_mass.setter
    def propellant_mass(self, value: float):
        if value < 0:
            msg = f'Propellant mass cannot be negative. Received: {value}'
            log_and_raise(ValueError, msg)
        previous_thruster_wet_mass = self.thruster.wet_mass
        previous_propellant_mass = self.thruster.propellant_mass

        self.thruster._propellant_mass = value
        self.thruster._wet_mass = previous_thruster_wet_mass - value
        self.thruster._client_id = None

        previous_platform_mass = self.platform_mass
        self._platform_mass = previous_platform_mass - (previous_propellant_mass - value)
        self._client_id = None

    @property
    def dry_mass(self) -> float:
        return self.platform_mass - self.propellant_mass

    def destroy(self, destroy_subcomponents: bool = False):
        super().destroy()
        if destroy_subcomponents:
            self.battery.destroy()
            self.thruster.destroy()
            self.solar_array.destroy()

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'max_angular_acceleration': obj_data['maxAngularAcceleration'],
                'max_angular_velocity': obj_data['maxAngularAcceleration'],
                'length_x': obj_data['spacecraftLengthX'],
                'length_y': obj_data['spacecraftLengthY'],
                'length_z': obj_data['spacecraftLengthZ'],
                'battery': Battery.retrieve_by_id(obj_data['battery']['id']),
                'solar_array': SolarArray.retrieve_by_id(obj_data['solarArray']['id']),
                'thruster': Thruster.retrieve_generic_by_id(obj_data['thruster']['id'])
            })
        return d

    def api_create_map(self, force_save: bool = False) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'max_angular_acceleration': self.max_angular_acceleration,
                'max_angular_velocity': self.max_angular_velocity,
                'spacecraft_length_x': self.length.x,
                'spacecraft_length_y': self.length.y,
                'spacecraft_length_z': self.length.z,
                'battery_id': self.battery.save(force_save).client_id,
                'thruster_id': self.thruster.save(force_save).client_id,
                'solar_array_id': self.solar_array.save(force_save).client_id,
            }
        )
        return d

    @classmethod
    def import_from_config_file(cls, config_filepath: str | Path, battery: Battery = None,
                                solar_array: SolarArray = None,
                                thruster: ThrusterElectrical | ThrusterChemical = None) -> Self:
        config_dict = cls._get_config_dict_from_file(config_filepath)
        if battery is None:
            battery = Battery.import_from_config_dict(config_dict)
        if solar_array is None:
            solar_array = SolarArray.import_from_config_dict(config_dict)
        if thruster is None:
            if ThrusterChemical.FDS_TYPE in config_dict:
                thruster = ThrusterChemical.import_from_config_dict(config_dict)
            elif ThrusterElectrical.FDS_TYPE in config_dict:
                thruster = ThrusterElectrical.import_from_config_dict(config_dict)
            else:
                msg = (f'Neither a {ThrusterChemical.FDS_TYPE} nor a {ThrusterElectrical.FDS_TYPE} are in the config'
                       f' file.')
                log_and_raise(ValueError, msg)
        return super().import_from_config_file(config_filepath, battery=battery, solar_array=solar_array,
                                               thruster=thruster)

    def compute_maneuver_delta_v(self, initial_mass: float, final_mass: float) -> float:
        return compute_delta_v_with_rocket_equation(self.thruster.isp, initial_mass, final_mass)


class SpacecraftSphere(Spacecraft, FromConfigBaseModel):
    FDS_TYPE = FdsClient.Models.SPACECRAFT_SPHERE

    def __init__(
            self,
            platform_mass: float,
            cross_section: float,
            drag_coefficient: float,
            reflectivity_coefficient: float,
            nametag: str = None
    ):
        """
        Args:
            platform_mass (float): Mass (Unit: kg).
            cross_section (float): (Unit: m²).
            drag_coefficient (float): Drag coefficient (adimensional)
            reflectivity_coefficient (float): Reflection coefficient (adimensional)
            nametag (str, optional): Defaults to None.

        """

        super().__init__(platform_mass, drag_coefficient, reflectivity_coefficient, nametag)

        # Add attributes
        self._cross_section = cross_section

    @property
    def cross_section(self) -> float:
        return self._cross_section

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        d = super().api_retrieve_map(obj_data)
        d.update(
            {
                'cross_section': obj_data['sphericalCrossSection']
            }
        )
        return d

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'sphericalCrossSection': self.cross_section
            }
        )
        return d
