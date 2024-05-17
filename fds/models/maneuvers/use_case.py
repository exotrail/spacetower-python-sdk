from dataclasses import dataclass

from fds.client import FdsClient
from fds.models._use_case import OrbitalStateUseCase
from fds.models.maneuvers.result import ResultManeuverGeneration
from fds.models.maneuvers.strategy import ManeuverStrategy
from fds.models.orbital_state import OrbitalState, RequiredOrbitalStates
from fds.utils.log import log_and_raise


class ManeuverGeneration(OrbitalStateUseCase):
    FDS_TYPE = FdsClient.UseCases.MANEUVER_GENERATION
    ResultType = ResultManeuverGeneration

    @dataclass
    class DeltaContainer:
        semi_major_axis: float
        inclination: float
        eccentricity: float

    def __init__(
            self,
            initial_orbital_state: OrbitalState,
            strategy: ManeuverStrategy,
            maximum_duration: float,
            delta_inclination: float,
            delta_eccentricity: float,
            delta_semi_major_axis: float,
            quaternion_step: float,
            required_orbital_states: str | RequiredOrbitalStates = RequiredOrbitalStates.LAST,
            nametag: str = None
    ):
        """
        Args:
            initial_orbital_state (OrbitalState): The initial orbital state object.
            strategy (ManeuverStrategy): The strategy object.
            maximum_duration (float): The maximum duration of the maneuver.
            delta_inclination (float): The inclination delta (Unit: deg).
            delta_eccentricity (float): The eccentricity delta (Unit: dimensionless).
            delta_semi_major_axis (float): The semi-major axis delta (Unit: km).
            quaternion_step (float): The quaternion step.
            required_orbital_states (str | RequiredOrbitalStates): The required orbital states included in the output
                (ALL or NONE). Defaults to RequiredOrbitalStates.LAST.
            nametag (str): The name of the use case. Defaults to None.
        """
        super().__init__(initial_orbital_state, nametag)

        if {delta_inclination, delta_eccentricity, delta_semi_major_axis} == {0}:
            msg = "This maneuver has no deltas for SMA, ECC and INC!"
            log_and_raise(ValueError, msg)

        self._strategy = strategy
        self._maximum_duration = maximum_duration
        self._delta = self.DeltaContainer(delta_semi_major_axis, delta_inclination, delta_eccentricity)
        self._required_orbital_states = RequiredOrbitalStates.from_input(required_orbital_states)
        self._quaternion_step = quaternion_step

    @property
    def delta(self) -> DeltaContainer:
        return self._delta

    @property
    def strategy(self) -> ManeuverStrategy:
        return self._strategy

    @property
    def required_orbital_states(self) -> RequiredOrbitalStates:
        return self._required_orbital_states

    @property
    def quaternion_step(self) -> float:
        return self._quaternion_step

    @property
    def maximum_duration(self) -> float:
        return self._maximum_duration

    @property
    def result(self) -> ResultManeuverGeneration:
        return self._result

    def api_run_map(self, force_save: bool = False) -> dict:
        d = super().api_run_map()
        d.update(
            {
                'strategy_id': self.strategy.save(force=force_save).client_id,
                'delta_eccentricity': self.delta.eccentricity,
                'delta_inclination': self.delta.inclination,
                'delta_semi_major_axis': self.delta.semi_major_axis,
                'maximum_duration': self.maximum_duration,
                'required_output_orbital_states': self.required_orbital_states.value,
                'quaternion_step': self.quaternion_step
            }
        )
        return d
