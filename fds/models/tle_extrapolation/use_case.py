from datetime import datetime
from typing import Sequence

from fds.client import FdsClient
from fds.models._use_case import BaseUseCase
from fds.models.tle_extrapolation.result import ResultTleExtrapolation
from fds.models.two_line_element import TwoLineElement
from fds.utils.dates import get_datetime, datetime_to_iso_string


class TleExtrapolation(BaseUseCase):
    """
    This class is used to specify the data of a TLE extrapolation computation.
    """
    ResultType = ResultTleExtrapolation
    ":meta private:"
    FDS_TYPE = FdsClient.UseCases.TLE_EXTRAPOLATION
    ":meta private:"

    def __init__(
            self,
            initial_tle: TwoLineElement | str,
            target_dates: Sequence[datetime] | Sequence[str],
            nametag: str = None,
    ):
        super().__init__(nametag)

        if isinstance(initial_tle, str):
            initial_tle = TwoLineElement.from_single_line(initial_tle)

        self._initial_tle = initial_tle
        self._target_dates = [get_datetime(td) for td in target_dates]

    @property
    def initial_tle(self) -> TwoLineElement:
        """
        The TLE to propagate.
        """
        return self._initial_tle

    @property
    def target_dates(self) -> list[datetime]:
        """
        The dates to which the TLE is to be propagated.
        """
        return self._target_dates

    @property
    def result(self) -> ResultTleExtrapolation | None:
        """
        Computation results given as a ResultTleExtrapolation object.
        """
        return self._result

    def api_run_map(self, **kwargs) -> dict:
        """
        :meta private:
        """
        return {
            'initial_tle': self.initial_tle.to_api_tle(),
            'dates': [datetime_to_iso_string(td) for td in self.target_dates]
        }
