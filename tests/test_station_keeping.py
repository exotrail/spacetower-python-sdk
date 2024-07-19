import datetime
import unittest

import numpy as np
from leo_station_keeping import SpacecraftGeometry, \
    NumericalLeoStationKeepingResponse

from fds.config import get_station_keeping_api_url
from fds.models.actions import ActionFiring
from fds.models.orbital_state import PropagationContext
from fds.models.orbits import KeplerianOrbit, OrbitMeanOsculatingType, PositionAngleType
from fds.models.quaternion import Quaternion, get_univoque_list_of_dated_quaternions
from fds.models.spacecraft import SpacecraftBox, SolarArray, SpacecraftSphere
from fds.models.station_keeping.requests import EphemeridesRequest, SpacecraftStatesRequest, ThrustEphemeridesRequest
from fds.models.station_keeping.result import ResultStationKeeping, get_ephemerides_data, \
    select_ephemerides_data_with_specific_prefix
from fds.models.station_keeping.strategy import StationKeepingStrategy
from fds.models.station_keeping.tolerance import SemiMajorAxisTolerance, AlongTrackTolerance
from fds.models.station_keeping.use_case import LeoStationKeeping
from fds.utils.dates import datetime_to_iso_string, get_datetime
from tests import TestUseCases, DATA_DIR


class TestStationKeepingRequest(unittest.TestCase):

    def setUp(self):
        self.orbit = KeplerianOrbit(
            6378 + 500, 0, 0, 0, 0, 0,
            kind=OrbitMeanOsculatingType.OSCULATING, anomaly_kind=PositionAngleType.TRUE,
            date='2023-05-22T00:00:00Z'
        )

        self.solar_array_deployable_fixed = SolarArray(
            efficiency=0.3,
            kind="DEPLOYABLE_FIXED",
            initialisation_kind=SolarArray.InitialisationKind.SURFACE,
            surface=1.0,
            normal_in_satellite_frame=(0.0, 0.0, -1.0),
        )

        self.spacecraft_box = SpacecraftBox.import_from_config_file(
            config_filepath=TestUseCases.CONFIG_TEST_FILEPATH, solar_array=self.solar_array_deployable_fixed)

        perturbations = (
            PropagationContext.Perturbation.DRAG,
            PropagationContext.Perturbation.SRP,
            PropagationContext.Perturbation.EARTH_POTENTIAL,
            PropagationContext.Perturbation.THIRD_BODY,
        )
        self.prop_ctx = PropagationContext.import_from_config_file(
            config_filepath=TestUseCases.CONFIG_TEST_FILEPATH, model_perturbations=perturbations
        )

        self.eph_request = EphemeridesRequest(
            timestep=3600.0,
            types=[EphemeridesRequest.EphemeridesType.KEPLERIAN],
            mean=True,
            osculating=True
        )

        self.states_request = SpacecraftStatesRequest(
            osculating=True,
            mean=True
        )

        self.tolerance = SemiMajorAxisTolerance(.01)

        self.sk = LeoStationKeeping(initial_orbit=self.orbit,
                                    propagation_context=self.prop_ctx,
                                    spacecraft=self.spacecraft_box,
                                    maximum_duration=86400 * 2,
                                    tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                                    average_available_on_board_power=1000,
                                    simulate_attitude_and_power_system=True)

    def test_orbit_is_correctly_mapped(self):
        initial_orbit = self.orbit
        expected_initial_orbit = self.sk.request.inputs.initial_orbit

        self.assertEqual(initial_orbit.orbital_elements.SMA * 1e3, expected_initial_orbit.sma)
        self.assertEqual(initial_orbit.orbital_elements.ECC, expected_initial_orbit.eccentricity)
        self.assertEqual(initial_orbit.orbital_elements.INC, np.degrees(expected_initial_orbit.inclination))

        self.assertEqual("ELLIPTICAL_SMA_ECC", expected_initial_orbit.parameters.parameters_type)

        self.assertEqual(initial_orbit.kind.value, expected_initial_orbit.advanced_parameters.orbital_element_type)
        self.assertEqual(datetime_to_iso_string(initial_orbit.date),
                         expected_initial_orbit.advanced_parameters.orbit_date)
        self.assertEqual("RAAN", expected_initial_orbit.advanced_parameters.ascending_node_type)
        self.assertEqual(initial_orbit.orbital_elements.RAAN,
                         np.degrees(expected_initial_orbit.advanced_parameters.raan))
        self.assertEqual(initial_orbit.anomaly_kind.value,
                         expected_initial_orbit.advanced_parameters.anomaly_type)
        self.assertEqual(initial_orbit.orbital_elements.TA,
                         np.degrees(expected_initial_orbit.advanced_parameters.anomaly))
        self.assertEqual(initial_orbit.orbital_elements.AOP,
                         np.degrees(expected_initial_orbit.advanced_parameters.perigee_argument))

    def test_platform_is_correctly_mapped(self):
        spacecraft = self.spacecraft_box
        expected_spacecraft = self.sk.request.inputs.platform

        self.assertEqual(spacecraft.platform_mass, expected_spacecraft.mass)
        self.assertEqual(self.sk.average_available_on_board_power, expected_spacecraft.on_board_average_power)

    def _test_box_spacecraft_geometry_is_correctly_mapped(self, spacecraft: SpacecraftBox,
                                                          expected_geometry: SpacecraftGeometry):
        self.assertEqual(spacecraft.length.x, expected_geometry.dimensions.x)
        self.assertEqual(spacecraft.length.y, expected_geometry.dimensions.y)
        self.assertEqual(spacecraft.length.z, expected_geometry.dimensions.z)

        self.assertEqual(spacecraft.thruster.axis_in_satellite_frame[0],
                         expected_geometry.thruster_axis.x)
        self.assertEqual(spacecraft.thruster.axis_in_satellite_frame[1],
                         expected_geometry.thruster_axis.y)
        self.assertEqual(spacecraft.thruster.axis_in_satellite_frame[2],
                         expected_geometry.thruster_axis.z)

        self.assertEqual(spacecraft.solar_array.efficiency, expected_geometry.solar_array.efficiency)
        self.assertEqual(spacecraft.solar_array.kind.value, expected_geometry.solar_array.type)

    def test_deployable_fixed_solar_array_is_correctly_mapped(self):
        spacecraft = self.spacecraft_box
        expected_geometry = self.sk.request.inputs.spacecraft_geometry

        self._test_box_spacecraft_geometry_is_correctly_mapped(spacecraft, expected_geometry)

        self.assertEqual(spacecraft.solar_array.normal_in_satellite_frame[0],
                         expected_geometry.solar_array.normal_direction.x)
        self.assertEqual(spacecraft.solar_array.normal_in_satellite_frame[1],
                         expected_geometry.solar_array.normal_direction.y)
        self.assertEqual(spacecraft.solar_array.normal_in_satellite_frame[2],
                         expected_geometry.solar_array.normal_direction.z)
        self.assertEqual(spacecraft.solar_array.surface, expected_geometry.solar_array.surface)

    def test_deployable_rotating_solar_array_is_correctly_mapped(self):
        solar_array = SolarArray(
            kind=SolarArray.Kind.DEPLOYABLE_ROTATING,
            axis_in_satellite_frame=(0.0, 0.0, 1.0),
            efficiency=0.3,
            surface=1.0,
            initialisation_kind=SolarArray.InitialisationKind.SURFACE,
            normal_in_satellite_frame=(1.0, 0.0, 0.0),
        )

        spacecraft = SpacecraftBox.import_from_config_file(
            config_filepath=TestUseCases.CONFIG_TEST_FILEPATH, solar_array=solar_array)

        sk = LeoStationKeeping(initial_orbit=self.orbit,
                               propagation_context=self.prop_ctx,
                               spacecraft=spacecraft,
                               maximum_duration=86400 * 2,
                               tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                               average_available_on_board_power=1000)

        expected_geometry = sk.request.inputs.spacecraft_geometry

        self._test_box_spacecraft_geometry_is_correctly_mapped(spacecraft, expected_geometry)

        self.assertEqual(spacecraft.solar_array.axis_in_satellite_frame[0],
                         expected_geometry.solar_array.rotation_axis.x)
        self.assertEqual(spacecraft.solar_array.axis_in_satellite_frame[1],
                         expected_geometry.solar_array.rotation_axis.y)
        self.assertEqual(spacecraft.solar_array.axis_in_satellite_frame[2],
                         expected_geometry.solar_array.rotation_axis.z)
        self.assertEqual(spacecraft.solar_array.surface, expected_geometry.solar_array.surface)

    def test_body_fixed_solary_array_is_correctly_mapped(self):
        solar_array = SolarArray(
            kind=SolarArray.Kind.BODY,
            efficiency=0.3,
            surface=1.0,
            initialisation_kind=SolarArray.InitialisationKind.SURFACE,
            satellite_faces=[SolarArray.SatelliteFace.PLUS_X],
            normal_in_satellite_frame=(0.0, 0.0, -1.0),
        )

        spacecraft = SpacecraftBox.import_from_config_file(
            config_filepath=TestUseCases.CONFIG_TEST_FILEPATH, solar_array=solar_array)

        sk = LeoStationKeeping(initial_orbit=self.orbit,
                               propagation_context=self.prop_ctx,
                               spacecraft=spacecraft,
                               maximum_duration=86400 * 2,
                               tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                               average_available_on_board_power=1000)

        expected_geometry = sk.request.inputs.spacecraft_geometry

        self._test_box_spacecraft_geometry_is_correctly_mapped(spacecraft, expected_geometry)

        self.assertEqual(spacecraft.solar_array.satellite_faces[0].value,
                         expected_geometry.solar_array.faces[0].value)

    def test_propulsion_system_is_correctly_mapped(self):
        spacecraft = self.spacecraft_box
        expected_propulsion_system = self.sk.request.inputs.propulsion_system

        self.assertEqual(spacecraft.propulsion_kind, expected_propulsion_system.type)
        self.assertEqual(spacecraft.thruster.isp, expected_propulsion_system.isp)
        self.assertEqual(spacecraft.thruster.power, expected_propulsion_system.power)
        self.assertEqual(spacecraft.thruster.thrust, expected_propulsion_system.thrust)
        self.assertEqual(spacecraft.thruster.stand_by_power, expected_propulsion_system.standby_power)
        self.assertEqual(spacecraft.thruster.warm_up_power, expected_propulsion_system.warm_up_power)
        self.assertEqual(spacecraft.thruster.warm_up_duration, expected_propulsion_system.warm_up_duration)
        self.assertEqual(spacecraft.thruster.propellant_mass, expected_propulsion_system.propellant_mass)
        self.assertEqual(spacecraft.thruster.wet_mass, expected_propulsion_system.total_mass)
        self.assertEqual(spacecraft.thruster.impulse, expected_propulsion_system.total_impulse)
        self.assertEqual(spacecraft.thruster.maximum_thrust_duration,
                         expected_propulsion_system.maximum_thrust_duration)
        self.assertEqual(None, expected_propulsion_system.consumption)
        self.assertEqual("PROPELLANT", expected_propulsion_system.propellant_capacity_choice)

    def test_battery_is_correctly_mapped(self):
        battery = self.spacecraft_box.battery
        expected_battery = self.sk.request.inputs.battery

        self.assertEqual(battery.nominal_capacity, expected_battery.nominal_capacity)
        self.assertEqual(battery.depth_of_discharge, expected_battery.depth_of_discharge)
        self.assertEqual(battery.minimum_charge_for_firing, expected_battery.minimum_charge_for_firing)
        self.assertEqual(battery.initial_charge, expected_battery.initial_charge)

    def test_strategy_with_thrust_duration_arc_is_correctly_mapped(self):
        strategy = StationKeepingStrategy(
            thrust_arcs_position=StationKeepingStrategy.ThrustArcPosition.ASCENDING_AND_DESCENDING_NODES,
            thrust_arcs_number=StationKeepingStrategy.ThrustArcNumber.TWO,
            number_of_thrust_orbits=1,
            number_of_rest_orbits=0,
            number_of_shift_orbits=0,
            stop_thrust_at_eclipse=False,
            thrust_arc_initialisation_kind=StationKeepingStrategy.ThrustArcInitialisationKind.THRUST_DURATION,
            thrust_arc_duration=1500,
        )

        sk = LeoStationKeeping(initial_orbit=self.orbit,
                               propagation_context=self.prop_ctx,
                               spacecraft=self.spacecraft_box,
                               maximum_duration=86400 * 2,
                               tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                               average_available_on_board_power=1000, strategy=strategy)

        expected_strategy = sk.request.inputs.custom_maneuvering_strategy

        self._test_strategy_is_correctly_mapped(expected_strategy, strategy)

        self.assertEqual(strategy.thrust_arc_duration, expected_strategy.thrust_arc_definition.thrust_arc_duration)

    def test_strategy_with_duty_cycle_arc_is_correctly_mapped(self):
        strategy = StationKeepingStrategy(
            thrust_arcs_position=StationKeepingStrategy.ThrustArcPosition.ASCENDING_AND_DESCENDING_NODES,
            thrust_arcs_number=StationKeepingStrategy.ThrustArcNumber.TWO,
            number_of_thrust_orbits=1,
            number_of_rest_orbits=0,
            number_of_shift_orbits=0,
            stop_thrust_at_eclipse=False,
            thrust_arc_initialisation_kind=StationKeepingStrategy.ThrustArcInitialisationKind.DUTY_CYCLE,
            orbital_duty_cycle=.1,
        )
        expected_strategy = strategy.to_microservice_format()

        self._test_strategy_is_correctly_mapped(expected_strategy, strategy)

        self.assertEqual(strategy.orbital_duty_cycle, expected_strategy.thrust_arc_definition.duty_cycle)

    def _test_strategy_is_correctly_mapped(self, expected_strategy, strategy):
        number = {'ONE': 1, 'TWO': 2}
        self.assertEqual(strategy.thrust_arcs_position.value, expected_strategy.thrust_arcs_position)
        self.assertEqual(number[strategy.thrust_arcs_number.value], expected_strategy.thrust_arcs_number)
        self.assertEqual(strategy.number_of_thrust_orbits, expected_strategy.number_of_thrust_orbits)
        self.assertEqual(strategy.number_of_rest_orbits, expected_strategy.number_of_rest_orbits)
        self.assertEqual(strategy.number_of_shift_orbits, expected_strategy.number_of_shift_orbits)
        self.assertEqual(strategy.stop_thrust_at_eclipse, expected_strategy.stop_thrusting_during_eclipse)
        self.assertEqual(strategy.dynamic_duty_cycle, expected_strategy.dynamic_duty_cycle)
        self.assertEqual(strategy.thrust_arc_initialisation_kind.value, expected_strategy.thrust_arc_definition.type)

    def test_sma_tolerance_is_correctly_mapped(self):
        tolerance = SemiMajorAxisTolerance(.01)
        expected_tolerance = tolerance.to_microservice_format()
        self.assertEqual(self.tolerance.value * 1e3, expected_tolerance.sma_tolerance)
        self.assertEqual("SMA", expected_tolerance.type)

    def test_along_track_tolerance_is_correctly_mapped(self):
        tolerance = AlongTrackTolerance(.01)
        expected_tolerance = tolerance.to_microservice_format()
        self.assertEqual(self.tolerance.value * 1e3, expected_tolerance.along_track_tolerance)
        self.assertEqual("ALONG_TRACK", expected_tolerance.type)

    def test_perturbations_are_correctly_mapped(self):
        spacecraft = self.spacecraft_box
        perturbations = self.prop_ctx.model.perturbations
        expected_perturbations = self.sk.request.inputs.perturbations

        self.assertEqual(len(perturbations), len(expected_perturbations))

        for pert, exp_pert in zip(perturbations, expected_perturbations):
            self.assertEqual(pert.value, exp_pert.type)
            match pert.value:
                case PropagationContext.Perturbation.DRAG:
                    self.assertEqual(spacecraft.drag_coefficient, exp_pert.drag_coefficient)
                    self.assertEqual(self.sk.drag_lift_ratio, exp_pert.lift_ratio)
                    atmosphere_kind = self.prop_ctx.model.atmosphere_kind
                    self.assertEqual(atmosphere_kind.value, exp_pert.atmospheric_model.type)
                    if atmosphere_kind == PropagationContext.AtmosphereModel.HARRIS_PRIESTER:
                        self.assertEqual(self.prop_ctx.model.solar_flux, exp_pert.atmospheric_model.custom_solar_flux)
                case PropagationContext.Perturbation.SRP:
                    self.assertEqual(spacecraft.reflectivity_coefficient, exp_pert.reflection_coefficient)
                    self.assertEqual(self.sk.srp_absorption_coefficient, exp_pert.absorption_coefficient)
                case PropagationContext.Perturbation.EARTH_POTENTIAL:
                    self.assertEqual(self.prop_ctx.model.earth_potential_ord,
                                     exp_pert.custom_earth_potential_configuration.order)
                    self.assertEqual(self.prop_ctx.model.earth_potential_deg,
                                     exp_pert.custom_earth_potential_configuration.degree)

    def test_invalid_station_keeping_if_spacecraft_is_spherical(self):
        with self.assertRaises(ValueError):
            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=SpacecraftSphere.import_from_config_file(
                    config_filepath=TestUseCases.CONFIG_TEST_FILEPATH),
                maximum_duration=86400 * 2,
                tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                average_available_on_board_power=1000
            )

    def test_invalid_station_keeping_if_solar_panels_are_not_initialised_with_surface(self):
        with self.assertRaises(ValueError):
            sa = SolarArray(
                kind=SolarArray.Kind.DEPLOYABLE_FIXED,
                efficiency=0.3,
                maximum_power=1.0,
                initialisation_kind=SolarArray.InitialisationKind.MAXIMUM_POWER,
                normal_in_satellite_frame=(0.0, 0.0, -1.0),
            )

            spacecraft = SpacecraftBox.import_from_config_file(
                config_filepath=TestUseCases.CONFIG_TEST_FILEPATH, solar_array=sa)

            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=spacecraft,
                maximum_duration=86400 * 2,
                tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                average_available_on_board_power=1000
            )

    def test_invalid_station_keeping_if_maximum_duration_less_or_equal_to_zero(self):
        with self.assertRaises(ValueError):
            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=self.spacecraft_box,
                maximum_duration=0,
                tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                average_available_on_board_power=1000
            )

    def test_invalid_station_keeping_if_average_available_on_board_power_less_than_zero(self):
        with self.assertRaises(ValueError):
            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=self.spacecraft_box,
                maximum_duration=86400 * 2,
                tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                average_available_on_board_power=-1000
            )

    def test_invalid_station_keeping_if_drag_lift_ratio_less_than_zero(self):
        with self.assertRaises(ValueError):
            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=self.spacecraft_box,
                maximum_duration=86400 * 2,
                tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                average_available_on_board_power=1000,
                drag_lift_ratio=-1
            )

    def test_invalid_station_keeping_if_srp_absorption_coefficient_less_than_zero(self):
        with self.assertRaises(ValueError):
            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=self.spacecraft_box,
                maximum_duration=86400 * 2,
                tolerance=self.tolerance, output_requests=[self.eph_request, self.states_request],
                average_available_on_board_power=1000,
                srp_absorption_coefficient=-1
            )

    def test_invalid_station_keeping_if_system_ephemerides_in_output_requests_and_system_not_simulated(self):
        eph_request = EphemeridesRequest(
            timestep=3600.0,
            types=[EphemeridesRequest.EphemeridesType.POWER_SYSTEM],
            mean=True,
            osculating=False
        )
        with self.assertRaises(ValueError):
            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=self.spacecraft_box,
                maximum_duration=86400 * 2,
                tolerance=self.tolerance, output_requests=[eph_request],
                average_available_on_board_power=1000,
                simulate_attitude_and_power_system=False
            )

    # TODO To be changed once the thrust ephemerides are implemented
    def test_invalid_station_keeping_if_thrust_ephemerides_in_output_requests(self):
        thrust_ephemerides = ThrustEphemeridesRequest(
            mean=True,
            osculating=False
        )
        with self.assertRaises(NotImplementedError):
            LeoStationKeeping(
                initial_orbit=self.orbit,
                propagation_context=self.prop_ctx,
                spacecraft=self.spacecraft_box,
                maximum_duration=86400 * 2,
                tolerance=self.tolerance, output_requests=[thrust_ephemerides],
            )

    def test_microservice_configuration(self):
        self.assertEqual(self.sk.microservice_configuration.host, get_station_keeping_api_url())

    def test_end_to_end(self):
        res = self.sk.run().result
        self.assertIsNotNone(res)
        self.assertIsNotNone(res.raw_spacecraft_states)
        self.assertIsNotNone(res.raw_spacecraft_states.get('osculating'))
        self.assertIsNotNone(res.raw_spacecraft_states.get('mean'))
        self.assertIsNotNone(res.raw_spacecraft_states.get('thrusting'))
        self.assertIsNotNone(res.raw_ephemerides)
        self.assertIsNotNone(res.ephemerides_field_indexes)
        self.assertTrue(self.sk.response.errors is None or len(self.sk.response.errors) == 0)


class TestStationKeepingResults(unittest.TestCase):
    def setUp(self):
        with open(DATA_DIR / "station_keeping/response.json") as f:
            self.response_json = f.read()

        self.input_data = {
            "maximum_duration": 86400 * 15,
            "date": "2024-06-01T00:00:00Z"
        }

        response = NumericalLeoStationKeepingResponse.from_json(self.response_json)

        self.result = ResultStationKeeping.from_microservice_response(response, start_date=self.input_data["date"])

        self.test_raw_ephemerides = [[0, 2, 3, 4, 123], [120, 6, 7, 8, 345]]
        self.test_field_indexes = {
            "simulationDuration": 0,
            "positionX": 1,
            "positionY": 2,
            "positionZ": 3,
            "positionKeyToBeChanged": 4
        }

        self.test_expected_all_ephemerides = [
            {
                'date': get_datetime(self.input_data["date"]),
                'positionX': 2,
                'positionY': 3,
                'positionZ': 4,
                'simulationDuration': 0,
                'positionKeyToBeChanged': 123
            },
            {
                'date': get_datetime(self.input_data["date"]) + datetime.timedelta(seconds=120),
                'positionX': 6,
                'positionY': 7,
                'positionZ': 8,
                'simulationDuration': 120,
                'positionKeyToBeChanged': 345
            }
        ]

    def test_roadmap_generation(self):
        roadmap = self.result.generate_maneuver_roadmap(quaternion_step=0.0)
        self.assertIsNotNone(roadmap)

        # Assert the duration of the roadmap
        self.assertEqual(roadmap.duration, self.input_data["maximum_duration"])

        # Assert the number of firings
        firing_count = 0
        for action in roadmap.actions:
            if isinstance(action, ActionFiring):
                firing_count += 1

        # self.assertEqual(firing_count, self.result.report.number_of_burns) # TODO: Fix this in µservice
        self.assertEqual(firing_count, len(self.result.raw_spacecraft_states.get('thrusting')))

        # Assert the number of quaternions
        quaternion_count = len(roadmap.actions[0].quaternions)
        raw_quaternions = self.result.raw_spacecraft_states.get('osculating').get('attitude').get('rotation')
        raw_quaternion_dates = self.result.raw_spacecraft_states.get('timestamps')
        raw_quaternions = Quaternion.from_collections(raw_quaternions, raw_quaternion_dates)
        quaternions = get_univoque_list_of_dated_quaternions(raw_quaternions,
                                                             ignore_different_quaternions_at_same_date=True)
        expected_quaternion_count = len(quaternions)
        self.assertEqual(quaternion_count, expected_quaternion_count)
        for q, rq in zip(roadmap.actions[0].quaternions, quaternions):
            self.assertEqual(q, rq)

    def test_invalid_roadmap_generation_if_states_not_computed(self):
        response = NumericalLeoStationKeepingResponse.from_json(self.response_json)
        response.spacecraft_states = None
        wrong_result = ResultStationKeeping.from_microservice_response(response, start_date=self.input_data["date"])

        with self.assertRaises(ValueError):
            wrong_result.generate_maneuver_roadmap()

    def test_invalid_roadmap_generation_if_osculating_states_not_computed(self):
        response = NumericalLeoStationKeepingResponse.from_json(self.response_json)
        response.spacecraft_states.osculating = None
        wrong_result = ResultStationKeeping.from_microservice_response(response, start_date=self.input_data["date"])

        with self.assertRaises(ValueError):
            wrong_result.generate_maneuver_roadmap()

    def test_raw_ephemerides_export(self):
        start_date = get_datetime(self.input_data["date"])
        raw_data = get_ephemerides_data(self.test_raw_ephemerides, self.test_field_indexes,
                                        start_date)
        self.assertEqual(len(raw_data), 2)
        self.assertEqual(raw_data, self.test_expected_all_ephemerides)

    def test_ephemerides_prefix_selection(self):
        selected_data = select_ephemerides_data_with_specific_prefix(
            self.test_expected_all_ephemerides,
            prefix_list=["position"],
            remove_prefix=True
        )
        expected_selected_data = [
            {
                'date': get_datetime(self.input_data["date"]),
                'X': 2,
                'Y': 3,
                'Z': 4,
                'KeyToBeChanged': 123
            },
            {
                'date': get_datetime(self.input_data["date"]) + datetime.timedelta(seconds=120),
                'X': 6,
                'Y': 7,
                'Z': 8,
                'KeyToBeChanged': 345
            }
        ]
        self.assertEqual(selected_data, expected_selected_data)

    def test_ephemerides_prefix_selection_without_removal(self):
        selected_data = select_ephemerides_data_with_specific_prefix(
            self.test_expected_all_ephemerides,
            prefix_list=["position"],
            remove_prefix=False
        )
        expected_selected_data = [
            {
                'date': get_datetime(self.input_data["date"]),
                'positionX': 2,
                'positionY': 3,
                'positionZ': 4,
                'positionKeyToBeChanged': 123
            },
            {
                'date': get_datetime(self.input_data["date"]) + datetime.timedelta(seconds=120),
                'positionX': 6,
                'positionY': 7,
                'positionZ': 8,
                'positionKeyToBeChanged': 345
            }
        ]
        self.assertEqual(selected_data, expected_selected_data)

    def test_ephemerides_prefix_selection_with_removal(self):
        selected_data = select_ephemerides_data_with_specific_prefix(
            self.test_expected_all_ephemerides,
            prefix_list=["position"],
            remove_prefix=True
        )
        expected_selected_data = [
            {
                'date': get_datetime(self.input_data["date"]),
                'X': 2,
                'Y': 3,
                'Z': 4,
                'KeyToBeChanged': 123
            },
            {
                'date': get_datetime(self.input_data["date"]) + datetime.timedelta(seconds=120),
                'X': 6,
                'Y': 7,
                'Z': 8,
                'KeyToBeChanged': 345
            }
        ]
        self.assertEqual(selected_data, expected_selected_data)

    def test_ephemerides_prefix_selection_with_no_prefix(self):
        selected_data = select_ephemerides_data_with_specific_prefix(
            self.test_expected_all_ephemerides,
            prefix_list=[],
            remove_prefix=False
        )
        self.assertEqual(selected_data, self.test_expected_all_ephemerides)

    def test_ephemerides_prefix_selection_with_change_of_key(self):
        selected_data = select_ephemerides_data_with_specific_prefix(
            self.test_expected_all_ephemerides,
            prefix_list=["position"],
            remove_prefix=True,
            keys_to_update={"positionKeyToBeChanged": "NewKey"}
        )
        expected_selected_data = [
            {
                'date': get_datetime(self.input_data["date"]),
                'X': 2,
                'Y': 3,
                'Z': 4,
                'NewKey': 123
            },
            {
                'date': get_datetime(self.input_data["date"]) + datetime.timedelta(seconds=120),
                'X': 6,
                'Y': 7,
                'Z': 8,
                'NewKey': 345
            }
        ]
        self.assertEqual(selected_data, expected_selected_data)
