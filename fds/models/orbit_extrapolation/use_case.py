from datetime import datetime, timedelta

from fds.client import FdsClient
from fds.models._use_case import OrbitalStateUseCase
from fds.models.actions import ActionFiring
from fds.models.orbit_extrapolation.requests import MeasurementsRequest, OrbitDataMessageRequest, EventsRequestOrbital, \
    EventsRequestStationVisibility, EventsRequestSensor, EphemeridesRequest
from fds.models.orbit_extrapolation.result import ResultOrbitExtrapolation
from fds.models.orbital_state import OrbitalState, RequiredOrbitalStates
from fds.models.roadmaps import RoadmapFromSimulation, RoadmapFromActions
from fds.models.spacecraft import SpacecraftBox
from fds.utils.dates import get_datetime
from fds.utils.log import log_and_raise


class OrbitExtrapolation(OrbitalStateUseCase):
    FDS_TYPE = FdsClient.UseCases.ORBIT_EXTRAPOLATION
    ResultType = ResultOrbitExtrapolation

    def __init__(
            self,
            initial_orbital_state: OrbitalState,
            measurements_request: MeasurementsRequest = None,
            orbit_data_message_request: OrbitDataMessageRequest = None,
            duration: float = None,
            roadmap: RoadmapFromActions | RoadmapFromSimulation = None,
            orbital_events_request: EventsRequestOrbital = None,
            station_visibility_events_request: EventsRequestStationVisibility = None,
            sensor_events_request: EventsRequestSensor = None,
            required_orbital_states: str | RequiredOrbitalStates = RequiredOrbitalStates.LAST,
            ephemerides_request: EphemeridesRequest = None,
            extrapolate_covariance: bool = False,
            nametag: str = None
    ):
        """
        Args:
            initial_orbital_state (OrbitalState): The initial orbital state object.
            measurements_request (MeasurementsRequest): The measurements request object. Defaults to None.
            orbit_data_message_request (OrbitDataMessageRequest): The orbit data message request object. Defaults to
                None.
            duration (float): The duration of the orbit_extrapolation. Defaults to None. If None, roadmap is needed.
                roadmap (RoadmapFromActions | RoadmapFromSimulation): The roadmap object. Defaults to None. If None,
                duration is needed.
            orbital_events_request (EventsRequestOrbital): The orbital events request object. Defaults to None.
            station_visibility_events_request (EventsRequestStationVisibility): The station visibility events request
                object. Defaults to None.
            sensor_events_request (EventsRequestSensor): The sensor events request object. Defaults to None.
            ephemerides_request (EphemeridesRequest): The ephemerides request object. Defaults to None.
            required_orbital_states (str | RequiredOrbitalStates): The required orbital states included in the output
                (ALL or LAST). Defaults to LAST.
            extrapolate_covariance (bool): Whether to extrapolate the covariance matrix. Defaults to False.
            nametag (str): The name of the use case. Defaults to None.
        """

        super().__init__(initial_orbital_state, nametag)

        if roadmap is not None and isinstance(roadmap, RoadmapFromActions):
            self._check_roadmap_from_actions_against_spacecraft(roadmap, initial_orbital_state.spacecraft)

        if ephemerides_request is not None:
            self._check_ephemerides_request(ephemerides_request)

        if extrapolate_covariance:
            self._check_covariance_matrix_availability()

        self._duration = duration
        self._roadmap = roadmap
        self._measurements_request = measurements_request
        self._orbit_data_message_request = orbit_data_message_request
        self._orbital_events_request = orbital_events_request
        self._station_visibility_events_request = station_visibility_events_request
        self._sensor_events_request = sensor_events_request
        self._required_orbital_states = RequiredOrbitalStates.from_input(required_orbital_states)
        self._ephemerides_request = ephemerides_request
        self._extrapolate_covariance = extrapolate_covariance

        if self.duration is None and self.roadmap is None:
            msg = "'duration' and/or 'roadmap' are a needed input!"
            log_and_raise(ValueError, msg)

        if self.roadmap is not None:
            if self.initial_date != self.roadmap.start_date:
                msg = (f"Roadmap start date ({self.roadmap.start_date}) is different from initial orbital state date "
                       f"({self.initial_date}).")
                log_and_raise(ValueError, msg)

        if self.duration is not None and self.roadmap is not None:
            if self.final_date < self.roadmap.end_date:
                msg = (f"Extrapolation duration ({self.duration} s) is shorter than roadmap duration "
                       f"({self.roadmap.duration} s). This is not allowed in the current version.")
                log_and_raise(ValueError, msg)
            if isinstance(self.roadmap, RoadmapFromSimulation):
                msg = "Roadmap from simulation cannot be extended."
                log_and_raise(ValueError, msg)
            self._roadmap = self.roadmap.create_new_extended_after(self.final_date)

    @property
    def duration(self) -> float | None:
        return self._duration

    @property
    def final_date(self):
        if self.duration is None:
            return self.roadmap.end_date
        return self.initial_orbital_state.date + timedelta(seconds=self.duration)

    @property
    def initial_date(self):
        return self.initial_orbital_state.date

    @property
    def orbital_events_request(self) -> EventsRequestOrbital:
        return self._orbital_events_request

    @property
    def station_visibility_events_request(self) -> EventsRequestStationVisibility:
        return self._station_visibility_events_request

    @property
    def sensor_events_request(self) -> EventsRequestSensor:
        return self._sensor_events_request

    @property
    def ephemerides_request(self) -> EphemeridesRequest:
        return self._ephemerides_request

    @property
    def measurements_request(self) -> MeasurementsRequest:
        return self._measurements_request

    @property
    def orbit_data_message_request(self) -> OrbitDataMessageRequest:
        return self._orbit_data_message_request

    @property
    def roadmap(self) -> RoadmapFromSimulation | RoadmapFromActions | None:
        return self._roadmap

    @property
    def result(self) -> ResultOrbitExtrapolation:
        return self._result

    @property
    def required_orbital_states(self) -> RequiredOrbitalStates:
        return self._required_orbital_states

    @property
    def api_response(self):
        return self._api_response

    @property
    def extrapolate_covariance(self) -> bool:
        return self._extrapolate_covariance

    @classmethod
    def with_target_date(
            cls,
            target_date: datetime | str,
            initial_orbital_state: OrbitalState,
            measurements_request: MeasurementsRequest = None,
            orbit_data_message_request: OrbitDataMessageRequest = None,
            roadmap: RoadmapFromActions | RoadmapFromSimulation = None,
            orbital_events_request: EventsRequestOrbital = None,
            station_visibility_events_request: EventsRequestStationVisibility = None,
            sensor_events_request: EventsRequestSensor = None,
            required_orbital_states: str | RequiredOrbitalStates = RequiredOrbitalStates.LAST,
            ephemerides_request: EphemeridesRequest = None,
            extrapolate_covariance: bool = False,
            nametag: str = None
    ):
        """
        Args:
            target_date (datetime | str): The target date (only future dates are allowed).
            initial_orbital_state (OrbitalState): The initial orbital state object.
            measurements_request (MeasurementsRequest): The measurements request object. Defaults to None.
            orbit_data_message_request (OrbitDataMessageRequest): The orbit data message request object. Defaults to
                None.
            roadmap (RoadmapFromActions | RoadmapFromSimulation): The roadmap object. Defaults to None.
                If None, duration is needed.
            orbital_events_request (EventsRequestOrbital): The orbital events request object. Defaults to None.
            station_visibility_events_request (EventsRequestStationVisibility): The station visibility events request
                object. Defaults to None.
            sensor_events_request (EventsRequestSensor): The sensor events request object. Defaults to None.
            required_orbital_states (str | RequiredOrbitalStates): The required orbital states included in the output
                (ALL or LAST). Defaults to LAST.
            ephemerides_request (EphemeridesRequest): The ephemerides request object. Defaults to None.
            extrapolate_covariance (bool): Whether to extrapolate the covariance matrix. Defaults to False.
            nametag (str): The name of the use case. Defaults to None.
        """
        target_date = get_datetime(target_date)

        if target_date < initial_orbital_state.date:
            msg = (f"Target date ({target_date}) is before initial orbital state date "
                   f"({initial_orbital_state.date}).")
            log_and_raise(ValueError, msg)

        duration = (target_date - initial_orbital_state.date).total_seconds()
        return cls(
            initial_orbital_state=initial_orbital_state,
            measurements_request=measurements_request,
            orbit_data_message_request=orbit_data_message_request,
            duration=duration,
            roadmap=roadmap,
            orbital_events_request=orbital_events_request,
            station_visibility_events_request=station_visibility_events_request,
            sensor_events_request=sensor_events_request,
            required_orbital_states=required_orbital_states,
            ephemerides_request=ephemerides_request,
            extrapolate_covariance=extrapolate_covariance,
            nametag=nametag
        )

    def api_run_map(self, force_save: bool = False) -> dict:
        d = super().api_run_map()
        events_request_ids = []
        for request in (
                self.orbital_events_request, self.station_visibility_events_request, self.sensor_events_request):
            if request is not None:
                events_request_ids.append(request.save(force=force_save).client_id)
        d.update(
            {
                'events_request_ids': events_request_ids,
                'measurements_request_id': self.measurements_request.save(force=force_save).client_id if
                self.measurements_request is not None else None,
                'orbit_data_message_request_id': self.orbit_data_message_request.save(force=force_save).client_id if
                self.orbit_data_message_request is not None else None,
                'roadmap_id': self.roadmap.save(force=force_save).client_id if self.roadmap is not None else None,
                'ephemeris_request_id': self.ephemerides_request.save(force=force_save).client_id if
                self.ephemerides_request is not None else None,
                'extrapolation_duration': self.duration if self.duration is not None else 1,
                'required_output_orbital_states': self.required_orbital_states.value,
                'extrapolate_covariance': self.extrapolate_covariance,
            }
        )
        return d

    @staticmethod
    def _check_roadmap_from_actions_against_spacecraft(roadmap: RoadmapFromActions, spacecraft: SpacecraftBox):
        firing_actions = [action for action in roadmap.actions if isinstance(action, ActionFiring)]

        for firing in firing_actions:
            if firing.duration > spacecraft.thruster.maximum_thrust_duration:
                msg = (f"Firing duration ({firing.duration}) is longer than the maximum thrust duration "
                       f"({spacecraft.thruster.maximum_thrust_duration}).")
                log_and_raise(ValueError, msg)

    def _check_ephemerides_request(self, ephemerides_request):
        if EphemeridesRequest.EphemerisType.POWER in ephemerides_request.ephemeris_types or \
                EphemeridesRequest.EphemerisType.PROPULSION in ephemerides_request.ephemeris_types:
            if not isinstance(self.initial_orbital_state.spacecraft, SpacecraftBox):
                msg = (f"Spacecraft must be of type SpacecraftBox to request ephemerides data of type "
                       f"{EphemeridesRequest.EphemerisType.POWER} or {EphemeridesRequest.EphemerisType.PROPULSION}.")
                log_and_raise(ValueError, msg)

    def _check_covariance_matrix_availability(self):
        if self.initial_orbital_state.covariance_matrix is None:
            msg = "Initial orbital state covariance matrix is not available."
            log_and_raise(ValueError, msg)
