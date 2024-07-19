from fds.client import FdsClient
from fds.models._model import FromConfigBaseModel, RetrievableModel
from fds.models.strategy import Strategy, CustomArcPosition
from fds.utils.log import log_and_raise


class ManeuverStrategy(Strategy, FromConfigBaseModel, RetrievableModel):
    FDS_TYPE = FdsClient.Models.MANEUVER_STRATEGY

    def __init__(
            self,
            thrust_arcs_position: str | Strategy.ThrustArcPosition,
            thrust_arcs_number: str | Strategy.ThrustArcNumber,
            thrust_arc_initialisation_kind: str | Strategy.ThrustArcInitialisationKind,
            number_of_thrust_orbits: int,
            number_of_rest_orbits: int,
            number_of_shift_orbits: int,
            stop_thrust_at_eclipse: bool,
            orbital_duty_cycle: float = None,
            thrust_arc_duration: float = None,
            custom_thrust_arc_position: CustomArcPosition = None,
            thrust_arc_mean_longitude_argument: float = None,
            nametag: str = None
    ):
        """
        Args:
            thrust_arcs_position (str | ThrustArcPosition): The position of the thrust arcs.
            thrust_arcs_number (str | ThrustArcNumber): The number of thrust arcs.
            thrust_arc_initialisation_kind (str | ThrustArcInitialisationKind): The thrust arc initialisation kind.
            number_of_thrust_orbits (int): Number of orbits to thrust.
            number_of_rest_orbits (int): Number of orbits to rest.
            number_of_shift_orbits (int): Number of orbits to shift.
            stop_thrust_at_eclipse (bool): If True, the thrust will stop at eclipse.
            orbital_duty_cycle (float): (Unit: dimensionless) The orbital duty cycle. Defaults to None.
            thrust_arc_duration (float): (Unit: s) The thrust arc duration. Defaults to None.
            custom_thrust_arc_position (CustomArcPosition): Defaults to None. Not implemented yet.
            thrust_arc_mean_longitude_argument (float): Defaults to None. Not implemented yet.
            nametag (str): Defaults to None.
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
        )
        RetrievableModel.__init__(self, nametag)
        self._check_not_implemented_features(custom_thrust_arc_position, thrust_arc_mean_longitude_argument)

    def _check_not_implemented_features(self, custom_thrust_arc_position, thrust_arc_mean_longitude_argument):
        # TODO: temporary, to be implemented in the future
        if custom_thrust_arc_position is not None or self.thrust_arcs_position == self.ThrustArcPosition.CUSTOM:
            msg = "Custom thrust arc position is not implemented yet."
            raise log_and_raise(NotImplementedError, msg)
        if (thrust_arc_mean_longitude_argument is not None
                or self.thrust_arcs_position.value == self.ThrustArcPosition.MEAN_LONGITUDE):
            msg = "Mean longitude argument is not implemented yet."
            raise log_and_raise(NotImplementedError, msg)

    def api_create_map(self, **kwargs) -> dict:
        d = super().api_create_map()
        d.update(
            {
                'thrust_arcs_position': self.thrust_arcs_position.value,
                'thrust_arcs_number': self.thrust_arcs_number.value,
                'thrust_arc_definition': self.thrust_arc_initialisation_kind.value,
                'number_of_thrust_orbits': self.number_of_thrust_orbits,
                'number_of_rest_orbits': self.number_of_rest_orbits,
                'number_of_shift_orbits': self.number_of_shift_orbits,
                'orbital_duty_cycle': self.orbital_duty_cycle,
                'thrust_arc_duration': self.thrust_arc_duration,
                'stop_thrust_at_eclipse': self.stop_thrust_at_eclipse
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'thrust_arcs_position': obj_data.get('thrustArcsPosition'),
            'thrust_arcs_number': obj_data.get('thrustArcsNumber'),
            'thrust_arc_initialisation_kind': obj_data.get('thrustArcDefinition'),
            'number_of_thrust_orbits': obj_data.get('numberOfThrustOrbits'),
            'number_of_rest_orbits': obj_data.get('numberOfRestOrbits'),
            'number_of_shift_orbits': obj_data.get('numberOfShiftOrbits'),
            'orbital_duty_cycle': obj_data.get('orbitalDutyCycle'),
            'thrust_arc_duration': obj_data.get('thrustArcDuration'),
            'stop_thrust_at_eclipse': obj_data.get('stopThrustAtEclipse')
        }
