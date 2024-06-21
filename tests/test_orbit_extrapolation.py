import datetime
import json
from datetime import timedelta

from fds.models.actions import ActionAttitude, AttitudeMode, ActionFiring
from fds.models.ground_station import GroundStation
from fds.models.orbit_extrapolation.events import SensorEvent, OrbitalEvent, EclipseEvent, StationVisibilityEvent, \
    EventWithDuration
from fds.models.orbit_extrapolation.requests import (EventsRequestOrbital, EventsRequestSensor,
                                                     EventsRequestStationVisibility, MeasurementsRequestOptical,
                                                     MeasurementsRequestRadar, MeasurementsRequestGpsPv,
                                                     MeasurementsRequestGpsNmea, OemRequest, EphemeridesRequest)
from fds.models.orbit_extrapolation.result import ResultOrbitExtrapolation
from fds.models.orbit_extrapolation.use_case import OrbitExtrapolation
from fds.models.orbital_state import CovarianceMatrix, PropagationContext, OrbitalState, RequiredOrbitalStates
from fds.models.orbits import KeplerianOrbit, OrbitMeanOsculatingType, PositionAngleType
from fds.models.roadmaps import RoadmapFromActions
from fds.models.spacecraft import SpacecraftSphere, SpacecraftBox
from fds.models.telemetry import TelemetryGpsPv, TelemetryGpsNmea
from fds.utils.dates import get_datetime
from fds.utils.frames import Frame
from tests import TestModels, _test_initialisation, TestModelsWithContainer, TestUseCases, DATA_DIR
from tests.test_ground_station import TestGroundStation


class TestEventsRequestOrbital(TestModels):
    CLIENT_TYPE = EventsRequestOrbital
    KWARGS = {'event_kinds': ["NODE"], 'start_date': "2023-05-22T00:00:00.000Z", 'nametag': 'TestOrbitalEventRequest'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS, )

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestEventsRequestSensor(TestModels):
    CLIENT_TYPE = EventsRequestSensor
    KWARGS = {
        'event_kinds': ["SUN_IN_FOV"],
        'start_date': "2023-05-22T00:00:00.000Z",
        'ephemerides_step': 60,
        'sensor_axis_in_spacecraft_frame': [1, 0, 0],
        'sensor_field_of_view_half_angle': 45,
        'nametag': 'TestSensorEventRequest'
    }

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS, )

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestEventsRequestStationVisibility(TestModels):
    CLIENT_TYPE = EventsRequestStationVisibility
    gs = GroundStation(**TestGroundStation.KWARGS)
    KWARGS = {'ground_stations': [gs], 'start_date': "2023-05-22T00:00:00.000Z",
              'nametag': 'TestStationVisibilityEventRequest'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    # @unittest.skip("Retrieve returns None from API, to be fixed")
    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestMeasurementsRequestOptical(TestModels):
    CLIENT_TYPE = MeasurementsRequestOptical
    gs = GroundStation(**TestGroundStation.KWARGS)
    KWARGS = {'azimuth_standard_deviation': 1, 'elevation_standard_deviation': 1,
              'ground_station': gs, 'generation_step': 1, 'nametag': 'TestMeasurementsRequestOptical'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestMeasurementsRequestRadar(TestModelsWithContainer):
    CLIENT_TYPE = MeasurementsRequestRadar
    gs = GroundStation(**TestGroundStation.KWARGS)
    KWARGS = {'azimuth_standard_deviation': 1, 'elevation_standard_deviation': 1,
              'ground_station': gs, 'generation_step': 1, 'two_way_measurement': True,
              'range_standard_deviation': 1, 'range_rate_standard_deviation': 1,
              'nametag': 'TestMeasurementsRequestRadar'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestMeasurementsRequestGpsPv(TestModelsWithContainer):
    CLIENT_TYPE = MeasurementsRequestGpsPv
    KWARGS = {'standard_deviation_position': 1,
              'standard_deviation_velocity': 1,
              'generation_step': 1,
              'frame': 'EME2000',
              'nametag': 'TestMeasurementsRequestGpsPv'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestMeasurementsRequestGpsNmea(TestModelsWithContainer):
    CLIENT_TYPE = MeasurementsRequestGpsNmea
    KWARGS = {'standard_deviation_ground_speed': 1, 'standard_deviation_latitude': 1, 'standard_deviation_longitude': 1,
              'standard_deviation_altitude': 1, 'generation_step': 1,
              'nametag': 'TestMeasurementsRequestGpsNmea'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestOemRequest(TestModels):
    CLIENT_TYPE = OemRequest
    KWARGS = {
        'creator': "EXOTRAIL",
        'ephemerides_step': 60,
        'frame': "EME2000",
        'object_id': "00000",
        'object_name': "test-spacecraft",
        'write_acceleration': False,
        'write_covariance': False
    }

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestEphemeridesRequest(TestModels):
    CLIENT_TYPE = EphemeridesRequest
    KWARGS = {'ephemeris_types': ["CARTESIAN", "KEPLERIAN", "POWER", "PROPULSION"],
              'step': 60}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestOrbitExtrapolation(TestUseCases):
    CLIENT_TYPE = OrbitExtrapolation

    def setUp(self) -> None:
        initial_covariance_matrix = CovarianceMatrix.from_diagonal(
            diagonal=(100, 100, 100, 0.1, 0.1, 0.1),
            frame="TNW"
        )

        self.orbit = KeplerianOrbit(
            7000, 0, 90, 1e-3,
            97, 10, kind=OrbitMeanOsculatingType.MEAN, anomaly_kind=PositionAngleType.MEAN,
            date='2023-05-22T00:00:00Z'
        )
        self.spacecraftsphere = SpacecraftSphere.import_from_config_file(
            config_filepath=TestUseCases.CONFIG_TEST_FILEPATH)

        self.spacecraft_box = SpacecraftBox.import_from_config_file(
            config_filepath=TestUseCases.CONFIG_TEST_FILEPATH)
        self.prop_ctx = PropagationContext.import_from_config_file(
            config_filepath=TestUseCases.CONFIG_TEST_FILEPATH)

        self.initial_orbital_state_box = OrbitalState.from_orbit(
            covariance_matrix=initial_covariance_matrix,
            propagation_context=self.prop_ctx,
            spacecraft=self.spacecraft_box,
            orbit=self.orbit
        )

        self.initial_orbital_state_sphere = OrbitalState.from_orbit(
            covariance_matrix=initial_covariance_matrix,
            propagation_context=self.prop_ctx,
            spacecraft=self.spacecraftsphere,
            orbit=self.orbit
        )

        self.kwargs = {'duration': 100,
                       'initial_orbital_state': self.initial_orbital_state_box,
                       'nametag': "TestOrbitExtrapolation"}

        self.TELEMETRY_GPS_PV = TelemetryGpsPv(
            dates=['2023-05-22T00:00:00Z', '2023-05-22T00:01:00Z', '2023-05-22T00:02:00Z', '2023-05-22T00:03:00Z',
                   '2023-05-22T00:04:00Z', '2023-05-22T00:05:00Z', '2023-05-22T00:06:00Z', '2023-05-22T00:07:00Z',
                   '2023-05-22T00:08:00Z', '2023-05-22T00:09:00Z', '2023-05-22T00:10:00Z', '2023-05-22T00:11:00Z',
                   '2023-05-22T00:12:00Z', '2023-05-22T00:13:00Z', '2023-05-22T00:14:00Z', '2023-05-22T00:15:00Z',
                   '2023-05-22T00:16:00Z', '2023-05-22T00:16:40Z'],
            measurements=[
                [147431.48824208856, -840482.558767527, 6943646.545579434,
                 -7429.938086459201, -1309.0700862295932, -2.35390915335785],
                [-298415.3374911323, -917283.9308431068, 6929088.6795984795,
                 -7424.696675997389, -1247.9941486960604, -485.7679579292192],
                [-743018.8445842541, -990263.2395725865, 6885576.114824878,
                 -7388.508029107471, -1181.711836699526, -967.176758504099],
                [-1184525.9588209533, -1059116.2067277294, 6813289.14769968,
                 -7321.518443708431, -1110.4967408227485, -1444.5828451018285],
                [-1621096.159225033, -1123555.5813512665, 6712527.5007401835,
                 -7224.00006158435, -1034.6426978809247, -1916.0040248175444],
                [-2050909.0107929315, -1183312.3238840613, 6583709.181121769,
                 -7096.350019364646, -954.4626965899399, -2379.481119689925],
                [-2472171.6257473934, -1238136.7192306097, 6427368.858800257,
                 -6939.089220456871, -870.2877333591405, -2833.0856075589177],
                [-2883126.042537426, -1287799.422483103, 6244155.809471065,
                 -6752.86067131679, -782.4655900976833, -3274.927254846985],
                [-3282056.4953351007, -1332092.4275940128, 6034831.38371823,
                 -6538.427450367321, -691.3595552734465, -3703.16166823756],
                [-3667296.541051205, -1370829.956100473, 5800266.028745258,
                 -6296.670266873482, -597.3470700484129, -4115.997816269159],
                [-4037236.042697766, -1403849.267173831, 5541435.874468004,
                 -6028.584550526285, -500.81828951836695, -4511.7055111169475],
                [-4390327.942062858, -1431011.3704730852, 5259418.84029748,
                 -5735.277115148812, -402.17456927860735, -4888.622838428625],
                [-4725094.838948842, -1452201.6548126985, 4955390.336468772,
                 -5417.962230696309, -301.82685478156543, -5245.163485881703],
                [-5040135.30229369, -1467330.4109370683, 4630618.5011794865,
                 -5077.957173128193, -200.19399494479808, -5579.82392753347],
                [-5334129.899188706, -1476333.2526704501, 4286459.023161102,
                 -4716.677168836666, -97.70097897900189, -5891.190378160389],
                [-5605846.917223955, -1479171.434403417, 3924349.5667343214,
                 -4335.629754821789, 5.222883170290404, -6177.945406576935],
                [-5854147.703578411, -1475832.0496559024, 3545803.786428277,
                 -3936.4086068951524, 108.14582304684131, -6438.87420013541],
                [-6006154.488424431, -1470179.1781613957, 3285087.8624907224,
                 -3660.9878334442815, 176.5470673777237, -6597.927808533711]],
            frame=Frame.EME2000,
            standard_deviation_velocity=1,
            standard_deviation_position=100)

        self.TELEMETRY_GPS_NMEA = TelemetryGpsNmea(
            dates=[datetime.datetime(2023, 5, 22, 0, 0, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 1, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 2, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 3, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 4, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 5, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 6, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 7, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 8, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 9, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 10, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 11, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 12, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 13, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 14, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 15, 0, 684714,
                                     tzinfo=datetime.timezone.utc),
                   datetime.datetime(2023, 5, 22, 0, 16, 0, 684715,
                                     tzinfo=datetime.timezone.utc)],
            measurements=[[83.0379466750268, 40.88198733200118, 7606.621981082701, 638867.5047940415, 0.0],
                          [82.12292554190742, 12.657629292428558, 7606.224322864173, 638912.4239597841, 0.0],
                          [79.86845086457618, -6.453347295981341, 7609.337053915862, 638688.0714467271, 0.0],
                          [76.95069388133513, -18.022569394014614, 7608.177482229294, 638317.4491379353, 0.0],
                          [73.7207129541341, -25.34687884527845, 7610.598272734814, 637836.2831652411, 0.0],
                          [70.32879231381764, -30.340258925583253, 7611.564318913264, 637501.5795174987, 0.0],
                          [66.85195537984478, -33.971068655795484, 7609.144871579202, 636663.6216733309, 0.0],
                          [63.316683177376156, -36.756696294959305, 7611.793078715922, 636014.6238464187, 0.0],
                          [59.74212952194894, -38.98616822725177, 7612.612535610811, 635486.0362635454, 0.0],
                          [56.14311603231686, -40.83062628765313, 7614.322386603491, 634526.0681804309, 0.0],
                          [52.524973888704196, -42.40319824301523, 7614.647649144307, 633712.9150552289, 0.0],
                          [48.89114914044278, -43.77362801600602, 7614.365456037037, 632787.8276680621, 0.0],
                          [45.24506169855951, -44.99337036488518, 7616.374066143648, 631899.7028169412, 0.0],
                          [41.59047390074882, -46.094326944242134, 7618.895984129033, 631028.7571374972, 0.0],
                          [37.92772963062461, -47.108527741522074, 7619.431313359822, 630291.6075715033, 0.0],
                          [34.257628382807944, -48.048094647240625, 7620.945222326946, 629436.1905695638, 0.0],
                          [30.578887886957055, -48.929188185792526, 7623.208194332948, 629048.5433090786, 0.0]],
            standard_deviation_altitude=100,
            standard_deviation_longitude=0.001,
            standard_deviation_latitude=0.001,
            standard_deviation_ground_speed=1)

        self.ground_stations = [
            GroundStation(
                name="test station",
                latitude=0,
                longitude=0,
                altitude=0,
            ).save(),
            GroundStation(
                name="Iceland",
                latitude=64.9631,
                longitude=-19.0208,
                altitude=0.0,
            ).save(),
            GroundStation(
                name="Azores",
                latitude=37.7412,
                longitude=-25.6751,
                altitude=0.0,
            ).save(),
        ]

    def test_orbit_extrapolation_initialisation(self):
        self._test_initialisation()

    def test_orbit_extrapolation_run(self):
        self._test_client_run()

    # @unittest.skip("Not working at the moment")
    def test_orbit_extrapolation_with_covariance_matrix(self):
        oe_witho_covariance_matrix = OrbitExtrapolation(
            duration=100,
            initial_orbital_state=self.initial_orbital_state_box,
            extrapolate_covariance=False
        )
        res_without = oe_witho_covariance_matrix.run()

        oe_with_covariance_matrix = OrbitExtrapolation(
            duration=100,
            initial_orbital_state=self.initial_orbital_state_box,
            extrapolate_covariance=True
        )
        res_with = oe_with_covariance_matrix.run()
        self.assertTrue(res_without.result.last_orbital_state.covariance_matrix is None)
        self.assertTrue(res_with.result.last_orbital_state.covariance_matrix.client_id is not None)

    def _error_in_orbit_extrapolation_if_covariance_not_in_initial_orbital_state(self):
        orbital_state_without_covariance = OrbitalState.from_orbit(
            orbit=self.orbit,
            propagation_context=self.prop_ctx,
            spacecraft=self.spacecraft_box
        )

        OrbitExtrapolation(
            initial_orbital_state=orbital_state_without_covariance,
            extrapolate_covariance=True
        ).run()

    def test_error_in_orbit_extrapolation_if_covariance_not_in_initial_orbital_state(self):
        self.assertRaises(ValueError, self._error_in_orbit_extrapolation_if_covariance_not_in_initial_orbital_state)

    def test_orbit_extrapolation_with_duration(self):
        oe_only_duration = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=3600 * 10)
        oe_only_duration.run()
        self.assertTrue(oe_only_duration.result.last_orbital_state.mean_orbit.date,
                        (self.orbit.date + timedelta(seconds=3600 * 10)))

    def test_orbit_extrapolation_with_roadmap(self):
        roadmap_final_date = (self.orbit.date +
                              timedelta(seconds=1000))
        attitude_action = ActionAttitude(attitude_mode=AttitudeMode.NORMAL, transition_date=self.orbit.date)
        firing = ActionFiring(
            firing_start_date=self.orbit.date + timedelta(seconds=100),
            duration=100,
            warm_up_duration=30,
            firing_attitude_mode=AttitudeMode.PROGRADE,
            post_firing_attitude_mode=AttitudeMode.PROGRADE
        )
        roadmap = RoadmapFromActions(
            end_date=roadmap_final_date,
            actions=(attitude_action, firing)
        )

        oe_only_roadmap = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            required_orbital_states=RequiredOrbitalStates.ALL,
            roadmap=roadmap
        )
        res = oe_only_roadmap.run().result

        self.assertTrue(res.last_orbital_state.mean_orbit.date == roadmap_final_date)
        self.assertTrue(len(res.orbital_states) == 5)
        self.assertTrue(res.orbital_states[0].date == self.orbit.date)
        self.assertTrue(res.orbital_states[1].date == firing.warm_up_start_date)
        self.assertTrue(res.orbital_states[2].date == firing.firing_start_date)
        self.assertTrue(res.orbital_states[3].date == firing.firing_end_date)
        self.assertTrue(res.orbital_states[4].date == roadmap_final_date)

    def test_orbit_extrapolation_with_roadmap_and_duration(self):
        roadmap_final_date = (self.orbit.date +
                              timedelta(seconds=1000))
        attitude_action = ActionAttitude(attitude_mode=AttitudeMode.NORMAL,
                                         transition_date=self.orbit.date)
        roadmap = RoadmapFromActions(
            end_date=roadmap_final_date,
            actions=(attitude_action,)
        )

        # roadmap shorter than oe
        duration = roadmap.duration + 100
        oe_duration_and_roadmap = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            roadmap=roadmap,
            duration=duration)
        oe_duration_and_roadmap.run()

        correct_final_date = max(roadmap_final_date, self.orbit.date + timedelta(seconds=duration))
        self.assertTrue(oe_duration_and_roadmap.result.last_orbital_state.mean_orbit.date == correct_final_date)

    def _roadmap_and_duration_error(self):
        roadmap_final_date = (self.orbit.date +
                              timedelta(seconds=1000))
        attitude_action = ActionAttitude(attitude_mode=AttitudeMode.NORMAL,
                                         transition_date=self.orbit.date)
        roadmap = RoadmapFromActions(start_date=attitude_action.transition_date,
                                     end_date=roadmap_final_date,
                                     actions=(attitude_action,))

        # roadmap longer than oe
        duration = roadmap.duration - 100
        oe_duration_and_roadmap = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_sphere,
            roadmap=roadmap,
            duration=duration)
        oe_duration_and_roadmap.run()

    def test_orbit_extrapolation_with_roadmap_and_duration_error(self):
        self.assertRaises(ValueError, self._roadmap_and_duration_error)

    def _roadmap_firing_and_spacecraft_thruster_error(self):
        thruster_max_duration = self.initial_orbital_state_box.spacecraft.thruster.maximum_thrust_duration

        firing = ActionFiring(
            firing_start_date=self.orbit.date + timedelta(seconds=100),
            duration=thruster_max_duration + 100,
            warm_up_duration=30,
            firing_attitude_mode=AttitudeMode.PROGRADE,
            post_firing_attitude_mode=AttitudeMode.PROGRADE
        )
        roadmap = RoadmapFromActions(
            start_date=self.orbit.date,
            actions=(firing,)
        )

        oe_firing_and_roadmap = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            roadmap=roadmap
        )
        oe_firing_and_roadmap.run()

    def test_orbit_extrapolation_with_roadmap_firing_and_spacecraft_thruster_error(self):
        self.assertRaises(ValueError, self._roadmap_firing_and_spacecraft_thruster_error)

    def test_orbit_extrapolation_with_oem_request(self):
        ATOL_COVARIANCE = 1e-3
        oem_request = OemRequest(
            'Exotrail',
            3600,
            Frame.ECI,
            "0000",
            "my-spacecraft",
            True,
            True
        )

        oe_with_oem_request = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=3600 * 10,
            orbit_data_message_request=oem_request,
            extrapolate_covariance=True
        )
        oe_with_oem_request.run()
        results = oe_with_oem_request.result

        test_file_path = DATA_DIR / f"orbit_extrapolation/oem_test_{oem_request.frame.value.lower()}.txt"
        with open(test_file_path, 'r') as f:
            oem_test = f.read()
        oem_test = oem_test.split('\n')
        oem_test.pop(1)  # remove date line (creation date is always different)
        results_orbit_data_message = results.orbit_data_message.split('\n')
        results_orbit_data_message.pop(1)  # remove date line (creation date is always different)

        for i in range(15, 26):  # Compare positions and velocities
            oem_line = oem_test[i].split()
            oem_line = [float(x) for x in oem_line[1:]]
            results_line = results_orbit_data_message[i].split()
            results_line = [float(x) for x in results_line[1:]]
            for x1, x2 in zip(oem_line[:3], results_line[:3]):
                self.assertTrue(self.is_value_close(x1, x2, atol=self.ATOL_POSITION))
            for x1, x2 in zip(oem_line[3:], results_line[3:]):
                self.assertTrue(self.is_value_close(x1, x2, atol=self.ATOL_VELOCITY))

        for i in range(27, 105):
            oem_line = oem_test[i].split()
            if oem_line[0] != "EPOCH":
                oem_line = [float(x) for x in oem_line[1:]]
                results_line = results_orbit_data_message[i].split()
                results_line = [float(x) for x in results_line[1:]]
                for x1, x2 in zip(oem_line, results_line):
                    self.assertTrue(abs(x1 - x2) < ATOL_COVARIANCE)

    def test_orbit_extrapolation_with_pv_measurements(self):
        measurement_request_pv = MeasurementsRequestGpsPv(
            standard_deviation_position=self.TELEMETRY_GPS_PV.standard_deviation.position,
            standard_deviation_velocity=self.TELEMETRY_GPS_PV.standard_deviation.velocity,
            frame=Frame.EME2000,
            generation_step=60)

        oe_with_pv_meas_request = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=1000,
            measurements_request=measurement_request_pv)
        oe_with_pv_meas_request.run()

        result_pv = oe_with_pv_meas_request.result

        self.assertTrue(self.TELEMETRY_GPS_PV.is_same_object_as(result_pv.computed_measurements[0], check_id=False))

    def test_orbit_extrapolation_with_nmea_measurements(self):
        measurement_request_nmea = MeasurementsRequestGpsNmea(
            standard_deviation_ground_speed=self.TELEMETRY_GPS_NMEA.standard_deviation.ground_speed,
            standard_deviation_altitude=self.TELEMETRY_GPS_NMEA.standard_deviation.altitude,
            standard_deviation_longitude=self.TELEMETRY_GPS_NMEA.standard_deviation.longitude,
            standard_deviation_latitude=self.TELEMETRY_GPS_NMEA.standard_deviation.latitude,
            generation_step=60
        )

        oe_with_nmea_meas_request = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=1000,
            measurements_request=measurement_request_nmea)
        oe_with_nmea_meas_request.run()

        result_nmea = oe_with_nmea_meas_request.result.computed_measurements[0]

        self.assertTrue(self.TELEMETRY_GPS_NMEA.is_same_object_as(result_nmea, check_id=False))

    def test_orbit_extrapolation_with_station_visibility_event(self):

        station_visibility_events_request = EventsRequestStationVisibility(
            ground_stations=[self.ground_stations[0]],
            start_date=self.orbit.date,
        )
        station_visibility_events_request.save()

        oe_with_station_visibility_event = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=86400 / 2,
            station_visibility_events_request=station_visibility_events_request
        )

        oe_with_station_visibility_event.run()

        result_station_visibility_event = oe_with_station_visibility_event.result

        station_visibility_event_list = [
            StationVisibilityEvent(
                end_date=get_datetime("2023-05-22 07:47:59.609726+00:00"),
                start_date=get_datetime("2023-05-22 07:37:36.834664+00:00"),
                ground_station=self.ground_stations[0]),
            StationVisibilityEvent(
                end_date=get_datetime("2023-05-22 09:24:58.025851+00:00"),
                start_date=get_datetime("2023-05-22 09:12:43.475980+00:00"),
                ground_station=self.ground_stations[0])
        ]

        for event, event_result in zip(station_visibility_event_list,
                                       result_station_visibility_event.station_visibility_events):
            self.assertTrue(self.is_datetime_close(event.start_date, event_result.start_date))
            self.assertTrue(self.is_datetime_close(event.end_date, event_result.end_date))
            self.assertTrue(event.ground_station.is_same_object_as(event_result.ground_station))

    def test_orbit_extrapolation_station_event_grouping_intersect(self):
        events_intersect = [
            {'groundStationId': self.ground_stations[1].client_id,
             'utcDate': '2000-01-01T00:00:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_ENTER},
            {'groundStationId': self.ground_stations[2].client_id,
             'utcDate': '2000-01-01T00:01:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_ENTER},
            {'groundStationId': self.ground_stations[2].client_id,
             'utcDate': '2000-01-01T00:02:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_EXIT},
            {'groundStationId': self.ground_stations[1].client_id,
             'utcDate': '2000-01-01T00:03:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_EXIT}
        ]

        object_events_intersect = [
            StationVisibilityEvent(
                start_date=get_datetime("2000-01-01T00:00:00.000000Z"),
                end_date=get_datetime("2000-01-01T00:03:00.000000Z"),
                ground_station=self.ground_stations[1]),
            StationVisibilityEvent(
                start_date=get_datetime("2000-01-01T00:01:00.000000Z"),
                end_date=get_datetime("2000-01-01T00:02:00.000000Z"),
                ground_station=self.ground_stations[2])
        ]

        _, _, station, _ = ResultOrbitExtrapolation._group_events_into_objects(
            events_intersect)

        for event, event_result in zip(object_events_intersect, station):
            self.assertTrue(event.start_date == event_result.start_date)
            self.assertTrue(event.end_date == event_result.end_date)
            self.assertTrue(event.ground_station.is_same_object_as(event_result.ground_station))

    def test_orbit_extrapolation_station_event_grouping_no_start_no_exit(self):
        events_no_start_no_exit = [
            {'groundStationId': self.ground_stations[2].client_id,
             'utcDate': '2000-01-01T00:01:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_ENTER},
            {'groundStationId': self.ground_stations[2].client_id,
             'utcDate': '2000-01-01T00:02:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_EXIT},
            {'groundStationId': self.ground_stations[1].client_id,
             'utcDate': '2000-01-01T00:03:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_EXIT},
            {'groundStationId': self.ground_stations[1].client_id,
             'utcDate': '2000-01-01T00:04:00.000000Z',
             'eventType': EventWithDuration.EventKind.STATION_ENTER}
        ]

        object_events_no_start_no_exit = [
            StationVisibilityEvent(
                start_date=None,
                end_date=get_datetime("2000-01-01T00:03:00.000000Z"),
                ground_station=self.ground_stations[1]),
            StationVisibilityEvent(
                start_date=get_datetime("2000-01-01T00:01:00.000000Z"),
                end_date=get_datetime("2000-01-01T00:02:00.000000Z"),
                ground_station=self.ground_stations[2]),
            StationVisibilityEvent(
                start_date=get_datetime("2000-01-01T00:04:00.000000Z"),
                end_date=None,
                ground_station=self.ground_stations[1])
        ]

        _, _, station, _ = ResultOrbitExtrapolation._group_events_into_objects(
            events_no_start_no_exit)

        for event, event_result in zip(object_events_no_start_no_exit, station):
            self.assertTrue(event.start_date == event_result.start_date)
            self.assertTrue(event.end_date == event_result.end_date)
            self.assertTrue(event.ground_station.is_same_object_as(event_result.ground_station))

    def test_orbit_extrapolation_with_orbital_events(self):
        orbital_events = EventsRequestOrbital(
            start_date=self.orbit.date,
            event_kinds=[EventsRequestOrbital.EventKind.NODE, EventsRequestOrbital.EventKind.ECLIPSE]
        )

        oe_with_orbital_events = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=3600,
            orbital_events_request=orbital_events)

        oe_with_orbital_events.run()

        result_orbital_events = oe_with_orbital_events.result

        orbital_events_list = [
            OrbitalEvent(
                date=get_datetime("2023-05-22 00:24:16.989954+00:00"),
                kind=OrbitalEvent.EventKind.DESCENDING_NODE)]
        eclipse_events_list = [
            EclipseEvent(
                end_date=get_datetime("2023-05-22 00:44:12.386461+00:00"),
                start_date=get_datetime("2023-05-22 00:16:25.512540+00:00"),
            )]

        for event, event_result in zip(orbital_events_list,
                                       result_orbital_events.orbital_events):
            self.assertTrue(self.is_datetime_close(event.date, event_result.date))
            self.assertTrue(event.kind == event_result.kind)

        for event, event_result in zip(eclipse_events_list,
                                       result_orbital_events.eclipse_events):
            self.assertTrue(self.is_datetime_close(event.start_date, event_result.start_date))
            self.assertTrue(self.is_datetime_close(event.end_date, event_result.end_date))

    def test_orbit_extrapolation_with_sensor_events(self):
        sensor_events_request = EventsRequestSensor(
            start_date=self.orbit.date,
            event_kinds=[EventsRequestSensor.EventKind.SUN_IN_FOV],
            sensor_axis_in_spacecraft_frame=[0, 0, -1],
            sensor_field_of_view_half_angle=20,
            ephemerides_step=60  # Not used in this test
        )

        attitude_actions_list = [
            ActionAttitude(attitude_mode=AttitudeMode.PROGRADE,
                           transition_date=get_datetime("2023-05-22 00:00:00+00:00")),
            ActionAttitude(attitude_mode=AttitudeMode.SUN_POINTING,
                           transition_date=get_datetime("2023-05-22 00:01:00+00:00")),
            ActionAttitude(attitude_mode=AttitudeMode.PROGRADE,
                           transition_date=get_datetime("2023-05-22 00:03:00+00:00")),
            ActionAttitude(attitude_mode=AttitudeMode.PROGRADE,
                           transition_date=get_datetime("2023-05-22 00:04:00+00:00")),
        ]

        roadmap_from_actions = RoadmapFromActions(
            start_date=attitude_actions_list[0].transition_date,
            end_date=attitude_actions_list[-1].transition_date,
            actions=attitude_actions_list
        )

        duration = (attitude_actions_list[-1].transition_date - attitude_actions_list[
            0].transition_date).total_seconds()

        oe_with_sensor_events = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=duration,
            roadmap=roadmap_from_actions,
            sensor_events_request=sensor_events_request)

        oe_with_sensor_events.run()

        result_orbital_events = oe_with_sensor_events.result

        sensor_events_list = [
            SensorEvent(
                start_date=get_datetime("2023-05-22 00:01:00+00:00"),
                end_date=get_datetime("2023-05-22 00:03:00+00:00"),
                kind=SensorEvent.EventKind.SUN_IN_FOV),
            SensorEvent(
                start_date=get_datetime("2023-05-22 00:04:00+00:00"),
                end_date=None,
                kind=SensorEvent.EventKind.SUN_IN_FOV)
        ]

        for event, event_result in zip(sensor_events_list,
                                       result_orbital_events.sensor_events):
            self.assertTrue(self.is_datetime_close(event.start_date, event_result.start_date))
            self.assertTrue(self.is_datetime_close(event.end_date, event_result.end_date))
            self.assertTrue(event.kind == event_result.kind)

    def test_orbit_extrapolation_event_export(self):
        station_visibility_events_request = EventsRequestStationVisibility(
            ground_stations=[self.ground_stations[1], self.ground_stations[2]],
            start_date=self.orbit.date,
        )

        orbital_events_request = EventsRequestOrbital(
            start_date=self.orbit.date,
            event_kinds=[EventsRequestOrbital.EventKind.NODE, EventsRequestOrbital.EventKind.ECLIPSE]
        )
        sensor_axis = self.initial_orbital_state_box.spacecraft.solar_array.normal_in_satellite_frame

        sensor_events_request = EventsRequestSensor(
            start_date=self.orbit.date,
            event_kinds=[EventsRequestSensor.EventKind.SUN_IN_FOV],
            sensor_axis_in_spacecraft_frame=sensor_axis,
            sensor_field_of_view_half_angle=20,
            ephemerides_step=60  # Not used in this test
        )

        attitude_actions_list = [
            ActionAttitude(attitude_mode=AttitudeMode.PROGRADE,
                           transition_date=get_datetime("2023-05-22 00:00:00+00:00")),
            ActionAttitude(attitude_mode=AttitudeMode.SUN_POINTING,
                           transition_date=get_datetime("2023-05-22 01:00:00+00:00")),
            ActionAttitude(attitude_mode=AttitudeMode.PROGRADE,
                           transition_date=get_datetime("2023-05-22 02:00:00+00:00")),
            ActionAttitude(attitude_mode=AttitudeMode.PROGRADE,
                           transition_date=get_datetime("2023-05-22 04:00:00+00:00")),
        ]

        roadmap_from_actions = RoadmapFromActions(
            actions=attitude_actions_list,
            start_date=attitude_actions_list[0].transition_date,
            end_date=attitude_actions_list[-1].transition_date
        )

        oe = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            station_visibility_events_request=station_visibility_events_request,
            orbital_events_request=orbital_events_request,
            sensor_events_request=sensor_events_request,
            roadmap=roadmap_from_actions
        )

        result = oe.run().result

        data_df = result.export_event_timeline_data()
        data_gantt = result.export_event_gantt_data()

        data_df_with_string_values = [
            {k: str(v) for k, v in event.items()} for event in data_df
        ]
        data_gantt_with_string_values = [
            {k: str(v) for k, v in event.items()} for event in data_gantt
        ]

        json_filepath = DATA_DIR / 'orbit_extrapolation/events_df.json'
        with open(json_filepath, 'r') as f:
            data_df_test = json.load(f)

        json_filepath = DATA_DIR / 'orbit_extrapolation/events_gantt.json'
        with open(json_filepath, 'r') as f:
            data_gantt_test = json.load(f)

        # Remove ground_station_id column from lists to compare (it changes at each test run)
        for event in data_df_with_string_values:
            event.pop('ground_station_id')
        for event in data_df_test:
            event.pop('ground_station_id')
        for event in data_gantt_with_string_values:
            event.pop('ground_station_id')
        for event in data_gantt_test:
            event.pop('ground_station_id')

        for event, event_test in zip(data_df_with_string_values, data_df_test):
            for k, v in event.items():
                if k == 'date':
                    self.is_string_date_close(v, event_test[k])
                else:
                    self.assertTrue(v == event_test[k])

        for event, event_test in zip(data_gantt_with_string_values, data_gantt_test):
            for k, v in event.items():
                if k in ('start_date', 'end_date'):
                    self.is_string_date_close(v, event_test[k])
                elif k == 'duration':
                    self.is_value_close(v, event_test[k], atol=self.ATOL_TIME)
                else:
                    is_true = v == event_test[k]
                    if not is_true:
                        print(k, v, event_test[k])
                    self.assertTrue(is_true)

    def test_orbit_extrapolation_with_ephemerides(self):
        import csv
        from pathlib import Path
        import numpy as np

        def compare_csv_to_list(csv_file: Path, list_to_compare: list[dict]):
            are_same = True
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    for d in list_to_compare:
                        if all(row[key] == str(value) for key, value in d.items()):
                            are_same *= True
                        if not are_same:
                            # verify if there are nan values that are not saved
                            for key, value in d.items():
                                if row[key] == 'nan' and np.isnan(value):
                                    are_same = True
                                    break
            return are_same

        ephemerides_request = EphemeridesRequest(
            ephemeris_types=[EphemeridesRequest.EphemerisType.CARTESIAN, EphemeridesRequest.EphemerisType.KEPLERIAN,
                             EphemeridesRequest.EphemerisType.POWER, EphemeridesRequest.EphemerisType.PROPULSION,
                             EphemeridesRequest.EphemerisType.ATTITUDE_QUATERNIONS,
                             EphemeridesRequest.EphemerisType.ATTITUDE_EULER_ANGLES],
            step=100
        )

        oe_with_ephemerides = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state_box,
            duration=1000,
            ephemerides_request=ephemerides_request
        )

        oe_with_ephemerides.run()

        result = oe_with_ephemerides.result

        self.assertTrue(result.ephemerides.cartesian is not None)
        self.assertTrue(result.ephemerides.keplerian is not None)
        self.assertTrue(result.ephemerides.power is not None)
        self.assertTrue(result.ephemerides.propulsion is not None)
        self.assertTrue(result.ephemerides.attitude_quaternions is not None)
        self.assertTrue(result.ephemerides.attitude_euler_angles is not None)

        # export ephemerides and save them in a file
        cartesian = result.export_cartesian_ephemeris()
        keplerian = result.export_keplerian_ephemeris()
        power = result.export_power_ephemeris()
        propulsion = result.export_propulsion_ephemeris()
        quaternion = result.export_quaternion_ephemeris()
        euler_angles = result.export_euler_angles_ephemeris()

        # load test data from data/orbit_extrapolation/ephemerides
        self.assertTrue(compare_csv_to_list(DATA_DIR / 'orbit_extrapolation/ephemerides/cartesian.csv', cartesian))
        self.assertTrue(compare_csv_to_list(DATA_DIR / 'orbit_extrapolation/ephemerides/keplerian.csv', keplerian))
        self.assertTrue(compare_csv_to_list(DATA_DIR / 'orbit_extrapolation/ephemerides/power.csv', power))
        self.assertTrue(compare_csv_to_list(DATA_DIR / 'orbit_extrapolation/ephemerides/propulsion.csv', propulsion))
        self.assertTrue(compare_csv_to_list(DATA_DIR / 'orbit_extrapolation/ephemerides/quaternions.csv', quaternion))
        self.assertTrue(
            compare_csv_to_list(DATA_DIR / 'orbit_extrapolation/ephemerides/euler_angles.csv', euler_angles)
        )
