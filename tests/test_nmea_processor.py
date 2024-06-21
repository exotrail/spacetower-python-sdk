import unittest
from datetime import UTC, datetime
from pathlib import Path

from fds.utils import nmea


class TestNmeaProcessor(unittest.TestCase):
    TELEMETRY_FOLDER_PATH = Path(__file__).parent / 'data' / 'nmea_processor'

    def test_nmea_processor_from_multiple_files_all(self):
        folder_path = self.TELEMETRY_FOLDER_PATH / 'multiple_files'
        processed_sentences = nmea.parse_raw_sentences_from_folder(folder_path)
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_multiple_files_all.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = nmea.export_list_of_sentences(processed_sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_all.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        processed_sentences = nmea.parse_raw_sentences_from_file(file_path)
        sentences_merged = nmea.export_list_of_sentences(processed_sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_filter_by_start_date(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        processed_sentences = nmea.parse_raw_sentences_from_file(file_path)
        filtered_sentences = nmea.filter_sentences(
            processed_sentences, measurement_start_date_limit=datetime(2024, 1, 7, tzinfo=UTC))
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_filtered_start_date.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = nmea.export_list_of_sentences(filtered_sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_filter_by_end_date(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        processed_sentences = nmea.parse_raw_sentences_from_file(file_path)
        filtered_sentences = nmea.filter_sentences(processed_sentences,
                                                   measurement_end_date_limit=datetime(2024, 1, 7, tzinfo=UTC))
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_filtered_end_date.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = nmea.export_list_of_sentences(filtered_sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_filter_by_step(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        processed_sentences = nmea.parse_raw_sentences_from_file(file_path)
        filtered_sentences = nmea.filter_sentences(processed_sentences, measurement_min_step=20)
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_filtered_step.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = nmea.export_list_of_sentences(filtered_sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_no_gga(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        processed_sentences = nmea.parse_raw_sentences_from_file(file_path)
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_no_gga.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = nmea.export_list_of_sentences(processed_sentences, use_gga=False)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_write_measurements(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        processed_sentences = nmea.parse_raw_sentences_from_file(file_path)
        measurements: list[nmea.NmeaMeasurement] = nmea.get_list_of_measurements_from_sentences(processed_sentences)
        valid_measurements_path = self.TELEMETRY_FOLDER_PATH / 'valid_measurements_single_file.txt'
        with open(valid_measurements_path, 'r') as f:
            test_measurements = f.readlines()
        for measurement, test_measurement in zip(measurements, test_measurements):
            test_measurement_split = test_measurement.strip().split(',')
            self.assertEqual(measurement.date, datetime.fromisoformat(test_measurement_split[0]))
            self.assertEqual(measurement.latitude, float(test_measurement_split[1]))
            self.assertEqual(measurement.longitude, float(test_measurement_split[2]))
            self.assertEqual(measurement.ground_speed, float(test_measurement_split[3]))
            altitude = test_measurement_split[4]
            if altitude == 'None':
                self.assertIsNone(measurement.altitude)
            else:
                self.assertEqual(measurement.altitude, float(altitude))

            geoid_height = test_measurement_split[5]
            if geoid_height == 'None':
                self.assertIsNone(measurement.geoid_height)
            else:
                self.assertEqual(measurement.geoid_height, float(geoid_height))

    def test_transformation_of_raw_data_in_list_of_measurements(self):

        valid_measurements_path = self.TELEMETRY_FOLDER_PATH / 'valid_measurements_single_file.txt'
        with open(valid_measurements_path, 'r') as f:
            test_measurements = f.readlines()

        dates = []
        raw_measurements = []
        for test_measurement in test_measurements:
            test_measurement_split = test_measurement.strip().split(',')
            dates.append(datetime.fromisoformat(test_measurement_split[0]))
            altitude = float(test_measurement_split[4]) if test_measurement_split[4] != 'None' else None
            geoid_height = float(test_measurement_split[5]) if test_measurement_split[5] != 'None' else None
            raw_measurements.append([
                float(test_measurement_split[1]),
                float(test_measurement_split[2]),
                float(test_measurement_split[3]),
                altitude,
                geoid_height
            ])

        measurements = nmea.get_list_of_measurements_from_raw_and_dates(
            raw_measurements, dates
        )

        for measurement, raw_measurement, raw_date in zip(measurements, raw_measurements, dates):
            self.assertEqual(measurement.date, raw_date)
            self.assertEqual(measurement.latitude, raw_measurement[0])
            self.assertEqual(measurement.longitude, raw_measurement[1])
            self.assertEqual(measurement.ground_speed, raw_measurement[2])
            self.assertEqual(measurement.altitude, raw_measurement[3])
            self.assertEqual(measurement.geoid_height, raw_measurement[4])

    def test_rmc_sentence_parsing(self):
        from fds.constants import KN_TO_MPS
        rmc = "$GPRMC,161229.487,A,3723.2475,N,12158.3416,W,0.13,309.62,120598,,,*10"
        rmc_sentence = nmea.RmcSentence.parse(rmc)

        self.assertEqual(rmc_sentence.utc_time, "161229.487")
        self.assertEqual(rmc_sentence.status, "A")
        latitude_deg = 37
        latitude_min = 23.2475
        latitude = latitude_deg + latitude_min / 60
        self.assertEqual(rmc_sentence.latitude, latitude)
        longitude_deg = 121
        longitude_min = 58.3416
        longitude = - (longitude_deg + longitude_min / 60)
        self.assertEqual(rmc_sentence.longitude, longitude)
        self.assertEqual(rmc_sentence.ground_speed, 0.13 * KN_TO_MPS)
        self.assertEqual(rmc_sentence.course_over_ground, 309.62)
        date = datetime(1998, 5, 12, 16, 12, 29, 487000, tzinfo=UTC)
        self.assertEqual(rmc_sentence.date, date)
        self.assertEqual(rmc_sentence.magnetic_variation, None)
        self.assertEqual(rmc_sentence.sentence, rmc.replace(' ', ''))

    def test_gga_sentence_parsing(self):
        gga = "$GPGGA,161229.487,3723.2475,N,12158.3416,W,1,07,1.0,9.0,M, , , ,0000*18"
        gga_sentence = nmea.GgaSentence.parse(gga)

        self.assertEqual(gga_sentence.utc_time, "161229.487")
        latitude_deg = 37
        latitude_min = 23.2475
        latitude = latitude_deg + latitude_min / 60
        self.assertEqual(gga_sentence.latitude, latitude)
        longitude_deg = 121
        longitude_min = 58.3416
        longitude = - (longitude_deg + longitude_min / 60)
        self.assertEqual(gga_sentence.longitude, longitude)
        self.assertEqual(gga_sentence.quality_indicator, 1)
        self.assertEqual(gga_sentence.satellites_used, 7)
        self.assertEqual(gga_sentence.hdop, 1.0)
        self.assertEqual(gga_sentence.msl_altitude, 9.0)
        self.assertEqual(gga_sentence.geoid_separation, None)
        self.assertEqual(gga_sentence.differential_base_station_id, "0000")
        self.assertEqual(gga_sentence.age_of_diff_corr, None)
        self.assertEqual(gga_sentence.sentence, gga.replace(' ', ''))

    def test_sentence_validity(self):

        valid_rmc = "$GPRMC,161229.487,A,3723.2475,N,12158.3416,W,0.13,309.62,120598,,,*10"
        is_valid_1 = nmea.RmcSentence.is_valid(valid_rmc, raise_if_false=False)
        self.assertTrue(is_valid_1)

        valid_rmc = "$GPRMC,090341.00,A,7042.8523999,N,17951.6887751,E,14925.246,335.8,040524,0.0,E,A*36"
        is_valid = nmea.RmcSentence.is_valid(valid_rmc, raise_if_false=False)
        self.assertTrue(is_valid)

        wrong_rmc_1 = "$GPSSS,161229.487,A,3723.2475,N,12158.3416,W,0.13,309.62,120598,,*10"
        is_valid_2 = nmea.RmcSentence.is_valid(wrong_rmc_1, raise_if_false=False)
        self.assertFalse(is_valid_2)

        wrong_rmc_2 = "$GPRMC,161229.487,A,3723.2475,N,12158.3416,W,0.13,309.62,120598,*10"
        is_valid_3 = nmea.RmcSentence.is_valid(wrong_rmc_2, raise_if_false=False)
        self.assertFalse(is_valid_3)

        valid_gga = "$GPGGA,161229.487,3723.2475,N,12158.3416,W,1,07,1.0,9.0,M,,,,0000*18"
        is_valid_4 = nmea.GgaSentence.is_valid(valid_gga, raise_if_false=False)
        self.assertTrue(is_valid_4)

        wrong_gga_1 = "$GPGGA,161229.487,3723.2475,N,12158.3416,W,1,07,1.0,9.0,M, , , ,0000"
        is_valid_5 = nmea.GgaSentence.is_valid(wrong_gga_1, raise_if_false=False)
        self.assertFalse(is_valid_5)

        wrong_gga_2 = "$GPGGA,161229.487,3723.2475,N,12158.3416,W,1,07,1.0,9.0,M, , , ,0000*18*18"
        is_valid_6 = nmea.GgaSentence.is_valid(wrong_gga_2, raise_if_false=False)
        self.assertFalse(is_valid_6)
