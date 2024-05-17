from fds.models.spacecraft import Battery, SolarArray, ThrusterElectrical, SpacecraftSphere, SpacecraftBox
from tests import TestModels, _test_initialisation, TestModelsWithContainer


class TestBattery(TestModels):
    CLIENT_TYPE = Battery
    KWARGS = {'depth_of_discharge': 1, 'nominal_capacity': 1,
              'minimum_charge_for_firing': 1,
              'initial_charge': 1, 'nametag': "TestBattery"}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestSolarArray(TestModels):
    CLIENT_TYPE = SolarArray
    KWARGS = {'kind': 'DEPLOYABLE_FIXED',
              'initialisation_kind': 'MAXIMUM_POWER',
              'efficiency': 0.1,
              'normal_in_satellite_frame': [1, 0, 0],
              'maximum_power': 100,
              'axis_in_satellite_frame': [1, 0, 0],
              'satellite_faces': ['MINUS_X', 'PLUS_X'],
              'nametag': 'TestSolarArray'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestElectricalThruster(TestModels):
    CLIENT_TYPE = ThrusterElectrical
    KWARGS = {'impulse': 1, 'maximum_thrust_duration': 1, 'propellant_mass': 1, 'thrust': 1,
              'axis_in_satellite_frame': [1, 0, 0], 'isp': 1, 'wet_mass': 1, 'warm_up_duration': 1,
              'power': 1, 'stand_by_power': 1, 'warm_up_power': 1, 'nametag': 'TestElectricalThruster'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_update_of_thrust(self):
        thruster = self.CLIENT_TYPE(**self.KWARGS)
        thruster.save()
        previous_id = thruster.client_id
        thruster.destroy()
        thruster.thrust = 0.9
        self.assertTrue(thruster.client_id is None)
        thruster.save()
        new_id = thruster.client_id
        self.assertNotEqual(previous_id, new_id)
        self.assertEqual(thruster.thrust, 0.9)
        thruster.destroy()

    def test_update_of_power(self):
        thruster = self.CLIENT_TYPE(**self.KWARGS)
        thruster.save()
        previous_id = thruster.client_id
        thruster.destroy()
        thruster.power = 0.9
        self.assertTrue(thruster.client_id is None)
        thruster.save()
        new_id = thruster.client_id
        self.assertNotEqual(previous_id, new_id)
        self.assertEqual(thruster.power, 0.9)
        thruster.destroy()


class TestSpacecraftSphere(TestModels):
    CLIENT_TYPE = SpacecraftSphere
    KWARGS = {'platform_mass': 100, 'drag_coefficient': 1,
              'cross_section': 1, 'reflectivity_coefficient': 1, 'nametag': 'TestSpacecraftSphere'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestSpacecraftBox(TestModelsWithContainer):
    CLIENT_TYPE = SpacecraftBox
    bat = Battery(**TestBattery.KWARGS)
    sa = SolarArray(**TestSolarArray.KWARGS)
    thr = ThrusterElectrical(**TestElectricalThruster.KWARGS)
    KWARGS = {'platform_mass': 100, 'drag_coefficient': 1,
              'reflectivity_coefficient': 1,
              'max_angular_acceleration': 1, 'max_angular_velocity': 1,
              'length_x': 1, 'length_y': 1, 'length_z': 1,
              'nametag': 'TestSpacecraftSphere',
              'battery': bat, 'solar_array': sa, 'thruster': thr}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE)

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS,
                                                       destroy_subcomponents=True)

    def test_update_of_propellant_mass(self):
        spacecraft = self.CLIENT_TYPE(**self.KWARGS)
        previous_propellant_mass = spacecraft.propellant_mass
        previous_wet_mass = spacecraft.platform_mass
        previous_dry_mass = spacecraft.dry_mass

        spacecraft.save()
        previous_id = spacecraft.client_id
        previous_thruster_id = spacecraft.thruster.client_id

        spacecraft.destroy(destroy_subcomponents=True)

        spacecraft.propellant_mass = 0.9
        self.assertTrue(spacecraft.client_id is None)
        self.assertTrue(spacecraft.thruster.client_id is None)

        spacecraft.save()

        new_id = spacecraft.client_id

        self.assertNotEqual(previous_id, new_id)
        self.assertNotEqual(previous_thruster_id, spacecraft.thruster.client_id)

        self.assertEqual(spacecraft.propellant_mass, 0.9)
        self.assertEqual(spacecraft.dry_mass, previous_dry_mass)
        self.assertEqual(spacecraft.platform_mass, previous_wet_mass - (previous_propellant_mass - 0.9))

        spacecraft.destroy(destroy_subcomponents=True)
