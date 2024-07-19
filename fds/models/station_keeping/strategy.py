from leo_station_keeping import CustomManeuveringStrategy, ThrustArcDefinition, ThrustDurationThrustArcDefinition, \
    DutyCycleThrustArcDefinition

from fds.models.strategy import Strategy, CustomArcPosition


class StationKeepingStrategy(Strategy):

    def __init__(
            self,
            thrust_arcs_position: str | Strategy.ThrustArcPosition,
            thrust_arcs_number: str | Strategy.ThrustArcNumber,
            number_of_thrust_orbits: int,
            number_of_rest_orbits: int,
            number_of_shift_orbits: int,
            stop_thrust_at_eclipse: bool,
            thrust_arc_initialisation_kind: str | Strategy.ThrustArcInitialisationKind,
            orbital_duty_cycle: float = None,
            thrust_arc_duration: float = None,
            custom_thrust_arc_position: CustomArcPosition = None,
            thrust_arc_mean_longitude_argument: float = None,
            dynamic_duty_cycle: bool = False,
    ):
        """
        Args:
            thrust_arcs_position (str | ThrustArcPosition): The position of the thrust arcs.
            thrust_arcs_number (str | ThrustArcNumber): The number of thrust arcs.
            number_of_thrust_orbits (int): Number of orbits to thrust.
            number_of_rest_orbits (int): Number of orbits to rest.
            number_of_shift_orbits (int): Number of orbits to shift.
            stop_thrust_at_eclipse (bool): If True, the thrust will stop at eclipse.
            thrust_arc_initialisation_kind (str | ThrustArcInitialisationKind): The thrust arc initialisation kind.
            orbital_duty_cycle (float): (Unit: dimensionless) The orbital duty cycle. Defaults to None.
            thrust_arc_duration (float): (Unit: s) The thrust arc duration. Defaults to None.
            custom_thrust_arc_position (CustomArcPosition): The custom thrust arc position. Defaults to None.
            thrust_arc_mean_longitude_argument (float): If thrust_arcs_position is set to MEAN_LONGITUDE, the mean
                longitude of the center of the arc. Defaults to None.
            dynamic_duty_cycle (bool): To update the duty cycle during the simulation. Defaults to False.
        """
        Strategy.__init__(
            self,
            thrust_arcs_position=thrust_arcs_position,
            thrust_arcs_number=thrust_arcs_number,
            thrust_arc_initialisation_kind=thrust_arc_initialisation_kind,
            number_of_thrust_orbits=number_of_thrust_orbits,
            number_of_rest_orbits=number_of_rest_orbits,
            number_of_shift_orbits=number_of_shift_orbits,
            orbital_duty_cycle=orbital_duty_cycle,
            thrust_arc_duration=thrust_arc_duration,
            stop_thrust_at_eclipse=stop_thrust_at_eclipse,
            custom_thrust_arc_position=custom_thrust_arc_position,
            thrust_arc_mean_longitude_argument=thrust_arc_mean_longitude_argument
        )

        self._dynamic_duty_cycle = dynamic_duty_cycle

    @property
    def dynamic_duty_cycle(self) -> bool:
        return self._dynamic_duty_cycle

    def to_microservice_format(self) -> CustomManeuveringStrategy:
        custom_thrust_arc_position = self.custom_thrust_arc_position.to_microservice_format() \
            if self.custom_thrust_arc_position else None
        thrust_arc_definition = self._map_thrust_arc_definition()
        return CustomManeuveringStrategy(
            thrust_arcs_position=self.thrust_arcs_position.value,
            thrust_arcs_number=self.thrust_arcs_number.to_int(),
            thrust_arc_definition=thrust_arc_definition,
            number_of_thrust_orbits=self.number_of_thrust_orbits,
            number_of_rest_orbits=self.number_of_rest_orbits,
            number_of_shift_orbits=self.number_of_shift_orbits,
            custom_thrust_arcs_position=custom_thrust_arc_position,
            thrust_arc_mean_longitude_argument=self.thrust_arc_mean_longitude_argument,
            stop_thrusting_during_eclipse=self.stop_thrust_at_eclipse,
            dynamic_duty_cycle=self.dynamic_duty_cycle
        )

    def _map_thrust_arc_definition(self) -> ThrustArcDefinition:
        match self.thrust_arc_initialisation_kind:
            case self.ThrustArcInitialisationKind.THRUST_DURATION:
                return ThrustDurationThrustArcDefinition(
                    thrust_arc_duration=self.thrust_arc_duration,
                    type=self.ThrustArcInitialisationKind.THRUST_DURATION.value
                )
            case self.ThrustArcInitialisationKind.DUTY_CYCLE:
                return DutyCycleThrustArcDefinition(
                    duty_cycle=self.orbital_duty_cycle,
                    type=self.ThrustArcInitialisationKind.DUTY_CYCLE.value
                )
