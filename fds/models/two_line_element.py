from datetime import datetime, UTC, timedelta
from typing import Self

import numpy as np

from fds.utils.dates import check_datetime_time_zone_is_utc
from fds.utils.log import log_and_raise
from spacetower_python_client import TLE


class TwoLineElement:
    def __init__(self, line_1: str, line_2: str):
        """
        Args:
            line_1 (str): First line of the TLE
            line_2 (str): Second line of the TLE
        """
        self._line_1 = self.check_line(line_1)
        self._line_2 = self.check_line(line_2)

    @property
    def line_1(self):
        return self._line_1

    @property
    def line_2(self):
        return self._line_2

    @property
    def single_line(self):
        return '\n'.join([self.line_1, self.line_2])

    @property
    def date(self) -> datetime:
        values = self.line_1.split()
        try:
            year = int(values[3][:2]) + 2000
        except ValueError:
            year = int(values[2][:2]) + 2000
        day_of_year = float(values[3][2:])
        return datetime(year, 1, 1, tzinfo=UTC) + timedelta(day_of_year - 1)

    @property
    def spacecraft_data(self):
        return self._line_1.split()[1]

    @property
    def launch_data(self):
        return self._line_1.split()[2]

    @spacecraft_data.setter
    def spacecraft_data(self, value):
        if len(value) != 6:
            log_and_raise(ValueError, "Spacecraft data (ID + object type) should be 6 characters long")
        line_1 = list(self._line_1)
        line_1[2:8] = list(value)
        line_2 = list(self._line_2)
        line_2[2:7] = list(value[:-1])
        new_line_1 = ''.join(line_1)
        checksum_line_1 = self._compute_checksum(new_line_1[:-1])
        line_1[-1] = str(checksum_line_1)
        new_line_2 = ''.join(line_2)
        checksum_line_2 = self._compute_checksum(new_line_2[:-1])
        line_2[-1] = str(checksum_line_2)
        self._line_1 = str(''.join(line_1))
        self._line_2 = str(''.join(line_2))

    @launch_data.setter
    def launch_data(self, value):
        match len(value):
            case 6:
                index_end = 15
            case 7:
                index_end = 16
            case 8:
                index_end = 17
            case _:
                log_and_raise(ValueError,
                              "Launch data (Launch year, day, piece) should be 6, 7 or 8 characters long")
        line_1 = list(self._line_1)
        line_1[9:index_end] = list(value)
        new_line = ''.join(line_1)
        checksum = self._compute_checksum(new_line[:-1])
        line_1[-1] = str(checksum)
        self._line_1 = str(''.join(line_1))

    def __eq__(self, other: Self) -> bool:
        return self.single_line == other.single_line

    @classmethod
    def from_single_line(cls, single_line_tle: str):
        """
        Args:
            single_line_tle (str): Single line TLE
        """
        [tle_line_1, tle_line_2] = single_line_tle.strip().split("\n")
        return cls(tle_line_1, tle_line_2)

    @classmethod
    def select_from_tle_list(
            cls,
            tle_list: list[Self],
            closest_date: datetime = datetime.now(UTC),
            force_past: bool = False,
    ):
        check_datetime_time_zone_is_utc(closest_date)

        tles = sorted(tle_list, key=lambda x: x.date)
        if closest_date is None or len(tles) == 1:
            return max(tles, key=lambda x: x.date)
        if force_past:
            available_tles = [tle for tle in tles if tle.date <= closest_date]
            if len(available_tles) == 0:
                msg = f"No TLE found before {closest_date}."
                log_and_raise(ValueError, msg)
            return max(available_tles, key=lambda x: x.date)
        return min(tles, key=lambda x: abs((x.date - closest_date).total_seconds()))

    @classmethod
    def _get_tles_from_spacetrack(
            cls,
            spacetrack_client,
            norad_cat_id: int,
            start_date_limit: datetime,
            end_date_limit: datetime
    ) -> list[Self]:
        """
        Args:
            spacetrack_client (SpaceTrackClient): SpaceTrackClient object from spacetrack package
            norad_cat_id (int): NORAD Catalogue ID
            start_date_limit (datetime): Start date limit (must be UTC)
            end_date_limit (datetime): End date limit (must be UTC)

        Returns:
            list[TwoLineElement]: List of TLEs
        """
        if start_date_limit >= end_date_limit:
            msg = f"Start date ({start_date_limit}) must be before end date ({end_date_limit})."
            log_and_raise(ValueError, msg)

        check_datetime_time_zone_is_utc(start_date_limit)
        check_datetime_time_zone_is_utc(end_date_limit)

        # Remove timezone info from dates (SpaceTrackClient does not support timezone aware dates)
        start_date_limit = start_date_limit.replace(tzinfo=None)
        end_date_limit = end_date_limit.replace(tzinfo=None)

        drange = start_date_limit.isoformat(sep=" ") + "--" + end_date_limit.isoformat(sep=" ")

        tles = spacetrack_client.gp_history(
            epoch=drange,
            norad_cat_id=int(norad_cat_id),
            format='tle'
        )

        tles = tles.split("\n")
        tles = tles[:-1]
        return TwoLineElement.create_from_string_list(tles)

    @classmethod
    def create_from_string_list(cls, tles):
        return [cls(tles[i], tles[i + 1]) for i in range(0, len(tles), 2)]

    @classmethod
    def from_spacetrack(
            cls,
            spacetrack_client,
            norad_cat_id: int,
            closest_date: datetime = datetime.now(UTC),
            force_past: bool = False,
    ):
        """
        Args:
            spacetrack_client (SpaceTrackClient): SpaceTrackClient object from spacetrack package
            norad_cat_id (int): NORAD Catalogue ID
            closest_date (datetime, optional): Date limit, gets the TLE closest to this date. Defaults to None.
            force_past (bool, optional): If True, gets the TLE closest to the date but before it. Defaults to False.
        """

        tles = cls._get_tles_from_spacetrack(
            spacetrack_client, norad_cat_id,
            start_date_limit=closest_date - timedelta(days=5),
            end_date_limit=closest_date + timedelta(days=5)
        )

        if len(tles) == 0:
            msg = f"No TLE found for NORAD ID {norad_cat_id}."
            log_and_raise(ValueError, msg)

        return cls.select_from_tle_list(tles, closest_date, force_past)

    def to_api_tle(self) -> TLE:
        return TLE(line1=self.line_1, line2=self.line_2)

    @classmethod
    def from_api_tle(cls, tle: TLE):
        return cls(tle.line1, tle.line2)

    @staticmethod
    def check_line(line: str) -> str:
        line = line.replace('\r', '')
        line = TwoLineElement._check_line_length(line)
        line = TwoLineElement._check_line_checksum(line)
        return line

    @staticmethod
    def _check_line_length(line: str) -> str:
        if len(line) != 69:
            log_and_raise(ValueError, f"TLE line should be 69 characters long, not {len(line)}.")
        return line

    @staticmethod
    def _check_line_checksum(line: str) -> str:
        check_sum = TwoLineElement._compute_checksum(line[:-1])
        if check_sum != int(line[-1]):
            log_and_raise(ValueError, f"Checksum of the TLE line is incorrect. "
                                      f"Expected {check_sum}, got {line[-1]}.")
        return line

    @staticmethod
    def _compute_checksum(line: str) -> int:
        """
        Args:
            line (str): Line of the TLE (without the checksum)

        Returns:
            int: Checksum of the line

        Source:
            Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL__tle_checksum
        """
        nb = len(line)

        if nb != 68:
            log_and_raise(ValueError, f"Line should be 68 characters long, not {nb}.")

        asc = np.array(list(map(ord, line)))
        val = np.zeros_like(asc)
        idx = np.where(asc == ord("-"))
        val[idx] = 1
        idx = np.where((asc >= ord("0")) & (asc <= ord("9")))
        if len(idx[0]) > 0:
            val[idx] = asc[idx] - ord("0")
        return np.sum(val) % 10

# %%
