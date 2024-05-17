import numpy as np

from fds.models.orbital_state import OrbitalState, PropagationContext, CovarianceMatrix
from fds.models.orbits import KeplerianOrbit, CartesianState
from fds.models.spacecraft import SpacecraftSphere
from fds.models.two_line_element import TwoLineElement
from tests import TestModelsWithContainer, _test_initialisation, TestModels
from tests.test_spacecraft import TestSpacecraftSphere


class TestKeplerianOrbit(TestModelsWithContainer):
    CLIENT_TYPE = KeplerianOrbit
    KWARGS = {'semi_major_axis': 7000, 'anomaly': 0, 'argument_of_perigee': 0, 'eccentricity': 0.0001,
              'inclination': 45, 'raan': 0, 'anomaly_kind': "MEAN",
              'kind': "OSC", 'date': "2000-01-01T00:00:00.000Z", 'nametag': "TestKeplerianOrbit"}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_angle_ranges(self):
        raan_out_of_range = 200
        raan_in_range = -160

        inclination_out_of_range = 200
        inclination_in_range = 20

        argument_of_perigee_out_of_range = -50
        argument_of_perigee_in_range = 310

        anomaly_out_of_range = -50
        anomaly_in_range = 310

        orbit = KeplerianOrbit(
            semi_major_axis=7000,
            eccentricity=0.1,
            inclination=inclination_out_of_range,
            raan=raan_out_of_range,
            argument_of_perigee=argument_of_perigee_out_of_range,
            anomaly=anomaly_out_of_range,
            anomaly_kind="MEAN",
            kind="OSC",
            date="2021-04-24T14:55:01.769664+00:00",
        )

        self.assertTrue(orbit.orbital_elements.RAAN == raan_in_range)
        self.assertTrue(orbit.orbital_elements.INC == inclination_in_range)
        self.assertTrue(orbit.orbital_elements.AOP == argument_of_perigee_in_range)
        self.assertTrue(orbit.orbital_elements.MA == anomaly_in_range)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestCartesianOrbit(TestModelsWithContainer):
    CLIENT_TYPE = CartesianState
    KWARGS = {
        'position_x': 7000, 'position_y': 0, 'position_z': 0,
        'velocity_x': 0, 'velocity_y': 7.546, 'velocity_z': 0,
        'frame': "TNW", 'date': "2000-01-01T00:00:00.000Z", 'nametag': "TestCartesianOrbit"
    }

    KWARGS_POSITION_VELOCITY = {
        'position': [7000, 0, 0],
        'velocity': [0, 7.546, 0],
        'frame': "TNW", 'date': "2000-01-01T00:00:00.000Z", 'nametag': "TestCartesianOrbit"
    }

    KWARGS_STATE = {
        'state': [7000, 0, 0, 0, 7.546, 0],
        'frame': "TNW", 'date': "2000-01-01T00:00:00.000Z", 'nametag': "TestCartesianOrbit"
    }

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def _test_save_and_destroy_position_velocity(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS_POSITION_VELOCITY)

    def _test_save_and_destroy_state(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS_STATE)


class TestPropagationContext(TestModelsWithContainer):
    CLIENT_TYPE = PropagationContext
    KWARGS = {'integrator_min_step': 0.1, 'integrator_max_step': 1, 'integrator_kind': "DORMAND_PRINCE_54",
              'model_perturbations': ["DRAG", "SRP"], 'model_solar_flux': 1, 'model_earth_potential_deg': 2,
              'model_earth_potential_ord': 0, 'model_atmosphere_kind': "HARRIS_PRIESTER",
              'nametag': 'TestPropagationContext'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS, )

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestCovarianceMatrix(TestModels):
    CLIENT_TYPE = CovarianceMatrix
    KWARGS = {'matrix': np.eye(6),
              'orbit_type': 'CARTESIAN',
              'frame': "TNW",
              'nametag': 'TestCovarianceMatrix'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestOrbitalState(TestModels):
    CLIENT_TYPE = OrbitalState
    cov = CovarianceMatrix(**TestCovarianceMatrix.KWARGS)
    mean_orb = KeplerianOrbit(**TestKeplerianOrbit.KWARGS)
    osc_orb = KeplerianOrbit(**TestKeplerianOrbit.KWARGS)
    prop = PropagationContext(**TestPropagationContext.KWARGS)
    spacecraft = SpacecraftSphere(**TestSpacecraftSphere.KWARGS)

    KWARGS_INITIALISATION = {'covariance_matrix': cov,
                             'creation_date': "2023-05-23T00:00:00.000Z",
                             'fitted_tle': TwoLineElement(
                                 '1 00000U 00000    21001.00000000  .00000000  00000-0  00000-0 0    07',
                                 '2 00000   9.9949  10.2446 0012938 208.9322 171.0909 14.84346361    05'),
                             'mean_orbit': mean_orb,
                             'osculating_orbit': osc_orb,
                             'propagation_context': prop,
                             'source': OrbitalState.Source.MANUAL,
                             'spacecraft': spacecraft,
                             'nametag': 'TestOrbitalState'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS_INITIALISATION)

    def test_creation_request(self):
        os_from_orbit = OrbitalState.from_orbit(
            covariance_matrix=self.KWARGS_INITIALISATION.get('covariance_matrix'),
            orbit=self.KWARGS_INITIALISATION.get('mean_orbit'),
            propagation_context=self.KWARGS_INITIALISATION.get('propagation_context'),
            spacecraft=self.KWARGS_INITIALISATION.get('spacecraft')
        )

        tle = os_from_orbit.fitted_tle

        os_from_tle = OrbitalState.from_tle(
            covariance_matrix=self.KWARGS_INITIALISATION.get('covariance_matrix'),
            tle=tle,
            propagation_context=self.KWARGS_INITIALISATION.get('propagation_context'),
            spacecraft=self.KWARGS_INITIALISATION.get('spacecraft')
        )

        self.assertTrue(os_from_orbit.fitted_tle.line_1 == os_from_tle.fitted_tle.line_1)
        self.assertTrue(os_from_orbit.fitted_tle.line_2 == os_from_tle.fitted_tle.line_2)

        # Test deletion
        os_from_orbit.destroy()
        os_from_tle.destroy()

    def test_creation_with_and_without_covariance(self):
        kwargs_with = self.KWARGS_INITIALISATION.copy()
        os = OrbitalState(**kwargs_with).save()
        kwargs_without = self.KWARGS_INITIALISATION.copy()
        kwargs_without.pop('covariance_matrix')
        os_without = OrbitalState(**kwargs_without).save()
        self.assertTrue(os.covariance_matrix.client_id is not None)
        self.assertTrue(os_without.covariance_matrix is None)
        os.destroy()
        os_without.destroy()

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS_INITIALISATION)

    def test_spacecraft_update(self):
        os_from_orbit = OrbitalState.from_orbit(
            covariance_matrix=self.KWARGS_INITIALISATION.get('covariance_matrix'),
            orbit=self.KWARGS_INITIALISATION.get('mean_orbit'),
            propagation_context=self.KWARGS_INITIALISATION.get('propagation_context'),
            spacecraft=self.KWARGS_INITIALISATION.get('spacecraft')
        )

        # Update spacecraft
        new_spacecraft = SpacecraftSphere(platform_mass=200, drag_coefficient=2,
                                          cross_section=2, reflectivity_coefficient=2, nametag='TestSpacecraftSphere2')
        os_from_orbit.spacecraft = new_spacecraft
        os_from_orbit.save()

        os_from_orbit_retrieved = OrbitalState.retrieve_by_id(os_from_orbit.client_id)

        self.assertTrue(os_from_orbit_retrieved.spacecraft.client_id == new_spacecraft.client_id)
        self.assertTrue(os_from_orbit_retrieved.spacecraft.platform_mass == 200)
        self.assertTrue(os_from_orbit_retrieved.spacecraft.drag_coefficient == 2)
        self.assertTrue(os_from_orbit_retrieved.spacecraft.cross_section == 2)
        self.assertTrue(os_from_orbit_retrieved.spacecraft.reflectivity_coefficient == 2)

    def test_covariance_update(self):
        os_from_orbit = OrbitalState.from_orbit(
            covariance_matrix=self.KWARGS_INITIALISATION.get('covariance_matrix'),
            orbit=self.KWARGS_INITIALISATION.get('mean_orbit'),
            propagation_context=self.KWARGS_INITIALISATION.get('propagation_context'),
            spacecraft=self.KWARGS_INITIALISATION.get('spacecraft')
        )

        # Update covariance
        new_covariance = CovarianceMatrix(matrix=np.eye(6), orbit_type='CARTESIAN', frame='TNW',
                                          nametag='TestCovarianceMatrix2')
        os_from_orbit.covariance_matrix = new_covariance
        os_from_orbit.save()

        os_from_orbit_retrieved = OrbitalState.retrieve_by_id(os_from_orbit.client_id)

        self.assertTrue(os_from_orbit_retrieved.covariance_matrix.client_id == new_covariance.client_id)
        self.assertTrue(np.array_equal(os_from_orbit_retrieved.covariance_matrix.matrix, np.eye(6)))
        self.assertTrue(os_from_orbit_retrieved.covariance_matrix.orbit_type == 'CARTESIAN')
        self.assertTrue(os_from_orbit_retrieved.covariance_matrix.frame == 'TNW')
