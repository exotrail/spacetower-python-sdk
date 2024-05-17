from fds.models.ground_station import GroundStation
from tests import TestModelsWithContainer, _test_initialisation


class TestGroundStation(TestModelsWithContainer):
    CLIENT_TYPE = GroundStation
    KWARGS = {'name': "My_ground_station", 'latitude': 0, 'longitude': 0, 'altitude': 0,
              'min_elevation': 0,
              'elevation_masks': [[1, 2], ],
              'nametag': 'TestGroundStation'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS, )

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)
