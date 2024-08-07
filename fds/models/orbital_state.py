from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import numpy as np

from fds.client import FdsClient
from fds.models._model import RetrievableModel, TimestampedRetrievableModel, FromConfigBaseModel
from fds.models.orbits import OrbitType, Orbit, KeplerianOrbit, OrbitMeanOsculatingType
from fds.models.spacecraft import SpacecraftSphere, SpacecraftBox, Spacecraft
from fds.models.two_line_element import TwoLineElement
from fds.utils.dates import datetime_to_iso_string, get_datetime
from fds.utils.enum import EnumFromInput
from fds.utils.frames import Frame
from fds.utils.log import log_and_raise
from spacetower_python_client import TLE


class PropagationContext(FromConfigBaseModel, RetrievableModel):
    """
    This class holds all the data configuring the physics and mathematical model used in the space mechanics
    computation. It is used to describe everything other than the spacecraft in itself.
    """
    FDS_TYPE = FdsClient.Models.PROPAGATION_CONTEXT
    ":meta private:"

    class IntegratorKind(EnumFromInput):
        """
        This class enumerates all the numerical integrator supported.
        """
        DORMAND_PRINCE_853 = 'DORMAND_PRINCE_853'
        DORMAND_PRINCE_54 = 'DORMAND_PRINCE_54'
        ADAMS_MOULTON = 'ADAMS_MOULTON'
        RUNGE_KUTTA = 'RUNGE_KUTTA'

    @dataclass
    class IntegratorData:
        """
        This class holds the data relevant for numerical integrator specification.
        """
        kind: 'PropagationContext.IntegratorKind'
        min_step: float
        max_step: float

    @dataclass
    class ModelData:
        """
        This class holds all the physical data for the perturbations considered in the space mechanics computation.
        """
        perturbations: Sequence['PropagationContext.Perturbation']
        solar_flux: float
        earth_potential_deg: int
        earth_potential_ord: int
        atmosphere_kind: 'PropagationContext.AtmosphereModel'

    class Perturbation(EnumFromInput):
        """
        This class enumerates all the perturbations that can be simulated in the space mechanics computations.
        """
        EARTH_POTENTIAL = "EARTH_POTENTIAL"
        SRP = "SRP"
        THIRD_BODY = "THIRD_BODY"
        DRAG = "DRAG"
        CONSTANT_THRUST = "CONSTANT_THRUST"
        IMPULSIVE_THRUST = "IMPULSIVE_THRUST"

    class AtmosphereModel(EnumFromInput):
        """
        This class enumerates all the atmosphere models that can be simulated in the space mechanics computations.
        """
        HARRIS_PRIESTER = 'HARRIS_PRIESTER'
        NRL_MSISE00 = 'NRL_MSISE00'

    def __init__(
            self,
            integrator_min_step: float = None,
            integrator_max_step: float = None,
            integrator_kind: str | IntegratorKind = None,
            model_perturbations: Sequence[str | Perturbation] = None,
            model_solar_flux: float = None,
            model_earth_potential_deg: int = None,
            model_earth_potential_ord: int = None,
            model_atmosphere_kind: str | AtmosphereModel = None,
            nametag: str = None
    ):
        """
        Args:
            integrator_min_step (float): (Unit: s)
            integrator_max_step (float): (Unit: s)
            integrator_kind (str | IntegratorKind): Integrator kind
            model_perturbations (Sequence[str | Perturbation]): Perturbations
            model_solar_flux (float): (Unit: SFU). Value for nominal activity is 150 SFU.
            model_earth_potential_deg (int): Earth potential degree
            model_earth_potential_ord (int): Earth potential order
            model_atmosphere_kind (str | AtmosphereModel): Atmosphere kind
            nametag (str, optional): Defaults to None.
        """
        super().__init__(nametag)
        if integrator_kind is not None:
            integrator_kind = self.IntegratorKind.from_input(integrator_kind)
        self._integrator = self.IntegratorData(integrator_kind,
                                               integrator_min_step, integrator_max_step)
        if model_perturbations is not None:
            model_perturbations = [self.Perturbation.from_input(p) for p in model_perturbations]
        if model_atmosphere_kind is not None:
            model_atmosphere_kind = self.AtmosphereModel.from_input(model_atmosphere_kind)
        self._model = self.ModelData(model_perturbations, model_solar_flux,
                                     model_earth_potential_deg,
                                     model_earth_potential_ord,
                                     model_atmosphere_kind)

    @property
    def integrator(self) -> IntegratorData:
        """
        The configuration of the integrator used in the computations.
        """
        return self._integrator

    @property
    def model(self) -> ModelData:
        """
        The configuration of the perturbations models used in the computations.
        """
        return self._model

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        """
        :meta private:
        """
        return {
            'integrator_min_step': obj_data['integratorMinStep'],
            'integrator_max_step': obj_data['integratorMaxStep'],
            'integrator_kind': obj_data['integratorType'],
            'model_perturbations': obj_data['perturbations'],
            'model_solar_flux': obj_data.get('solarFlux'),
            'model_earth_potential_deg': obj_data.get('earthPotentialDeg'),
            'model_earth_potential_ord': obj_data.get('earthPotentialOrd'),
            'model_atmosphere_kind': obj_data.get('atmosphereType')
        }

    def api_create_map(self, **kwargs) -> dict:
        """
        :meta private:
        """
        perturbations_output = [p.value for p in
                                self.model.perturbations] if self.model.perturbations is not None else None

        d = super().api_create_map()
        d.update(
            {
                'integratorMinStep': self.integrator.min_step,
                'integratorMaxStep': self.integrator.max_step,
                'integratorType': self.integrator.kind.value if self.integrator.kind is not None else None,
                'perturbations': perturbations_output,
                'solarFlux': self.model.solar_flux,
                'earthPotentialDeg': self.model.earth_potential_deg,
                'earthPotentialOrd': self.model.earth_potential_ord,
                'atmosphereType': self.model.atmosphere_kind.value
                if self.model.atmosphere_kind is not None else self.model.atmosphere_kind
            }
        )
        return d


class CovarianceMatrix(TimestampedRetrievableModel):
    """
    This class is used to represent uncertainties on an orbit position through covariance matrices.
    """
    FDS_TYPE = FdsClient.Models.COVARIANCE_MATRIX
    ":meta private:"

    def __init__(
            self,
            matrix: Sequence[Sequence[float]] | np.ndarray,
            frame: str | Frame,
            date: str | datetime = None,
            orbit_type: str | OrbitType = OrbitType.CARTESIAN,
            nametag: str = None
    ):
        """
        Args:
            matrix (Sequence[Sequence[float]] | np.ndarray): The covariance matrix.
            frame (str | Frame): The reference frame of the covariance matrix.
            date (str | datetime): The date of the covariance matrix.
            orbit_type (str | OrbitType): The orbit type of the covariance matrix.
            nametag (str): Defaults to None.
        """
        # Check matrix
        matrix = np.array(matrix)
        if len(matrix.shape) != 2:
            msg = "Wrong dimension of covariance matrix, it should be 2."
            log_and_raise(ValueError, msg)
        if matrix.shape[0] != matrix.shape[1]:
            msg = "Wrong dimension of covariance matrix, it should be square."
            log_and_raise(ValueError, msg)

        super().__init__(date, nametag)

        self._matrix = matrix
        self._orbit_type = OrbitType.from_input(orbit_type)
        self._frame = Frame.from_input(frame)

    @property
    def matrix(self) -> np.ndarray:
        """
        The covariance matrix.
        """
        return self._matrix

    @property
    def frame(self) -> Frame:
        """
        The reference frame of the covariance matrix.
        """
        return self._frame

    @property
    def orbit_type(self) -> OrbitType:
        """
        If the orbit this covariance matrix describes the uncertainties of is mean or osculating.
        """
        return self._orbit_type

    @property
    def diagonal(self) -> np.ndarray:
        """
        Diagonal coefficients of the covariance matrix (i.e variances of all the parameters).
        """
        return np.diag(self.matrix)

    @property
    def standard_deviation(self) -> np.ndarray:
        """
        Standard deviation of the covariance matrix.
        """
        return np.sqrt(self.diagonal)

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        """
        :meta private:
        """
        return {'matrix': np.array(obj_data['matrix']),
                'date': obj_data['date'],
                'orbit_type': obj_data['orbitType'],
                'frame': obj_data['frame']}

    def api_create_map(self, **kwargs) -> dict:
        """
        :meta private:
        """
        return {
            'matrix': self.matrix.tolist(),
            'date': datetime_to_iso_string(self.date) if self.date is not None else None,
            'orbitType': self.orbit_type.value,
            'frame': self.frame.value_or_alias if self.frame is not None else None
        }

    @classmethod
    def from_diagonal(
            cls,
            diagonal: Sequence[float] | np.ndarray,
            frame: str | Frame,
            date: str | datetime = None,
            orbit_type: str | OrbitType = OrbitType.CARTESIAN,
            nametag: str = None
    ):
        """
        Instantiates a new CovarianceMatrix from its diagonal coefficients.

        Args:
            diagonal (Sequence[float] | np.ndarray): The diagonal of the covariance matrix.
            frame (str | Frame): The reference frame of the covariance matrix.
            date (str | datetime): The date of the covariance matrix.
            orbit_type (str | OrbitType): The orbit type of the covariance matrix.
            nametag (str): Defaults to None.

        Returns:
            a new CovarianceMatrix instance.
        """
        return cls(np.diag(diagonal), frame, date, orbit_type, nametag)


class RequiredOrbitalStates(EnumFromInput):
    """
    This class enumerates if the computation should return all the computed orbital states or just the last one.
    """
    ALL = "ALL"
    LAST = "LAST"


class OrbitalState(TimestampedRetrievableModel):
    """
    This class represents all the information known about a satellite at a given date, including but not limited to
    its mean and osculating orbits and their associated uncertainties, as well as the architecture of the spacecraft.
    """
    FDS_TYPE = FdsClient.Models.ORBITAL_STATE
    ":meta private:"

    class Source(EnumFromInput):
        """
        This class describes how the orbital state has been created.
        """
        ORBIT_DETERMINATION = 'ORBIT_DETERMINATION'
        ORBIT_EXTRAPOLATION = 'ORBIT_EXTRAPOLATION'
        MANUAL = 'MANUAL'
        MANEUVER_GENERATION = 'MANEUVER_GENERATION'

    class Initialisation(EnumFromInput):
        """
        This class describes what was the source for the orbital position of the orbital state.
        """
        FROM_TLE = 'FROM_TLE'
        FROM_MEAN_ORBIT = 'FROM_MEAN_ORBIT'
        FROM_OSCULATING_ORBIT = 'FROM_OSCULATING_ORBIT'

    def __init__(
            self,
            creation_date: str | datetime,
            fitted_tle: TwoLineElement | str,
            mean_orbit: KeplerianOrbit,
            osculating_orbit: KeplerianOrbit,
            propagation_context: PropagationContext,
            source: str | Source,
            spacecraft: SpacecraftSphere | SpacecraftBox,
            covariance_matrix: CovarianceMatrix = None,
            nametag: str = None
    ):
        """
        Args:
            covariance_matrix (CovarianceMatrix): The covariance matrix.
            creation_date (str): The creation date.
            fitted_tle (TwoLineElement): The fitted TLE.
            mean_orbit (KeplerianOrbit): The mean orbit.
            osculating_orbit (KeplerianOrbit): The osculating orbit.
            propagation_context (PropagationContext): The propagation context.
            source (str | Source): The source of the orbital state.
            spacecraft (SpacecraftSphere | SpacecraftBox): The spacecraft.
            nametag (str): Defaults to None.
        """

        super().__init__(osculating_orbit.date, nametag)
        self._covariance_matrix = covariance_matrix
        self._propagation_context = propagation_context
        self._spacecraft = spacecraft
        if isinstance(fitted_tle, str):
            fitted_tle = TwoLineElement.from_single_line(fitted_tle)
        self._fitted_tle = fitted_tle
        self._mean_orbit = mean_orbit
        self._osculating_orbit = osculating_orbit
        self._source = self.Source.from_input(source)
        self._creation_date = get_datetime(creation_date)
        self._initialisation = None

    @property
    def covariance_matrix(self) -> CovarianceMatrix:
        """
        The uncertainties associated with the OSCULATING orbit.
        """
        return self._covariance_matrix

    @covariance_matrix.setter
    def covariance_matrix(self, covariance_matrix: CovarianceMatrix):
        self._covariance_matrix = covariance_matrix
        self._client_id = None

    @property
    def creation_date(self) -> datetime:
        """
        The date at which this orbital state instance has been created. (Not the date at which the data hold by this
        orbital state instance is expressed!)
        """
        return self._creation_date

    @property
    def fitted_tle(self) -> TwoLineElement:
        """
        The TLE representing the orbital state. It is exact if the orbital state has been initiated from a TLE, or
        recomputed otherwise.
        """
        return self._fitted_tle

    @property
    def initialisation(self) -> Initialisation:
        """
        Has the orbital state been initialized from a mean orbit, an osculating orbit, or a TLE?
        """
        return self._initialisation

    @property
    def mean_orbit(self) -> KeplerianOrbit:
        """
        The mean orbit of the satellite. It is exact if the orbital state has been initiated from a mean orbit, or
        recomputed otherwise.
        """
        return self._mean_orbit

    @property
    def osculating_orbit(self) -> KeplerianOrbit:
        """
        The osculating orbit of the satellite. It is exact if the orbital state has been initiated from a osculating
        orbit, or recomputed otherwise.
        """
        return self._osculating_orbit

    @property
    def initialisation_orbit(self) -> KeplerianOrbit | None:
        """
        The orbit from which the orbital state has been initiated. Will return none if the orbital state has been
        initiated from a TLE.
        """
        match self._initialisation:
            case self.Initialisation.FROM_MEAN_ORBIT:
                return self.mean_orbit
            case self.Initialisation.FROM_OSCULATING_ORBIT:
                return self.osculating_orbit
            case _:
                return None

    @property
    def propagation_context(self) -> PropagationContext:
        """
        Configuration of the space dynamics models and the numerical integrator used to perform computation on this
        orbital state.
        """
        return self._propagation_context

    @property
    def source(self) -> Source:
        """
        Has the orbital state been created by the user, or is it the output of a space mechanics computation? (and if
        so, which one?)
        """
        return self._source

    @property
    def spacecraft(self) -> SpacecraftSphere | SpacecraftBox:
        """
        The model of the spacecraft in itself (mass, geometry, components ...).
        """
        return self._spacecraft

    @spacecraft.setter
    def spacecraft(self, spacecraft: SpacecraftSphere | SpacecraftBox):
        self._spacecraft = spacecraft
        self._client_id = None

    @classmethod
    def from_orbit(
            cls,
            propagation_context: PropagationContext,
            spacecraft: SpacecraftSphere | SpacecraftBox,
            orbit: Orbit,
            covariance_matrix: CovarianceMatrix = None,
            nametag: str = None
    ):
        """
        Creates a new orbital state from an orbit.

        Args:
            propagation_context:  Configuration of the space dynamics models and the numerical integrator used to
            perform computation on this orbital state.
            spacecraft: The model of the spacecraft in itself (mass, geometry, components ...).
            orbit: The orbit from which this new orbital state is to be created from.
            covariance_matrix: The uncertainties associated with the OSCULATING orbit.
            nametag: Nickname of the orbital state. Default value is none.

        Returns:
            a new orbital state.
        """
        if covariance_matrix is not None and covariance_matrix.date is None:
            covariance_matrix._date = orbit.date

        kwargs = {
            'covariance_matrix_id': covariance_matrix.save().client_id if covariance_matrix is not None else None,
            'propagation_context_id': propagation_context.save().client_id,
            'spacecraft_id': spacecraft.save().client_id,
            'orbit_id': orbit.save().client_id
        }
        obj_data = cls.api_client.create_object(cls.FDS_TYPE, **kwargs)
        os = cls._create_from_api_object_data(obj_data, nametag)
        match orbit.kind:
            case OrbitMeanOsculatingType.MEAN:
                os._initialisation = cls.Initialisation.FROM_MEAN_ORBIT
            case OrbitMeanOsculatingType.OSCULATING:
                os._initialisation = cls.Initialisation.FROM_OSCULATING_ORBIT
        return os

    @classmethod
    def from_tle(
            cls,
            propagation_context: PropagationContext,
            spacecraft: SpacecraftSphere | SpacecraftBox,
            tle: TwoLineElement | str,
            covariance_matrix: CovarianceMatrix = None,
            nametag: str = None
    ):
        """
        Creates a new orbital state from a TLE.

        Args:
            propagation_context:  Configuration of the space dynamics models and the numerical integrator used to
            perform computation on this orbital state.
            spacecraft: The model of the spacecraft in itself (mass, geometry, components ...).
            tle: The TLE from which this new orbital state is to be created from.
            covariance_matrix: The uncertainties associated with the OSCULATING orbit.
            nametag: Nickname of the orbital state. Default value is none.

        Returns:
            a new orbital state.
        """
        if isinstance(tle, str):
            tle = TwoLineElement.from_single_line(tle)
        if covariance_matrix is not None and covariance_matrix.date is None:
            covariance_matrix._date = tle.date

        kwargs = {
            'covariance_matrix_id': covariance_matrix.save().client_id if covariance_matrix is not None else None,
            'propagation_context_id': propagation_context.save().client_id,
            'spacecraft_id': spacecraft.save().client_id,
            'tle': tle.to_api_tle()
        }
        obj_data = cls.api_client.create_object(cls.FDS_TYPE, **kwargs)
        os = cls._create_from_api_object_data(obj_data, nametag)
        os._initialisation = cls.Initialisation.FROM_TLE
        return os

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        """
        :meta private:
        """
        covariance_id = obj_data.get('covarianceMatrixId')
        return {
            'covariance_matrix': CovarianceMatrix.retrieve_by_id(covariance_id) if covariance_id is not None else None,
            'creation_date': obj_data['creationDate'],
            'fitted_tle': TwoLineElement.from_api_tle(TLE(**obj_data['fittedTle'])),
            'mean_orbit': Orbit.retrieve_generic_by_id(obj_data['meanOrbitId']),
            'osculating_orbit': Orbit.retrieve_generic_by_id(obj_data['osculatingOrbitId']),
            'propagation_context': PropagationContext.retrieve_by_id(obj_data['propagationContextId']),
            'source': obj_data['source'],
            'spacecraft': Spacecraft.retrieve_generic_by_id(obj_data['spacecraftId'])
        }

    def api_create_map(self, force_save: bool = False) -> dict:
        """
        :meta private:
        """
        d = super().api_create_map()
        if self.covariance_matrix is not None:
            covariance_matrix_id = self.covariance_matrix.save(force=force_save).client_id
        else:
            covariance_matrix_id = None
        d.update(
            {
                'covariance_matrix_id': covariance_matrix_id,
                'propagation_context_id': self.propagation_context.save(force=force_save).client_id,
                'spacecraft_id': self.spacecraft.save(force=force_save).client_id,
                'orbit_id': self.osculating_orbit.save(force=force_save).client_id,
            }
        )
        return d

    def destroy(self, destroy_subcomponents: bool = False):
        """
        :meta private:
        """
        super().destroy()
        if destroy_subcomponents:
            self.mean_orbit.destroy()
            self.osculating_orbit.destroy()
            self.propagation_context.destroy()
            self.spacecraft.destroy()
            if self.covariance_matrix is not None:
                self.covariance_matrix.destroy()
