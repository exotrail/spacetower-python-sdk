import datetime
import unittest
from datetime import datetime, UTC, timedelta, timezone

import numpy as np

import fds.utils.dict as utils
import fds.utils.frames as frames
import fds.utils.geometry as g
import fds.utils.orbital_mechanics as orb_mech_utils
from fds.constants import EARTH_GRAV_CONSTANT
from fds.utils import math
from fds.utils.dates import get_datetime, convert_date_to_utc, datetime_to_iso_string, \
    filter_sequence_with_minimum_time_step, DateRange


class TestDictUtils(unittest.TestCase):

    def test_compare_dicts(self):
        blueprint = {
            "key1": {
                "key1_1": 1,
                "key1_2": 2
            },
            "key2": {
                "key2_1": 1,
                "key2_2": 2
            },
        }
        config = {
            "key1": {
                "key1_1": 1,
                "key1_2": 2
            },
            "key2": {
                "key2_1": 3,
                "key2_2": 4
            },
        }

        self.assertTrue(utils.compare_two_dicts(config, blueprint) is None)

        config = {
            "key1": {
                "key1_1": 1,
                "key1_2": 2
            },
        }

        self.assertTrue(utils.compare_two_dicts(config, blueprint) is None)

        config = {
            "key1": {
                "key1_1": 1,
                "key1_2": 2
            },
            "key2": {
                "key2_1": 1,
                "key2_2": 2
            },
            "key3": {
                "key3_1": 1,
                "key3_2": 2
            },
        }

        self.assertRaises(ValueError, utils.compare_two_dicts, config, blueprint)

        config = {
            "key1": {
                "key1_1": 1,
                "key1_2": 2
            },
            "key2": {
                "key2_1": 1,
                "key2_2": 2,
                "key2_3": 3
            },
        }

        self.assertRaises(ValueError, utils.compare_two_dicts, config, blueprint)

        config = {
            "key1": {
                "key1_1": 1,
                "key1_2": 2
            },
            "key2": {
                "key2_1": 1,
            },
        }

        self.assertRaises(ValueError, utils.compare_two_dicts, config, blueprint)

    def test_get_datetime(self):
        assert get_datetime("2021-03-04T00:00:00Z") == datetime(2021, 3, 4, 0, 0,
                                                                tzinfo=UTC)
        assert (get_datetime(datetime(2021, 3, 4, 0, 0, tzinfo=UTC))
                == datetime(2021, 3, 4, 0, 0, tzinfo=UTC))
        assert get_datetime(None) is None


class TestDatesUtils(unittest.TestCase):

    def test_convert_datetime_time_zone_to_utc(self):
        date_utc = datetime(2021, 3, 4, 0, 0, tzinfo=timezone.utc)
        date_no_tz = datetime(2021, 3, 4, 0, 0)
        new_date = convert_date_to_utc(date_no_tz)
        assert new_date == date_utc

        date_wrong_tz = datetime(2021, 3, 4, 1, 0, tzinfo=timezone(timedelta(hours=1)))
        new_date = convert_date_to_utc(date_wrong_tz)
        assert new_date == date_utc

    def test_datetime_to_iso_string(self):
        assert datetime_to_iso_string(
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC)
        ) == "2021-03-04T00:00:00.000000Z"
        assert datetime_to_iso_string(None) is None

    def test_filter_sequence_with_minimum_time_step(self):
        initial_sequence = [1, 2, 3, 4, 5]
        dates = [
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 1, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 2, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 3, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 4, tzinfo=UTC)
        ]
        min_step = 120
        assert filter_sequence_with_minimum_time_step(initial_sequence, dates, min_step) == [1, 3, 5]

    def test_filter_sequence_with_minimum_time_step_unsorted_dates(self):
        initial_sequence = [1, 2, 3, 4, 5]
        dates = [
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 2, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 1, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 3, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 4, tzinfo=UTC)
        ]
        min_step = 120
        self.assertRaises(ValueError, filter_sequence_with_minimum_time_step, initial_sequence, dates, min_step)

    def test_filter_sequence_with_minimum_time_step_negative_step(self):
        initial_sequence = [1, 2, 3, 4, 5]
        dates = [
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 1, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 2, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 3, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 4, tzinfo=UTC)
        ]
        min_step = -1
        self.assertRaises(ValueError, filter_sequence_with_minimum_time_step, initial_sequence, dates, min_step)

    def test_filter_sequence_with_minimum_time_step_zero_step(self):
        initial_sequence = [1, 2, 3, 4, 5]
        dates = [
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
            datetime(2021, 3, 4, 0, 0, tzinfo=UTC)
        ]
        min_step = 0
        self.assertTrue(filter_sequence_with_minimum_time_step(initial_sequence, dates, min_step) == initial_sequence)

    def test_date_ranges(self):
        drange1 = [datetime(2021, 3, 4, 0, 0, tzinfo=UTC),
                   datetime(2021, 3, 4, 0, 1, tzinfo=UTC)]
        drange2 = ["2021-03-04T00:00:00Z", "2021-03-04T00:01:00Z"]

        drange_dict1 = {"start": drange1[0], "end": drange1[1]}
        drange_dict2 = {"start": drange1[0], "end": drange1[1]}

        dr1 = DateRange.from_list(drange1)
        dr1_dict = DateRange.from_dict(drange_dict1)
        dr1_list = DateRange.from_input(drange1)

        dr2 = DateRange.from_list(drange2)
        dr2_dict = DateRange.from_dict(drange_dict2)
        dr2_list = DateRange.from_input(drange2)

        assert dr1 == dr1_dict == dr1_list
        assert dr2 == dr2_dict == dr2_list
        assert dr1 == dr2
        assert dr1.duration_seconds == 60 == dr2.duration_seconds

        # test date range creations
        dr3 = DateRange.from_end_and_duration(drange1[1], 60)
        assert dr3 == dr1

        dr4 = DateRange.from_start_and_duration(drange1[0], 60)
        assert dr4 == dr1

        # test repr and str
        assert str(dr1) == "2021-03-04 00:00:00+00:00 to 2021-03-04 00:01:00+00:00 (0:01:00)"
        assert repr(dr1) == "2021-03-04 00:00:00+00:00 to 2021-03-04 00:01:00+00:00 (0:01:00)"

        # test invalid date range
        self.assertRaises(ValueError, DateRange, drange1[1], drange1[0])
        self.assertRaises(ValueError, DateRange.from_end_and_duration, drange1[1], -60)

        # test union
        dr5 = DateRange(drange1[0], drange1[1])
        dr6 = DateRange(drange1[1] - timedelta(seconds=30), drange1[1] + timedelta(seconds=30))

        dr7 = dr5.get_union(dr6)
        assert dr7.start == dr5.start
        assert dr7.end == dr6.end

        dr8 = dr6.get_intersection(dr5)
        assert dr8.start == dr6.start
        assert dr8.end == dr5.end

        # test booleans
        dr9 = DateRange(drange1[1], drange1[1] + timedelta(seconds=30))
        assert dr5.is_adjacent(dr9)
        assert not dr5.is_adjacent(dr6)
        assert dr5.is_overlapping(dr6)
        assert not dr5.is_overlapping(dr9)
        assert dr5.is_inside(dr7)
        assert dr7.is_containing(dr5)

        date = datetime(2021, 3, 4, 0, 0, second=30, tzinfo=UTC)
        assert dr5.contains(date)


class TestMath(unittest.TestCase):

    def test_modulo_with_range(self):
        x_original = np.random.rand(100) * 2 * np.pi
        x_min = -np.pi
        x_max = np.pi
        for x in x_original:
            x_clip = math.modulo_with_range(x, x_min, x_max)
            x_reconstruct = x_clip + (x_max - x_min) * np.floor((x - x_min) / (x_max - x_min))
            self.assertTrue(x_min <= x_clip <= x_max)
            self.assertTrue(np.isclose(x, x_reconstruct))

        # check if x_original is the max, it should clip to the min
        x = x_max
        x_clip = math.modulo_with_range(x, x_min, x_max)
        self.assertTrue(x_clip == x_min)

    def test_modulo_with_range_border_cases(self):
        # Test specific cases where the value is close to the limits
        x_min = 1
        x_close_to_min = 1e-15 + x_min
        x_close_to_min_neg = -1e-15 + x_min
        x_clip = math.modulo_with_range(x_close_to_min, x_min, 100)
        self.assertTrue(np.isclose(x_clip, x_min))
        x_clip_neg = math.modulo_with_range(x_close_to_min_neg, x_min, 100)
        self.assertTrue(np.isclose(x_clip_neg, x_min))

        x_max = 100
        x_close_to_max = x_max - 1e-15
        x_close_to_max_but_still_max = x_max - 1e-5
        x_clip = math.modulo_with_range(x_close_to_max, x_min, x_max)
        x_clip_still_max = math.modulo_with_range(x_close_to_max_but_still_max, x_min, x_max)
        self.assertTrue(np.isclose(x_clip, x_min))
        self.assertTrue(np.isclose(x_clip_still_max, x_max))

    def test_pmodulo(self):
        x_original = (np.random.rand(100) - 0.5)
        m = 1
        for x in x_original:
            sign_x = np.sign(x)
            x_clip = math.pmodulo(x, m)
            x_reconstruct = x_clip - m * np.floor(x / m) * sign_x
            self.assertTrue(0 <= x_clip <= m)
            self.assertTrue(np.isclose(x, x_reconstruct))


class TestOrbMechUtils(unittest.TestCase):
    def setUp(self):
        self.eccentricity = 0.37255
        self.inclination = np.radians(51.638)
        self.argument_of_perigee = np.radians(90)
        self.true_anomaly = np.radians(120)
        self.eccentric_anomaly = 1.7281
        self.mean_anomaly = 1.3601

        self.kep_to_tnw_mat = np.array(
            [[0., 1.95577826, 0., 1., 0.62062788, 1.],
             [-1., 0.20912401, 0., 0., 0., 0.],
             [0., 0., 0.20912401, 0., 0.766768, 0.],
             [-0.5, 0.20912401, 0., 0., 0., 0.],
             [0., 0.97788913, 0., 1., 0.62062788, 1.],
             [0., 0., -0.97788913, 0., 0.16397523, 0.]]
        )

        self.p_test = np.array([4.243401159045579E-10, 6001556.04822616, 3464999.9999999995]) / 1e3
        self.v_test = np.array([-7621.894924414581, 4.0417965144985753E-13, 2.333532305655443E-13]) / 1e3

    def test_mean_anomaly_from_eccentric_anomaly(self):
        assert np.isclose(
            orb_mech_utils.mean_anomaly_from_eccentric_anomaly(self.eccentricity, self.eccentric_anomaly),
            self.mean_anomaly,
            rtol=1e-4
        )

    def test_mean_anomaly_from_true_anomaly(self):
        assert np.isclose(
            orb_mech_utils.mean_anomaly_from_true_anomaly(self.eccentricity, self.true_anomaly),
            self.mean_anomaly,
            rtol=1e-4
        )

    def test_eccentric_anomaly_from_true_anomaly(self):
        assert np.isclose(
            orb_mech_utils.eccentric_anomaly_from_true_anomaly(self.eccentricity, self.true_anomaly),
            self.eccentric_anomaly,
            rtol=1e-4
        )

    def test_eccentric_anomaly_from_mean_anomaly(self):
        assert np.isclose(
            orb_mech_utils.eccentric_anomaly_from_mean_anomaly(self.eccentricity, self.mean_anomaly),
            self.eccentric_anomaly,
            rtol=1e-4
        )

    def test_true_anomaly_from_eccentric_anomaly(self):
        assert np.isclose(
            orb_mech_utils.true_anomaly_from_eccentric_anomaly(self.eccentricity, self.eccentric_anomaly),
            self.true_anomaly,
            rtol=1e-4
        )

    def test_true_anomaly_from_mean_anomaly(self):
        assert np.isclose(
            orb_mech_utils.true_anomaly_from_mean_anomaly(self.eccentricity, self.mean_anomaly),
            self.true_anomaly,
            rtol=1e-4
        )

    def test_true_to_mean_to_true(self):
        true_anomalies = np.random.rand(100) * 2 * np.pi
        eccentricities = np.random.rand(100) * 0.9
        for true_anomaly, eccentricity in zip(true_anomalies, eccentricities):
            mean_anomaly = orb_mech_utils.mean_anomaly_from_true_anomaly(eccentricity, true_anomaly)
            true_anomaly_from_mean = orb_mech_utils.true_anomaly_from_mean_anomaly(eccentricity, mean_anomaly)
            self.assertTrue(np.isclose(math.modulo_with_range(true_anomaly, -np.pi, np.pi),
                                       true_anomaly_from_mean))

    def test_true_to_eccentric_to_true(self):
        true_anomalies = np.random.rand(100) * 2 * np.pi
        eccentricities = np.random.rand(100) * 0.9
        for true_anomaly, eccentricity in zip(true_anomalies, eccentricities):
            eccentric_anomaly = orb_mech_utils.eccentric_anomaly_from_true_anomaly(eccentricity, true_anomaly)
            true_anomaly_from_eccentric = orb_mech_utils.true_anomaly_from_eccentric_anomaly(eccentricity,
                                                                                             eccentric_anomaly)
            self.assertTrue(
                np.isclose(math.modulo_with_range(true_anomaly, -np.pi, np.pi), true_anomaly_from_eccentric)
            )

    def test_mean_to_eccentric_to_mean(self):
        mean_anomalies = np.random.rand(100) * 2 * np.pi
        eccentricities = np.random.rand(100) * 0.9
        for mean_anomaly, eccentricity in zip(mean_anomalies, eccentricities):
            eccentric_anomaly = orb_mech_utils.eccentric_anomaly_from_mean_anomaly(eccentricity, mean_anomaly)
            mean_anomaly_from_eccentric = orb_mech_utils.mean_anomaly_from_eccentric_anomaly(eccentricity,
                                                                                             eccentric_anomaly)
            self.assertTrue(
                np.isclose(mean_anomaly, mean_anomaly_from_eccentric)
            )

    def test_get_delta_cartesian_tnw_between_two_keplerian_states(self):
        kep1 = np.array([7000, 0.01, np.radians(30), np.radians(90), 0, 0])
        kep2 = np.array([7000, 0.01, np.radians(30), np.radians(90), 0, 0])
        delta = orb_mech_utils.get_delta_cartesian_tnw_between_two_keplerian_states(*kep1, *kep2)

        assert np.allclose(delta, np.zeros(6), rtol=1e-4)

        kep1 = np.array([7000, 0.0, np.radians(30), np.radians(90), 0, 0])
        kep2 = np.array([6950, 0.0, np.radians(30), np.radians(90), 0, 0])
        delta = orb_mech_utils.get_delta_cartesian_tnw_between_two_keplerian_states(*kep1, *kep2)

        new_orbital_speed = np.sqrt(EARTH_GRAV_CONSTANT / kep2[0])
        delta_speed = new_orbital_speed - np.sqrt(EARTH_GRAV_CONSTANT / kep1[0])
        delta_test = np.array([0.0, 50, 0.0, delta_speed, 0.0, 0.0])
        assert np.allclose(delta, delta_test, rtol=1e-4)

        kep1 = np.array([6892.722641687978,
                         0.0010049055093967285,
                         np.radians(97.4724721856229),
                         np.radians(195.30478309196604),
                         np.radians(129.83969435709736),
                         np.radians(215.4406578560032)])
        kep2 = np.array([6893.0239146876565,
                         0.0009659953574527639,
                         np.radians(97.47002778594978),
                         np.radians(197.30903365677037),
                         np.radians(129.8396200474828),
                         np.radians(213.44027831777225)])

        delta = orb_mech_utils.get_delta_cartesian_tnw_between_two_keplerian_states(*kep1, *kep2)
        delta_test = np.array([1.1613284, -0.21466292, -0.22209321, -0.0000697311, 0.0008968572, -0.0002127992])

        assert np.allclose(delta, delta_test, rtol=1e-4)

    def test_kep_to_car(self):
        kep = np.array([7000, 0.01, np.radians(30), np.radians(90), 0, 0])
        x = orb_mech_utils.kep_to_car(*kep)

        assert np.allclose(x[:3], self.p_test, rtol=1e-4)
        assert np.allclose(x[3:], self.v_test, rtol=1e-4)

    def test_compute_delta_v(self):
        initial_mass = 1000
        final_mass = 900
        isp = 300
        delta_v = orb_mech_utils.compute_delta_v_with_rocket_equation(isp, initial_mass, final_mass)
        self.assertTrue(np.isclose(delta_v, 309.9701))


class TestGeomUtils(unittest.TestCase):
    def setUp(self):
        self.v_unit_test = np.array([0.26726124, 0.53452248, 0.80178373])

    def test_unit_vector(self):
        v_test = np.array([0.1, 0.2, 0.3])
        v_unit = g.unit_vector(v_test)
        assert np.allclose(v_unit, self.v_unit_test, rtol=1e-4)

    def test_check_vector_length(self):
        v = np.array([1, 2, 3])
        self.assertTrue(g.check_vector_shape(v, (3,)) is None)
        self.assertRaises(ValueError, g.check_vector_shape, v, 4)

    def test_convert_to_numpy_array_and_check_shape(self):
        v = [1, 2, 3]
        v_np = g.convert_to_numpy_array_and_check_shape(v, (3,))
        self.assertTrue(np.allclose(v, v_np, rtol=1e-4))
        self.assertRaises(ValueError, g.convert_to_numpy_array_and_check_shape, v, (4,))

    def test_angle_between_vectors(self):
        v = [3, 4, 0]
        v = g.convert_to_numpy_array_and_check_shape(v, (3,))
        u = g.convert_to_numpy_array_and_check_shape([4, 4, 2], (3,))
        norm = lambda v: np.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
        angle_result = np.arccos((v[0] * u[0] + v[1] * u[1] + v[2] * u[2]) / (norm(v) * norm(u)))
        self.assertTrue(g.angle_between(v, u) == angle_result)
        self.assertRaises(ValueError, g.angle_between, v, np.array([1, 2]))


class TestFrameUtils(unittest.TestCase):

    def setUp(self):
        self.p_test = np.array([4.243401159045579E-10, 6001556.04822616, 3464999.9999999995]) / 1e3
        self.v_test = np.array([-7621.894924414581, 4.0417965144985753E-13, 2.333532305655443E-13]) / 1e3

    def test_frame_creation(self):
        all_names = ["CIRF", "ECI", "TEME", "J2000", "EME2000", "GCRF", "ITRF", "GTOD", "ECF", "TNW", "QSW"]
        for frame_name in all_names:
            frame = frames.Frame(frame_name)
            if frame_name in frames._frame_alias_map:
                assert frame.value_or_alias == frames._frame_alias_map[frame_name]
            else:
                assert frame.value_or_alias == frame_name

    def test_rot_mat_in_to_tnw(self):
        state_in = np.concatenate([self.p_test, self.v_test])
        rot_mat_in_to_tnw_test = np.array([
            [-1.0, 5.3028761936245346E-17, 3.0616169978683824E-17],
            [-6.123233995736767E-17, -0.8660254037844388, -0.5],
            [-4.009074440407614E-33, -0.5, 0.8660254037844388]
        ])
        rot_mat = frames.transformation_matrix_in_to_tnw(state_in)
        pos_tnw = np.dot(rot_mat, state_in[:3])
        pos_in_reconstruct = np.dot(rot_mat.T, pos_tnw)

        self.assertTrue(np.allclose(rot_mat, rot_mat_in_to_tnw_test, rtol=1e-4))
        self.assertTrue(np.allclose(state_in[:3], pos_in_reconstruct, rtol=1e-4))

    def test_rot_mat_in_to_lvlh(self):
        state_in = np.array([1, 2, 3, 4, 5, 6])
        rot_mat = frames.transformation_matrix_in_to_lvlh(state_in)

        rot_mat_in_to_lvlh_test = np.array([
            [0.8728715609439696, 0.21821789023599242, -0.4364357804719848],
            [0.408248290463863, -0.816496580927726, 0.408248290463863],
            [-0.2672612419124244, -0.5345224838248488, -0.8017837257372732]
        ])

        pos_lvlh = np.dot(rot_mat, state_in[:3])
        pos_in_reconstruct = np.dot(rot_mat.T, pos_lvlh)

        self.assertTrue(np.allclose(rot_mat, rot_mat_in_to_lvlh_test, rtol=1e-4))
        self.assertTrue(np.allclose(state_in[:3], pos_in_reconstruct, rtol=1e-4))

    def test_rot_mat_string_to_float(self):
        rot_mat_str = ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX", "ZXZ", "ZYZ", "XYX", "XZX", "YXY", "YZY"]
        rot_mat_index_test = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0], [2, 0, 2],
                              [2, 1, 2], [0, 1, 0], [0, 2, 0], [1, 0, 1], [1, 2, 1]]
        for i, rot_mat in enumerate(rot_mat_str):
            self.assertTrue(np.allclose(frames.get_rot_order_axes(rot_mat), rot_mat_index_test[i], rtol=1e-4))
