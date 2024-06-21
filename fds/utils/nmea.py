import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path

from loguru import logger

from fds.constants import GGA_REGEX, RMC_REGEX, KN_TO_MPS
from fds.utils.dates import filter_sequence_with_minimum_time_step
from fds.utils.log import log_and_raise


@dataclass
class NmeaMeasurement:
    longitude: float
    latitude: float
    ground_speed: float
    date: datetime
    altitude: float | None = None
    geoid_height: float | None = None


class NmeaSentence(ABC):
    _MESSAGE_ID_INDEX = 0
    _TIME_INDEX = 1
    _LATITUDE_INDEX: int
    _LATITUDE_DIRECTION_INDEX: int
    _LONGITUDE_INDEX: int
    _LONGITUDE_DIRECTION_INDEX: int

    @classmethod
    @abstractmethod
    def parse(cls, sentence: str):
        pass

    @staticmethod
    def get_coordinate_from_string_and_direction(coordinate: str, direction: str) -> float:
        coordinate_split = coordinate.split(".")
        if len(coordinate_split[0]) == 5:  # Longitude
            degree_index = 3
        else:  # Latitude
            degree_index = 2
        degrees = int(coordinate[:degree_index])
        minutes = float(coordinate[degree_index:])
        angle = degrees + minutes / 60
        if direction in {"S", "W"}:
            angle = -angle
        return angle

    @staticmethod
    def get_measure_in_meters(measure: float, unit: str) -> float:
        if unit == "M":
            return measure
        else:
            raise log_and_raise(ValueError, f"Unknown unit: {unit}")

    @classmethod
    def parse_latitude(cls, split_sentence: list[str]) -> float:
        return cls.get_coordinate_from_string_and_direction(
            split_sentence[cls._LATITUDE_INDEX],
            split_sentence[cls._LATITUDE_DIRECTION_INDEX]
        )

    @classmethod
    def parse_longitude(cls, split_sentence: list[str]) -> float:
        return cls.get_coordinate_from_string_and_direction(
            split_sentence[cls._LONGITUDE_INDEX],
            split_sentence[cls._LONGITUDE_DIRECTION_INDEX]
        )


@dataclass
class GgaSentence(NmeaSentence):
    _LATITUDE_INDEX = 2
    _LATITUDE_DIRECTION_INDEX = 3
    _LONGITUDE_INDEX = 4
    _LONGITUDE_DIRECTION_INDEX = 5
    _QUALITY_INDICATOR_INDEX = 6
    _SATELLITES_USED_INDEX = 7
    _HDOP_INDEX = 8
    _MSL_ALTITUDE_INDEX = 9
    _MSL_UNIT_INDEX = 10
    _GEOID_SEPARATION_INDEX = 11
    _GEOID_UNIT_INDEX = 12
    _AGE_OF_CORRECTION_DATA_INDEX = 13
    _DIFFERENTIAL_BASE_STATION_ID_INDEX = 14
    _gga_pattern = re.compile(GGA_REGEX)

    message_id: str
    utc_time: str
    latitude: float
    longitude: float
    quality_indicator: int
    satellites_used: int
    hdop: float
    msl_altitude: float
    geoid_separation: float
    age_of_diff_corr: str
    differential_base_station_id: str
    sentence: str

    @classmethod
    def parse(cls, sentence: str):
        cls.is_valid(sentence, raise_if_false=True)

        sentence = sentence.replace(" ", "")
        split_sentence = sentence.split(",")

        message_id = split_sentence[cls._MESSAGE_ID_INDEX]
        utc_time = split_sentence[cls._TIME_INDEX]
        latitude = cls.parse_latitude(split_sentence)
        longitude = cls.parse_longitude(split_sentence)
        quality_indicator = int(split_sentence[cls._QUALITY_INDICATOR_INDEX])
        satellites_used = int(split_sentence[cls._SATELLITES_USED_INDEX])
        hdop = float(split_sentence[cls._HDOP_INDEX])
        msl_altitude = cls.parse_altitude(split_sentence)
        geoid_separation = cls.parse_geoid_separation(split_sentence)
        age_of_correction_data = split_sentence[cls._AGE_OF_CORRECTION_DATA_INDEX]
        differential_base_station_id_and_checksum = split_sentence[cls._DIFFERENTIAL_BASE_STATION_ID_INDEX]
        differential_base_station_id = differential_base_station_id_and_checksum.split("*")[0]

        return cls(
            message_id=message_id,
            utc_time=utc_time,
            latitude=latitude,
            longitude=longitude,
            quality_indicator=quality_indicator,
            satellites_used=satellites_used,
            hdop=hdop,
            msl_altitude=msl_altitude,
            geoid_separation=geoid_separation,
            age_of_diff_corr=age_of_correction_data if age_of_correction_data != "" else None,
            differential_base_station_id=differential_base_station_id if differential_base_station_id != "" else None,
            sentence=sentence
        )

    @classmethod
    def parse_altitude(cls, split_sentence: list[str]) -> float:
        return cls.get_measure_in_meters(
            float(split_sentence[cls._MSL_ALTITUDE_INDEX]),
            split_sentence[cls._MSL_UNIT_INDEX]
        )

    @classmethod
    def parse_geoid_separation(cls, split_sentence: list[str]) -> float | None:
        geoid_sep = split_sentence[cls._GEOID_SEPARATION_INDEX]
        if geoid_sep == "":
            return None
        return cls.get_measure_in_meters(
            float(split_sentence[cls._GEOID_SEPARATION_INDEX]),
            split_sentence[cls._GEOID_UNIT_INDEX]
        )

    @classmethod
    def is_valid(cls, sentence: str, raise_if_false: bool = True) -> bool:
        sentence = sentence.replace(" ", "")
        valid_format = bool(cls._gga_pattern.match(sentence))
        valid_length = len(sentence.split(',')) == 15
        valid_gga = sentence.startswith("$GPGGA")
        error_message = "Invalid sentence:"
        error_reasons = []
        if not valid_format:
            error_reasons.append("regex pattern not matched")
        if not valid_length:
            error_reasons.append(f"invalid number of terms {len(sentence.split(','))}")
        if not valid_gga:
            error_reasons.append("not a GGA sentence")
        if error_reasons:
            error_message += " " + ", ".join(error_reasons)

        if valid_gga and valid_format and valid_length:
            return True
        if raise_if_false:
            log_and_raise(ValueError, error_message)
        return False


@dataclass
class RmcSentence(NmeaSentence):
    _STATUS_INDEX = 2
    _LATITUDE_INDEX = 3
    _LATITUDE_DIRECTION_INDEX = 4
    _LONGITUDE_INDEX = 5
    _LONGITUDE_DIRECTION_INDEX = 6
    _GROUND_SPEED_INDEX = 7
    _COURSE_OVER_GROUND_INDEX = 8
    _DATE_INDEX = 9
    _MAGNETIC_VARIATION_INDEX = 10
    _MAGNETIC_VARIATION_DIRECTION_INDEX = 11
    _POSITIONING_SYSTEM_MODE_INDEX = 12
    _rmc_pattern = re.compile(RMC_REGEX)

    message_id: str
    utc_time: str
    latitude: float
    longitude: float
    ground_speed: float
    course_over_ground: float
    date: datetime
    magnetic_variation: float | None
    positioning_system_mode: str | None
    status: str
    sentence: str

    @classmethod
    def parse(cls, sentence: str):

        sentence = sentence.replace(" ", "")
        cls.is_valid(sentence, raise_if_false=True)

        split_sentence = sentence.split(",")

        message_id = split_sentence[cls._MESSAGE_ID_INDEX]
        utc_time = split_sentence[cls._TIME_INDEX]
        status = split_sentence[cls._STATUS_INDEX]

        if status == "V":
            log_and_raise(ValueError, "This is not a valid RMC sentence")

        latitude = cls.parse_latitude(split_sentence)
        longitude = cls.parse_longitude(split_sentence)
        ground_speed = float(split_sentence[cls._GROUND_SPEED_INDEX]) * KN_TO_MPS
        course_over_ground = float(split_sentence[cls._COURSE_OVER_GROUND_INDEX])
        date = cls.parse_datetime(split_sentence)
        magnetic_variation = cls.parse_magnetic_variation(split_sentence)
        positioning_system_mode = split_sentence[cls._POSITIONING_SYSTEM_MODE_INDEX]

        return cls(
            message_id=message_id,
            utc_time=utc_time,
            latitude=latitude,
            longitude=longitude,
            ground_speed=ground_speed,
            course_over_ground=course_over_ground,
            date=date,
            magnetic_variation=magnetic_variation,
            status=status,
            positioning_system_mode=positioning_system_mode if positioning_system_mode != "" else None,
            sentence=sentence
        )

    @classmethod
    def parse_datetime(cls, split_sentence: list[str]) -> datetime:
        time = split_sentence[cls._TIME_INDEX]
        date = datetime.strptime(split_sentence[cls._DATE_INDEX] + ' ' + time, '%d%m%y %H%M%S.%f')
        return date.replace(tzinfo=UTC)

    @classmethod
    def parse_magnetic_variation(cls, split_sentence: list[str]) -> float | None:
        magnetic_variation = split_sentence[cls._MAGNETIC_VARIATION_INDEX]
        if magnetic_variation == "":
            return None
        magnetic_variation_direction = split_sentence[cls._MAGNETIC_VARIATION_DIRECTION_INDEX]
        if magnetic_variation_direction == "W":
            return -float(magnetic_variation)
        return float(magnetic_variation)

    @classmethod
    def is_valid(cls, sentence: str, raise_if_false: bool = True) -> bool:
        valid_format = bool(cls._rmc_pattern.match(sentence))
        valid_length = len(sentence.split(',')) == 13
        valid_status = sentence.split(',')[2] == 'A'
        error_message = "Invalid sentence:"
        error_reasons = []
        if not valid_format:
            error_reasons.append("regex pattern not matched")
        if not valid_length:
            error_reasons.append(f"invalid number of terms {len(sentence.split(','))}")
        if not valid_status:
            error_reasons.append("invalid status")
        if error_reasons:
            error_message += " " + ", ".join(error_reasons)

        if valid_format and valid_length and valid_status:
            return True
        if raise_if_false:
            log_and_raise(ValueError, error_message)
        return False


@dataclass
class SentenceBundle:
    rmc: RmcSentence
    gga: GgaSentence = None

    @property
    def date(self) -> datetime:
        return self.rmc.date

    @classmethod
    def from_strings(cls, rmc: str, gga: str = None):
        rmc_sentence = RmcSentence.parse(rmc)
        if gga is not None:
            gga_sentence = GgaSentence.parse(gga)
            return cls(rmc=rmc_sentence, gga=gga_sentence)
        return cls(rmc=rmc_sentence)


def get_raw_sentences_from_folder(folder_path: str | Path) -> list[str]:
    def _read_raw_sentences(_folder_path: Path) -> list[str]:
        _raw_sentences = []
        all_files = os.listdir(_folder_path)
        for filename in all_files:
            with open(os.path.join(folder_path, filename), "r") as f:
                _raw_sentences += f.readlines()
        return _raw_sentences

    folder_path = Path(folder_path).resolve()
    if not folder_path.exists():
        log_and_raise(ValueError, f"Folder {folder_path} does not exist.")
    if not folder_path.is_dir():
        log_and_raise(ValueError, f"{folder_path} is not a folder.")
    return _read_raw_sentences(folder_path)


def get_raw_sentences_from_single_file(file_path: str | Path) -> list[str]:
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        log_and_raise(ValueError, f"File {file_path} does not exist.")
    if not file_path.is_file():
        log_and_raise(ValueError, f"{file_path} is not a file.")
    with open(file_path, "r") as f:
        raw_sentences = f.readlines()
    return raw_sentences


def parse_raw_sentences(
        raw_sentences: list[str],
        return_statistics: bool = False
) -> list[SentenceBundle] | tuple[list[SentenceBundle], dict]:
    n_rmc_sentences = 0
    n_gga_sentences = 0
    n_valid_rmc_sentences = 0
    n_valid_gga_sentences = 0
    sentences = []
    no_gga_dates = []
    corrupted_gga_dates = []

    for i, line in enumerate(raw_sentences):
        line = _remove_return_char(line)
        line_type = line.split(',')[0]
        if line_type == '$GPRMC':
            n_rmc_sentences += 1
            if RmcSentence.is_valid(line, raise_if_false=False):
                rmc_sentence = RmcSentence.parse(line)
                sentences.append(SentenceBundle(rmc=rmc_sentence))
                n_valid_rmc_sentences += 1
                previous_line = _remove_return_char(raw_sentences[i - 1]) if i > 0 else None
                if previous_line is not None and previous_line.startswith("$GPGGA"):
                    n_gga_sentences += 1
                    if GgaSentence.is_valid(previous_line, raise_if_false=False):
                        gga_sentence = GgaSentence.parse(previous_line)
                        if gga_sentence.utc_time == rmc_sentence.utc_time:
                            sentences[-1] = SentenceBundle(
                                rmc=rmc_sentence,
                                gga=gga_sentence
                            )
                            n_valid_gga_sentences += 1
                    else:
                        corrupted_gga_dates.append(rmc_sentence.date)
                else:
                    no_gga_dates.append(rmc_sentence.date)

    if len(sentences) == 0:
        msg = "No RMC sentences found in the telemetry log file. Processing of NMEA sentences failed."
        log_and_raise(NmeaFileError, msg)

    if n_valid_gga_sentences == 0:
        logger.debug("No GGA sentences found in the telemetry log file.")

    # Sort the sentences by date
    sentences.sort(key=lambda x: x.date)

    stats = {
        "number_of_sentences": len(sentences),
        "number_of_all_rmc_sentences": n_rmc_sentences,
        "number_of_all_gga_sentences": n_gga_sentences,
        "number_of_valid_gga_sentences": n_valid_gga_sentences,
        "number_of_valid_rmc_sentences": n_valid_rmc_sentences,
        "dates_with_no_gga": no_gga_dates,
        "dates_with_corrupted_gga": corrupted_gga_dates
    }
    if return_statistics:
        return sentences, stats
    return list(sentences)


def parse_raw_sentences_from_file(
        file_path: str | Path,
        return_statistics: bool = False
) -> list[SentenceBundle] | tuple[list[SentenceBundle], dict]:
    raw_sentences = get_raw_sentences_from_single_file(file_path)
    return parse_raw_sentences(raw_sentences, return_statistics)


def parse_raw_sentences_from_folder(
        folder_path: str | Path,
        return_statistics: bool = False
) -> list[SentenceBundle] | tuple[list[SentenceBundle], dict]:
    raw_sentences = get_raw_sentences_from_folder(folder_path)
    return parse_raw_sentences(raw_sentences, return_statistics)


def export_list_of_sentences(sentences: list[SentenceBundle], use_gga: bool = True) -> list[str]:
    sentences_merged = []
    for sentence in sentences:
        if sentence.gga is not None and use_gga:  # there is a GGA sentence
            sentences_merged.append(sentence.gga.sentence)
            sentences_merged.append(sentence.rmc.sentence)
        else:
            sentences_merged.append(sentence.rmc.sentence)
    return sentences_merged


def _remove_return_char(string: str):
    if string[-1] == '\n':
        string = string[:-1]
    return string


def filter_sentences(
        sentences: list[SentenceBundle],
        measurement_start_date_limit: datetime = None,
        measurement_end_date_limit: datetime = None,
        measurement_min_step: float = None,
) -> list[SentenceBundle]:
    selected_sentences = filter_sentences_by_date(
        sentences,
        measurement_start_date_limit,
        measurement_end_date_limit)

    selected_sentences = filter_sentences_by_step(
        selected_sentences, measurement_min_step)

    return selected_sentences


def filter_sentences_by_date(
        sentences: list[SentenceBundle],
        measurement_start_date_limit: datetime, measurement_end_date_limit: datetime
) -> list[SentenceBundle]:
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


def filter_sentences_by_step(
        sentences: list[SentenceBundle],
        measurement_min_step: float
) -> list[SentenceBundle]:
    sentences.sort(key=lambda x: x.date)
    dates = [sentence.date for sentence in sentences]

    if measurement_min_step is None:
        return sentences

    return list(filter_sequence_with_minimum_time_step(sentences, dates, measurement_min_step))


def get_list_of_measurements_from_sentences(sentences: list[SentenceBundle]) -> list[NmeaMeasurement]:
    measurements = []
    for s in sentences:
        altitude = None
        geoid_height = None
        if s.gga is not None:
            altitude = s.gga.msl_altitude
            geoid_height = s.gga.geoid_separation if s.gga.geoid_separation is not None else 0.0
        measurements.append(
            NmeaMeasurement(
                longitude=s.rmc.longitude,
                latitude=s.rmc.latitude,
                ground_speed=s.rmc.ground_speed,
                date=s.rmc.date,
                altitude=altitude,
                geoid_height=geoid_height
            )
        )
    return measurements


def get_list_of_measurements_from_raw_and_dates(
        raw_measurements: list[list[float]],
        dates: list[datetime]
) -> list[NmeaMeasurement]:
    measurements = []
    for raw_measurement, date in zip(raw_measurements, dates):
        measurements.append(NmeaMeasurement(
            latitude=raw_measurement[0],
            longitude=raw_measurement[1],
            ground_speed=raw_measurement[2],
            date=date,
            altitude=raw_measurement[3],
            geoid_height=raw_measurement[4]
        ))
    return measurements


class NmeaFileError(ValueError):
    pass
