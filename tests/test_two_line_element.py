import unittest
from datetime import UTC, datetime
from pathlib import Path

from fds.models.two_line_element import TwoLineElement


class TestTwoLineElement(unittest.TestCase):
    TLE_FOLDER_PATH = Path(__file__).parent / 'data' / 'tles'

    def setUp(self):
        self.norad_id = 25544  # ISS
        self.line_1 = "1 25544U 98067A   21114.62154826  .00001929  00000-0  43263-4 0  9996"
        self.line_2 = "2 25544  51.6432 247.6705 0002585 270.7825 202.4775 15.48929355280294"
        self.tle = TwoLineElement(self.line_1, self.line_2)

    def test_from_single_line(self):
        single_line = f"{self.line_1}\n{self.line_2}"
        tle = TwoLineElement.from_single_line(single_line)

        self.assertTrue(tle.line_1 == self.line_1)
        self.assertTrue(tle.line_2 == self.line_2)
        self.assertTrue(tle.single_line == single_line)

    def test_date_extraction(self):
        date = self.tle.date
        self.assertTrue(date == datetime(2021, 4, 24, 14, 55, 1, 769664, tzinfo=UTC))

    def test_data_update(self):
        tle_start = TwoLineElement(
            line_1="1 00000U 00000    24108.30660880  .00000000  00000-0  00000-0 0    09",
            line_2="2 00000  97.4598 183.5897 0012441  81.8469 108.2618 15.16163926    09"
        )

        new_spacecraft_data = "99999U"
        new_launch_data = "12345AR"
        tle_start.spacecraft_data = new_spacecraft_data
        tle_start.launch_data = new_launch_data

        self.assertTrue(tle_start.spacecraft_data == new_spacecraft_data)
        self.assertTrue(tle_start.launch_data == new_launch_data)
        new_line_1 = "1 99999U 12345AR  24108.30660880  .00000000  00000-0  00000-0 0    09"
        new_line_2 = "2 99999  97.4598 183.5897 0012441  81.8469 108.2618 15.16163926    04"
        self.assertTrue(tle_start.line_1 == new_line_1)
        self.assertTrue(tle_start.line_2 == new_line_2)

    def test_checksum_calculation(self):
        starting_line_1 = "1 00000U 00000    24108.30660880  .00000000  00000-0  00000-0 0    09"
        starting_line_2 = "2 00000  97.4598 183.5897 0012441  81.8469 108.2618 15.16163926    09"
        correct_checksum_1 = int(starting_line_1[-1])
        correct_checksum_2 = int(starting_line_2[-1])
        tle = TwoLineElement(starting_line_1, starting_line_2)
        checksum_1 = tle._compute_checksum(tle.line_1[:-1])
        checksum_2 = tle._compute_checksum(tle.line_2[:-1])
        self.assertTrue(checksum_1 == correct_checksum_1)
        self.assertTrue(checksum_2 == correct_checksum_2)

    def test_from_spacetrack(self):
        # Read test file with previously downloaded TLEs (to avoid spamming the API)
        tle_file_path = self.TLE_FOLDER_PATH / 'tle_test.txt'
        with open(tle_file_path, 'r') as f:
            tles_test = f.read().splitlines()

        reference_date = datetime(2021, 4, 24, 12, 00, 00, tzinfo=UTC)

        tles_test = TwoLineElement.create_from_string_list(tles_test)
        tle_from_spacetrack = TwoLineElement.select_from_tle_list(
            tles_test,
            closest_date=reference_date,
            force_past=True
        )

        # Check which one should be the closest
        closest_past_tle = tles_test[5]  # confirmed by the test file
        self.assertTrue(tle_from_spacetrack == closest_past_tle)

        other_tle_from_spacetrack = TwoLineElement.select_from_tle_list(
            tles_test,
            closest_date=reference_date,
            force_past=False
        )

        closest_tle = tles_test[6]  # confirmed by the test file
        self.assertTrue(other_tle_from_spacetrack == closest_tle)

    def test_line_format_error(self):
        line_1_wrong_checksum = "1 25544U 98067A   21114.62154826  .00001929  00000-0  43263-4 0  9995"
        line_1_wrong_lenght = "1 25544U 98067A   21114.62154826  .00001929  00000-0  43263-4 0  999"
        self.assertRaises(ValueError, TwoLineElement.check_line, line_1_wrong_checksum)
        self.assertRaises(ValueError, TwoLineElement.check_line, line_1_wrong_lenght)

        line_with_slash_r = "1 25544U 98067A   21114.62154826  .00001929  00000-0  43263-4 0  9996\r"
        line_without_slash_r = "1 25544U 98067A   21114.62154826  .00001929  00000-0  43263-4 0  9996"
        self.assertTrue(TwoLineElement.check_line(line_with_slash_r) == line_without_slash_r)
