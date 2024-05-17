from datetime import datetime

from fds.client import FdsClient
from fds.models._use_case import OrbitalStateUseCase
from fds.models.determination.configuration import OrbitDeterminationConfiguration
from fds.models.determination.requests import ParameterEstimationRequest
from fds.models.determination.result import ResultOrbitDetermination
from fds.models.orbital_state import OrbitalState
from fds.models.roadmaps import RoadmapFromActions, RoadmapFromSimulation
from fds.models.telemetry import TelemetryNmea, TelemetryGpsPv


class OrbitDetermination(OrbitalStateUseCase):
    FDS_TYPE = FdsClient.UseCases.ORBIT_DETERMINATION
    ResultType = ResultOrbitDetermination

    def __init__(
            self,
            initial_orbital_state: OrbitalState,
            telemetry: TelemetryNmea | TelemetryGpsPv,
            configuration: OrbitDeterminationConfiguration,
            parameter_estimation_requests: list[ParameterEstimationRequest] = None,
            actual_roadmap: RoadmapFromActions | RoadmapFromSimulation = None,
            estimated_results_min_step: float = 0.0,
            nametag: str = None
    ):
        """
        Args:
            initial_orbital_state (OrbitalState): The initial orbital state object.
            telemetry (TelemetryNmea | TelemetryGpsPv): The telemetry object.
            configuration (OrbitDeterminationConfiguration): The configuration object.
            parameter_estimation_requests (list[ParameterEstimationRequest]): The list of parameter estimation requests.
                Defaults to None.
            actual_roadmap (RoadmapFromActions | RoadmapFromSimulation): The actual roadmap object. Defaults to None.
            estimated_results_min_step (float): Minimum step for the estimated results. Unit: s. Defaults to 0.0 s.
            nametag (str): The name of the use case. Defaults to None.
        """
        super().__init__(initial_orbital_state, nametag)

        self._telemetry = telemetry
        self._configuration = configuration
        self._parameter_estimation_requests = parameter_estimation_requests
        self._actual_roadmap = actual_roadmap
        self._estimated_results_min_step = estimated_results_min_step
        self._initial_orbital_state = initial_orbital_state

    @property
    def configuration(self) -> OrbitDeterminationConfiguration:
        return self._configuration

    @property
    def telemetry(self) -> TelemetryNmea | TelemetryGpsPv:
        return self._telemetry

    @property
    def actual_roadmap(self) -> RoadmapFromSimulation | RoadmapFromActions:
        return self._actual_roadmap

    @property
    def parameter_estimation_requests(self) -> list[ParameterEstimationRequest]:
        return self._parameter_estimation_requests

    @property
    def initial_orbital_state(self) -> OrbitalState:
        return self._initial_orbital_state

    @property
    def initial_date(self) -> datetime:
        return self.initial_orbital_state.date

    @property
    def result(self) -> ResultOrbitDetermination:
        return self._result

    @property
    def estimated_results_min_step(self) -> float:
        return self._estimated_results_min_step

    def api_run_map(self, force_save: bool = False) -> dict:
        d = super().api_run_map()
        param_est = [
            per.save(force=force_save).client_id for per in
            self.parameter_estimation_requests
        ] if self.parameter_estimation_requests else None
        d.update({
            'telemetry_id': self.telemetry.save(force=force_save).client_id,
            'configuration_id': self.configuration.save(force=force_save).client_id,
            'parameter_estimation_request_ids': param_est,
            'roadmap_id': self.actual_roadmap.save(force=force_save).client_id if
            self.actual_roadmap is not None else None,
            'estimated_results_min_step': self.estimated_results_min_step
        })
        return d
