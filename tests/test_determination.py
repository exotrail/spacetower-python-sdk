import unittest
from datetime import datetime, UTC, timedelta

import numpy as np

from fds.models.actions import ActionAttitude, AttitudeMode, ActionFiring
from fds.models.determination.configuration import OrbitDeterminationConfiguration
from fds.models.determination.requests import DragCoefficientEstimationRequest, \
    ReflectivityCoefficientEstimationRequest, ThrustVectorEstimationRequest
from fds.models.determination.result import ResultOrbitDetermination
from fds.models.determination.use_case import OrbitDetermination
from fds.models.orbit_extrapolation.requests import MeasurementsRequestGpsNmea
from fds.models.orbit_extrapolation.use_case import OrbitExtrapolation
from fds.models.orbital_state import CovarianceMatrix, PropagationContext, OrbitalState
from fds.models.orbits import KeplerianOrbit, PositionAngleType, OrbitMeanOsculatingType
from fds.models.quaternion import Quaternion
from fds.models.roadmaps import RoadmapFromActions
from fds.models.spacecraft import SpacecraftBox
from fds.models.telemetry import TelemetryGpsNmeaRaw
from fds.utils.dates import get_datetime
from fds.utils.frames import Frame
from tests import TestModels, TestModelsWithContainer, _test_initialisation, TestUseCases, DATA_DIR
from tests.test_orbital_state import TestCovarianceMatrix


class TestDragCoefficientEstimationRequest(TestModels):
    CLIENT_TYPE = DragCoefficientEstimationRequest
    KWARGS = {
        'standard_deviation': 0.1,  # float
        'process_noise_standard_deviation': 0.1,  # float
        'nametag': 'TestDragCoefficientEstimationRequest'
    }

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestReflectivityCoefficientEstimationRequest(TestModels):
    CLIENT_TYPE = ReflectivityCoefficientEstimationRequest
    KWARGS = {
        'standard_deviation': 0.1,  # float
        'process_noise_standard_deviation': 0.1,  # float
        'nametag': 'TestReflectivityCoefficientEstimationRequest'
    }

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestThrustVectorEstimationRequest(TestModels):
    CLIENT_TYPE = ThrustVectorEstimationRequest
    KWARGS = {
        'standard_deviation': 0.1,  # float
        'process_noise_standard_deviation': 0.1,  # float
        'nametag': 'TestThrustVectorEstimationRequest'
    }

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestOrbitDeterminationConfiguration(TestModelsWithContainer):
    CLIENT_TYPE = OrbitDeterminationConfiguration
    noise = CovarianceMatrix(**TestCovarianceMatrix.KWARGS)
    KWARGS = {'tuning_alpha': 0.5,  # float
              'tuning_beta': 2,  # float
              'tuning_kappa': -2,  # float
              'outliers_manager_scale': 10,  # float
              'outliers_manager_warmup': 0,  # float, (s)
              'noise_provider_kind': "BASIC",
              'process_noise_matrix': noise,
              'nametag': 'TestOrbitDeterminationConfiguration'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE, process_noise_matrix=self.noise)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS,
                                                       destroy_subcomponents=True)


class TestOrbitDetermination(TestUseCases, unittest.TestCase):
    CLIENT_TYPE = OrbitDetermination

    INITIAL_TLE = '\n'.join([
        "1 99999U 98067AF  23180.77623843 -.00000000  00000-0 -39596-4 0    11",
        "2 99999  97.5099 297.1364 0014987 151.2712  78.3813 15.13639674000012"
    ])

    INITIAL_TLE_MIXED = '\n'.join([
        "1 58295U 23174AR  24059.48814215  .00002816  00000-0  15242-3 0  9993",
        "2 58295  97.4674 135.5968 0009692 246.6806 113.3407 15.15425370 17069"
    ])

    FINAL_TLE = '\n'.join([
        "1 99999U 98067AF  23180.77633102  .00000000  00000-0 -39596-4 0    19",
        "2 99999  97.5099 297.1365 0014959 150.7167  79.4400 15.13673192    17"
    ])

    INITIAL_DATE = "2023-05-22T00:00:00.000Z"

    def setUp(self) -> None:
        with open(DATA_DIR / "orbit_determination/nmea_simple.txt", 'r') as f:
            NMEA_TEST_DATA = f.readlines()
        self.NMEA_TEST_DATA = [x.strip() for x in NMEA_TEST_DATA]

        with open(DATA_DIR / "orbit_determination/nmea_mixed.txt", 'r') as f:
            NMEA_TEST_DATA_MIXED = f.readlines()
        self.NMEA_TEST_DATA_MIXED = [x.strip() for x in NMEA_TEST_DATA_MIXED]

        self.propagation_context = PropagationContext.import_from_config_file(self.CONFIG_TEST_FILEPATH)
        self.propagation_context_with_srp = PropagationContext.import_from_config_file(
            self.CONFIG_TEST_FILEPATH
        )
        self.propagation_context_with_srp.model.perturbations.append(PropagationContext.Perturbation.SRP)

        spacecraft = SpacecraftBox.import_from_config_file(self.CONFIG_TEST_FILEPATH)
        spacecraft.thruster.thrust = 1  # N

        initial_covariance_matrix = CovarianceMatrix.from_diagonal(diagonal=(100, 100, 100, 0.1, 0.1, 0.1),
                                                                   frame="TNW")

        self.initial_orbital_state = OrbitalState.from_tle(
            covariance_matrix=initial_covariance_matrix,
            propagation_context=self.propagation_context,
            spacecraft=spacecraft,
            tle=self.INITIAL_TLE
        )

        self.initial_orbital_state_with_srp = OrbitalState.from_tle(
            covariance_matrix=initial_covariance_matrix,
            propagation_context=self.propagation_context_with_srp,
            spacecraft=spacecraft,
            tle=self.INITIAL_TLE
        )

        process_noise_matrix = CovarianceMatrix.from_diagonal(diagonal=(1E-1, 1E-1, 1E-1, 1E-4, 1E-4, 1E-4),
                                                              frame="TNW")
        self.od_config = (
            OrbitDeterminationConfiguration.import_from_config_file(self.CONFIG_TEST_FILEPATH,
                                                                    process_noise_matrix=process_noise_matrix))

        self.nmea_measure = TelemetryGpsNmeaRaw(
            self.NMEA_TEST_DATA,
            standard_deviation_ground_speed=1,  # m/s
            standard_deviation_altitude=100,  # m
            standard_deviation_longitude=0.001,  # deg
            standard_deviation_latitude=0.001,  # deg
        )

        self.kwargs = {
            'initial_orbital_state': self.initial_orbital_state,
            'telemetry': self.nmea_measure,
            'configuration': self.od_config,
        }

    def test_orbit_determination_initialisation(self):
        self._test_initialisation()

    def test_orbit_determination_run(self):
        res = self._test_client_run()
        os = res.estimated_states[-1]

        final_date = get_datetime('2023-06-29 18:37:55+00:00')
        final_cov_mat = CovarianceMatrix(
            matrix=[[96.16102727403323, -0.8160783099252733, 0.40638571653154276, 0.691994334551828,
                     0.08549990181436279, 0.09167335041127644],
                    [-0.8160783099252733, 99.94103807309796, -0.016461908338637088, 0.08561833791299005,
                     0.650945574507383, -0.12437697164554287],
                    [0.40638571653154276, -0.016461908338637088, 100.07793765192385, 0.092024318322771,
                     -0.12469511413828294, 0.6504866350448696],
                    [0.691994334551828, 0.08561833791299005, 0.092024318322771, 0.09192395246194768,
                     0.011817979924014232, 0.011910459482900978],
                    [0.08549990181436279, 0.650945574507383, -0.12469511413828294, 0.011817979924014232,
                     0.0844161784675575, -0.016324113928652614],
                    [0.09167335041127644, -0.12437697164554287, 0.6504866350448696, 0.011910459482900978,
                     -0.016324113928652614, 0.0842578336754444]],
            date='2023-06-29 18:37:55+00:00',
            frame=Frame.ECI,
        ).save()

        self.assertTrue(self.is_datetime_close(os.date, final_date))
        self.assertTrue(os.covariance_matrix.frame == final_cov_mat.frame)
        self.assertTrue(os.covariance_matrix.orbit_type == final_cov_mat.orbit_type)
        self.assertTrue(np.isclose(np.array(os.covariance_matrix.matrix), np.array(final_cov_mat.matrix)).all())
        self.assertTrue(os.propagation_context.is_same_object_as(self.propagation_context, check_id=False))

    def assert_parameter_estimation(self, estimated_parameters: list[float], correct_lenght: int, last_value: float):
        self.assertTrue(estimated_parameters is not None)
        self.assertTrue(len(estimated_parameters) > 0)
        self.assertTrue(len(estimated_parameters) == correct_lenght)
        self.assertTrue(estimated_parameters[-1] == last_value)

    def test_orbit_determination_with_parameter_requests(self):
        drag_coefficient_request = DragCoefficientEstimationRequest(
            standard_deviation=1,
            process_noise_standard_deviation=0.1,
            nametag="drag_coefficient_request"
        )
        reflectivity_coefficient_request = ReflectivityCoefficientEstimationRequest(
            standard_deviation=1,
            process_noise_standard_deviation=0.1,
            nametag="reflectivity_coefficient_request"
        )
        self.kwargs['initial_orbital_state'] = self.initial_orbital_state_with_srp
        self.kwargs['parameter_estimation_requests'] = [drag_coefficient_request, reflectivity_coefficient_request]
        res = self._test_client_run()

        # Assert that both parameters were estimated
        self.assert_parameter_estimation(
            [v.value for v in res.in_depth_results.estimated_drag_coefficients],
            len(res.in_depth_results.dates),
            res.estimated_orbital_state.spacecraft.drag_coefficient
        )
        self.assert_parameter_estimation(
            [v.value for v in res.in_depth_results.estimated_reflectivity_coefficients],
            len(res.in_depth_results.dates),
            res.estimated_orbital_state.spacecraft.reflectivity_coefficient
        )

    def test_orbit_determination_with_mixed_rmc_gga_sentences(self):
        nmea_measure_mixed = TelemetryGpsNmeaRaw(
            self.NMEA_TEST_DATA_MIXED,
            standard_deviation_ground_speed=1,  # m/s
            standard_deviation_altitude=100,  # m
            standard_deviation_longitude=0.001,  # deg
            standard_deviation_latitude=0.001,  # deg
        )

        initial_orbital_state = OrbitalState.from_tle(
            covariance_matrix=self.initial_orbital_state.covariance_matrix,
            propagation_context=self.initial_orbital_state.propagation_context,
            spacecraft=self.initial_orbital_state.spacecraft,
            tle=self.INITIAL_TLE_MIXED
        )

        self.kwargs['initial_orbital_state'] = initial_orbital_state
        self.kwargs['telemetry'] = nmea_measure_mixed

        self._test_client_run()

    def test_orbit_determination_with_prograde_roadmap(self):
        attitude_action = ActionAttitude(
            transition_date=datetime(2023, 5, 22, 0, 0, 0, 0, tzinfo=UTC),
            attitude_mode=AttitudeMode.PROGRADE,
        )

        firing = ActionFiring(
            firing_attitude_mode=AttitudeMode.PROGRADE,
            post_firing_attitude_mode=AttitudeMode.PROGRADE,
            firing_start_date=datetime(2023, 5, 22, 1, 0, 0, 0, tzinfo=UTC),
            duration=1200,
            warm_up_duration=60,
        )

        roadmap = RoadmapFromActions(
            actions=[attitude_action, firing],
            end_date=firing.firing_end_date + timedelta(hours=1),
        )

        self._test_orbit_determination_with_roadmap(roadmap)

    def test_orbit_determination_with_retrograde_roadmap(self):
        attitude_action = ActionAttitude(
            transition_date=datetime(2023, 5, 22, 0, 0, 0, 0, tzinfo=UTC),
            attitude_mode=AttitudeMode.RETROGRADE,
        )

        firing = ActionFiring(
            firing_attitude_mode=AttitudeMode.RETROGRADE,
            post_firing_attitude_mode=AttitudeMode.RETROGRADE,
            firing_start_date=datetime(2023, 5, 22, 1, 0, 0, 0, tzinfo=UTC),
            duration=1200,
            warm_up_duration=60,
        )

        roadmap = RoadmapFromActions(
            actions=[attitude_action, firing],
            end_date=firing.firing_end_date + timedelta(hours=1),
        )

        self._test_orbit_determination_with_roadmap(roadmap)

    def test_orbit_determination_with_multiple_firings_roadmap(self):
        attitude_action = ActionAttitude(
            transition_date=datetime(2023, 5, 22, 0, 0, 0, 0, tzinfo=UTC),
            attitude_mode=AttitudeMode.PROGRADE,
        )

        firings = []

        for i in range(1, 10):
            firings.append(ActionFiring(
                firing_attitude_mode=AttitudeMode.PROGRADE,
                post_firing_attitude_mode=AttitudeMode.PROGRADE,
                firing_start_date=datetime(2023, 5, 22, 1, 0, 0, 0, tzinfo=UTC) + timedelta(hours=i),
                duration=1200,
                warm_up_duration=60,
            ))

        roadmap = RoadmapFromActions(
            actions=[attitude_action] + firings,
            end_date=firings[-1].firing_end_date + timedelta(hours=1),
        )

        res = self._test_orbit_determination_with_roadmap(roadmap)
        firing_data = res.export_firings_report_data()
        self.compare_csv_to_list_of_dict(DATA_DIR / "orbit_determination/firings_report.csv", firing_data)

        parameters_data = res.export_parameter_estimation_data()
        self.compare_csv_to_list_of_dict(DATA_DIR / "orbit_determination/parameters_estimation.csv", parameters_data)

        thrust_data = res.export_thrust_estimation_data()
        self.compare_csv_to_list_of_dict(DATA_DIR / "orbit_determination/thrust_estimation.csv", thrust_data)

    def test_orbit_determination_with_quaternion_roadmap(self):
        start_date = datetime(2023, 5, 22, 0, 0, 0, 0, tzinfo=UTC)
        quaternions = []
        for i in range(0, 3600 * 3, 60):
            rand_quat = np.random.rand(4)
            rand_quat /= np.linalg.norm(rand_quat)
            quaternions.append(Quaternion(*rand_quat, date=start_date + timedelta(seconds=i)))

        attitude_action = ActionAttitude(
            transition_date=start_date,
            attitude_mode=AttitudeMode.QUATERNION,
            quaternions=quaternions,
        )

        firing = ActionFiring(
            firing_attitude_mode=AttitudeMode.QUATERNION,
            post_firing_attitude_mode=AttitudeMode.QUATERNION,
            firing_start_date=start_date + timedelta(hours=1),
            duration=1200,
            warm_up_duration=60,
        )

        roadmap = RoadmapFromActions(
            actions=[attitude_action, firing],
        )

        self._test_orbit_determination_with_roadmap(roadmap)

    def _test_orbit_determination_with_roadmap(self, roadmap: RoadmapFromActions) -> ResultOrbitDetermination:
        orbit = KeplerianOrbit(
            semi_major_axis=7000,
            eccentricity=0.001,
            inclination=45,
            raan=0,
            argument_of_perigee=0,
            anomaly=0,
            date=roadmap.start_date,
            anomaly_kind=PositionAngleType.TRUE,
            kind=OrbitMeanOsculatingType.MEAN,
        )

        orbital_state = OrbitalState.from_orbit(
            orbit=orbit,
            covariance_matrix=CovarianceMatrix.from_diagonal([100, 100, 100, 0.1, 0.1, 0.1], Frame.TNW),
            propagation_context=self.propagation_context,
            spacecraft=self.initial_orbital_state.spacecraft,
        )

        measurement_request = MeasurementsRequestGpsNmea(
            standard_deviation_altitude=100,
            standard_deviation_ground_speed=1,
            standard_deviation_latitude=0.001,
            standard_deviation_longitude=0.001,
            generation_step=60,
        )

        orbit_extrapolation = OrbitExtrapolation(
            initial_orbital_state=orbital_state,
            roadmap=roadmap,
            measurements_request=measurement_request,
        )

        oe_result = orbit_extrapolation.run().result

        orbit_extrapolation_without_roadmap = OrbitExtrapolation(
            duration=roadmap.duration,
            initial_orbital_state=orbital_state,
            measurements_request=measurement_request,
        )

        oe_result_without_roadmap = orbit_extrapolation_without_roadmap.run().result

        thrust_estimation_request = ThrustVectorEstimationRequest(
            standard_deviation=1,
            process_noise_standard_deviation=0.1,
            nametag="thrust_estimation_request"
        )

        drag_coefficient_request = DragCoefficientEstimationRequest(
            standard_deviation=1,
            process_noise_standard_deviation=0.1,
            nametag="drag_coefficient_request"
        )

        # Perform the OD with the same roadmap and measurements
        od = OrbitDetermination(
            initial_orbital_state=orbital_state,
            telemetry=oe_result.computed_measurements[0],
            configuration=self.od_config,
            actual_roadmap=roadmap,
            estimated_results_min_step=measurement_request.generation_step * 1,
            parameter_estimation_requests=[thrust_estimation_request, drag_coefficient_request],
        )

        od_result = od.run().result

        # check that the orbital state found with the OD is close to the one found with the extrapolation
        od_state_date = od_result.estimated_states[-1].date
        oe_state_date = oe_result.last_orbital_state.date
        oe_state_date_without_roadmap = oe_result_without_roadmap.last_orbital_state.date

        self.assertTrue(self.is_datetime_close(od_state_date, oe_state_date))
        self.assertTrue(self.is_datetime_close(od_state_date, oe_state_date_without_roadmap))

        od_state_osc = od_result.estimated_states[-1].osculating_orbit.orbital_elements
        oe_state_osc = oe_result.last_orbital_state.osculating_orbit.orbital_elements
        oe_state_osc_without_roadmap = oe_result_without_roadmap.last_orbital_state.osculating_orbit.orbital_elements

        self.assertTrue(np.isclose(od_state_osc.SMA, oe_state_osc.SMA, atol=1))  # 1 km
        self.assertTrue(np.isclose(od_state_osc.ECC, oe_state_osc.ECC, atol=1E-4))
        self.assertFalse(np.isclose(od_state_osc.SMA, oe_state_osc_without_roadmap.SMA, atol=1))
        self.assertFalse(np.isclose(od_state_osc.ECC, oe_state_osc_without_roadmap.ECC, atol=1E-4))

        return od_result
