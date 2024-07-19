from dataclasses import dataclass
from datetime import datetime, UTC

from leo_station_keeping import NumericalLeoStationKeepingResponse, NumericalLeoStationKeepingResponseResults

from fds.models.actions import ActionFiring, AttitudeMode, ActionAttitude
from fds.models.orbits import Orbit
from fds.models.quaternion import Quaternion, get_univoque_list_of_dated_quaternions
from fds.models.roadmaps import RoadmapFromActions
from fds.utils.dates import convert_date_to_utc, DateRange, filter_sequence_with_minimum_time_step, get_datetime
from fds.utils.log import log_and_raise


def get_ephemerides_data(raw_ephemerides: list[list[float]], field_indexes: dict[str, int],
                         start_date: datetime) -> list[dict]:
    res = []
    for eph in raw_ephemerides:
        line = {}
        for key, index in field_indexes.items():
            line[key] = eph[index]
        line["date"] = convert_date_to_utc(
            datetime.fromtimestamp(line.get("simulationDuration") + convert_date_to_utc(start_date).timestamp(),
                                   tz=UTC))
        res.append(line)
    return res


def select_ephemerides_data_with_specific_prefix(
        all_ephemerides_data: list[dict],
        prefix_list: str | list[str],
        remove_prefix: bool = True,
        keys_to_update: dict[str, str] | None = None
):
    if keys_to_update is None:
        keys_to_update = {}

    if not isinstance(prefix_list, list):
        prefix_list = [prefix_list]

    def remove_prefix_if_present(key: str) -> str:
        for p in prefix_list:
            if key.startswith(p):
                return key.replace(p, "")
        return key

    def update_key(key: str) -> str:
        old_key = key
        if remove_prefix:
            key = remove_prefix_if_present(key)
        if keys_to_update is not None:
            key = keys_to_update.get(key, keys_to_update.get(old_key, key))
        return key

    keys = [key for key in all_ephemerides_data[0].keys() if
            any([key.startswith(p) for p in prefix_list]) or key in keys_to_update]
    if not keys:
        return all_ephemerides_data
    res = []
    for eph in all_ephemerides_data:
        line = {update_key(key): eph[key] for key in keys}
        line["date"] = eph["date"]
        res.append(line)
    return res


class ResultStationKeeping:
    @dataclass
    class Report:
        number_of_burns: int
        thrust_duration: float
        total_consumption: float
        total_delta_v: float
        thruster_mean_duty_cycle: float
        total_warmup_duty_cycle: float
        mean_burn_duration_estimation: float
        simulation_duration: float
        number_of_orbital_periods: int
        total_impulse: float
        final_duty_cycle: float
        maneuver_model: str
        final_orbit: Orbit | None

        @classmethod
        def create_from_api_results(cls, results: NumericalLeoStationKeepingResponseResults):
            return cls(
                number_of_burns=results.number_of_burns,
                thrust_duration=results.thrust_duration,
                total_consumption=results.used_propellant,
                total_delta_v=results.delta_v,
                thruster_mean_duty_cycle=results.thruster_mean_duty_cycle,
                total_warmup_duty_cycle=results.total_warmup_duty_cycle,
                mean_burn_duration_estimation=results.mean_burn_duration_estimation,
                simulation_duration=results.mission_duration,
                number_of_orbital_periods=results.number_of_periods,
                total_impulse=results.total_impulse,
                final_duty_cycle=results.final_duty_cycle,
                maneuver_model=results.maneuver_model,
                final_orbit=results.final_orbit
            )

    def __init__(
            self,
            report: Report,
            raw_ephemerides: list[list[float]],
            field_indexes: list[dict[str, int | str]],
            start_date: datetime,
            raw_spacecraft_states: dict | None = None,
    ):
        """
        Args:
            report (Report): The report object.
            raw_ephemerides (list[list[float]]): The raw ephemerides.
            field_indexes (list[dict[str, int | str]]): The field indexes.
            start_date (datetime): The start date of the use case.
            raw_spacecraft_states (dict): The raw spacecraft states data.
        """
        self._report = report
        self._raw_ephemerides = raw_ephemerides
        self._field_indexes = self._get_field_indexes(field_indexes)
        self._start_date = convert_date_to_utc(start_date)
        self._raw_spacecraft_states = raw_spacecraft_states

        # TODO: consider mapping raw ephemerides to Ephemeris objects in orbit_extrapolation module

    @property
    def report(self) -> Report:
        return self._report

    @property
    def raw_ephemerides(self) -> list[list[float]]:
        return self._raw_ephemerides

    @property
    def ephemerides_field_indexes(self) -> dict[str, int]:
        return self._field_indexes

    @property
    def raw_spacecraft_states(self) -> dict:
        return self._raw_spacecraft_states

    @property
    def start_date(self) -> datetime:
        return self._start_date

    @staticmethod
    def _get_field_indexes(field_indexes: list[dict[str, int | str]]) -> dict[str, int]:
        return {field["key"]: field["index"] for field in field_indexes}

    @classmethod
    def from_microservice_response(cls, response: NumericalLeoStationKeepingResponse, start_date: datetime | str):
        return cls(
            report=cls.Report.create_from_api_results(response.results),
            raw_ephemerides=response.ephemerides,
            field_indexes=[r.to_dict() for r in response.field_indexes],
            raw_spacecraft_states=response.spacecraft_states.to_dict() if response.spacecraft_states else None,
            start_date=get_datetime(start_date),
        )

    def export_raw_ephemerides_data(self) -> list[dict]:
        return get_ephemerides_data(self.raw_ephemerides, self.ephemerides_field_indexes, self.start_date)

    def export_keplerian_ephemerides_data(self) -> list[dict] | None:
        if not any(key.startswith("keplerian") for key in self.ephemerides_field_indexes.keys()):
            return None
        all_ephemerides_data = self.export_raw_ephemerides_data()
        return select_ephemerides_data_with_specific_prefix(all_ephemerides_data, "keplerian")

    def export_state_error_ephemerides_data(self) -> list[dict] | None:
        if not any(key.startswith("positionError") for key in self.ephemerides_field_indexes.keys()):
            return None
        all_ephemerides_data = self.export_raw_ephemerides_data()
        return select_ephemerides_data_with_specific_prefix(all_ephemerides_data,
                                                            ["positionError", "velocityError"],
                                                            remove_prefix=False)

    def export_cartesian_ephemerides_data(self) -> list[dict] | None:
        if not any(key.startswith("cartesian") for key in self.ephemerides_field_indexes.keys()):
            return None
        all_ephemerides_data = self.export_raw_ephemerides_data()
        return select_ephemerides_data_with_specific_prefix(all_ephemerides_data, "cartesian")

    def export_power_system_ephemerides_data(self) -> list[dict] | None:
        if not any(key.startswith("battery") for key in self.ephemerides_field_indexes.keys()):
            return None
        all_ephemerides_data = self.export_raw_ephemerides_data()
        keys_to_update = {
            "State": "battery_charge",
            "ContributionCharge": "solar_array_collected_power",
            "ContributionThrusterConsumption": "thruster_power_consumption",
            "ContributionThrusterWarmupConsumption": "thruster_warm_up_power_consumption",
            "ContributionTotal": "battery_charging_power",
        }
        data = select_ephemerides_data_with_specific_prefix(all_ephemerides_data, "battery",
                                                            keys_to_update=keys_to_update)
        return data

    def generate_maneuver_roadmap(self, quaternion_step: float = 0.0) -> RoadmapFromActions:
        """
        Generate a roadmap with the maneuvers performed during the station keeping. The roadmap will contain the
        quaternions and the firing dates.

        Args:
            quaternion_step (float): The minimum time step between two quaternions (in seconds). Default is 0.0.
        """

        if self.raw_spacecraft_states is None:
            msg = ("No spacecraft states found. Add a SpacecraftStatesRequest to"
                   " the output requests.")
            log_and_raise(ValueError, msg)
        raw_firings_info = self.raw_spacecraft_states.get('thrusting')
        firing_date_ranges = [DateRange(start=firing.get('begin'), end=firing.get('end')) for firing in
                              raw_firings_info]

        quaternions_osculating = self._get_osculating_quaternions(quaternion_step=quaternion_step)

        # create roadmap with firing dates and attitude quaternions
        firing_actions = [ActionFiring.from_firing_date_range(
            firing_date_range,
            firing_attitude_mode=AttitudeMode.QUATERNION,
            post_firing_attitude_mode=AttitudeMode.QUATERNION
        ) for firing_date_range in firing_date_ranges]

        attitude_action = ActionAttitude(
            attitude_mode=AttitudeMode.QUATERNION,
            transition_date=quaternions_osculating[0].date,
            quaternions=quaternions_osculating
        )

        return RoadmapFromActions(actions=[attitude_action] + firing_actions)

    def _get_osculating_quaternions(self, quaternion_step: float = 0.0) -> list[Quaternion]:
        return self._get_quaternions_without_duplicates(kind='osculating', quaternion_step=quaternion_step)

    def _get_mean_quaternions(self, quaternion_step: float = 0.0) -> list[Quaternion]:
        return self._get_quaternions_without_duplicates(kind='mean', quaternion_step=quaternion_step)

    def _get_quaternions_without_duplicates(self, kind: str = 'osculating', quaternion_step: float = 0.0) \
            -> list[Quaternion]:
        if self.raw_spacecraft_states.get(kind) is None:
            msg = f"No {kind} attitude states found. Use a SpacecraftStatesRequest with {kind} set to True."
            log_and_raise(ValueError, msg)
        raw_quaternions_osculating = self.raw_spacecraft_states.get(kind).get('attitude').get('rotation')
        raw_dates = self.raw_spacecraft_states.get('timestamps')
        quaternions_osculating = Quaternion.from_collections(raw_quaternions_osculating, raw_dates)
        quaternions = get_univoque_list_of_dated_quaternions(quaternions_osculating,
                                                             ignore_different_quaternions_at_same_date=True)
        dates = [q.date for q in quaternions]
        return list(filter_sequence_with_minimum_time_step(quaternions, dates, quaternion_step))
