from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import numpy as np

from fds.client import FdsClient
from fds.models._model import RetrievableModel
from fds.models.orbital_state import OrbitalState, CovarianceMatrix
from fds.models.orbits import Orbit
from fds.models.two_line_element import TwoLineElement
from fds.utils.dates import get_datetime
from fds.utils.enum import EnumFromInput
from fds.utils.geometry import convert_to_numpy_array_and_check_shape


class ResultOrbitDetermination(RetrievableModel):
    class Status(EnumFromInput):
        SUCCESS, ANALYSIS_NEEDED, FAILURE = "SUCCESS", "ANALYSIS_NEEDED", "FAILURE"

    @dataclass
    class Report:
        @dataclass
        class ResidualsStatistics:
            class ResidualsNames(EnumFromInput):
                ALTITUDE, LATITUDE, LONGITUDE, GROUND_SPEED = "ALTITUDE", "LATITUDE", "LONGITUDE", "GROUND_SPEED"
                POSITION, VELOCITY = "POSITION", "VELOCITY"
                AZIMUTH, ELEVATION = "AZIMUTH", "ELEVATION"
                RANGE, RANGE_RATE = "RANGE", "RANGE_RATE"

            @dataclass
            class NormalisedResidualStatistics:
                mean: float
                standard_deviation: float
                median: float
                values: np.ndarray
                dates: Sequence[datetime]

                @property
                def max(self) -> float:
                    return np.max(self.values)

                @property
                def min(self) -> float:
                    return np.min(self.values)

                @classmethod
                def create_from_api_dict(cls, obj_data: dict):
                    residuals_api = obj_data['residuals']
                    residuals_array = np.empty(len(residuals_api))
                    dates = []
                    for i, residual in enumerate(residuals_api):
                        residuals_array[i] = residual.get('value')
                        dates.append(get_datetime(residual.get('date')))
                    dates, residuals_array = zip(*sorted(zip(dates, residuals_array)))
                    return cls(
                        mean=obj_data['mean'],
                        standard_deviation=obj_data['standardDeviation'],
                        median=obj_data['median'],
                        values=residuals_array,
                        dates=dates
                    )

            altitude: NormalisedResidualStatistics = None
            latitude: NormalisedResidualStatistics = None
            longitude: NormalisedResidualStatistics = None
            ground_speed: NormalisedResidualStatistics = None
            position: NormalisedResidualStatistics = None
            velocity: NormalisedResidualStatistics = None
            azimuth: NormalisedResidualStatistics = None
            elevation: NormalisedResidualStatistics = None
            range: NormalisedResidualStatistics = None
            range_rate: NormalisedResidualStatistics = None

            _name_mapping = {
                ResidualsNames.ALTITUDE: 'altitude',
                ResidualsNames.LATITUDE: 'latitude',
                ResidualsNames.LONGITUDE: 'longitude',
                ResidualsNames.GROUND_SPEED: 'ground_speed',
                ResidualsNames.POSITION: 'position',
                ResidualsNames.VELOCITY: 'velocity',
                ResidualsNames.AZIMUTH: 'azimuth',
                ResidualsNames.ELEVATION: 'elevation',
                ResidualsNames.RANGE: 'range',
                ResidualsNames.RANGE_RATE: 'range_rate'
            }

            @classmethod
            def create_from_api_dict(cls, obj_data: list[dict]):
                residuals_statistics = {}
                for rs in obj_data:
                    residuals_statistics[cls._name_mapping[cls.ResidualsNames(rs['field'])]] = (
                        cls.NormalisedResidualStatistics.create_from_api_dict(rs))
                return cls(**residuals_statistics)

        rejected_measurements: int
        used_measurements: int
        residuals_statistics: ResidualsStatistics

        @classmethod
        def create_from_api_dict(cls, obj_data: dict):
            residuals_statistics = cls.ResidualsStatistics.create_from_api_dict(obj_data['residualsStatistics'])
            return cls(
                rejected_measurements=obj_data['numberOfRejectedMeasurements'],
                used_measurements=obj_data['numberOfUsedMeasurements'],
                residuals_statistics=residuals_statistics,
            )

    @dataclass
    class InDepthResults:

        @dataclass
        class DragCoefficient:
            value: float
            date: datetime

            @classmethod
            def create_from_api_dict(cls, obj_data: dict):
                return cls(
                    value=obj_data['value'],
                    date=get_datetime(obj_data['date'])
                )

        @dataclass
        class ReflectivityCoefficient:
            value: float
            date: datetime

            @classmethod
            def create_from_api_dict(cls, obj_data: dict):
                return cls(
                    value=obj_data['value'],
                    date=get_datetime(obj_data['date'])
                )

        @dataclass
        class EstimatedThrust:
            tnw_direction: np.ndarray
            magnitude: float
            scale_factors: np.ndarray
            date: datetime

            @classmethod
            def create_from_api_dict(cls, obj_data: dict):
                tnw_direction = convert_to_numpy_array_and_check_shape(obj_data['tnwDirection'], (3,))
                scale_factors = convert_to_numpy_array_and_check_shape(obj_data['scaleFactors'], (3,))
                return cls(
                    tnw_direction=tnw_direction,
                    magnitude=obj_data['magnitude'],
                    scale_factors=scale_factors,
                    date=get_datetime(obj_data['date'])
                )

        mean_orbits: list[Orbit]
        osculating_orbits: list[Orbit]
        covariance_matrices: list[CovarianceMatrix]
        estimated_drag_coefficients: list[DragCoefficient] = None
        estimated_reflectivity_coefficients: list[ReflectivityCoefficient] = None
        estimated_thrust_data: list[EstimatedThrust] = None

        @property
        def dates(self) -> list[datetime]:
            return [o.date for o in self.osculating_orbits]

        @classmethod
        def create_from_api_dict(cls, obj_data: dict):
            mean_orbits = [Orbit.retrieve_generic_by_id(o['id']) for o in
                           obj_data['meanOrbits']]
            osculating_orbits = [Orbit.retrieve_generic_by_id(o['id']) for o in
                                 obj_data['osculatingOrbits']]
            mean_orbits.sort(key=lambda x: x.date)
            osculating_orbits.sort(key=lambda x: x.date)

            covariance_matrices = [CovarianceMatrix._create_from_api_object_data(cm) for cm in
                                   obj_data['covarianceMatrices']]
            covariance_matrices.sort(key=lambda x: x.date)

            # Check if parameters were estimated
            estimated_drag = obj_data['estimatedDragCoefficients']
            if estimated_drag is not None:
                estimated_drag_coefficients = [cls.DragCoefficient.create_from_api_dict(ed) for ed in estimated_drag]
                estimated_drag_coefficients.sort(key=lambda x: x.date)
            else:
                estimated_drag_coefficients = None

            estimated_reflectivity = obj_data['estimatedReflectivityCoefficients']
            if estimated_reflectivity is not None:
                estimated_reflectivity_coefficients = [cls.ReflectivityCoefficient.create_from_api_dict(er) for er in
                                                       estimated_reflectivity]
                estimated_reflectivity_coefficients.sort(key=lambda x: x.date)
            else:
                estimated_reflectivity_coefficients = None

            estimated_thrust = obj_data.get('estimatedThrustData')
            if estimated_thrust is not None:
                estimated_thrust_data = [cls.EstimatedThrust.create_from_api_dict(et) for et in estimated_thrust]
                estimated_thrust_data.sort(key=lambda x: x.date)
            else:
                estimated_thrust_data = None

            return cls(
                mean_orbits=mean_orbits,
                osculating_orbits=osculating_orbits,
                estimated_drag_coefficients=estimated_drag_coefficients,
                estimated_reflectivity_coefficients=estimated_reflectivity_coefficients,
                covariance_matrices=covariance_matrices,
                estimated_thrust_data=estimated_thrust_data
            )

    @dataclass
    class FiringAnalysisReport:

        @dataclass
        class FiringAnalysis:
            @dataclass
            class DeltaKeplerianElements:
                delta_semi_major_axis: float
                delta_eccentricity: float
                delta_inclination: float
                delta_raan: float
                delta_argument_of_perigee: float

                @classmethod
                def create_from_api_dict(cls, obj_data: dict):
                    return cls(
                        delta_semi_major_axis=obj_data['semiMajorAxisDelta'],
                        delta_eccentricity=obj_data['eccentricityDelta'],
                        delta_inclination=obj_data['inclinationDelta'],
                        delta_raan=obj_data['raanDelta'],
                        delta_argument_of_perigee=obj_data['argumentOfPerigeeDelta'],
                    )

                def to_array(self):
                    return np.array([self.delta_semi_major_axis, self.delta_eccentricity, self.delta_inclination,
                                     self.delta_argument_of_perigee, self.delta_raan])

            @dataclass
            class SmoothedKeplerianElements:
                semi_major_axis: float
                eccentricity: float
                inclination: float
                raan: float
                argument_of_perigee: float
                semi_major_axis_standard_deviation: float
                eccentricity_standard_deviation: float
                inclination_standard_deviation: float
                raan_standard_deviation: float
                argument_of_perigee_standard_deviation: float

                @classmethod
                def create_from_api_dict(cls, obj_data: dict):
                    return cls(
                        semi_major_axis=obj_data['semiMajorAxis'],
                        eccentricity=obj_data['eccentricity'],
                        inclination=obj_data['inclination'],
                        raan=obj_data['raan'],
                        argument_of_perigee=obj_data['argumentOfPerigee'],
                        semi_major_axis_standard_deviation=obj_data['semiMajorAxisStandardDeviation'],
                        eccentricity_standard_deviation=obj_data['eccentricityStandardDeviation'],
                        inclination_standard_deviation=obj_data['inclinationStandardDeviation'],
                        raan_standard_deviation=obj_data['raanStandardDeviation'],
                        argument_of_perigee_standard_deviation=obj_data['argumentOfPerigeeStandardDeviation']
                    )

                def to_array(self):
                    return (np.array([self.semi_major_axis, self.eccentricity, self.inclination,
                                      self.argument_of_perigee, self.raan]),
                            np.array([self.semi_major_axis_standard_deviation, self.eccentricity_standard_deviation,
                                      self.inclination_standard_deviation, self.argument_of_perigee_standard_deviation,
                                      self.raan_standard_deviation]))

            delta_keplerian_elements: DeltaKeplerianElements
            smoothed_keplerian_elements_before_firing: SmoothedKeplerianElements
            smoothed_keplerian_elements_after_firing: SmoothedKeplerianElements
            estimated_acceleration: float
            estimated_thrust: float
            date: datetime
            estimated_thrust_direction_tnw: np.ndarray = None

        processed_analyses: list[FiringAnalysis]
        number_of_processed_analyses: int
        number_of_failed_analyses: int
        number_of_pending_analyses: int
        failed_analyses_dates: list[datetime]
        pending_analyses_dates: list[datetime]

        @property
        def number_of_firings(self):
            return self.number_of_processed_analyses + self.number_of_failed_analyses + self.number_of_pending_analyses

        @property
        def processed_analyses_dates(self):
            return [fa.date for fa in self.processed_analyses]

        @classmethod
        def create_from_api_dict(cls, obj_data: dict):
            processed_analyses = []
            for pa in obj_data['processedAnalyses']:
                delta_keplerian_elements = cls.FiringAnalysis.DeltaKeplerianElements.create_from_api_dict(pa)

                smoothed_ke_before_firing = cls.FiringAnalysis.SmoothedKeplerianElements.create_from_api_dict(
                    pa['smoothedKeplerianElementsBeforeFiring']
                )

                smoothed_ke_after_firing = cls.FiringAnalysis.SmoothedKeplerianElements.create_from_api_dict(
                    pa['smoothedKeplerianElementsAfterFiring']
                )
                thrust_direction = pa.get('estimatedThrustTnwDirection', None)
                if thrust_direction is not None:
                    thrust_direction = convert_to_numpy_array_and_check_shape(thrust_direction, (3,))

                processed_analyses.append(cls.FiringAnalysis(
                    delta_keplerian_elements=delta_keplerian_elements,
                    smoothed_keplerian_elements_before_firing=smoothed_ke_before_firing,
                    smoothed_keplerian_elements_after_firing=smoothed_ke_after_firing,
                    date=get_datetime(pa['date']),
                    estimated_acceleration=pa['estimatedAcceleration'],
                    estimated_thrust=pa['estimatedThrust'],
                    estimated_thrust_direction_tnw=thrust_direction
                ))

            return cls(
                processed_analyses=processed_analyses,
                number_of_processed_analyses=obj_data['numberOfProcessedAnalyses'],
                number_of_failed_analyses=obj_data['numberOfFailedAnalyses'],
                number_of_pending_analyses=obj_data['numberOfPendingAnalyses'],
                failed_analyses_dates=[get_datetime(d) for d in obj_data['failedAnalysesDates']],
                pending_analyses_dates=[get_datetime(d) for d in obj_data['pendingAnalysesDates']]
            )

    FDS_TYPE = FdsClient.Models.RESULT_ORBIT_DETERMINATION

    def __init__(
            self,
            status: Status,
            report: Report,
            in_depth_results: InDepthResults,
            estimated_states: list[OrbitalState],
            estimated_keplerian_covariance_matrix: CovarianceMatrix,
            firing_analysis_report: FiringAnalysisReport = None,
            nametag: str = None
    ):
        super().__init__(nametag)

        self._status = status
        self._report = report
        self._estimated_states = estimated_states
        self._estimated_keplerian_covariance_matrix = estimated_keplerian_covariance_matrix
        self._in_depth_results = in_depth_results
        self._firing_analysis_report = firing_analysis_report

    @property
    def status(self) -> Status:
        return self._status

    @property
    def report(self) -> Report:
        return self._report

    @property
    def in_depth_results(self) -> InDepthResults:
        return self._in_depth_results

    @property
    def estimated_states(self) -> list[OrbitalState]:
        return self._estimated_states

    @property
    def estimated_keplerian_covariance_matrix(self) -> CovarianceMatrix:
        return self._estimated_keplerian_covariance_matrix

    @property
    def firing_analysis_report(self) -> FiringAnalysisReport:
        return self._firing_analysis_report

    @property
    def estimated_tle(self) -> TwoLineElement:
        return self.estimated_states[-1].fitted_tle

    @property
    def estimated_orbital_state(self) -> OrbitalState:
        return self.estimated_states[-1]

    @classmethod
    def api_retrieve_map(cls, obj_data: dict) -> dict:
        estimated_states = [OrbitalState.retrieve_by_id(es['id']) for es in
                            obj_data['estimatedStates']]
        firing_analysis_report = cls.FiringAnalysisReport.create_from_api_dict(obj_data['firingAnalysisReport']) \
            if 'firingAnalysisReport' in obj_data else None
        estimated_keplerian_covariance_matrix = CovarianceMatrix._create_from_api_object_data(
            obj_data['estimatedKeplerianCovariance'])

        return {
            'status': obj_data['status'],
            'estimated_keplerian_covariance_matrix': estimated_keplerian_covariance_matrix,
            'report': cls.Report.create_from_api_dict(obj_data['report']),
            'in_depth_results': cls.InDepthResults.create_from_api_dict(
                obj_data['inDepthResults']),
            'estimated_states': estimated_states,
            'firing_analysis_report': firing_analysis_report
        }

    def export_firings_report_data(self) -> list[dict]:
        if self.firing_analysis_report is None:
            return []

        lines = []

        for pa in self.firing_analysis_report.processed_analyses:
            lines.append({
                'date': pa.date,
                'delta_semi_major_axis': pa.delta_keplerian_elements.delta_semi_major_axis,
                'delta_eccentricity': pa.delta_keplerian_elements.delta_eccentricity,
                'delta_inclination': pa.delta_keplerian_elements.delta_inclination,
                'delta_raan': pa.delta_keplerian_elements.delta_raan,
                'delta_argument_of_perigee': pa.delta_keplerian_elements.delta_argument_of_perigee,
                'status': 'processed'
            })

        for date in self.firing_analysis_report.failed_analyses_dates:
            lines.append({
                'date': date,
                'status': 'failed'
            })

        for date in self.firing_analysis_report.pending_analyses_dates:
            lines.append({
                'date': date,
                'status': 'pending'
            })
        return lines

    def export_parameter_estimation_data(self) -> list[dict]:
        lines = []
        if self.in_depth_results.estimated_drag_coefficients is not None:
            for ed in self.in_depth_results.estimated_drag_coefficients:
                lines.append({
                    'date': ed.date,
                    'value': ed.value,
                    'parameter': 'drag_coefficient'
                })

        if self.in_depth_results.estimated_reflectivity_coefficients is not None:
            for er in self.in_depth_results.estimated_reflectivity_coefficients:
                lines.append({
                    'date': er.date,
                    'value': er.value,
                    'parameter': 'reflectivity_coefficient'
                })

        lines = sorted(lines, key=lambda x: x['date'])

        return lines

    def export_thrust_estimation_data(self) -> list[dict]:
        lines = []
        if self.in_depth_results.estimated_thrust_data is not None:
            for et in self.in_depth_results.estimated_thrust_data:
                lines.append({
                    'date': et.date,
                    'magnitude': et.magnitude,
                    'tnw_direction_x': et.tnw_direction[0],
                    'tnw_direction_y': et.tnw_direction[1],
                    'tnw_direction_z': et.tnw_direction[2],
                    'scale_factor_x': et.scale_factors[0],
                    'scale_factor_y': et.scale_factors[1],
                    'scale_factor_z': et.scale_factors[2]
                })
        return lines
