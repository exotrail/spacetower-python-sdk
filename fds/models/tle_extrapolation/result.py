from typing import Sequence

from fds.client import FdsClient
from fds.models._model import RetrievableModel
from fds.models.orbits import Orbit


class ResultTleExtrapolation(RetrievableModel):
    FDS_TYPE = FdsClient.Models.RESULT_TLE_EXTRAPOLATION

    def __init__(
            self,
            extrapolated_orbits: list[Orbit],
            nametag: str = None
    ):
        super().__init__(nametag)
        extrapolated_orbits.sort(key=lambda x: x.date)
        self._extrapolated_orbits = extrapolated_orbits

    @property
    def extrapolated_orbits(self) -> Sequence[Orbit]:
        return self._extrapolated_orbits

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'extrapolated_orbits': [Orbit.retrieve_generic_by_id(o['id']) for o in
                                    obj_data['orbits']]
        }
