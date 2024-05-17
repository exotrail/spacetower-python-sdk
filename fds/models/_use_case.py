from abc import ABC, abstractmethod

from typing_extensions import Self

from fds.client import FdsClient
from fds.models._model import RetrievableModel
from fds.models.orbital_state import OrbitalState, PropagationContext
from fds.models.orbits import Orbit
from fds.models.spacecraft import Spacecraft


class BaseUseCase(ABC):
    FDS_TYPE: FdsClient.UseCases
    ResultType: RetrievableModel

    @abstractmethod
    def __init__(self, nametag: str):
        self._nametag = nametag
        self._is_run = False
        self._api_response = None
        self._fds_client = FdsClient.get_client()
        self._result = None

    @property
    def nametag(self) -> str:
        return self._nametag

    @property
    def is_run(self) -> bool:
        return self._is_run

    @property
    def api_response(self):
        return self._api_response

    @property
    def result(self) -> RetrievableModel | None:
        return self._result

    @property
    def fds_client(self) -> FdsClient:
        return self._fds_client

    def api_run_map(self, **kwargs) -> dict:
        return {}

    def run(self, force_save: bool = False) -> Self:
        api_response = self._fds_client.run_use_case(self.FDS_TYPE, **self.api_run_map(force_save=force_save))
        self._api_response = api_response
        self._is_run = True
        self._result = self.ResultType.retrieve_by_id(self.api_response.id)
        return self


class OrbitalStateUseCase(BaseUseCase, ABC):
    @abstractmethod
    def __init__(self, initial_orbital_state: OrbitalState, nametag: str):
        self._initial_orbital_state = initial_orbital_state
        super().__init__(nametag)

    @property
    def initial_orbital_state(self) -> OrbitalState:
        return self._initial_orbital_state

    @property
    def spacecraft(self) -> Spacecraft:
        return self.initial_orbital_state.spacecraft

    @property
    def propagation_context(self) -> PropagationContext:
        return self.initial_orbital_state.propagation_context

    @property
    def initial_osculating_orbit(self) -> Orbit | None:
        return self.initial_orbital_state.osculating_orbit

    @property
    def initial_mean_orbit(self) -> Orbit | None:
        return self.initial_orbital_state.mean_orbit

    def api_run_map(self, force_save: bool = False) -> dict:
        return {
            'initialOrbitalStateId': self.initial_orbital_state.save(force=force_save).client_id
        }
