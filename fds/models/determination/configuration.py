from dataclasses import dataclass
from pathlib import Path

from spacetower_python_client import OutlierManagerSettingsDto
from typing_extensions import Self

from fds.client import FdsClient
from fds.models._model import FromConfigBaseModel, RetrievableModel
from fds.models.orbital_state import CovarianceMatrix
from fds.utils.enum import EnumFromInput
from fds.utils.log import log_and_raise


class OrbitDeterminationConfiguration(FromConfigBaseModel, RetrievableModel):
    FDS_TYPE = FdsClient.Models.ORBIT_DETERMINATION_CONFIG

    @dataclass
    class OutliersManager:
        scale: float
        warmup: int
        max_number_of_consecutive_outliers: int

    @dataclass
    class TuningParameters:
        alpha: float
        beta: float
        kappa: float

    class NoiseProviderKind(EnumFromInput):
        BASIC = "BASIC"
        SNC = "SNC"
        DMC = "DMC"
        EDB_CD = "EDB_CD"

    def __init__(
            self,
            tuning_alpha: float,
            tuning_beta: float,
            tuning_kappa: float,
            outliers_manager_scale: float,
            outliers_manager_warmup: int,
            noise_provider_kind: str | NoiseProviderKind,
            process_noise_matrix: CovarianceMatrix,
            outliers_manager_max_number_of_consecutive_outliers: int = None,
            nametag: str = None
    ):
        """
        Args:
            tuning_alpha (float): (Unit: dimensionless) Defines the spread of the sigma points.
                Typical values from 1E-4 to 1E-1.
            tuning_beta (float): (Unit: dimensionless) Incorporates prior knowledge of the distribution of the state.
                For Gaussian x, beta=2 is optimal
            tuning_kappa (float): (Unit: dimensionless) Secondary scaling parameter. Typical values 0.
            outliers_manager_scale (float): (Unit: dimensionless) Tolerance threshold for outlier rejection (normalised
                with respect to the residuals standard deviation).
            outliers_manager_warmup (int): (Unit: dimensionless) Number of warmup iterations or number of measurement
                without outlier rejection.
            outliers_manager_max_number_of_consecutive_outliers (int): (Unit: dimensionless) Maximum number of
                consecutive outliers tolerated before the scale is increased. Defaults to None.
            noise_provider_kind (str | NoiseProviderKind): The noise provider kind.
            process_noise_matrix (CovarianceMatrix): The process noise matrix (state noise distribution).
            nametag (str): Defaults to None.
        """

        super().__init__(nametag)

        self._tuning_parameters = self.TuningParameters(tuning_alpha, tuning_beta, tuning_kappa)
        self._noise_provider_kind = self.NoiseProviderKind.from_input(noise_provider_kind)
        self._process_noise_matrix = process_noise_matrix
        self._outliers_manager = None

        if outliers_manager_warmup is not None and outliers_manager_scale is not None:
            self._outliers_manager = self.OutliersManager(outliers_manager_scale, outliers_manager_warmup,
                                                          outliers_manager_max_number_of_consecutive_outliers)

    @property
    def tuning(self) -> TuningParameters:
        return self._tuning_parameters

    @property
    def outliers_manager(self) -> OutliersManager:
        return self._outliers_manager

    @property
    def noise_provider_kind(self) -> NoiseProviderKind:
        return self._noise_provider_kind

    @property
    def process_noise_matrix(self) -> CovarianceMatrix:
        return self._process_noise_matrix

    def destroy(self, destroy_subcomponents: bool = True):
        super().destroy()
        if destroy_subcomponents:
            self.process_noise_matrix.destroy()

    def api_create_map(self, force_save: bool = False) -> dict:
        if self.outliers_manager is not None:
            outlier_manager = OutlierManagerSettingsDto(
                max_number_of_consecutive_outliers=self.outliers_manager.max_number_of_consecutive_outliers,
                outlier_max_scale=self.outliers_manager.scale,
                outlier_warmup_iterations=self.outliers_manager.warmup)
        else:
            outlier_manager = None

        d = super().api_create_map()
        d.update(
            {
                'alpha': self.tuning.alpha,
                'beta': self.tuning.beta,
                'kappa': self.tuning.kappa,
                'outlier_manager_settings': outlier_manager,
                'noise_provider_type': self.noise_provider_kind.value,
                'process_noise_matrix_id': self.process_noise_matrix.save(force_save).client_id
            }
        )
        return d

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        return {
            'tuning_alpha': obj_data.get('alpha'),
            'tuning_beta': obj_data.get('beta'),
            'tuning_kappa': obj_data.get('kappa'),
            'outliers_manager_scale': obj_data.get('outlierManagerSettings').get('outlierMaxScale'),
            'outliers_manager_warmup': obj_data.get('outlierManagerSettings').get('outlierWarmupIterations'),
            'outliers_manager_max_number_of_consecutive_outliers': obj_data.get('outlierManagerSettings').get(
                'maxNumberOfConsecutiveOutliers'),
            'noise_provider_kind': obj_data.get('noiseProviderType'),
            'process_noise_matrix': CovarianceMatrix.retrieve_by_id(
                obj_data.get('processNoiseMatrixId'))
        }

    @classmethod
    def import_from_config_file(cls, config_filepath: str | Path,
                                process_noise_matrix: CovarianceMatrix = None,
                                max_number_of_consecutive_outliers: int = None) -> Self:
        """
        Import the configuration from a configuration file.

        Args:
            config_filepath (str | Path): The configuration file path.
            process_noise_matrix (CovarianceMatrix): The process noise matrix.
            max_number_of_consecutive_outliers (int): The maximum number of consecutive outliers tolerated before the
                scale is increased. Defaults to None.
        """

        if process_noise_matrix is None:
            log_and_raise(ValueError, "The argument 'process_noise_matrix' is required!")
        return super().import_from_config_file(
            config_filepath,
            process_noise_matrix=process_noise_matrix,
            outliers_manager_max_number_of_consecutive_outliers=max_number_of_consecutive_outliers
        )
