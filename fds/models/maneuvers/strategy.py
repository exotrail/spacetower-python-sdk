from fds.client import FdsClient
from fds.models._model import FromConfigBaseModel, RetrievableModel
from fds.utils.enum import EnumFromInput


class ManeuverStrategy(FromConfigBaseModel, RetrievableModel):
    FDS_TYPE = FdsClient.Models.MANEUVER_STRATEGY

    class ThrustArcPosition(EnumFromInput):
        ASCENDING_AND_DESCENDING_NODES = 'ASCENDING_AND_DESCENDING_NODES'
        ASCENDING_NODE = 'ASCENDING_NODE'
        CUSTOM = 'CUSTOM'
        DESCENDING_NODE = 'DESCENDING_NODE'
        APOGEE_AND_PERIGEE = 'APOGEE_AND_PERIGEE'
        APOGEE = 'APOGEE'
        PERIGEE = 'PERIGEE'
        ASCENDING_AND_DESCENDING_ANTINODES = 'ASCENDING_AND_DESCENDING_ANTINODES'
        ASCENDING_ANTINODE = 'ASCENDING_ANTINODE'
        DESCENDING_ANTINODE = 'DESCENDING_ANTINODE'
        MEAN_LONGITUDE = 'MEAN_LONGITUDE'

    class ThrustArcNumber(EnumFromInput):
        ONE = "ONE"
        TWO = "TWO"

    class ThrustArcInitialisationKind(EnumFromInput):
        DUTY_CYCLE = 'DUTY_CYCLE'
        THRUST_DURATION = 'THRUST_DURATION'

    def __init__(
            self,
            thrust_arcs_position: str | ThrustArcPosition,
            thrust_arcs_number: str | ThrustArcNumber,
            thrust_arc_initialisation_kind: str | ThrustArcInitialisationKind,
            number_of_thrust_orbits: int,
            number_of_rest_orbits: int,
            number_of_shift_orbits: int,
            orbital_duty_cycle: float,
            thrust_arc_duration: float,
            stop_thrust_at_eclipse: bool,
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
            orbital_duty_cycle (float): (Unit: dimensionless) The orbital duty cycle.
            thrust_arc_duration (float): (Unit: s) The thrust arc duration.
            stop_thrust_at_eclipse (bool): If True, the thrust will stop at eclipse.
            nametag (str): Defaults to None.
        """
        super().__init__(nametag)
        self._thrust_arcs_position = self.ThrustArcPosition.from_input(thrust_arcs_position)
        self._thrust_arcs_number = self.ThrustArcNumber.from_input(thrust_arcs_number)
        self._thrust_arc_initialisation_kind = (
            self.ThrustArcInitialisationKind.from_input(thrust_arc_initialisation_kind))
        self._number_of_thrust_orbits = number_of_thrust_orbits
        self._number_of_rest_orbits = number_of_rest_orbits
        self._number_of_shift_orbits = number_of_shift_orbits
        self._orbital_duty_cycle = orbital_duty_cycle
        self._thrust_arc_duration = thrust_arc_duration
        self._stop_thrust_at_eclipse = stop_thrust_at_eclipse

    @property
    def thrust_arcs_position(self):
        return self._thrust_arcs_position

    @property
    def thrust_arcs_number(self):
        return self._thrust_arcs_number

    @property
    def thrust_arc_initialisation_kind(self):
        return self._thrust_arc_initialisation_kind

    @property
    def number_of_thrust_orbits(self):
        return self._number_of_thrust_orbits

    @property
    def number_of_rest_orbits(self):
        return self._number_of_rest_orbits

    @property
    def number_of_shift_orbits(self):
        return self._number_of_shift_orbits

    @property
    def orbital_duty_cycle(self):
        return self._orbital_duty_cycle

    @property
    def thrust_arc_duration(self):
        return self._thrust_arc_duration

    @property
    def stop_thrust_at_eclipse(self):
        return self._stop_thrust_at_eclipse

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
