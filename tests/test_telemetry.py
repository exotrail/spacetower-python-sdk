from fds.models.ground_station import GroundStation
from fds.models.telemetry import TelemetryGpsNmea, TelemetryGpsNmeaRaw, TelemetryGpsPv, TelemetryRadar, TelemetryOptical
from tests import TestModelsWithContainer, _test_initialisation
from tests.test_ground_station import TestGroundStation


class TestTelemetryGpsNmea(TestModelsWithContainer):
    CLIENT_TYPE = TelemetryGpsNmea
    KWARGS_4 = {'measurements': [[1, 2, 3, 2], ],
                'dates': ["2023-05-22T00:00:00.000Z"],
                'standard_deviation_ground_speed': 1,
                'standard_deviation_latitude': 1,
                'standard_deviation_longitude': 1,
                'standard_deviation_altitude': 1,
                'nametag': 'TestTelemetryGpsNmea'}

    KWARGS_5 = {'measurements': [[1, 2, 3, 1, 2], ],
                'dates': ["2023-05-22T00:00:00.000Z"],
                'standard_deviation_ground_speed': 1,
                'standard_deviation_latitude': 1,
                'standard_deviation_longitude': 1,
                'standard_deviation_altitude': 1,
                'nametag': 'TestTelemetryGpsNmea'}

    KWARGS_6 = {'measurements': [[1, 2, 3, 1, 2, 4], ],
                'dates': ["2023-05-22T00:00:00.000Z"],
                'standard_deviation_ground_speed': 1,
                'standard_deviation_latitude': 1,
                'standard_deviation_longitude': 1,
                'standard_deviation_altitude': 1,
                'nametag': 'TestTelemetryGpsNmea'}

    def test_initialisation_4(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS_4)

    def test_initialisation_5(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS_5)

    def test_initialisation_error(self):
        try:
            _test_initialisation(self.CLIENT_TYPE, **self.KWARGS_5)
        except ValueError as v:
            self.assertTrue(v == "Wrong dimension of NMEA measurements, it should be 4 or 5 (if geoid is included)")

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS_4)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE, measurements=self.KWARGS_4.get('measurements'),
                                           dates=self.KWARGS_4.get('dates'))

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS_4)


class TestTelemetryGpsNmeaRaw(TestModelsWithContainer):
    CLIENT_TYPE = TelemetryGpsNmeaRaw
    KWARGS_1 = {'nmea_sentences': [
        "$GPGGA,183747.00,4930.0428,S,08843.6229,W,1,20,0.7,542291.75,M,-2.00,M,,*44",
        "$GPRMC,183747.00,A,4930.0428270,S,08843.6229247,W,14896.408,194.0,290623,0.0,E,A*36"
    ],
        'standard_deviation_ground_speed': 1,
        'standard_deviation_latitude': 1,
        'standard_deviation_longitude': 1,
        'standard_deviation_altitude': 1, 'nametag': 'TestTelemetryGpsNmeaRawWithRmcAndGga'}

    KWARGS_2 = {'nmea_sentences': [KWARGS_1.get('nmea_sentences')[1]],
                'standard_deviation_ground_speed': 1,
                'standard_deviation_latitude': 1,
                'standard_deviation_longitude': 1,
                'standard_deviation_altitude': 1, 'nametag': 'TestTelemetryGpsNmeaRawWithRmc'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS_1)
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS_2)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS_1)
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS_2)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE, nmea_sentences=self.KWARGS_1.get('nmea_sentences'))
        self._test_import_from_config_file(self.CLIENT_TYPE, nmea_sentences=self.KWARGS_2.get('nmea_sentences'))

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS_1)
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS_2)


class TestTelemetryGpsPv(TestModelsWithContainer):
    CLIENT_TYPE = TelemetryGpsPv
    KWARGS = {'dates': ["2023-05-22T00:00:00.000Z"], 'measurements': [[1, 2, 3, 4, 5, 6], ],
              'standard_deviation_position': 1,
              'standard_deviation_velocity': 1,
              'frame': 'TEME',
              'nametag': 'TestTelemetryGpsPv'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE, measurements=self.KWARGS.get('measurements'),
                                           dates=self.KWARGS.get('dates'), frame=self.KWARGS.get('frame'))

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestTelemetryRadar(TestModelsWithContainer):
    CLIENT_TYPE = TelemetryRadar
    gs = GroundStation(**TestGroundStation.KWARGS)
    KWARGS = {'dates': ["2023-05-22T00:00:00.000Z"], 'measurements': [[1, 2, 3, 4], ],
              'ground_station': gs,
              'two_way_measurement': True,
              'standard_deviation_azimuth': 1,
              'standard_deviation_elevation': 1,
              'standard_deviation_range': 1,
              'standard_deviation_range_rate': 1,
              'nametag': 'TestTelemetryRadar'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE, measurements=self.KWARGS.get('measurements'),
                                           dates=self.KWARGS.get('dates'),
                                           ground_station=self.KWARGS.get('ground_station'))

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)


class TestTelemetryOptical(TestModelsWithContainer):
    CLIENT_TYPE = TelemetryOptical
    gs = GroundStation(**TestGroundStation.KWARGS)
    KWARGS = {'dates': ["2023-05-22T00:00:00.000Z"], 'measurements': [[1, 2], ],
              'ground_station': gs,
              'standard_deviation_azimuth': 1,
              'standard_deviation_elevation': 1,
              'nametag': 'TestTelemetryOptical'}

    def test_initialisation(self):
        _test_initialisation(self.CLIENT_TYPE, **self.KWARGS)

    def test_save_and_destroy(self):
        self._test_save_and_destroy(self.CLIENT_TYPE, **self.KWARGS)

    def test_import_from_config_file(self):
        self._test_import_from_config_file(self.CLIENT_TYPE, measurements=self.KWARGS.get('measurements'),
                                           dates=self.KWARGS.get('dates'),
                                           ground_station=self.KWARGS.get('ground_station'))

    def test_save_and_retrieve_by_id_and_destroy(self):
        self._test_save_and_retrieve_by_id_and_destroy(self.CLIENT_TYPE, **self.KWARGS)
