from abc import ABC, abstractmethod

from fds.client import FdsClient
from fds.models._model import RetrievableModel, ModelSource
from fds.utils.enum import EnumFromInput


class ParameterEstimationRequest(RetrievableModel, ABC):
    FDS_TYPE = FdsClient.Models.PARAMETER_ESTIMATION_REQUEST

    class EstimatedParameter(EnumFromInput):
        DRAG_COEFFICIENT = "DRAG_COEFFICIENT"
        REFLECTIVITY_COEFFICIENT = "REFLECTIVITY_COEFFICIENT"
        THRUST_VECTOR = "THRUST_VECTOR"

    @abstractmethod
    def __init__(
            self,
            standard_deviation: float,
            process_noise_standard_deviation: float,
            nametag: str = None
    ):
        super().__init__(nametag)
        self._standard_deviation = standard_deviation
        self._process_noise_standard_deviation = process_noise_standard_deviation

    @property
    def standard_deviation(self) -> float:
        return self._standard_deviation

    @property
    def process_noise_standard_deviation(self) -> float:
        return self._process_noise_standard_deviation

    def api_create_map(self, **kwargs) -> dict:
        return {
            'parameter_standard_deviation': self.standard_deviation,
            'process_noise_standard_deviation': self.process_noise_standard_deviation
        }

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'standard_deviation': obj_data['parameterStandardDeviation'],
            'process_noise_standard_deviation': obj_data['processNoiseStandardDeviation']
        }

    @classmethod
    def retrieve_generic_by_id(cls, client_id: str, nametag: str = None):
        obj_data = FdsClient.get_client().retrieve_model(cls.FDS_TYPE, client_id)
        if not isinstance(obj_data, dict):
            obj_data = obj_data.to_dict()

        match obj_data.get('estimatedParameter'):
            case cls.EstimatedParameter.DRAG_COEFFICIENT:
                obj_type = DragCoefficientEstimationRequest
            case cls.EstimatedParameter.REFLECTIVITY_COEFFICIENT:
                obj_type = ReflectivityCoefficientEstimationRequest
            case _:
                raise ValueError("Unknown estimated parameter")
        new_obj = obj_type(**obj_type.api_retrieve_map(obj_data), nametag=nametag)
        new_obj._client_id = client_id
        new_obj._model_source = ModelSource.CLIENT
        new_obj._client_retrieved_object_data.update(obj_data)
        return new_obj


class DragCoefficientEstimationRequest(ParameterEstimationRequest):
    FDS_TYPE = FdsClient.Models.DRAG_COEFFICIENT_ESTIMATION_REQUEST

    def __init__(
            self,
            standard_deviation: float,
            process_noise_standard_deviation: float,
            nametag: str = None
    ):
        """
        Drag coefficient estimation request.

        Args:
            standard_deviation (float): The standard deviation of the estimated parameter.
            process_noise_standard_deviation (float): The standard deviation of the process noise.
            nametag (str): Defaults to None.
        """
        super().__init__(standard_deviation, process_noise_standard_deviation, nametag)

    @property
    def estimated_parameter(self) -> ParameterEstimationRequest.EstimatedParameter:
        return self.EstimatedParameter.DRAG_COEFFICIENT


class ReflectivityCoefficientEstimationRequest(ParameterEstimationRequest):
    FDS_TYPE = FdsClient.Models.REFLECTIVITY_COEFFICIENT_ESTIMATION_REQUEST

    def __init__(
            self,
            standard_deviation: float,
            process_noise_standard_deviation: float,
            nametag: str = None
    ):
        """
        Reflectivity estimation request.

        Args:
            standard_deviation (float): The standard deviation of the estimated parameter.
            process_noise_standard_deviation (float): The standard deviation of the process noise.
            nametag (str): Defaults to None.
        """
        super().__init__(standard_deviation, process_noise_standard_deviation, nametag)

    @property
    def estimated_parameter(self) -> ParameterEstimationRequest.EstimatedParameter:
        return self.EstimatedParameter.REFLECTIVITY_COEFFICIENT


class ThrustVectorEstimationRequest(ParameterEstimationRequest):
    FDS_TYPE = FdsClient.Models.THRUST_VECTOR_ESTIMATION_REQUEST

    def __init__(
            self,
            standard_deviation: float,
            process_noise_standard_deviation: float,
            nametag: str = None
    ):
        """
        Thrust vector estimation request.

        Args:
            standard_deviation (float): The standard deviation of the estimated parameter.
            process_noise_standard_deviation (float): The standard deviation of the process noise.
            nametag (str): Defaults to None.
        """
        super().__init__(standard_deviation, process_noise_standard_deviation, nametag)

    @property
    def estimated_parameter(self) -> ParameterEstimationRequest.EstimatedParameter:
        return self.EstimatedParameter.THRUST_VECTOR
