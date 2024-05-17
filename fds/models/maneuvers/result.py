from dataclasses import dataclass

from fds.client import FdsClient
from fds.models._model import RetrievableModel
from fds.models.orbital_state import OrbitalState
from fds.models.roadmaps import RoadmapFromSimulation


class ResultManeuverGeneration(RetrievableModel):
    @dataclass
    class Report:
        average_thrust_duration: float
        final_duty_cycle: float
        number_of_orbital_periods: int
        orbital_states: list[OrbitalState]
        simulation_duration: float
        thruster_duty_cycle: float
        total_burns_duration: float
        total_consumption: float
        total_delta_v: float
        total_impulse: float
        total_number_of_burns: int
        total_warmup_duty_cycle: float

        @classmethod
        def create_from_api_dict(cls, obj_data: dict):
            orbital_states = [OrbitalState.retrieve_by_id(os['id']) for os in
                              obj_data['orbitalStates']]
            return cls(
                average_thrust_duration=obj_data['averageThrustDuration'],
                final_duty_cycle=obj_data['finalDutyCycle'],
                number_of_orbital_periods=obj_data['numberOfPeriod'],
                orbital_states=orbital_states,
                simulation_duration=obj_data['simulationDuration'],
                thruster_duty_cycle=obj_data['thrusterDutyCycle'],
                total_burns_duration=obj_data['totalBurnsDuration'],
                total_consumption=obj_data['totalConsumption'],
                total_delta_v=obj_data['totalDeltaV'],
                total_impulse=obj_data['totalImpulse'],
                total_number_of_burns=obj_data['totalNumberOfBurns'],
                total_warmup_duty_cycle=obj_data['totalWarmupDutyCycle']
            )

    FDS_TYPE = FdsClient.Models.RESULT_MANEUVER_GENERATION

    def __init__(
            self,
            report: Report,
            generated_roadmap: RoadmapFromSimulation,
            nametag: str = None
    ):
        """
        Args:
            report (Report): The report object.
            generated_roadmap (RoadmapFromSimulation): The generated roadmap object.
            nametag (str): The name of the use case. Defaults to None.
        """
        super().__init__(nametag)
        self._report = report
        self._generated_roadmap = generated_roadmap

    @property
    def generated_roadmap(self) -> RoadmapFromSimulation:
        return self._generated_roadmap

    @property
    def report(self) -> Report:
        return self._report

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'report': cls.Report.create_from_api_dict(obj_data['report']),
            'generated_roadmap': RoadmapFromSimulation.retrieve_by_id(obj_data['roadmap']['id'])
        }

    def export_roadmap_data_for_dataframe(self) -> tuple[list[str], list[list]]:
        columns = ['Date', 'Attitude mode', 'Thruster mode']
        data = []
        for action in self.generated_roadmap.attitude_actions:
            data.append([action.date, action.attitude_mode.value, ""])
        for action in self.generated_roadmap.thruster_actions:
            data.append([action.date, "", action.thruster_mode.value])

        # Now merge the data, sorting by date
        data.sort(key=lambda x: x[0])

        # If times are the same, merge the rows by having attitude in attitude column and thruster in thruster column
        i = 0
        while i < len(data) - 1:
            if data[i][0] == data[i + 1][0]:
                data[i][1] = data[i][1] + data[i + 1][1]
                data[i][2] = data[i][2] + data[i + 1][2]
                data.pop(i + 1)
            else:
                i += 1
        # If attitude or thruster is empt, copy the previous value
        for i in range(1, len(data)):
            if data[i][1] == "":
                data[i][1] = data[i - 1][1]
            if data[i][2] == "":
                data[i][2] = data[i - 1][2]

        return columns, data

    def export_thruster_data_for_gantt(self) -> tuple[list[str], list[list]]:
        columns = ['Start', 'End', 'Mode']
        data = []
        for action in self.generated_roadmap.thruster_actions:
            # Find the next thruster action
            next_action = None
            for a in self.generated_roadmap.thruster_actions:
                if a.date > action.date:
                    next_action = a
                    break
            if next_action is None:
                next_action = self.generated_roadmap.thruster_actions[-1]
            data.append([action.date, next_action.date, action.thruster_mode.value])

        # Now merge the data, sorting by date
        data.sort(key=lambda x: x[0])

        # If there are two consecutive actions with the same mode, merge them (keep the first date)
        self.merge_consecutive_actions(data)
        return columns, data

    def export_attitude_data_for_gantt(self) -> tuple[list[str], list[list]]:
        columns = ['Start', 'End', 'Mode']
        data = []
        for action in self.generated_roadmap.attitude_actions:
            # Find the next attitude action
            next_action = None
            for a in self.generated_roadmap.attitude_actions:
                if a.date > action.date:
                    next_action = a
                    break
            if next_action is None:
                next_action = self.generated_roadmap.attitude_actions[-1]  # last action
            data.append([action.date, next_action.date, action.attitude_mode.value])

        # Now merge the data, sorting by date
        data.sort(key=lambda x: x[0])

        # If there are two consecutive actions with the same mode, merge them (keep the first date)
        self.merge_consecutive_actions(data)
        return columns, data

    @staticmethod
    def merge_consecutive_actions(data):
        i = 0
        while i < len(data) - 1:
            if data[i][2] == data[i + 1][2]:
                data[i][1] = data[i + 1][1]
                data.pop(i + 1)
            else:
                i += 1
