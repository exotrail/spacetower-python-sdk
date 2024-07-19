import unittest
from datetime import datetime, UTC, timedelta

from fds.models.actions import ActionFiring, AttitudeMode, ActionAttitude, ActionThruster
from fds.models.maneuvers.strategy import ManeuverStrategy
from fds.models.maneuvers.use_case import ManeuverGeneration
from fds.models.orbit_extrapolation.use_case import OrbitExtrapolation
from fds.models.orbital_state import PropagationContext, CovarianceMatrix, OrbitalState, RequiredOrbitalStates
from fds.models.orbits import KeplerianOrbit, OrbitMeanOsculatingType, PositionAngleType
from fds.models.quaternion import Quaternion
from fds.models.roadmaps import RoadmapFromActions
from fds.models.spacecraft import SpacecraftBox
from fds.utils.dates import get_datetime, DateRange
from tests import TestModels, _test_initialisation, TestUseCases


class TestActionFiring(TestModels):
    CLIENT_TYPE = ActionFiring
    KWARGS = {'firing_attitude_mode': AttitudeMode.PROGRADE, 'duration': 60,
              'post_firing_attitude_mode': AttitudeMode.PROGRADE,
              'firing_start_date': "2023-05-22T00:01:00.000Z", 'warm_up_duration': 60, 'nametag': 'TestActionFiring'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_action_with_warmup_attitude(self):
        aa = ActionFiring(
            duration=60,
            warm_up_duration=60,
            firing_start_date='2023-05-22T01:01:00Z',
            firing_attitude_mode=AttitudeMode.NORMAL,
            post_firing_attitude_mode=AttitudeMode.SUN_POINTING,
            warm_up_attitude_mode=AttitudeMode.PROGRADE,
        )
        aa.save()
        aa_retrieved = ActionFiring.retrieve_by_id(aa.client_id)
        self.assertTrue(aa.is_same_object_as(aa_retrieved, check_id=False))
        aa.destroy()


class TestActionAttitude(TestModels):
    CLIENT_TYPE = ActionAttitude
    KWARGS = {'attitude_mode': AttitudeMode.NORMAL,
              'transition_date': "2023-05-22T02:00:00.000Z", 'nametag': 'TestActionAttitude'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_action_with_quaternion(self):
        q1 = Quaternion(
            real=1, i=1, j=1, k=1, date=datetime(2023, 5, 22, 0, 0, 0, tzinfo=UTC),
        )
        q2 = Quaternion(
            real=2, i=2, j=2, k=2, date=datetime(2023, 5, 22, 0, 0, 1, tzinfo=UTC),
        )
        aa = ActionAttitude(
            attitude_mode=AttitudeMode.QUATERNION,
            quaternions=[q1, q2],
            transition_date="2023-05-22T00:00:00.000Z",
            nametag='TestActionAttitude'
        )
        aa.save()
        aa_retrieved = ActionAttitude.retrieve_by_id(aa.client_id)

        for q, qr in zip(aa.quaternions, aa_retrieved.quaternions):
            self.assertTrue(q == qr)
            self.assertTrue(q.date == qr.date)
        aa.destroy()


class TestRoadmapFromActions(TestModels):
    CLIENT_TYPE = RoadmapFromActions
    af = ActionFiring(**TestActionFiring.KWARGS)
    aa = ActionAttitude(**TestActionAttitude.KWARGS)
    KWARGS = {
        'actions': [af, aa],
        'start_date': "2023-05-22T00:00:00.000Z",
        'end_date': "2023-05-23T00:00:00.000Z",
        'nametag': 'TestRoadmapFromActions'
    }

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_export_of_data_for_dataframe(self):
        action_attitude = ActionAttitude(
            attitude_mode=AttitudeMode.PROGRADE,
            transition_date=get_datetime("2023-05-22T00:00:00.000Z")
        )
        action_firing = ActionFiring(
            duration=60,
            warm_up_duration=60,
            firing_start_date='2023-05-22T01:01:00Z',
            firing_attitude_mode=AttitudeMode.NORMAL,
            post_firing_attitude_mode=AttitudeMode.SUN_POINTING,
        )

        roadmap = RoadmapFromActions(
            start_date=get_datetime("2023-05-22T00:00:00.000Z"),
            end_date=action_firing.firing_end_date,
            actions=[action_attitude, action_firing],
        )

        data = roadmap.timeline
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0].get('Date'), roadmap.start_date)
        self.assertEqual(data[0].get('Thruster mode'), 'STANDBY')
        self.assertEqual(data[0].get('Attitude mode'), action_attitude.attitude_mode.value)
        self.assertEqual(data[1].get('Date'), action_firing.warm_up_start_date)
        self.assertEqual(data[1].get('Thruster mode'), 'WARMUP')
        self.assertEqual(
            data[1].get('Attitude mode'),
            action_firing.warm_up_attitude_mode.value
        )
        self.assertEqual(data[2].get('Date'), action_firing.firing_start_date)
        self.assertEqual(data[2].get('Thruster mode'), 'THRUSTER_ON')
        self.assertEqual(data[2].get('Attitude mode'), action_firing.firing_attitude_mode.value)
        self.assertEqual(data[3].get('Date'), action_firing.firing_end_date)
        self.assertEqual(data[3].get('Thruster mode'), 'STANDBY')
        self.assertEqual(data[3].get('Attitude mode'), action_firing.post_firing_attitude_mode.value)

        data_thruster = roadmap.export_thruster_gantt()
        self.assertEqual(len(data_thruster), 3)
        self.assertEqual(data_thruster[0].get('Mode'), 'STANDBY')
        self.assertEqual(data_thruster[0].get('Start'), roadmap.start_date)
        self.assertEqual(data_thruster[0].get('End'), action_firing.warm_up_start_date)
        self.assertEqual(data_thruster[1].get('Mode'), 'WARMUP')
        self.assertEqual(data_thruster[1].get('Start'), action_firing.warm_up_start_date)
        self.assertEqual(data_thruster[1].get('End'), action_firing.firing_start_date)
        self.assertEqual(data_thruster[2].get('Mode'), 'THRUSTER_ON')
        self.assertEqual(data_thruster[2].get('Start'), action_firing.firing_start_date)
        self.assertEqual(data_thruster[2].get('End'), action_firing.firing_end_date)

        data_attitude = roadmap.export_attitude_gantt()
        self.assertEqual(len(data_attitude), 2)
        self.assertEqual(data_attitude[0].get('Mode'), action_attitude.attitude_mode.value)
        self.assertEqual(data_attitude[0].get('Start'), roadmap.start_date)
        self.assertEqual(data_attitude[0].get('End'), action_firing.warm_up_start_date)
        self.assertEqual(data_attitude[1].get('Mode'), 'NORMAL')
        self.assertEqual(data_attitude[1].get('Start'), action_firing.warm_up_start_date)
        self.assertEqual(data_attitude[1].get('End'), action_firing.firing_end_date)

    def test_automatic_start_and_end_dates(self):
        action_attitude = ActionAttitude(
            attitude_mode=AttitudeMode.PROGRADE,
            transition_date=get_datetime("2023-05-22T00:00:00.000Z")
        )
        action_firing = ActionFiring(
            duration=60,
            warm_up_duration=60,
            firing_start_date='2023-05-22T01:01:00Z',
            firing_attitude_mode=AttitudeMode.NORMAL,
            post_firing_attitude_mode=AttitudeMode.SUN_POINTING,
        )

        roadmap = RoadmapFromActions(
            actions=[action_attitude, action_firing],
        )

        self.assertEqual(roadmap.start_date, action_attitude.transition_date)
        self.assertEqual(roadmap.end_date, action_firing.firing_end_date)

        quaternions = []
        for i in range(10):
            quaternions.append(Quaternion(
                real=i, i=i, j=i, k=i, date=datetime(2023, 5, 22, 0, 0, i, tzinfo=UTC),
            ))
        quaternion_action = ActionAttitude(
            attitude_mode=AttitudeMode.QUATERNION,
            quaternions=quaternions,
            transition_date=quaternions[0].date
        )

        roadmap2 = RoadmapFromActions(
            actions=[quaternion_action]
        )

        self.assertEqual(roadmap2.start_date, quaternions[0].date)
        self.assertEqual(roadmap2.start_date, quaternion_action.transition_date)
        self.assertEqual(roadmap2.end_date, quaternions[-1].date)

    def test_roadmap_extension_after(self):
        action_attitude = ActionAttitude(
            attitude_mode=AttitudeMode.PROGRADE,
            transition_date=get_datetime("2023-05-22T00:00:00.000Z")
        )
        action_firing = ActionFiring(
            duration=60,
            warm_up_duration=60,
            firing_start_date='2023-05-22T01:01:00Z',
            firing_attitude_mode=AttitudeMode.NORMAL,
            post_firing_attitude_mode=AttitudeMode.SUN_POINTING,
        )

        roadmap = RoadmapFromActions(
            actions=[action_attitude, action_firing],
        )
        new_final_date = roadmap.end_date + timedelta(days=1)
        new_roadmap = roadmap.create_new_extended_after(final_date=new_final_date)

        self.assertEqual(new_roadmap.start_date, roadmap.start_date)
        self.assertEqual(new_roadmap.end_date, new_final_date)
        for new_action, action in zip(new_roadmap.actions, roadmap.actions):
            self.assertTrue(new_action.is_same_object_as(action, check_id=False))

    @staticmethod
    def _raise_error_of_roadmap_with_quaternions_extension():
        quaternions = []
        for i in range(10):
            quaternions.append(Quaternion(
                real=i, i=i, j=i, k=i, date=datetime(2023, 5, 22, 0, 0, i, tzinfo=UTC),
            ))
        quaternion_action = ActionAttitude(
            attitude_mode=AttitudeMode.QUATERNION,
            quaternions=quaternions,
            transition_date=quaternions[0].date
        )

        roadmap = RoadmapFromActions(
            actions=[quaternion_action]
        )
        new_final_date = roadmap.end_date + timedelta(days=1)
        roadmap.create_new_extended_after(final_date=new_final_date)

    def test_roadmap_extension_before(self):
        self.assertRaises(ValueError, self._raise_error_of_roadmap_with_quaternions_extension)


class TestManeuverStrategy(TestModels):
    CLIENT_TYPE = ManeuverStrategy
    KWARGS = {'thrust_arcs_position': "DESCENDING_NODE",
              'thrust_arcs_number': "ONE",
              'thrust_arc_initialisation_kind': "DUTY_CYCLE",
              'number_of_thrust_orbits': 1,
              'number_of_rest_orbits': 1,
              'number_of_shift_orbits': 1,
              'orbital_duty_cycle': 0.2,
              'stop_thrust_at_eclipse': True,
              'nametag': 'TestOrbitDeterminationConfiguration'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy_with_thrust_duration_initialisation(self):
        kwargs = self.KWARGS.copy()
        kwargs['thrust_arc_initialisation_kind'] = "THRUST_DURATION"
        kwargs['thrust_arc_duration'] = 60
        kwargs.pop('orbital_duty_cycle')
        self._test_save_and_destroy(self.CLIENT_TYPE, **kwargs)


class TestManeuverGeneration(TestUseCases, unittest.TestCase):
    CLIENT_TYPE = ManeuverGeneration

    def setUp(self) -> None:
        self.propagation_context = PropagationContext.import_from_config_file(self.CONFIG_TEST_FILEPATH)
        spacecraft = SpacecraftBox.import_from_config_file(self.CONFIG_TEST_FILEPATH)
        initial_covariance_matrix = CovarianceMatrix.from_diagonal(diagonal=(100, 100, 100, 0.1, 0.1, 0.1),
                                                                   frame="TNW")
        self.orbit = KeplerianOrbit(
            7000, 0, 90, 1e-3, 97, 10,
            kind=OrbitMeanOsculatingType.MEAN, anomaly_kind=PositionAngleType.MEAN,
            date='2023-05-22T00:00:00Z'
        )

        self.initial_orbital_state = OrbitalState.from_orbit(
            covariance_matrix=initial_covariance_matrix,
            propagation_context=self.propagation_context,
            spacecraft=spacecraft,
            orbit=self.orbit
        )

        self.maneuver_strategy = ManeuverStrategy.import_from_config_file(self.CONFIG_TEST_FILEPATH)

        self.kwargs = {'initial_orbital_state': self.initial_orbital_state,
                       'strategy': self.maneuver_strategy,
                       'delta_semi_major_axis': .2,  # km
                       'delta_eccentricity': 0.,
                       'delta_inclination': 0.0,
                       'required_orbital_states': RequiredOrbitalStates.LAST,
                       'maximum_duration': 10 * 24 * 60 * 60,
                       'quaternion_step': 60}

    def test_maneuver_generation_initialisation(self):
        self._test_initialisation()

    def test_maneuver_generation_run(self):
        res = self._test_client_run()
        roadmap_final_date = get_datetime('2023-05-22 04:36:56.187622+00:00')
        roadmap_initial_date = get_datetime('2023-05-22 00:00:00+00:00')
        attitude_actions_list = [
            ActionAttitude(attitude_mode=AttitudeMode.SUN_POINTING,
                           transition_date=get_datetime("2023-05-22 00:00:00+00:00"), ),
            ActionAttitude(attitude_mode=AttitudeMode.PROGRADE,
                           transition_date=get_datetime("2023-05-22 04:17:29.633053+00:00"), ),
            ActionAttitude(attitude_mode=AttitudeMode.SUN_POINTING,
                           transition_date=get_datetime("2023-05-22 04:36:56.187622+00:00"), ),
        ]

        thruster_actions_list = [
            ActionThruster(thruster_mode=ActionThruster.ThrusterMode.STANDBY,
                           date=get_datetime("2023-05-22 00:00:00+00:00"), ),
            ActionThruster(thruster_mode=ActionThruster.ThrusterMode.WARMUP,
                           date=get_datetime("2023-05-22 04:13:29.633053+00:00"), ),
            ActionThruster(thruster_mode=ActionThruster.ThrusterMode.THRUSTER_ON,
                           date=get_datetime("2023-05-22 04:17:29.633053+00:00"), ),
            ActionThruster(thruster_mode=ActionThruster.ThrusterMode.STOP,
                           date=get_datetime("2023-05-22 04:36:56.187622+00:00"), ),
        ]

        self.assertTrue(self.is_datetime_close(res.generated_roadmap.start_date, roadmap_initial_date))
        self.assertTrue(self.is_datetime_close(res.generated_roadmap.end_date, roadmap_final_date))

        for attitude_action, attitude_action_result in zip(attitude_actions_list,
                                                           res.generated_roadmap.attitude_actions):
            self.assertTrue(attitude_action.is_same_object_as(attitude_action_result, check_id=False))
        for thruster_action, thruster_action_result in zip(thruster_actions_list,
                                                           res.generated_roadmap.thruster_actions):
            self.assertTrue(thruster_action.is_same_object_as(thruster_action_result, check_id=False))

        # Add tests for report
        report_data = {
            'total_burns_duration': 1166.9753648002807,
            'total_impulse': 16.33765510720393,
            'total_delta_v': 0.14652720705834066,
            'total_consumption': 0.0017536601889323684,
            'thruster_duty_cycle': 0.07023086396036486,
            'total_number_of_burns': 1,
            'number_of_orbital_periods': 2.8508583316947314,
            'average_thrust_duration': 1166.9753648002807,
            'total_warmup_duty_cycle': 0.014443670242663817,
            'simulation_duration': 16616.275224221492,
            'final_duty_cycle': 0.2062939808090732
        }

        for key, value in report_data.items():
            self.assertTrue(self.is_value_close(getattr(res.report, key), value, rtol=1E-3))

    def test_maneuver_generation_with_inclination_change(self):
        kwargs = self.kwargs.copy()
        kwargs['delta_inclination'] = 0.01  # deg
        self.kwargs = kwargs
        self._test_client_run()

    def test_export_of_data_for_dataframe(self):
        res = self._test_client_run()
        data = res.generated_roadmap.timeline
        self.assertEqual(len(data), 4)
        self.assertTrue(
            self.is_datetime_close(data[0].get('Date'), datetime.fromisoformat('2023-05-22 00:00:00+00:00')))
        self.assertEqual(data[0].get('Thruster mode'), 'STANDBY')
        self.assertEqual(data[0].get('Attitude mode'), 'SUN_POINTING')
        self.assertTrue(
            self.is_datetime_close(data[1].get('Date'), datetime.fromisoformat('2023-05-22 04:13:29.633053+00:00')))
        self.assertEqual(data[1].get('Thruster mode'), 'WARMUP')
        self.assertEqual(data[1].get('Attitude mode'), 'SUN_POINTING')
        self.assertTrue(
            self.is_datetime_close(data[2].get('Date'), datetime.fromisoformat('2023-05-22 04:17:29.633053+00:00')))
        self.assertEqual(data[2].get('Thruster mode'), 'THRUSTER_ON')
        self.assertEqual(data[2].get('Attitude mode'), 'PROGRADE')
        self.assertTrue(
            self.is_datetime_close(data[3].get('Date'), datetime.fromisoformat('2023-05-22 04:36:56.187622+00:00')))
        self.assertEqual(data[3].get('Thruster mode'), 'STOP')

        data_thruster = res.generated_roadmap.export_thruster_gantt()
        self.assertEqual(len(data_thruster), 3)
        self.assertEqual(data_thruster[0].get('Mode'), 'STANDBY')
        self.assertTrue(self.is_datetime_close(data_thruster[0].get('Start'),
                                               datetime.fromisoformat('2023-05-22 00:00:00+00:00')))
        self.assertTrue(self.is_datetime_close(data_thruster[0].get('End'),
                                               datetime.fromisoformat('2023-05-22 04:13:29.633053+00:00')))
        self.assertEqual(data_thruster[1].get('Mode'), 'WARMUP')
        self.assertTrue(self.is_datetime_close(data_thruster[1].get('Start'),
                                               datetime.fromisoformat('2023-05-22 04:13:29.633053+00:00')))
        self.assertTrue(self.is_datetime_close(data_thruster[1].get('End'),
                                               datetime.fromisoformat('2023-05-22 04:17:29.633053+00:00')))
        self.assertEqual(data_thruster[2].get('Mode'), 'THRUSTER_ON')
        self.assertTrue(self.is_datetime_close(data_thruster[2].get('Start'),
                                               datetime.fromisoformat('2023-05-22 04:17:29.633053+00:00')))
        self.assertTrue(self.is_datetime_close(data_thruster[2].get('End'),
                                               datetime.fromisoformat('2023-05-22 04:36:56.187622+00:00')))

        data_attitude = res.generated_roadmap.export_attitude_gantt()
        self.assertEqual(len(data_attitude), 2)
        self.assertEqual(data_attitude[0].get('Mode'), 'SUN_POINTING')
        self.assertTrue(self.is_datetime_close(data_attitude[0].get('Start'),
                                               datetime.fromisoformat('2023-05-22 00:00:00+00:00')))
        self.assertTrue(self.is_datetime_close(data_attitude[0].get('End'),
                                               datetime.fromisoformat('2023-05-22 04:17:29.633053+00:00')))
        self.assertEqual(data_attitude[1].get('Mode'), 'PROGRADE')
        self.assertTrue(self.is_datetime_close(data_attitude[1].get('Start'),
                                               datetime.fromisoformat('2023-05-22 04:17:29.633053+00:00')))
        self.assertTrue(self.is_datetime_close(data_attitude[1].get('End'),
                                               datetime.fromisoformat('2023-05-22 04:36:56.187622+00:00')))

    def test_use_generated_roadmap_for_orbit_extrapolation(self):
        kwargs = self.kwargs.copy()
        kwargs['delta_inclination'] = 0
        self.kwargs = kwargs
        res = self._test_client_run()
        oe = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state,
            roadmap=res.generated_roadmap
        )
        oe.run()
        self.assertTrue(oe.result.last_orbital_state.mean_orbit.date == res.generated_roadmap.end_date)
        self.assertTrue(oe.initial_date == res.generated_roadmap.start_date)

    def test_use_generated_roadmap_for_orbit_extrapolation_with_delta_inclination(self):
        kwargs = self.kwargs.copy()
        kwargs['delta_inclination'] = 0.01
        self.kwargs = kwargs
        res_inc = self._test_client_run()
        oe_inc = OrbitExtrapolation(
            initial_orbital_state=self.initial_orbital_state,
            roadmap=res_inc.generated_roadmap
        )
        oe_inc.run()
        self.assertTrue(self.is_datetime_close(oe_inc.result.last_orbital_state.mean_orbit.date,
                                               res_inc.generated_roadmap.end_date))
        self.assertTrue(self.is_datetime_close(oe_inc.initial_date, res_inc.generated_roadmap.start_date))

    def test_no_firing_intervals_constraints(self):
        kwargs = self.kwargs.copy()
        kwargs['delta_semi_major_axis'] = 1
        self.kwargs = kwargs

        # Run normal maneuver generation
        res = self._test_client_run()

        # get date of first burn
        thruster_actions = res.generated_roadmap.thruster_actions
        # get the action where thruster_mode is THRUSTER_ON
        burn_start_dates = [action.date for action in thruster_actions if action.thruster_mode == 'THRUSTER_ON']
        no_firing_date_range = DateRange.from_midpoint_and_duration(burn_start_dates[0], 60)

        kwargs['no_firing_date_ranges'] = [no_firing_date_range]
        self.kwargs = kwargs

        # Run maneuver generation with no firing date range
        res_with_constraints = self._test_client_run()

        # get date of first burn
        thruster_actions_with_constraints = res_with_constraints.generated_roadmap.thruster_actions
        # get the action where thruster_mode is THRUSTER_ON
        burn_with_constraints_start_dates = [action.date for action in thruster_actions_with_constraints
                                             if action.thruster_mode == 'THRUSTER_ON']

        assert burn_with_constraints_start_dates[0] > no_firing_date_range.end
        assert burn_with_constraints_start_dates[0] > burn_start_dates[0]
