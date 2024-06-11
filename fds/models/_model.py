from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import yaml
from loguru import logger
from typing_extensions import Self

from fds.client import FdsClient
from fds.models import DEFAULT_CONFIG
from fds.utils.dates import get_datetime
from fds.utils.dict import compare_two_dicts
from fds.utils.enum import EnumFromInput
from fds.utils.log import log_and_raise


class ModelSource(EnumFromInput):
    USER = "USER"
    CONFIG = "IMPORT"
    CLIENT = "CLIENT"


class BaseModel(ABC):
    FDS_TYPE: FdsClient.Models
    api_client = FdsClient.get_client()


class RetrievableModel(BaseModel, ABC):
    @abstractmethod
    def __init__(self, nametag: str = None, **kwargs):
        self._client_id = None
        self._nametag = nametag
        self._model_source = None
        self._client_retrieved_object_data = {}

    @property
    def model_source(self) -> ModelSource:
        return self._model_source

    @property
    def client_id(self) -> str | None:
        return self._client_id

    @property
    def nametag(self) -> str:
        return self._nametag

    def _id_exists(self, client_id: str) -> bool:
        return self.api_client.model_exists(self.FDS_TYPE, client_id)

    def is_saved_on_client(self) -> bool:
        if self.client_id is not None:
            return self._id_exists(self.client_id)
        return False

    def api_create_map(self, **kwargs) -> dict:
        return {}

    def save(self, force: bool = False) -> Self:
        if self.is_saved_on_client() and not force:
            # logger.debug(f"Object '{self.FDS_TYPE}' already saved on client server with ID '{self.client_id}'.")
            return self
        obj_data = self.api_client.create_object(self.FDS_TYPE, **self.api_create_map(force_save=force))
        new_obj = self._create_from_api_object_data(obj_data, self.nametag)
        self.__dict__.update(new_obj.__dict__)
        return self

    def destroy(self) -> Self:
        if self.is_saved_on_client():
            self.api_client.destroy_object(self.FDS_TYPE, self.client_id)
            self._client_id = None
        else:
            logger.warning(f"Impossible to destroy '{self.FDS_TYPE}', it is not in the client server.")
            self._client_id = None if self.client_id is not None else self.client_id
        return self

    def is_same_object_as(self, other: Self, check_id=True) -> bool:
        if not isinstance(other, self.__class__):
            msg = f"Object {other} is not of type {self.__class__}"
            logger.warning(msg)
            return False
        self_dict = self._client_retrieved_object_data
        other_dict = other._client_retrieved_object_data
        # check if the two dictionaries are equal
        are_equal = True
        for key in self_dict.keys():
            if key not in other_dict.keys():
                msg = f"Key {key} is not in the other dictionary"
                logger.warning(msg)
                return False
            if key == 'id' and check_id is False:
                continue
            # There might be a list that has different order but same elements. Let's check that
            if isinstance(self_dict[key], list):
                if len(self_dict[key]) == 0 and other_dict[key] is None:
                    continue  # empty lists are equal
                if len(self_dict[key]) == len(other_dict[key]):
                    are_lists_equal = all([x in other_dict[key] for x in self_dict[key]])
                    are_equal *= are_lists_equal
                else:
                    msg = f"List {key} has different lengths: {len(self_dict[key])} and {len(other_dict[key])}"
                    logger.warning(msg)
                    return False
            # There might be a date that has a resolution problem. Let's check that
            elif isinstance(self_dict[key], str) and "date" in key.lower():
                if key != 'creation_date':  # creation date is always different
                    date_self = get_datetime(self_dict[key])
                    date_other = get_datetime(other_dict[key])
                    delta = date_self - date_other
                    are_dates_equal = abs(delta.total_seconds()) < 1E-5
                    are_equal *= are_dates_equal
            else:
                are_equal *= self_dict[key] == other_dict[key]
        return bool(are_equal)

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {}

    @classmethod
    def retrieve_by_id(cls, client_id: str, nametag: str = None):
        """
        Args:
            client_id (str): the UUID of the object to be retrieved
            nametag (str): the desired nametag to be assigned to the retrieved object
        """
        if client_id is None:
            msg = f"client_id cannot be None"
            log_and_raise(ValueError, msg)
        obj_data = cls._retrieve_api_object_data(client_id)
        return cls._create_from_api_object_data(obj_data, nametag)

    @classmethod
    def _retrieve_api_object_data(cls, client_id: str):
        if cls.api_client.model_exists(cls.FDS_TYPE, client_id):
            return cls.api_client.retrieve_model(cls.FDS_TYPE, client_id)
        msg = f"Impossible to retrieve '{cls.FDS_TYPE}', it is not in the client server."
        log_and_raise(ValueError, msg)

    @classmethod
    def _create_from_api_object_data(cls, obj_data, nametag: str = None):
        if not isinstance(obj_data, dict):
            obj_data = obj_data.to_dict()
        new_obj = cls(**cls.api_retrieve_map(obj_data), nametag=nametag)
        new_obj._client_id = obj_data['id']
        new_obj._model_source = ModelSource.CLIENT
        new_obj._client_retrieved_object_data.update(obj_data)
        return new_obj

    @classmethod
    def retrieve_all(cls, convert_to_sdk_format: bool = False):
        obj_list = cls.api_client.retrieve_all(cls.FDS_TYPE)
        ids = [cls.api_client.get_id(obj) for obj in obj_list]
        if convert_to_sdk_format:
            obj_converted = []
            try:
                for obj_data in obj_list:
                    obj_converted.append(cls._create_from_api_object_data(obj_data, None))
            except TypeError as e:
                msg = f"Object '{cls.FDS_TYPE}' cannot be converted to SDK object"
                log_and_raise(TypeError, msg)
            else:
                return {'id': ids, 'api_objects_raw': obj_list, 'sdk_objects': obj_converted}
        return {'id': ids, 'api_objects_raw': obj_list}


class TimestampedRetrievableModel(RetrievableModel, ABC):
    def __init__(self, date: datetime | str, nametag: str = None, **kwargs):
        super().__init__(nametag, **kwargs)
        self._date = get_datetime(date)

    @property
    def date(self) -> datetime:
        return self._date


class FromConfigBaseModel(BaseModel, ABC):

    @abstractmethod
    def __init__(self, nametag: str):
        super().__init__(nametag=nametag)

    @classmethod
    def import_from_config_file(cls, config_filepath: str | Path, **kwargs) -> Self:
        config_dict = cls._get_config_dict_from_file(config_filepath)
        return cls.import_from_config_dict(config_dict, **kwargs)

    @classmethod
    def import_from_config_dict(cls, config_dict: dict, **kwargs) -> Self:
        try:
            obj_data = config_dict[cls.FDS_TYPE]
        except KeyError:
            log_and_raise(KeyError, f'Object {cls.FDS_TYPE} not in the config file.')

        # if data is both in obj_data and kwargs, kwargs will overwrite obj_data
        for key in obj_data.keys():
            if key in kwargs:
                obj_data[key] = kwargs[key]
                kwargs.pop(key)

        obj = cls(**obj_data, **kwargs)
        obj._model_source = ModelSource.CONFIG
        return obj

    @staticmethod
    def _get_config_dict_from_file(config_filepath: str | Path) -> dict:
        with open(config_filepath, 'r') as f:
            config = yaml.safe_load(f)

        if config.get('version') != DEFAULT_CONFIG.get('version'):
            msg = (f"Configuration file version ({config.get('version')}) "
                   f"does not correspond to the default version ({DEFAULT_CONFIG.get('version')}).")
            log_and_raise(ValueError, msg)

        compare_two_dicts(config, DEFAULT_CONFIG)
        return config
