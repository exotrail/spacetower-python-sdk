import os
import re
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path

from loguru import logger

from fds.constants import RMC, GGA
from fds.utils.dates import filter_sequence_with_minimum_time_step
from fds.utils.log import log_and_raise


class NmeaProcessor:
    _rmc_pattern = re.compile(RMC)
    _gga_pattern = re.compile(GGA)

    @dataclass
    class Sentence:
        rmc: str
        date: datetime
        gga: str = None

    def __init__(
            self,
            raw_sentences: list[str],
    ):
        self._n_raw_sentences = len(raw_sentences)
        self._n_all_rmc_sentences = 0
        self._n_all_gga_sentences = 0
        self._n_valid_gga_sentences = 0
        self._n_valid_rmc_sentences = 0
        self._n_selected_rmc_sentences = 0
        self._n_selected_gga_sentences = 0
        self._no_gga_dates = []
        self._corrupted_gga_dates = []
        self._valid_dates_steps = []
        self._min_step = None

        self._valid_sentences = self._get_valid_sentences_and_dates(raw_sentences)

    @property
    def statistics(self):
        return {
            "raw_sentences": self._n_raw_sentences,
            "all_rmc_sentences": self._n_all_rmc_sentences,
            "all_gga_sentences": self._n_all_gga_sentences,
            "valid_gga_sentences": self._n_valid_gga_sentences,
            "valid_rmc_sentences": self._n_valid_rmc_sentences,
        }

    @property
    def no_gga_dates(self) -> list[datetime]:
        return self._no_gga_dates

    @property
    def corrupted_gga_dates(self) -> list[datetime]:
        return self._corrupted_gga_dates

    @property
    def valid_sentences(self) -> list[Sentence]:
        return self._valid_sentences

    @property
    def valid_dates_steps(self) -> list[float]:
        return self._valid_dates_steps

    @property
    def min_step(self) -> float:
        if self._min_step is None:
            self._min_step = min(self._valid_dates_steps)
        return self._min_step

    @classmethod
    def from_folder(
            cls,
            folder_path: str | Path,
    ):
        folder_path = Path(folder_path).resolve()

        if not folder_path.exists():
            log_and_raise(ValueError, f"Folder {folder_path} does not exist.")
        if not folder_path.is_dir():
            log_and_raise(ValueError, f"{folder_path} is not a folder.")

        raw_sentences = cls._read_raw_sentences(folder_path)

        return cls(raw_sentences)

    @classmethod
    def from_single_file(
            cls,
            file_path: str | Path,
    ):
        file_path = Path(file_path).resolve()

        if not file_path.exists():
            log_and_raise(ValueError, f"File {file_path} does not exist.")
        if not file_path.is_file():
            log_and_raise(ValueError, f"{file_path} is not a file.")

        with open(file_path, "r") as f:
            raw_sentences = f.readlines()

        return cls(raw_sentences)

    @staticmethod
    def get_merged_sentences(sentences: list[Sentence], use_gga: bool = True) -> list[str]:
        # Rebuild the list with gga first if it exists
        sentences_merged = []
        for sentence in sentences:
            if sentence.gga is not None and use_gga:  # there is a GGA sentence
                sentences_merged.append(sentence.gga)
                sentences_merged.append(sentence.rmc)
            else:
                sentences_merged.append(sentence.rmc)
        return sentences_merged

    @staticmethod
    def _read_raw_sentences(folder_path: Path) -> list[str]:
        raw_sentences = []
        all_files = os.listdir(folder_path)
        for filename in all_files:
            with open(os.path.join(folder_path, filename), "r") as f:
                raw_sentences += f.readlines()
        return raw_sentences

    def _get_valid_sentences_and_dates(
            self,
            raw_sentences: list[str]
    ) -> list[Sentence]:
        n_rmc_sentences = 0
        n_gga_sentences = 0
        n_valid_rmc_sentences = 0
        n_valid_gga_sentences = 0
        valid_sentences = []
        no_gga_dates = []
        corrupted_gga_dates = []

        for i, line in enumerate(raw_sentences):
            line = self.remove_return_char(line)
            line_type = line.split(',')[0]
            if line_type == '$GPRMC':
                n_rmc_sentences += 1
                if self._rmc_pattern.match(line):
                    if len(line.split(',')) == 13:
                        time_rmc = line.split(',')[1]
                        date_rmc = self.get_datetime_from_rmc_sentence(line)
                        valid_sentences.append(self.Sentence(rmc=line, date=date_rmc))
                        n_valid_rmc_sentences += 1
                        previous_line = self.remove_return_char(raw_sentences[i - 1]) if i > 0 else None
                        if previous_line is not None and previous_line.split(',')[0] == '$GPGGA':
                            n_gga_sentences += 1
                            if self._gga_pattern.match(previous_line):
                                time_gga = previous_line.split(',')[1]
                                if time_gga == time_rmc:
                                    valid_sentences[-1] = self.Sentence(rmc=line, gga=previous_line, date=date_rmc)
                                    n_valid_gga_sentences += 1
                            else:
                                corrupted_gga_dates.append(date_rmc)
                        else:
                            no_gga_dates.append(date_rmc)

        if len(valid_sentences) == 0:
            msg = "No RMC sentences found in the telemetry log file. Processing of NMEA sentences failed."
            log_and_raise(NmeaFileError, msg)

        if n_valid_gga_sentences == 0:
            logger.debug("No GGA sentences found in the telemetry log file.")

        # Sort the sentences by date
        valid_sentences.sort(key=lambda x: x.date)

        self._n_all_rmc_sentences = n_rmc_sentences
        self._n_all_gga_sentences = n_gga_sentences
        self._n_valid_gga_sentences = n_valid_gga_sentences
        self._n_valid_rmc_sentences = len(valid_sentences)
        self._no_gga_dates = no_gga_dates
        self._corrupted_gga_dates = corrupted_gga_dates
        self._valid_dates_steps = self.compute_time_step([sentence.date for sentence in valid_sentences])

        return list(valid_sentences)

    @staticmethod
    def remove_return_char(string: str):
        if string[-1] == '\n':
            string = string[:-1]
        return string

    @staticmethod
    def compute_time_step(dates: list[datetime]) -> list[float]:
        """Compute the time steps between the dates"""
        steps = []
        for i, date in enumerate(dates):
            if i > 0:
                step = (date - dates[i - 1]).total_seconds()
                steps.append(step)
        return steps

    @staticmethod
    def get_datetime_from_rmc_sentence(sentence: str) -> datetime:
        time = sentence.split(',')[1]
        date = datetime.strptime(sentence.split(',')[9] + ' ' + time, '%d%m%y %H%M%S.%f')
        return date.replace(tzinfo=UTC)

    def generate_sentences(
            self,
            measurement_start_date_limit: datetime = None,
            measurement_end_date_limit: datetime = None,
            measurement_min_step: float = None,
    ) -> list[Sentence]:

        selected_sentences = self.filter_sentences_by_date(
            self.valid_sentences,
            measurement_start_date_limit,
            measurement_end_date_limit)

        selected_sentences = self.filter_sentences_by_step(
            selected_sentences, measurement_min_step)

        self._min_step = measurement_min_step

        return selected_sentences

    @staticmethod
    def filter_sentences_by_date(sentences: list[Sentence],
                                 measurement_start_date_limit: datetime, measurement_end_date_limit: datetime) \
            -> list[Sentence]:
        sentences.sort(key=lambda x: x.date)
        dates = [sentence.date for sentence in sentences]
        if measurement_start_date_limit is None:
            measurement_start_date_limit = dates[0]

        if measurement_start_date_limit > dates[0]:
            if measurement_start_date_limit > dates[-1]:
                msg = (f"Desired start date limit {measurement_start_date_limit} is after the end date of the "
                       f"measurements {dates[-1]}.")
                log_and_raise(ValueError, msg)
            index_start = next(i for i, date in enumerate(dates) if date >= measurement_start_date_limit)
        else:
            index_start = 0

        if measurement_end_date_limit is None:
            measurement_end_date_limit = dates[-1]

        if measurement_end_date_limit < dates[-1]:
            if measurement_end_date_limit < dates[0]:
                msg = (f"Desired end date limit {measurement_end_date_limit} is before the start date of the "
                       f"measurements {dates[0]}.")
                log_and_raise(ValueError, msg)
            index_end = next(i for i, date in enumerate(dates) if date >= measurement_end_date_limit)
        else:
            index_end = len(dates)

        return sentences[index_start:index_end]

    @staticmethod
    def filter_sentences_by_step(sentences: list[Sentence],
                                 measurement_min_step: float) -> list[Sentence]:
        sentences.sort(key=lambda x: x.date)
        dates = [sentence.date for sentence in sentences]

        if measurement_min_step is None:
            return sentences

        return list(filter_sequence_with_minimum_time_step(sentences, dates, measurement_min_step))


class NmeaFileError(ValueError):
    pass
