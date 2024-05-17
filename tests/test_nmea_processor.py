import unittest
from datetime import UTC, datetime
from pathlib import Path

from fds.models.nmea_processor import NmeaProcessor


class TestNmeaProcessor(unittest.TestCase):
    TELEMETRY_FOLDER_PATH = Path(__file__).parent / 'data' / 'nmea_processor'

    def test_nmea_processor_from_multiple_files_all(self):
        folder_path = self.TELEMETRY_FOLDER_PATH / 'multiple_files'
        proc = NmeaProcessor.from_folder(folder_path)
        sentences = proc.generate_sentences()
        # compare with "valid_sentences_multiple_files_all.txt"
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_multiple_files_all.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = proc.get_merged_sentences(sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        proc = NmeaProcessor.from_single_file(file_path)
        sentences = proc.generate_sentences()
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_all.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = proc.get_merged_sentences(sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_filter_by_start_date(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        proc = NmeaProcessor.from_single_file(file_path)
        sentences = proc.generate_sentences(
            measurement_start_date_limit=datetime(2024, 1, 7, tzinfo=UTC),
        )
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_filtered_start_date.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = proc.get_merged_sentences(sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_filter_by_end_date(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        proc = NmeaProcessor.from_single_file(file_path)
        sentences = proc.generate_sentences(
            measurement_end_date_limit=datetime(2024, 1, 7, tzinfo=UTC),
        )
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_filtered_end_date.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = proc.get_merged_sentences(sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_filter_by_step(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        proc = NmeaProcessor.from_single_file(file_path)
        sentences = proc.generate_sentences(
            measurement_min_step=20,
        )
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_filtered_step.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = proc.get_merged_sentences(sentences)
        self.assertEqual(sentences_merged, valid_sentences)

    def test_nmea_processor_from_single_file_no_gga(self):
        file_path = self.TELEMETRY_FOLDER_PATH / 'raw_sentences_single_file.txt'
        proc = NmeaProcessor.from_single_file(file_path)
        sentences = proc.generate_sentences()
        valid_sentences_path = self.TELEMETRY_FOLDER_PATH / 'valid_sentences_single_file_no_gga.txt'
        with open(valid_sentences_path, 'r') as f:
            valid_sentences = f.readlines()
        valid_sentences = [s.strip() for s in valid_sentences]
        sentences_merged = proc.get_merged_sentences(sentences, use_gga=False)
        self.assertEqual(sentences_merged, valid_sentences)
