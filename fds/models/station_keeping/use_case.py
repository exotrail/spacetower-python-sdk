import leo_station_keeping as lsk
import numpy as np

from fds import config
from fds.models.orbital_state import PropagationContext, OrbitalState
from fds.models.orbits import Orbit, KeplerianOrbit
from fds.models.spacecraft import SpacecraftSphere, SpacecraftBox, SolarArray
from fds.models.station_keeping.requests import StationKeepingOutputRequest, EphemeridesRequest, \
    SpacecraftStatesRequest, ThrustEphemeridesRequest
from fds.models.station_keeping.result import ResultStationKeeping
from fds.models.station_keeping.strategy import StationKeepingStrategy
from fds.models.station_keeping.tolerance import Tolerance
from fds.utils.dates import datetime_to_iso_string
from fds.utils.log import log_and_raise


class LeoStationKeeping:
    ResultType = ResultStationKeeping

    def __init__(
            self,
            initial_orbit: KeplerianOrbit,
            propagation_context: PropagationContext,
            spacecraft: SpacecraftSphere | SpacecraftBox,
            maximum_duration: int,
            tolerance: Tolerance,
            output_requests: list[StationKeepingOutputRequest],
            simulate_attitude_and_power_system: bool = False,
            strategy: StationKeepingStrategy = None,
            drag_lift_ratio: float = 0.0,
            srp_absorption_coefficient: float = 1.0,
            average_available_on_board_power: float = 0.0,
            nametag: str = None
    ):
        """
        Args:
            initial_orbit (Orbit): The initial orbit of the spacecraft.
            propagation_context (PropagationContext): The propagation context.
            spacecraft (SpacecraftSphere | SpacecraftBox): The spacecraft object.
            maximum_duration (int): The maximum duration of the maneuver.
            tolerance (Tolerance): The tolerance object (SMA or ALONG_TRACK).
            output_requests (list[StationKeepingOutputRequest]): The list of output requests.
            simulate_attitude_and_power_system (bool): If True, the attitude and power system are simulated, and the
                average_available_on_board_power is only used to compute the duty cycle of the thruster. Defaults to
                False.
            strategy (StationKeepingStrategy): The strategy object. If None, the default strategy is used.
            drag_lift_ratio (float): The drag lift ratio. Defaults to 0.0.
            srp_absorption_coefficient (float): The SRP absorption coefficient. Defaults to 1.0.
            average_available_on_board_power (float): Unit: W. Average power available on board. If the attitude and
                power system are simulated, this value is used only to compute the duty cycle of the thruster. Defaults
                to 0.0.
            nametag (str): The name of the use case. Defaults to None.
        """
        self._initial_orbit = initial_orbit
        self._propagation_context = propagation_context
        self._spacecraft = spacecraft
        self._maximum_duration = maximum_duration
        self._tolerance = tolerance
        self._strategy = strategy
        self._drag_lift_ratio = drag_lift_ratio
        self._average_available_on_board_power = average_available_on_board_power
        self._srp_absorption_coefficient = srp_absorption_coefficient
        self._simulate_attitude_and_power_system = simulate_attitude_and_power_system
        self._output_requests = output_requests
        self._nametag = nametag
        self._response = None
        self._result = None

        # Check the input validity
        self._check_input_validity()

        # Get the microservice configuration
        self._api_url = config.get_station_keeping_api_url()
        self._microservice_configuration = lsk.Configuration(host=self._api_url)

        # Map the microservice request
        self._request = self._map_request()

    @property
    def initial_orbit(self) -> KeplerianOrbit:
        return self._initial_orbit

    @property
    def propagation_context(self) -> PropagationContext:
        return self._propagation_context

    @property
    def spacecraft(self) -> SpacecraftSphere | SpacecraftBox:
        return self._spacecraft

    @property
    def start_date(self):
        return self.initial_orbit.date

    @property
    def tolerance(self) -> Tolerance:
        return self._tolerance

    @property
    def maximum_duration(self) -> int:
        return self._maximum_duration

    @property
    def strategy(self) -> StationKeepingStrategy:
        return self._strategy

    @property
    def drag_lift_ratio(self) -> float:
        return self._drag_lift_ratio

    @property
    def average_available_on_board_power(self) -> float:
        return self._average_available_on_board_power

    @property
    def srp_absorption_coefficient(self) -> float:
        return self._srp_absorption_coefficient

    @property
    def output_requests(self) -> list[StationKeepingOutputRequest]:
        return self._output_requests

    @property
    def simulate_attitude_and_power_system(self) -> bool:
        return self._simulate_attitude_and_power_system

    @property
    def response(self) -> lsk.NumericalLeoStationKeepingResponse:
        return self._response

    @property
    def request(self) -> lsk.NumericalLeoStationKeepingRequest:
        return self._request

    @property
    def result(self) -> ResultStationKeeping:
        return self._result

    @property
    def microservice_configuration(self) -> lsk.Configuration:
        return self._microservice_configuration

    @property
    def nametag(self) -> str:
        return self._nametag

    @classmethod
    def from_initial_orbital_state(
            cls,
            initial_orbital_state: OrbitalState,
            maximum_duration: int,
            tolerance: Tolerance,
            output_requests: list[StationKeepingOutputRequest],
            simulate_attitude_and_power_system: bool = False,
            strategy: StationKeepingStrategy = None,
            drag_lift_ratio: float = 0.0,
            srp_absorption_coefficient: float = 1.0,
            average_available_on_board_power: float = 0.0,
            nametag: str = None
    ):
        """
        Args:
            initial_orbital_state (OrbitalState): The orbital state of the spacecraft.
            maximum_duration (int): The maximum duration of the maneuver.
            tolerance (Tolerance): The tolerance object (SMA or ALONG_TRACK).
            output_requests (list[StationKeepingOutputRequest]): The list of output requests.
            simulate_attitude_and_power_system (bool): If True, the attitude and power system are simulated, and the
                average_available_on_board_power is only used to compute the duty cycle of the thruster. Defaults to
                False.
            strategy (StationKeepingStrategy): The strategy object. If None, the default strategy is used.
            drag_lift_ratio (float): The drag lift ratio. Defaults to 0.0.
            srp_absorption_coefficient (float): The SRP absorption coefficient. Defaults to 1.0.
            average_available_on_board_power (float): Unit: W. Average power available on board. If the attitude and
                power system are simulated, this value is used only to compute the duty cycle of the thruster. Defaults
                to 0.0.
            nametag (str): The name of the use case. Defaults to None.
        """
        return cls(
            initial_orbit=initial_orbital_state.mean_orbit,
            propagation_context=initial_orbital_state.propagation_context,
            spacecraft=initial_orbital_state.spacecraft,
            maximum_duration=maximum_duration,
            tolerance=tolerance,
            output_requests=output_requests,
            simulate_attitude_and_power_system=simulate_attitude_and_power_system,
            strategy=strategy,
            drag_lift_ratio=drag_lift_ratio,
            srp_absorption_coefficient=srp_absorption_coefficient,
            average_available_on_board_power=average_available_on_board_power,
            nametag=nametag
        )

    def _check_input_validity(self):
        """This method checks every input to ensure they are valid."""
        if not isinstance(self.spacecraft, SpacecraftBox):
            msg = "The spacecraft must be of type Box."
            raise log_and_raise(ValueError, msg)
        elif (self.spacecraft.solar_array.initialisation_kind !=
              SolarArray.InitialisationKind.SURFACE):
            msg = "The solar panels must be defined with initialisation_kind equal to SURFACE."
            raise log_and_raise(ValueError, msg)

        if self.maximum_duration <= 0:
            msg = "The maximum duration must be greater than 0."
            raise log_and_raise(ValueError, msg)

        if self.drag_lift_ratio < 0:
            msg = "The drag lift ratio must be greater than or equal to 0."
            raise log_and_raise(ValueError, msg)

        if self.average_available_on_board_power < 0:
            msg = "The average on board power consumption must be greater than or equal to 0."
            raise log_and_raise(ValueError, msg)

        if self.srp_absorption_coefficient < 0:
            msg = "The SRP absorption coefficient must be greater than or equal to 0."
            raise log_and_raise(ValueError, msg)

        for output_request in self.output_requests:
            if isinstance(output_request, EphemeridesRequest):
                if EphemeridesRequest.EphemeridesType.POWER_SYSTEM in output_request.types:
                    if not self.simulate_attitude_and_power_system:
                        msg = ("The attitude and power system must be simulated if the power system epherides are "
                               "requested.")
                        raise log_and_raise(ValueError, msg)
            elif isinstance(output_request, ThrustEphemeridesRequest):
                msg = "Thrust ephemerides are not supported yet."
                raise log_and_raise(NotImplementedError, msg)

    def _map_request(self):
        # Map orbit
        orbit = self._map_orbit()

        # Map platform
        platform = self._map_platform()

        # Map spacecraft geometry
        spacecraft_geometry = self._map_spacecraft_geometry()

        # Map propulsion system
        propulsion_system = self._map_propulsion_system()

        # Map battery
        battery = None
        if self.simulate_attitude_and_power_system:
            battery = self._map_battery()

        # Map perturbations
        perturbations = self._map_perturbations()

        # Map tolerance
        tolerance = self.tolerance.to_microservice_format()

        # Map strategy
        strategy = None
        if self.strategy is not None:
            strategy = self.strategy.to_microservice_format()

        inputs = lsk.NumericalLeoStationKeepingRequestInputs(
            maximum_duration=self.maximum_duration,
            initial_orbit=orbit,
            propulsion_system=propulsion_system,
            platform=platform,
            spacecraft_geometry=spacecraft_geometry,
            tolerance=tolerance,
            perturbations=perturbations,
            target_date_definition_type="DURATION",
            custom_maneuvering_strategy=strategy,
            battery=battery
        )

        # Outputs
        output_requests = self._map_output_requests()

        return lsk.NumericalLeoStationKeepingRequest(
            inputs=inputs,
            outputs=output_requests
        )

    def _map_orbit(self) -> lsk.Orbit:
        orbit = lsk.Orbit()
        orbit.inclination = np.radians(self.initial_orbit.orbital_elements.INC)
        orbit.sma = self.initial_orbit.orbital_elements.SMA * 1e3
        orbit.eccentricity = self.initial_orbit.orbital_elements.ECC
        orbit.parameters = lsk.EllipticalSmaEccentricityOrbitParameters()
        orbit.parameters.parameters_type = "ELLIPTICAL_SMA_ECC"

        orbit.advanced_parameters = lsk.AdvancedOrbitParameters()
        orbit.advanced_parameters.orbital_element_type = self.initial_orbit.kind.value
        orbit.advanced_parameters.orbit_date = datetime_to_iso_string(self.start_date)
        orbit.advanced_parameters.ascending_node_type = "RAAN"
        orbit.advanced_parameters.raan = np.radians(self.initial_orbit.orbital_elements.RAAN)
        orbit.advanced_parameters.anomaly_type = self.initial_orbit.anomaly_kind.value
        orbit.advanced_parameters.anomaly = np.radians(self.initial_orbit.orbital_elements.TA)
        orbit.advanced_parameters.perigee_argument = np.radians(self.initial_orbit.orbital_elements.AOP)
        return orbit

    def _map_platform(self) -> lsk.Platform:
        platform = lsk.Platform()
        platform.mass = self.spacecraft.platform_mass
        platform.on_board_average_power = self.average_available_on_board_power
        return platform

    def _map_spacecraft_geometry(self) -> lsk.BoxSpacecraftGeometry:
        solar_array = self._map_solar_array()

        spacecraft_geometry = lsk.BoxSpacecraftGeometry()
        spacecraft_geometry.dimensions = lsk.SpacecraftGeometryDimension(
            x=self.spacecraft.length.x,
            y=self.spacecraft.length.y,
            z=self.spacecraft.length.z
        )
        spacecraft_geometry.thruster_axis = lsk.Axis(
            x=self.spacecraft.thruster.axis_in_satellite_frame[0],
            y=self.spacecraft.thruster.axis_in_satellite_frame[1],
            z=self.spacecraft.thruster.axis_in_satellite_frame[2]
        )
        spacecraft_geometry.solar_array = solar_array
        spacecraft_geometry.type = "BOX"
        return spacecraft_geometry

    def _map_solar_array(self) -> lsk.SolarArray:
        def _map_solar_array_body(sc: SpacecraftBox) -> lsk.BodySolarArray:
            faces = None
            if sc.solar_array.satellite_faces is not None:
                faces = [lsk.SolarArrayFace(f.value) for f in sc.solar_array.satellite_faces]
            return lsk.BodySolarArray(faces=faces, type=sc.solar_array.kind.value,
                                      efficiency=sc.solar_array.efficiency)

        def _map_solar_array_deployable_fixed(sc: SpacecraftBox) -> lsk.DeployableFixedSolarArray:
            return lsk.DeployableFixedSolarArray(
                normal_direction=lsk.Axis(x=sc.solar_array.normal_in_satellite_frame[0],
                                          y=sc.solar_array.normal_in_satellite_frame[1],
                                          z=sc.solar_array.normal_in_satellite_frame[2]),
                surface=sc.solar_array.surface,
                type=sc.solar_array.kind.value,
                efficiency=sc.solar_array.efficiency
            )

        def _map_solar_array_deployable_rotating(sc: SpacecraftBox) -> lsk.DeployableRotatingSolarArray:
            return lsk.DeployableRotatingSolarArray(
                rotation_axis=lsk.Axis(x=sc.solar_array.axis_in_satellite_frame[0],
                                       y=sc.solar_array.axis_in_satellite_frame[1],
                                       z=sc.solar_array.axis_in_satellite_frame[2]),
                surface=sc.solar_array.surface,
                type=sc.solar_array.kind.value,
                efficiency=sc.solar_array.efficiency
            )

        match self.spacecraft.solar_array.kind:
            case self.spacecraft.solar_array.Kind.BODY:
                return _map_solar_array_body(self.spacecraft)
            case self.spacecraft.solar_array.Kind.DEPLOYABLE_FIXED:
                return _map_solar_array_deployable_fixed(self.spacecraft)
            case self.spacecraft.solar_array.Kind.DEPLOYABLE_ROTATING:
                return _map_solar_array_deployable_rotating(self.spacecraft)

    def _map_propulsion_system(self) -> lsk.PropulsionSystem:
        propulsion_system = lsk.PropulsionSystem()
        propulsion_system.type = self.spacecraft.propulsion_kind
        propulsion_system.isp = self.spacecraft.thruster.isp
        propulsion_system.power = self.spacecraft.thruster.power
        propulsion_system.thrust = self.spacecraft.thruster.thrust
        propulsion_system.standby_power = self.spacecraft.thruster.stand_by_power
        propulsion_system.warm_up_power = self.spacecraft.thruster.warm_up_power
        propulsion_system.warm_up_duration = self.spacecraft.thruster.warm_up_duration
        propulsion_system.propellant_mass = self.spacecraft.thruster.propellant_mass
        propulsion_system.total_mass = self.spacecraft.thruster.wet_mass
        propulsion_system.total_impulse = self.spacecraft.thruster.impulse
        propulsion_system.maximum_thrust_duration = self.spacecraft.thruster.maximum_thrust_duration
        propulsion_system.consumption = None
        propulsion_system.propellant_capacity_choice = "PROPELLANT"
        return propulsion_system

    def _map_battery(self) -> lsk.Battery:
        battery = lsk.Battery()
        battery.nominal_capacity = self.spacecraft.battery.nominal_capacity
        battery.depth_of_discharge = self.spacecraft.battery.depth_of_discharge
        battery.minimum_charge_for_firing = self.spacecraft.battery.minimum_charge_for_firing
        battery.initial_charge = self.spacecraft.battery.initial_charge
        return battery

    def _map_perturbations(self) -> list[lsk.Perturbation]:
        model = self.propagation_context.model

        perturbations = []
        for pert in model.perturbations:
            match pert:
                case PropagationContext.Perturbation.DRAG:
                    perturbations.append(
                        lsk.DragPerturbation(
                            type=pert.value,
                            drag_coefficient=self.spacecraft.drag_coefficient,
                            lift_ratio=self.drag_lift_ratio,
                            atmospheric_model=self._get_atmospheric_model(model)
                        ))
                case PropagationContext.Perturbation.SRP:
                    perturbations.append(
                        lsk.SrpPerturbation(
                            type=pert.value,
                            absorption_coefficient=self.srp_absorption_coefficient,
                            reflection_coefficient=self.spacecraft.reflectivity_coefficient,
                        ))
                case PropagationContext.Perturbation.EARTH_POTENTIAL:
                    perturbations.append(lsk.EarthPotentialPerturbation(
                        type=pert.value,
                        custom_earth_potential_configuration=self._get_earth_potential_configuration(model)
                    ))
                case PropagationContext.Perturbation.THIRD_BODY:
                    perturbations.append(lsk.ThirdBodyPerturbation(
                        type=pert.value,
                    ))
        return perturbations if len(perturbations) > 0 else None

    @staticmethod
    def _get_atmospheric_model(model) -> lsk.AtmosphericModel:
        match model.atmosphere_kind:
            case PropagationContext.AtmosphereModel.HARRIS_PRIESTER:
                atmospheric_model = lsk.HarrisPriesterAtmosphericModel(
                    type=PropagationContext.AtmosphereModel.HARRIS_PRIESTER.value,
                    custom_solar_flux=model.solar_flux
                )
            case PropagationContext.AtmosphereModel.NRL_MSISE00:
                atmospheric_model = lsk.NRLMSISE00AtmosphericModel(
                    type=PropagationContext.AtmosphereModel.NRL_MSISE00.value.replace("_", ""),
                )
            case _:
                raise ValueError("Atmosphere model not recognized.")
        return atmospheric_model

    @staticmethod
    def _get_earth_potential_configuration(model) -> lsk.CustomEarthPotentialConfiguration:
        return lsk.CustomEarthPotentialConfiguration(
            degree=model.earth_potential_deg,
            order=model.earth_potential_ord
        )

    def _map_output_requests(self) -> lsk.NumericalLeoStationKeepingRequestOutputs:
        requests = {}
        for output_request in self.output_requests:
            if isinstance(output_request, EphemeridesRequest):
                requests["orbital_ephemerides"] = output_request.to_microservice_format()
            elif isinstance(output_request, SpacecraftStatesRequest):
                requests["spacecraft_states"] = output_request.to_microservice_format()
            elif isinstance(output_request, ThrustEphemeridesRequest):
                requests["thrust_ephemerides"] = output_request.to_microservice_format()
            else:
                raise ValueError("Output request not recognized.")
        return lsk.NumericalLeoStationKeepingRequestOutputs(**requests)

    def run(self) -> 'LeoStationKeeping':
        with lsk.ApiClient(self.microservice_configuration) as api_client:
            api = lsk.api.DefaultApi(api_client)
            response = api.compute_numerical_leo_station_keeping(self.request)
            if len(response.errors) > 0:
                msg = f"Computation terminated with errors : {response.errors[0]}"
                log_and_raise(ValueError, msg)

        # Map the response to the Result object
        self._response = response
        self._result = self.ResultType.from_microservice_response(self.response, self.initial_orbit.date)
        return self
