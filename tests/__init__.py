import csv
import datetime
import unittest
from pathlib import Path

import numpy as np
import yaml
from loguru import logger

from fds.models._model import ModelSource
from fds.models.determination.result import ResultOrbitDetermination
from fds.models.determination.use_case import OrbitDetermination
from fds.models.maneuvers.result import ResultManeuverGeneration
from fds.models.maneuvers.use_case import ManeuverGeneration
from fds.models.orbit_extrapolation.result import ResultOrbitExtrapolation
from fds.models.orbit_extrapolation.use_case import OrbitExtrapolation
from fds.utils.dates import get_datetime

DATA_DIR = Path(__file__).parent / "data"


def _test_initialisation(obj_type, **kwargs):
    return obj_type(**kwargs)


class TestModels(unittest.TestCase):
    CONFIG_TEST_FILEPATH = DATA_DIR / "fds_config_test.yaml"

    def _test_save_and_destroy(self, obj_type, **kwargs):
        obj = obj_type(**kwargs)
        obj.save()
        self.assertTrue(obj.is_saved_on_client(), f"Object {obj.FDS_TYPE} is not saved.")
        obj.destroy()
        self.assertFalse(obj.is_saved_on_client(), f"Destroyed object {obj.FDS_TYPE} is still saved.")

    def _test_import_from_config_file(self, obj_type, **kwargs):
        obj = obj_type.import_from_config_file(self.CONFIG_TEST_FILEPATH, **kwargs)
        with open(self.CONFIG_TEST_FILEPATH, 'r') as f:
            config = yaml.safe_load(f)
        obj_data = config[obj_type.FDS_TYPE]
        for key, value in obj_data.items():
            attr = getattr(obj, key)
            if isinstance(attr, np.ndarray):
                attr = attr.tolist()
            self.assertTrue(attr == value,
                            f"Object {obj.FDS_TYPE} value at key '{key}' '{attr}' does not correspond to "
                            f"value '{value}' in configuration file.")
        self.assertTrue(obj.model_source == ModelSource.CONFIG)

    def _test_save_and_retrieve_by_id_and_destroy(self, obj_type, **kwargs):
        destroy_subcomponents = False
        if 'destroy_subcomponents' in kwargs:
            destroy_subcomponents = kwargs['destroy_subcomponents']
            del kwargs['destroy_subcomponents']

        obj_original = obj_type(**kwargs).save()
        obj = obj_type.retrieve_by_id(obj_original.client_id)
        self.assertTrue(obj.is_same_object_as(obj_original))
        if destroy_subcomponents:
            obj.destroy(destroy_subcomponents=destroy_subcomponents)
        else:
            obj.destroy()  # this destroys the object in the server


class TestModelsWithContainer(TestModels):
    def _test_import_from_config_file(self, obj_type, **kwargs):
        obj = obj_type.import_from_config_file(self.CONFIG_TEST_FILEPATH, **kwargs)
        with open(self.CONFIG_TEST_FILEPATH, 'r') as f:
            config = yaml.safe_load(f)
        obj_data = config[obj_type.FDS_TYPE]
        attr = None
        for key, value in obj_data.items():
            try:
                attr = getattr(obj, key)
            except AttributeError:  # the attribute is hidden in a container (namedtuple)
                try:
                    container_name = key.split('_')[0]

                    attr_name = '_'.join(
                        key.split('_')[1:])  # TODO: find better way to do parametrically? Sensitive to variable names!
                    container = getattr(obj, container_name)
                except AttributeError:
                    container_name = '_'.join(key.split('_')[:2])
                    attr_name = '_'.join(key.split('_')[2:])
                    container = getattr(obj, container_name)
                attr = getattr(container, attr_name)
            finally:
                self.assertTrue(attr == value,
                                f"Object {obj.FDS_TYPE} value at key '{key}' ({attr}) does not correspond to value"
                                f" '{value}' in configuration file.")
        self.assertTrue(obj.model_source == ModelSource.CONFIG)


class TestUseCases(unittest.TestCase):
    CONFIG_TEST_FILEPATH = DATA_DIR / "fds_config_test.yaml"
    ATOL_TIME = 1  # seconds
    ATOL_POSITION = 1e-4  # km
    ATOL_VELOCITY = 1e-4  # km/s

    CLIENT_TYPE: None
    kwargs: {}

    def _test_initialisation(
            self) -> OrbitDetermination | OrbitExtrapolation | ManeuverGeneration:
        return self.CLIENT_TYPE(**self.kwargs)

    def _test_client_run(self) \
            -> ResultOrbitDetermination | ResultOrbitExtrapolation | ResultManeuverGeneration:
        client_object = self._test_initialisation()
        client_object.run()
        return client_object.result

    @staticmethod
    def is_datetime_close(date1: datetime.datetime, date2: datetime.datetime,
                          atol_seconds: float = ATOL_TIME) -> bool:
        if date1 is None:
            if date2 is None:
                return True
            logger.error(f"date1 is None and date2 is {date2}")
            return False
        condition = abs((date1 - date2).total_seconds()) < atol_seconds
        if not condition:
            logger.error(f"date1: {date1} and date2: {date2} are not close in the range of {atol_seconds} seconds.")
        return condition

    def is_string_date_close(self, date1: str, date2: str, atol_seconds: float = ATOL_TIME) -> bool:
        if date1 == 'None' or date1 is None:
            if date2 == 'None' or date2 is None:
                return True
            return False
        date1_datetime = get_datetime(date1)
        date2_datetime = get_datetime(date2)
        self.is_datetime_close(date1_datetime, date2_datetime, atol_seconds)

    @staticmethod
    def is_value_close(t1: float, t2: float, rtol: float = None, atol: float = None) -> bool:
        if t1 == 'None' or t1 is None:
            if t2 == 'None' or t2 is None:
                return True
            logger.error(f"t1 is None and t2 is {t2}")
            return False
        kwargs = {}
        if rtol is not None:
            kwargs['rtol'] = rtol
        if atol is not None:
            kwargs['atol'] = atol
        condition = np.isclose(float(t1), float(t2), **kwargs)
        if not condition:
            logger.error(f"t1: {float(t1)} and t2: {float(t2)} are not close in the range of {rtol}.")
        return condition

    @staticmethod
    def compare_csv_to_list_of_dict(csv_file: Path, list_to_compare: list[dict]):
        are_same = True
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                for d in list_to_compare:
                    if all(row[key] == str(value) for key, value in d.items()):
                        are_same *= True
                    if not are_same:
                        # verify if there are nan values that are not saved
                        for key, value in d.items():
                            if row[key] == 'nan' and np.isnan(value):
                                are_same = True
                                break
        return are_same
