from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from typing import Sequence, Self

from fds.client import FdsClient
from fds.models._model import RetrievableModel
from fds.models.actions import ActionAttitude, ActionFiring, Action, ActionThruster, AttitudeMode
from fds.utils.dates import get_datetime, datetime_to_iso_string
from fds.utils.log import log_and_raise


class Roadmap(RetrievableModel, ABC):

    @property
    @abstractmethod
    def start_date(self) -> datetime:
        pass

    @property
    @abstractmethod
    def end_date(self) -> datetime:
        pass

    @property
    @abstractmethod
    def timeline(self) -> list[dict]:
        pass

    def _export_column_data_for_gantt(self, column_name: str) -> list[dict]:
        data_list = []
        start_date_to_use = None

        for i, rd in enumerate(self.timeline):
            mode = rd[column_name]
            start_date = rd['Date']
            if start_date < self.end_date:
                next_mode = self.timeline[i + 1][column_name]
                if next_mode != mode:
                    data_list.append(
                        {
                            'Start': start_date_to_use if start_date_to_use is not None else start_date,
                            'End': self.timeline[i + 1]['Date'],
                            'Mode': mode
                        }
                    )
                    start_date_to_use = None
                else:
                    start_date_to_use = rd['Date']

        return data_list

    def export_thruster_gantt(self) -> list[dict]:
        return self._export_column_data_for_gantt('Thruster mode')

    def export_attitude_gantt(self) -> list[dict]:
        return self._export_column_data_for_gantt('Attitude mode')


class RoadmapFromActions(Roadmap, RetrievableModel):
    FDS_TYPE = FdsClient.Models.ROADMAP_FROM_ACTIONS

    def __init__(
            self,
            actions: Sequence[ActionAttitude | ActionFiring],
            start_date: str | datetime = None,
            end_date: str | datetime = None,
            nametag: str = None
    ):
        """
        Args:
            actions (Sequence[ActionAttitude | ActionFiring]): Sequence of Action
                objects.
            start_date (str): UTC format. Default is the first action start_date.
            end_date (str): UTC format. Default is the last action end_date.
            nametag (str): Defaults to None.
        """

        super().__init__(nametag)
        self._actions = self._get_actions(actions)

        self._first_action_date = self.actions[0].date
        self._last_action_date = self._get_actions_final_date(self.actions)

        self._start_date, self._end_date = self._get_dates(
            get_datetime(start_date),
            get_datetime(end_date),
            self._first_action_date,
            self._last_action_date
        )

        self._timeline = self._get_timeline()

    @staticmethod
    def _get_actions(actions) -> Sequence[ActionAttitude | ActionFiring]:
        if len(actions) == 0:
            msg = "Roadmap must have at least one action."
            raise log_and_raise(ValueError, msg)
        # sort roadmap actions by date
        actions = sorted(actions, key=lambda x: x.date)
        return actions

    @staticmethod
    def _get_dates(
            start_date: datetime,
            end_date: datetime,
            first_action_date: datetime,
            last_action_date: datetime
    ) -> tuple[datetime, datetime]:

        if start_date is None:
            start_date = first_action_date
        if end_date is None:
            if first_action_date == last_action_date:
                msg = "The roadmap has only one action, the end date must be provided."
                log_and_raise(ValueError, msg)
            end_date = last_action_date

        if start_date > end_date:
            msg = f"The start date {start_date} must be before the end date {end_date}"
            log_and_raise(ValueError, msg)
        if start_date > first_action_date:
            msg = f"The start date {start_date} must be before the first action date {first_action_date}"
            log_and_raise(ValueError, msg)
        if start_date > last_action_date:
            msg = f"The start date {start_date} must be before the last action date {last_action_date}"
            log_and_raise(ValueError, msg)
        if end_date < last_action_date:
            msg = f"The end date {end_date} must be after the last action date {last_action_date}"
            log_and_raise(ValueError, msg)
        return start_date, end_date

    @staticmethod
    def _get_actions_final_date(actions: Sequence[ActionAttitude | ActionFiring]) -> datetime:
        dates = []
        for action in actions:
            if isinstance(action, ActionAttitude):
                if action.attitude_mode == AttitudeMode.QUATERNION:
                    dates.append(action.quaternions[-1].date)
                else:
                    dates.append(action.transition_date)
            else:
                dates.append(action.firing_end_date)
        return max(dates)

    @property
    def actions(self) -> Sequence[ActionAttitude | ActionFiring]:
        return self._actions

    @property
    def start_date(self) -> datetime:
        return self._start_date

    @property
    def end_date(self) -> datetime:
        return self._end_date

    @property
    def duration(self):
        return (self.end_date - self.start_date).total_seconds()

    @property
    def timeline(self):
        return self._timeline

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'start_date': obj_data['initialDate'],
            'end_date': obj_data['finalDate'],
            'actions': cls._get_actions_from_id(obj_data['roadmapActionIDs'])
        }

    def api_create_map(self, force_save: bool = False) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'initialDate': datetime_to_iso_string(self.start_date),
                'finalDate': datetime_to_iso_string(self.end_date),
                'roadmapActionIDs': [ra.save(force_save).client_id for ra in self.actions]
            }
        )
        return d

    @staticmethod
    def _get_actions_from_id(actions_ids: Sequence[str]):
        actions = []
        for ra_id in actions_ids:
            api_object_data = Action._retrieve_api_object_data(ra_id)
            if "attitudeMode" in api_object_data:
                actions.append(ActionAttitude.retrieve_by_id(ra_id))
            else:
                actions.append(ActionFiring.retrieve_by_id(ra_id))
        return actions

    def _check_if_roadmap_has_quaternion(self) -> bool:
        for action in self.actions:
            if isinstance(action, ActionAttitude) and action.attitude_mode == AttitudeMode.QUATERNION:
                return True
        return False

    def create_new_extended_after(self, final_date: datetime) -> Self:
        if final_date < self.end_date:
            msg = f"The requested final date {final_date} must be after the roadmap final date {self.end_date}"
            log_and_raise(ValueError, msg)
        if self._check_if_roadmap_has_quaternion():
            msg = "Roadmap with quaternion cannot be extended at the current version"
            log_and_raise(ValueError, msg)
        return RoadmapFromActions(
            actions=deepcopy(self.actions),
            start_date=datetime_to_iso_string(self.start_date),
            end_date=datetime_to_iso_string(final_date)
        )

    def _get_timeline(self) -> list[dict]:
        data = []
        for action in self.actions:
            if isinstance(action, ActionAttitude):
                data.append(
                    {
                        'Date': action.transition_date,
                        'Attitude mode': action.attitude_mode.value,
                        'Thruster mode': ActionThruster.ThrusterMode.STANDBY.value
                    }
                )
            else:
                data.append(
                    {
                        'Date': action.warm_up_start_date,
                        'Attitude mode': action.firing_attitude_mode.value,  # TODO change when warmup attitude in API
                        'Thruster mode': ActionThruster.ThrusterMode.WARMUP.value
                    }
                )
                data.append(
                    {
                        'Date': action.firing_start_date,
                        'Attitude mode': action.firing_attitude_mode.value,
                        'Thruster mode': ActionThruster.ThrusterMode.THRUSTER_ON.value
                    }
                )
                data.append(
                    {
                        'Date': action.firing_end_date,
                        'Attitude mode': action.post_firing_attitude_mode.value,
                        'Thruster mode': ActionThruster.ThrusterMode.STANDBY.value
                    }
                )
        if self.start_date < self.actions[0].date:
            data.append(
                {
                    'Date': self.start_date,
                    'Attitude mode': AttitudeMode.SUN_POINTING.value,
                    'Thruster mode': ActionThruster.ThrusterMode.STANDBY.value
                }
            )
        if self.end_date > self._last_action_date:
            data.append(
                {
                    'Date': self.end_date,
                    'Attitude mode': AttitudeMode.SUN_POINTING.value,
                    'Thruster mode': ActionThruster.ThrusterMode.STANDBY.value
                }
            )

        data = sorted(data, key=lambda x: x['Date'])
        self._check_roadmap_timeline(data)
        return data

    @staticmethod
    def _check_roadmap_timeline(data: list[dict]):
        for i in range(len(data) - 1):
            if data[i]['Date'] == data[i + 1]['Date']:
                if data[i]['Attitude mode'] != data[i + 1]['Attitude mode']:
                    msg = f"Attitude mode must be the same for the same date {data[i]['Date']}"
                    raise log_and_raise(ValueError, msg)


class RoadmapFromSimulation(Roadmap, RetrievableModel):
    FDS_TYPE = FdsClient.Models.ROADMAP_FROM_SIMULATION

    def __init__(
            self,
            attitude_actions: list[ActionAttitude],
            thruster_actions: list[ActionThruster],
            metadata: dict = None,
            creation_date: str | datetime = None,
            nametag: str = None
    ):
        super().__init__(nametag)
        self._attitude_actions = attitude_actions
        self._thruster_actions = thruster_actions
        self._roadmap_timeline = self._get_roadmap_timeline()
        self._creation_date = get_datetime(creation_date)
        self._metadata = metadata

    @property
    def attitude_actions(self) -> list[ActionAttitude]:
        return self._attitude_actions

    @property
    def thruster_actions(self) -> list[ActionThruster]:
        return self._thruster_actions

    @property
    def creation_date(self) -> datetime:
        return self._creation_date

    @property
    def start_date(self) -> datetime:
        attitude_initial_date = self.attitude_actions[0].date
        thruster_initial_date = self.thruster_actions[0].date
        return min(attitude_initial_date, thruster_initial_date)

    @property
    def end_date(self):
        attitude_final_date = self.attitude_actions[-1].date
        thruster_final_date = self.thruster_actions[-1].date
        return max(attitude_final_date, thruster_final_date)

    @property
    def duration(self):
        return (self.end_date - self.start_date).total_seconds()

    @property
    def metadata(self) -> dict:
        return self._metadata

    @property
    def timeline(self):
        return self._roadmap_timeline

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        attitude_actions = [ActionAttitude._create_from_api_object_data(aa_data)
                            for aa_data in obj_data['attitudeActions']]
        thruster_actions = [ActionThruster._create_from_api_object_data(ta_data)
                            for ta_data in obj_data['thrusterActions']]
        return {
            'attitude_actions': attitude_actions,
            'thruster_actions': thruster_actions,
            'metadata': obj_data['meta'],
            'creation_date': obj_data['creationDate'],
        }

    def api_create_map(self, force_save: bool = False) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'attitudeActionIDs': [aa.save(force_save).client_id for aa in self.attitude_actions],
                'thrusterActionIDs': [ta.save(force_save).client_id for ta in self.thruster_actions],
                'roadmapMeta': self.metadata
            }
        )
        return d

    def _get_roadmap_timeline(self) -> list[dict]:
        data_list = []
        for action in self.attitude_actions:
            data_list.append(
                {
                    'Date': action.date,
                    'Attitude mode': action.attitude_mode.value,
                    'Thruster mode': ""
                }
            )
        for action in self.thruster_actions:
            data_list.append(
                {
                    'Date': action.date,
                    'Attitude mode': "",
                    'Thruster mode': action.thruster_mode.value
                }
            )
        merged_data = self._merge_data(data_list)

        return merged_data

    @staticmethod
    def _merge_data(input_data: list[dict]):
        # Sort the data by date
        data = sorted(input_data, key=lambda x: x['Date'])

        # If times are the same, merge the rows by having attitude in attitude column and thruster in thruster column
        i = 0
        while i < len(data) - 1:
            if i == 0 and data[i]['Attitude mode'] == "":
                data[i]['Attitude mode'] = AttitudeMode.SUN_POINTING.value
            if data[i]['Date'] == data[i + 1]['Date']:
                data[i]['Attitude mode'] = data[i]['Attitude mode'] + data[i + 1]['Attitude mode']
                data[i]['Thruster mode'] = data[i]['Thruster mode'] + data[i + 1]['Thruster mode']
                data.pop(i + 1)
            else:
                if data[i]['Attitude mode'] == "":
                    data[i]['Attitude mode'] = data[i - 1]['Attitude mode']
                i += 1
        # If attitude or thruster is empt, copy the previous value
        for i in range(1, len(data)):
            if data[i]['Attitude mode'] == "":
                data[i]['Attitude mode'] = data[i - 1]['Attitude mode']
            if data[i]['Thruster mode'] == "":
                data[i]['Thruster mode'] = data[i - 1]['Thruster mode']

        return data
