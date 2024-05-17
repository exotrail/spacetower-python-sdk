import unittest

import numpy as np

from fds.models.tle_extrapolation.use_case import TleExtrapolation
from fds.models.two_line_element import TwoLineElement
from tests import TestUseCases


class TestTleExtrapolation(TestUseCases, unittest.TestCase):
    CLIENT_TYPE = TleExtrapolation

    def setUp(self):
        self.initial_tle = TwoLineElement(
            line_1="1 99999U 98067AF  23180.77623843 -.00000000  00000-0 -39596-4 0    11",
            line_2="2 99999  97.5099 297.1364 0014987 151.2712  78.3813 15.13639674000012"
        )
        self.dates = ["2023-05-25T00:00:00.000Z", "2023-05-27T00:00:00.000Z", "2023-05-30T00:00:00.000Z"]

        self.kwargs = {
            'initial_tle': self.initial_tle,
            'target_dates': self.dates
        }

    def test_tle_extrapolation_initialisation(self):
        self._test_initialisation()

    def test_tle_extrapolation_run(self):
        self._test_client_run()

    def test_tle_extrapolation(self):
        tle_extrap = TleExtrapolation(
            initial_tle=self.initial_tle,
            target_dates=self.dates
        ).run()

        result = tle_extrap.result

        orbits = result.extrapolated_orbits
        orb_el = [
            np.array([6.90758168e+03, 8.36437463e-05, 9.75057825e+01, 2.52930812e+02, -9.84236894e+01, 2.68545088e+02]),
            np.array([6.89226366e+03, 1.22460828e-03, 9.75141789e+01, 5.79699646e+01, -9.64583636e+01, 1.95229193e+02]),
            np.array([6.90461576e+03, 6.31928535e-04, 9.75074165e+01, 1.89334229e+02, -9.35030475e+01, 2.01329379e+02])]
        for o, date, o_el in zip(orbits, self.dates, orb_el):
            self.is_string_date_close(o.date, date)
            self.assertTrue(np.allclose(o.orbital_elements.as_array(), o_el, atol=1e-3))
