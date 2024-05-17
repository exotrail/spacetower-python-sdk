from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Sequence

from fds.client import FdsClient
from fds.models._model import TimestampedRetrievableModel
from fds.models.quaternion import Quaternion
from fds.utils.dates import datetime_to_iso_string, get_datetime
from fds.utils.enum import EnumFromInput
from fds.utils.log import log_and_raise
from spacetower_python_client import QuaternionActionDto


class AttitudeMode(EnumFromInput):
    PROGRADE = "PROGRADE"
    RETROGRADE = "RETROGRADE"
    NORMAL = "NORMAL"
    ANTI_NORMAL = "ANTI_NORMAL"
    RADIAL = "RADIAL"
    ANTI_RADIAL = "ANTI_RADIAL"
    QUATERNION = "QUATERNION"
    SUN_POINTING = "SUN_POINTING"
    TELECOM = "TELECOM"
    PAYLOAD = "PAYLOAD"
    TRANSITIONAL = "TRANSITIONAL"
    LOF_ALIGNED_LVLH_CCSDS = "LOF_ALIGNED_LVLH_CCSDS"
    RETROGRADE_NADIR = "RETROGRADE_NADIR"


class Action(TimestampedRetrievableModel, ABC):
    FDS_TYPE = FdsClient.Models.ACTION

    @abstractmethod
    def __init__(
            self,
            date: str | datetime,
            nametag
    ):
        super().__init__(date, nametag)

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {}


class ActionAttitude(Action):
    FDS_TYPE = FdsClient.Models.ACTION_ATTITUDE

    def __init__(
            self,
            attitude_mode: str | AttitudeMode,
            transition_date: str | datetime,
            quaternions: Sequence[Quaternion] = None,
            nametag: str = None
    ):
        """
        Args:
            attitude_mode (str | AttitudeMode): The attitude mode of the satellite.
            transition_date (str): date of transition (in UTC format)
            nametag (str): Defaults to None.
        """
        super().__init__(transition_date, nametag)
        self._attitude_mode = AttitudeMode.from_input(attitude_mode)

        if quaternions is not None:
            # check that each quaternion has a date
            for q in quaternions:
                if not isinstance(q.date, datetime):
                    msg = f"Each quaternion must have a date."
                    log_and_raise(ValueError, msg)
            self._quaternions = sorted(quaternions, key=lambda x: x.date)
        else:
            self._quaternions = None
        self._quaternion_ids = []

    @property
    def attitude_mode(self) -> AttitudeMode:
        return self._attitude_mode

    @property
    def transition_date(self) -> datetime:
        return self._date

    @property
    def quaternions(self) -> Sequence[Quaternion] | None:
        return self._quaternions

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        quaternions = obj_data['quaternions']
        if quaternions is not None:
            if len(quaternions) == 0:
                quaternions = None
            else:
                quaternions = [
                    Quaternion(q['q0'], q['q1'], q['q2'], q['q3'],
                               date=q['transitionDate']) for q in quaternions
                ]
                quaternions = sorted(quaternions, key=lambda x: x.date)

        attitude_mode = obj_data['attitudeMode']
        if attitude_mode == 'NONE':
            attitude_mode = 'SUN_POINTING'

        return {
            'attitude_mode': attitude_mode,
            'transition_date': obj_data['transitionDate'],
            'quaternions': quaternions
        }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        if self.quaternions is not None:
            quaternions = [QuaternionActionDto(
                q0=qa.real,
                q1=qa.i,
                q2=qa.j,
                q3=qa.k,
                transition_date=datetime_to_iso_string(qa.date)
            ) for qa in self.quaternions]
        else:
            quaternions = None
        d.update(
            {
                'attitude_mode': self.attitude_mode.value,
                'transition_date': datetime_to_iso_string(self.date),
                'quaternions': quaternions
            }
        )
        return d


class ActionFiring(Action):
    FDS_TYPE = FdsClient.Models.ACTION_FIRING

    def __init__(
            self,
            firing_attitude_mode: str | AttitudeMode,
            post_firing_attitude_mode: str | AttitudeMode,
            duration: float,
            firing_start_date: str | datetime,
            warm_up_duration: float = 0,
            warm_up_attitude_mode: str | AttitudeMode = None,
            nametag: str = None
    ):
        """
        Args:
            firing_attitude_mode (str | AttitudeMode): The attitude mode of the satellite during the firing.
            post_firing_attitude_mode (str | AttitudeMode): The attitude mode of the satellite after the firing.
            duration (float): (Unit: s)
            firing_start_date (str | datetime): date of start of the firing (in UTC format)
            warm_up_duration (float): (Unit: s) Defaults to 0.
            warm_up_attitude_mode (str | AttitudeMode): Defaults to None.
            nametag (str): Defaults to None.
        """
        warm_up_start_date = get_datetime(firing_start_date) - timedelta(seconds=warm_up_duration)
        super().__init__(warm_up_start_date, nametag)

        self._duration = duration
        self._warm_up_duration = warm_up_duration
        self._firing_attitude_mode = AttitudeMode.from_input(firing_attitude_mode)
        self._post_firing_attitude_mode = AttitudeMode.from_input(post_firing_attitude_mode)
        self._warm_up_attitude_mode = AttitudeMode.from_input(
            warm_up_attitude_mode) if warm_up_attitude_mode is not None else None

        if self.warm_up_duration == 0 and self.warm_up_attitude_mode is not None:
            msg = "Warm-up attitude mode should be None if warm-up duration is 0."
            log_and_raise(ValueError, msg)

    @property
    def firing_attitude_mode(self) -> AttitudeMode:
        return self._firing_attitude_mode

    @property
    def firing_start_date(self) -> datetime:
        return self._date + timedelta(seconds=self.warm_up_duration)

    @property
    def firing_end_date(self) -> datetime:
        return self.firing_start_date + timedelta(seconds=self.duration)

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def post_firing_attitude_mode(self) -> AttitudeMode:
        return self._post_firing_attitude_mode

    @property
    def warm_up_duration(self) -> float:
        return self._warm_up_duration

    @property
    def warm_up_start_date(self) -> datetime:
        return self._date

    @property
    def warm_up_end_date(self) -> datetime:
        return self.firing_start_date

    @property
    def warm_up_attitude_mode(self) -> AttitudeMode:
        return self._warm_up_attitude_mode

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'firing_attitude_mode': obj_data['firingAttitude'],
            'duration': obj_data['firingDuration'],
            'firing_start_date': obj_data['startFiring'],
            'post_firing_attitude_mode': obj_data['postFiringAttitude'],
            'warm_up_duration': obj_data['warmUpDuration'],
            'warm_up_attitude_mode': obj_data.get('warmUpAttitude')
        }

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'firingAttitude': self.firing_attitude_mode.value,
                'firingDuration': self.duration,
                'startFiring': datetime_to_iso_string(self.firing_start_date),
                'postFiringAttitude': self.post_firing_attitude_mode.value,
                'warmUpDuration': self.warm_up_duration,
                'warmUpAttitude': self.warm_up_attitude_mode.value if self.warm_up_attitude_mode is not None else None
            }
        )
        return d


class ActionThruster(Action):
    class ThrusterMode(EnumFromInput):
        STOP = 'STOP'
        THRUSTER_ON = 'THRUSTER_ON'
        STANDBY = 'STANDBY'
        WARMUP = 'WARMUP'

    FDS_TYPE = FdsClient.Models.ACTION_THRUSTER

    def __init__(
            self,
            thruster_mode: str | ThrusterMode,
            date: str | datetime,
            nametag: str = None
    ):
        super().__init__(date, nametag)
        self._thruster_mode = self.ThrusterMode.from_input(thruster_mode)

    @property
    def thruster_mode(self) -> ThrusterMode:
        return self._thruster_mode

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {'thruster_mode': obj_data['action'],
                'date': obj_data['date']}

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'action': self.thruster_mode.value,
                'date': datetime_to_iso_string(self.date)
            }
        )
        return d
