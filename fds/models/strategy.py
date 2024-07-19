from abc import ABC, abstractmethod

from leo_station_keeping import CustomThrustArcsPosition

from fds.utils.enum import EnumFromInput


class CustomArcPosition:
    class Reference(EnumFromInput):
        ASCENDING_AND_DESCENDING_NODES = 'ASCENDING_AND_DESCENDING_NODES'
        APOGEE_AND_PERIGEE = 'APOGEE_AND_PERIGEE'
        ASCENDING_AND_DESCENDING_ANTINODES = 'ASCENDING_AND_DESCENDING_ANTINODES'

    def __init__(self, reference: str | Reference, delta_mean_longitude_argument: float = None):
        """
        Args:
            reference (str | Reference): The reference of the custom arc position.
            delta_mean_longitude_argument (float): The delta mean longitude argument (in degrees). Defaults to None.
        """
        self._reference = self.Reference.from_input(reference)
        self._delta_mean_longitude_argument = delta_mean_longitude_argument

    @property
    def reference(self) -> Reference:
        return self._reference

    @property
    def delta_mean_longitude_argument(self) -> float:
        return self._delta_mean_longitude_argument

    def to_microservice_format(self):
        return CustomThrustArcsPosition(
            reference=self.reference.value,
            deltaMeanLongitudeArgument=self.delta_mean_longitude_argument
        )


class Strategy(ABC):
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

        def to_int(self):
            values = {
                self.ONE: 1,
                self.TWO: 2
            }
            return values[self]

    class ThrustArcInitialisationKind(EnumFromInput):
        DUTY_CYCLE = 'DUTY_CYCLE'
        THRUST_DURATION = 'THRUST_DURATION'

    @abstractmethod
    def __init__(
            self,
            thrust_arcs_position: str | ThrustArcPosition,
            thrust_arcs_number: str | ThrustArcNumber,
            number_of_thrust_orbits: int,
            number_of_rest_orbits: int,
            number_of_shift_orbits: int,
            stop_thrust_at_eclipse: bool,
            thrust_arc_initialisation_kind: str | ThrustArcInitialisationKind,
            orbital_duty_cycle: float = None,
            thrust_arc_duration: float = None,
            custom_thrust_arc_position: CustomArcPosition = None,
            thrust_arc_mean_longitude_argument: float = None
    ):
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
        self._custom_thrust_arc_position = custom_thrust_arc_position
        self._thrust_arc_mean_longitude_argument = thrust_arc_mean_longitude_argument

        self._check_input_validity()

    def _check_input_validity(self):
        pass
        # self.check_initialisation_kind()  # TODO: implement this logic as two class methods from_duty_cycle and
        #                                       from_thrust_duration

    def check_initialisation_kind(self):
        match self.thrust_arc_initialisation_kind:
            case self.ThrustArcInitialisationKind.DUTY_CYCLE:
                if self.thrust_arc_duration is not None:
                    raise ValueError("Thrust arc duration should be None when initialisation kind is DUTY_CYCLE")
                if self.orbital_duty_cycle is None:
                    raise ValueError("Orbital duty cycle should be set when initialisation kind is DUTY_CYCLE")
            case self.ThrustArcInitialisationKind.THRUST_DURATION:
                if self.thrust_arc_duration is None:
                    raise ValueError("Thrust arc duration should be set when initialisation kind is THRUST_DURATION")
                if self.orbital_duty_cycle is not None:
                    raise ValueError("Orbital duty cycle should be None when initialisation kind is THRUST_DURATION")

    @property
    def thrust_arcs_position(self) -> ThrustArcPosition:
        return self._thrust_arcs_position

    @property
    def thrust_arcs_number(self) -> ThrustArcNumber:
        return self._thrust_arcs_number

    @property
    def thrust_arc_initialisation_kind(self) -> ThrustArcInitialisationKind:
        return self._thrust_arc_initialisation_kind

    @property
    def number_of_thrust_orbits(self) -> int:
        return self._number_of_thrust_orbits

    @property
    def number_of_rest_orbits(self) -> int:
        return self._number_of_rest_orbits

    @property
    def number_of_shift_orbits(self) -> int:
        return self._number_of_shift_orbits

    @property
    def orbital_duty_cycle(self):
        return self._orbital_duty_cycle

    @property
    def thrust_arc_duration(self):
        return self._thrust_arc_duration

    @property
    def stop_thrust_at_eclipse(self) -> bool:
        return self._stop_thrust_at_eclipse

    @property
    def custom_thrust_arc_position(self) -> CustomArcPosition:
        return self._custom_thrust_arc_position

    @property
    def thrust_arc_mean_longitude_argument(self) -> float:
        return self._thrust_arc_mean_longitude_argument
