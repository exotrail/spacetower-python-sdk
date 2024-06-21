import base64
from enum import Enum
from loguru import logger

import spacetower_python_client as fdsapi

from fds import config
from fds.utils.log import log_and_raise


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class FdsClient(metaclass=SingletonMeta):
    """This class wraps the functions of the Fds API ."""

    class Models(str, Enum):
        # SPACECRAFT
        BATTERY = "BATTERY"
        SOLAR_ARRAY = "SOLAR_ARRAY"
        THRUSTER_ELECTRICAL = "THRUSTER_ELECTRICAL"
        THRUSTER_CHEMICAL = "THRUSTER_CHEMICAL"
        THRUSTER = "THRUSTER"
        # SPACECRAFT
        SPACECRAFT = "SPACECRAFT"
        SPACECRAFT_BOX = "SPACECRAFT_BOX"
        SPACECRAFT_SPHERE = "SPACECRAFT_SPHERE"
        # ORBIT
        ORBIT = "ORBIT"
        KEPLERIAN_ORBIT = "KEPLERIAN_ORBIT"
        CARTESIAN_ORBIT = "CARTESIAN_ORBIT"
        # ORBIT DATA MESSAGES
        OEM_REQUEST = "OEM_REQUEST"
        # ORBIT EXTRAPOLATION
        PROPAGATION_CONTEXT = "PROPAGATION_CONTEXT"
        EVENT_REQUEST_ORBITAL = "EVENT_REQUEST_ORBITAL"
        EVENT_REQUEST_STATION_VISIBILITY = "EVENT_REQUEST_STATION_VISIBILITY"
        EVENT_REQUEST_SENSOR = "EVENT_REQUEST_SENSOR"
        GROUND_STATION = "GROUND_STATION"
        # MEASUREMENT REQUEST
        MEASUREMENT_REQUEST_GPS_NMEA = "MEASUREMENT_REQUEST_GPS_NMEA"
        MEASUREMENT_REQUEST_GPS_PV = "MEASUREMENT_REQUEST_GPS_PV"
        MEASUREMENT_REQUEST_RADAR = "MEASUREMENT_REQUEST_RADAR"
        MEASUREMENT_REQUEST_OPTICAL = "MEASUREMENT_REQUEST_OPTICAL"
        # TELEMETRY
        TELEMETRY = "TELEMETRY"
        TELEMETRY_GPS_NMEA = "TELEMETRY_GPS_NMEA"
        TELEMETRY_GPS_NMEA_RAW = "TELEMETRY_GPS_NMEA_RAW"
        TELEMETRY_GPS_PV = "TELEMETRY_GPS_PV"
        TELEMETRY_RADAR = "TELEMETRY_RADAR"
        TELEMETRY_OPTICAL = "TELEMETRY_OPTICAL"
        # MANEUVER GENERATION
        MANEUVER_STRATEGY = "MANEUVER_STRATEGY"
        # ORBIT DETERMINATION
        COVARIANCE_MATRIX = "COVARIANCE_MATRIX"
        DIAGONAL_COVARIANCE_MATRIX = "DIAGONAL_COVARIANCE_MATRIX"
        ORBIT_DETERMINATION_CONFIG = "ORBIT_DETERMINATION_CONFIG"
        DRAG_COEFFICIENT_ESTIMATION_REQUEST = "DRAG_COEFFICIENT_ESTIMATION_REQUEST"
        REFLECTIVITY_COEFFICIENT_ESTIMATION_REQUEST = "REFLECTIVITY_COEFFICIENT_ESTIMATION_REQUEST"
        THRUST_VECTOR_ESTIMATION_REQUEST = "THRUST_VECTOR_ESTIMATION_REQUEST"
        PARAMETER_ESTIMATION_REQUEST = "PARAMETER_ESTIMATION_REQUEST"
        # ROADMAPS
        ACTION = "ACTION"
        ACTION_QUATERNION = "ACTION_QUATERNION"
        ACTION_ATTITUDE = "ACTION_ATTITUDE"
        ACTION_FIRING = "ACTION_FIRING"
        ACTION_THRUSTER = "ACTION_THRUSTER"
        ROADMAP_FROM_ACTIONS = "ROADMAP_FROM_ACTIONS"
        ROADMAP_FROM_SIMULATION = "ROADMAP_FROM_SIMULATION"
        # ORBITAL STATE
        ORBITAL_STATE = "ORBITAL_STATE"
        # EPHEMERIDES
        EPHEMERIDES_REQUEST = "EPHEMERIDES_REQUEST"
        # RESULTS
        RESULT_ORBIT_DETERMINATION = "RESULT_ORBIT_DETERMINATION"
        RESULT_ORBIT_EXTRAPOLATION = "RESULT_ORBIT_EXTRAPOLATION"
        RESULT_MANEUVER_GENERATION = "RESULT_MANEUVER_GENERATION"
        RESULT_TLE_EXTRAPOLATION = "RESULT_TLE_EXTRAPOLATION"

    class UseCases(str, Enum):
        ORBIT_DETERMINATION = "ORBIT_DETERMINATION"
        ORBIT_EXTRAPOLATION = "ORBIT_EXTRAPOLATION"
        MANEUVER_GENERATION = "MANEUVER_GENERATION"
        TLE_EXTRAPOLATION = "TLE_EXTRAPOLATION"

    # Regex to find fdsapi.OBJECT
    MODELS_MAP = {
        Models.BATTERY: {
            'object': fdsapi.BatteryDto,
            'create': lambda client: fdsapi.BatteryApi(client).create_battery,
            'retrieve': lambda client: fdsapi.BatteryApi(client).retrieve_battery,
            'retrieve_all': lambda client: fdsapi.BatteryApi(client).retrieve_all_batteries(),
            'destroy': lambda client: fdsapi.BatteryApi(client).delete_battery
        },
        Models.SOLAR_ARRAY: {
            'object': fdsapi.SolarArrayDto,
            'create': lambda client: fdsapi.SolarArrayApi(client).create_solar_array,
            'retrieve': lambda client: fdsapi.SolarArrayApi(client).retrieve_solar_array,
            'retrieve_all': lambda client: fdsapi.SolarArrayApi(client).retrieve_all_solar_arrays(),
            'destroy': lambda client: fdsapi.SolarArrayApi(client).delete_solar_array
        },
        Models.SPACECRAFT: {
            'retrieve': lambda client: fdsapi.SpacecraftApi(client).retrieve_spacecraft,
            'retrieve_all': lambda client: fdsapi.SpacecraftApi(client).retrieve_all(),
            'destroy': lambda client: fdsapi.SpacecraftApi(client).delete_spacecraft
        },
        Models.SPACECRAFT_BOX: {
            'object': fdsapi.BoxSpacecraftInputDto,
            'create': lambda client: fdsapi.SpacecraftApi(client).create_box_spacecraft,
            'retrieve': lambda client: fdsapi.SpacecraftApi(client).retrieve_spacecraft,
            'retrieve_all': lambda client: fdsapi.SpacecraftApi(client).retrieve_all(),
            'destroy': lambda client: fdsapi.SpacecraftApi(client).delete_spacecraft
        },
        Models.SPACECRAFT_SPHERE: {
            'object': fdsapi.SphericalSpacecraftDto,
            'create': lambda client: fdsapi.SpacecraftApi(client).create_spherical_spacecraft,
            'retrieve': lambda client: fdsapi.SpacecraftApi(client).retrieve_spacecraft,
            'retrieve_all': lambda client: fdsapi.SpacecraftApi(client).retrieve_all(),
            'destroy': lambda client: fdsapi.SpacecraftApi(client).delete_spacecraft
        },
        Models.THRUSTER: {
            'retrieve': lambda client: fdsapi.ThrusterApi(client).retrieve_thruster,
            'retrieve_all': lambda client: fdsapi.ThrusterApi(client).retrieve_all_thrusters(),
            'destroy': lambda client: fdsapi.ThrusterApi(client).delete_thruster
        },
        Models.THRUSTER_CHEMICAL: {
            'object': fdsapi.ChemicalThrusterDto,
            'create': lambda client: fdsapi.ThrusterApi(client).create_chemical_thruster,
            'retrieve': lambda client: fdsapi.ThrusterApi(client).retrieve_thruster,
            'retrieve_all': lambda client: fdsapi.ThrusterApi(client).retrieve_all_thrusters(),
            'destroy': lambda client: fdsapi.ThrusterApi(client).delete_thruster
        },
        Models.THRUSTER_ELECTRICAL: {
            'object': fdsapi.ElectricalThrusterDto,
            'create': lambda client: fdsapi.ThrusterApi(client).create_electrical_thruster,
            'retrieve': lambda client: fdsapi.ThrusterApi(client).retrieve_thruster,
            'retrieve_all': lambda client: fdsapi.ThrusterApi(client).retrieve_all_thrusters(),
            'destroy': lambda client: fdsapi.ThrusterApi(client).delete_thruster
        },
        Models.CARTESIAN_ORBIT: {
            'object': fdsapi.CartesianOrbitDto,
            'create': lambda client: fdsapi.OrbitApi(client).create_cartesian_orbit,
            'retrieve': lambda client: fdsapi.OrbitApi(client).retrieve_orbit_by_id,
            'retrieve_all': lambda client: fdsapi.OrbitApi(client).retrieve_all2(),
            'destroy': lambda client: fdsapi.OrbitApi(client).delete_orbit
        },
        Models.KEPLERIAN_ORBIT: {
            'object': fdsapi.KeplerianOrbitDto,
            'create': lambda client: fdsapi.OrbitApi(client).create_keplerian_orbit,
            'retrieve': lambda client: fdsapi.OrbitApi(client).retrieve_orbit_by_id,
            'retrieve_all': lambda client: fdsapi.OrbitApi(client).retrieve_all2(),
            'destroy': lambda client: fdsapi.OrbitApi(client).delete_orbit
        },
        Models.ORBIT: {
            'retrieve': lambda client: fdsapi.OrbitApi(client).retrieve_orbit_by_id,
            'retrieve_all': lambda client: fdsapi.OrbitApi(client).retrieve_all2(),
            'destroy': lambda client: fdsapi.OrbitApi(client).delete_orbit
        },
        Models.OEM_REQUEST: {
            'object': fdsapi.OemRequestDto,
            'create': lambda client: fdsapi.OrbitDataMessageRequestApi(client).create_oem_request,
            'retrieve': lambda client: fdsapi
            .OrbitDataMessageRequestApi(client).retrieve_orbit_data_message_request_by_id,
            'retrieve_all': lambda client: fdsapi
            .OrbitDataMessageRequestApi(client).retrieve_all4,
            'destroy': lambda client: fdsapi.OrbitDataMessageRequestApi(client).delete_orbit_data_message_request
        },
        Models.PROPAGATION_CONTEXT: {
            'object': fdsapi.PropagationContextDto,
            'create': lambda client: fdsapi.PropagationContextApi(client).create_propagation_context,
            'retrieve': lambda client: fdsapi.PropagationContextApi(client).retrieve_context,
            'retrieve_all': lambda client: fdsapi.PropagationContextApi(client).retrieve_all_contexts(),
            'destroy': lambda client: fdsapi.PropagationContextApi(client).delete_propagation_context
        },
        Models.MEASUREMENT_REQUEST_GPS_NMEA: {
            'object': fdsapi.GpsNmeaMeasurementsRequestDto,
            'create': lambda client: fdsapi.MeasurementsRequestApi(client).create_gps_nmea_measurements_request,
            'retrieve': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_measurements_request_by_id,
            'retrieve_all': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_all6(),
            'destroy': lambda client: fdsapi.MeasurementsRequestApi(client).delete_measurements_request
        },
        Models.MEASUREMENT_REQUEST_GPS_PV: {
            'object': fdsapi.GpsPvMeasurementsRequestDto,
            'create': lambda client: fdsapi.MeasurementsRequestApi(client).create_gps_measurements_request,
            'retrieve': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_measurements_request_by_id,
            'retrieve_all': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_all6(),
            'destroy': lambda client: fdsapi.MeasurementsRequestApi(client).delete_measurements_request
        },
        Models.MEASUREMENT_REQUEST_RADAR: {
            'object': fdsapi.RadarMeasurementsRequestDto,
            'create': lambda client: fdsapi.MeasurementsRequestApi(client).create_radar_measurements_request,
            'retrieve': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_measurements_request_by_id,
            'retrieve_all': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_all6(),
            'destroy': lambda client: fdsapi.MeasurementsRequestApi(client).delete_measurements_request
        },
        Models.MEASUREMENT_REQUEST_OPTICAL: {
            'object': fdsapi.OpticalMeasurementsRequestDto,
            'create': lambda client: fdsapi.MeasurementsRequestApi(client).create_optical_measurements_request,
            'retrieve': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_measurements_request_by_id,
            'retrieve_all': lambda client: fdsapi.MeasurementsRequestApi(client).retrieve_all6(),
            'destroy': lambda client: fdsapi.MeasurementsRequestApi(client).delete_measurements_request
        },
        Models.TELEMETRY: {
            'retrieve': lambda client: fdsapi.TelemetryApi(client).retrieve,
            'retrieve_all': lambda client: fdsapi.TelemetryApi(client).retrieve_all5(),
            'destroy': lambda client: fdsapi.TelemetryApi(client).delete_telemetry
        },
        Models.TELEMETRY_GPS_PV: {
            'object': fdsapi.GpsPvTelemetryDto,
            'create': lambda client: fdsapi.TelemetryApi(client).create_gps_pv_telemetry,
            'retrieve': lambda client: fdsapi.TelemetryApi(client).retrieve,
            'retrieve_all': lambda client: fdsapi.TelemetryApi(client).retrieve_all5(),
            'destroy': lambda client: fdsapi.TelemetryApi(client).delete_telemetry
        },
        Models.TELEMETRY_GPS_NMEA: {
            'object': fdsapi.GpsNmeaTelemetryDto,
            'create': lambda client: fdsapi.TelemetryApi(client).create_gps_nmea_telemetry,
            'retrieve': lambda client: fdsapi.TelemetryApi(client).retrieve,
            'retrieve_all': lambda client: fdsapi.TelemetryApi(client).retrieve_all5(),
            'destroy': lambda client: fdsapi.TelemetryApi(client).delete_telemetry
        },
        Models.TELEMETRY_GPS_NMEA_RAW: {
            'object': fdsapi.GpsNmeaRawTelemetryDto,
            'create': lambda client: fdsapi.TelemetryApi(client).create_gps_nmea_telemetry_raw,
            'retrieve': lambda client: fdsapi.TelemetryApi(client).retrieve,
            'retrieve_all': lambda client: fdsapi.TelemetryApi(client).retrieve_all5(),
            'destroy': lambda client: fdsapi.TelemetryApi(client).delete_telemetry
        },
        Models.TELEMETRY_RADAR: {
            'object': fdsapi.RadarTelemetryDto,
            'create': lambda client: fdsapi.TelemetryApi(client).create_radar_telemetry,
            'retrieve': lambda client: fdsapi.TelemetryApi(client).retrieve,
            'retrieve_all': lambda client: fdsapi.TelemetryApi(client).retrieve_all5(),
            'destroy': lambda client: fdsapi.TelemetryApi(client).delete_telemetry
        },
        Models.TELEMETRY_OPTICAL: {
            'object': fdsapi.OpticalTelemetryDto,
            'create': lambda client: fdsapi.TelemetryApi(client).create_optical_telemetry,
            'retrieve': lambda client: fdsapi.TelemetryApi(client).retrieve,
            'retrieve_all': lambda client: fdsapi.TelemetryApi(client).retrieve_all5(),
            'destroy': lambda client: fdsapi.TelemetryApi(client).delete_telemetry
        },

        # EVENTS
        Models.GROUND_STATION: {
            'object': fdsapi.GroundStationDto,
            'create': lambda client: fdsapi.GroundStationApi(client).create_ground_station,
            'retrieve': lambda client: fdsapi.GroundStationApi(client).retrieve_ground_station,
            'retrieve_all': lambda client: fdsapi.GroundStationApi(client).retrieve_all_stations(),
            'destroy': lambda client: fdsapi.GroundStationApi(client).delete_ground_station
        },
        Models.EVENT_REQUEST_ORBITAL: {
            'object': fdsapi.OrbitalEventsRequestDto,
            'create': lambda client: fdsapi.EventsRequestApi(client).create_event_request,
            'retrieve': lambda client: fdsapi.EventsRequestApi(client).retrieve_events_request,
            'retrieve_all': lambda client: fdsapi.EventsRequestApi(client).retrieve_all8(),
            'destroy': lambda client: fdsapi.EventsRequestApi(client).delete_event_request
        },
        Models.EVENT_REQUEST_SENSOR: {
            'object': fdsapi.SensorEventRequestDto,
            'create': lambda client: fdsapi.EventsRequestApi(client).create_sensor_event_request,
            'retrieve': lambda client: fdsapi.EventsRequestApi(client).retrieve_events_request,
            'retrieve_all': lambda client: fdsapi.EventsRequestApi(client).retrieve_all8(),
            'destroy': lambda client: fdsapi.EventsRequestApi(client).delete_event_request
        },
        Models.EVENT_REQUEST_STATION_VISIBILITY: {
            'object': fdsapi.StationVisibilityEventsRequestDto,
            'create': lambda client: fdsapi.EventsRequestApi(client).create_station_visibility_event_request,
            'retrieve': lambda client: fdsapi.EventsRequestApi(client).retrieve_events_request,
            'retrieve_all': lambda client: fdsapi.EventsRequestApi(client).retrieve_all8(),
            'destroy': lambda client: fdsapi.EventsRequestApi(client).delete_event_request
        },
        # ROADMAPS
        Models.ROADMAP_FROM_SIMULATION: {
            'retrieve': lambda client: fdsapi.RoadmapApi(client).retrieve_roadmap,
            'retrieve_all': lambda client: fdsapi.RoadmapApi(client).retrieve_all_roadmaps(),
            'destroy': lambda client: fdsapi.RoadmapApi(client).delete_roadmap
        },
        Models.ROADMAP_FROM_ACTIONS: {
            'object': fdsapi.RoadmapFromActionsDto,
            'create': lambda client: fdsapi.RoadmapApi(client).create_roadmap,
            'retrieve': lambda client: fdsapi.RoadmapApi(client).retrieve_roadmap,
            'retrieve_all': lambda client: fdsapi.RoadmapApi(client).retrieve_all_roadmaps(),
            'destroy': lambda client: fdsapi.RoadmapApi(client).delete_roadmap
        },
        Models.ACTION: {
            'retrieve': lambda client: fdsapi.RoadmapActionApi(client).retrieve_roadmap_action,
            'retrieve_all': lambda client: fdsapi.RoadmapActionApi(client).retrieve_all_roadmap_actions(),
            'destroy': lambda client: fdsapi.RoadmapActionApi(client).delete_roadmap_action
        },
        Models.ACTION_FIRING: {
            'object': fdsapi.FiringActionDto,
            'create': lambda client: fdsapi.RoadmapActionApi(client).create_firing_action,
            'retrieve': lambda client: fdsapi.RoadmapActionApi(client).retrieve_roadmap_action,
            'retrieve_all': lambda client: fdsapi.RoadmapActionApi(client).retrieve_all_roadmap_actions(),
            'destroy': lambda client: fdsapi.RoadmapActionApi(client).delete_roadmap_action
        },
        Models.ACTION_THRUSTER: {
            'retrieve': lambda client: fdsapi.RoadmapActionApi(client).retrieve_roadmap_action,
            'retrieve_all': lambda client: fdsapi.RoadmapActionApi(client).retrieve_all_roadmap_actions(),
            'destroy': lambda client: fdsapi.RoadmapActionApi(client).delete_roadmap_action
        },
        Models.ACTION_ATTITUDE: {
            'object': fdsapi.AttitudeActionDto,
            'create': lambda client: fdsapi.RoadmapActionApi(client).create_attitude_action,
            'retrieve': lambda client: fdsapi.RoadmapActionApi(client).retrieve_roadmap_action,
            'retrieve_all': lambda client: fdsapi.RoadmapActionApi(client).retrieve_all_roadmap_actions(),
            'destroy': lambda client: fdsapi.RoadmapActionApi(client).delete_roadmap_action
        },
        Models.ORBIT_DETERMINATION_CONFIG: {
            'object': fdsapi.UkfOrbitDeterminationConfigurationDto,
            'create': lambda client: fdsapi.OrbitDeterminationConfigurationApi(client).
            create_ukf_orbit_determination_configuration,
            'retrieve': lambda client: fdsapi.OrbitDeterminationConfigurationApi(client).
            retrieve_orbit_determination_configuration_by_id,
            'retrieve_all': lambda client: fdsapi.OrbitDeterminationConfigurationApi(client).
            retrieve_all_orbit_determination_configurations(),
            'destroy': lambda client: fdsapi.OrbitDeterminationConfigurationApi(client).
            delete_ukf_orbit_determination_configuration
        },
        Models.PARAMETER_ESTIMATION_REQUEST: {
            'retrieve': lambda client:
            fdsapi.ParameterEstimationRequestApi(client).retrieve_parameter_estimation_request_by_id,
            'retrieve_all': lambda client: fdsapi.ParameterEstimationRequestApi(client).retrieve_all1(),
            'destroy': lambda client: fdsapi.ParameterEstimationRequestApi(client).delete_parameter_estimation_request
        },
        Models.DRAG_COEFFICIENT_ESTIMATION_REQUEST: {
            'object': fdsapi.DragCoefficientEstimationRequestInputDto,
            'create': lambda client:
            fdsapi.ParameterEstimationRequestApi(client).create_drag_coefficient_estimation_request,
            'retrieve': lambda client:
            fdsapi.ParameterEstimationRequestApi(client).retrieve_parameter_estimation_request_by_id,
            'retrieve_all': lambda client: fdsapi.ParameterEstimationRequestApi(client).retrieve_all1(),
            'destroy': lambda client: fdsapi.ParameterEstimationRequestApi(client).delete_parameter_estimation_request
        },
        Models.REFLECTIVITY_COEFFICIENT_ESTIMATION_REQUEST: {
            'object': fdsapi.ReflectivityCoefficientEstimationRequestInputDto,
            'create': lambda client:
            fdsapi.ParameterEstimationRequestApi(client).create_reflectivity_coefficient_estimation_request,
            'retrieve': lambda client:
            fdsapi.ParameterEstimationRequestApi(client).retrieve_parameter_estimation_request_by_id,
            'retrieve_all': lambda client: fdsapi.ParameterEstimationRequestApi(client).retrieve_all1(),
            'destroy': lambda client: fdsapi.ParameterEstimationRequestApi(client).delete_parameter_estimation_request
        },
        Models.THRUST_VECTOR_ESTIMATION_REQUEST: {
            'object': fdsapi.ThrustVectorEstimationRequestInputDto,
            'create': lambda client:
            fdsapi.ParameterEstimationRequestApi(client).create_thrust_vector_estimation_request,
            'retrieve': lambda client:
            fdsapi.ParameterEstimationRequestApi(client).retrieve_parameter_estimation_request_by_id,
            'retrieve_all': lambda client: fdsapi.ParameterEstimationRequestApi(client).retrieve_all1(),
            'destroy': lambda client: fdsapi.ParameterEstimationRequestApi(client).delete_parameter_estimation_request
        },
        Models.DIAGONAL_COVARIANCE_MATRIX: {
            'object': fdsapi.DiagonalCovarianceMatrixDto,
            'create': lambda client: fdsapi.CovarianceMatrixApi(client).create_diagonal_covariance_matrix,
            'retrieve': lambda client: fdsapi.CovarianceMatrixApi(client).retrieve2,
            'retrieve_all': lambda client: fdsapi.CovarianceMatrixApi(client).retrieve_all10(),
            'destroy': lambda client: fdsapi.CovarianceMatrixApi(client).delete1
        },
        Models.COVARIANCE_MATRIX: {
            'object': fdsapi.FullCovarianceMatrixDto,
            'create': lambda client: fdsapi.CovarianceMatrixApi(client).create_covariance_matrix,
            'retrieve': lambda client: fdsapi.CovarianceMatrixApi(client).retrieve2,
            'retrieve_all': lambda client: fdsapi.CovarianceMatrixApi(client).retrieve_all10(),
            'destroy': lambda client: fdsapi.CovarianceMatrixApi(client).delete1
        },
        Models.MANEUVER_STRATEGY: {
            'object': fdsapi.ManeuverStrategyDto,
            'create': lambda client: fdsapi.ManeuverStrategyApi(client).create_maneuver_strategy,
            'retrieve': lambda client: fdsapi.ManeuverStrategyApi(client).retrieve_manoeuvre_strategy_by_id,
            'retrieve_all': lambda client: fdsapi.ManeuverStrategyApi(client).retrieve_all7(),
            'destroy': lambda client: fdsapi.ManeuverStrategyApi(client).delete_manoeuvre_strategy
        },
        Models.ORBITAL_STATE: {
            'object': fdsapi.OrbitalStateCreationRequestDto,
            'create': lambda client: fdsapi.OrbitalStateApi(client).create_orbital_state,
            'retrieve': lambda client: fdsapi.OrbitalStateApi(client).retrieve_orbital_state_by_id,
            'retrieve_all': lambda client: fdsapi.OrbitalStateApi(client).retrieve_all3(),
            'destroy': lambda client: fdsapi.OrbitalStateApi(client).delete_orbital_state
        },
        Models.EPHEMERIDES_REQUEST: {
            'object': fdsapi.EphemerisRequestDto,
            'create': lambda client: fdsapi.EphemerisRequestControllerApi(client).create_ephemeris_request,
            'retrieve': lambda client: fdsapi.EphemerisRequestControllerApi(client).retrieve1,
            'retrieve_all': lambda client: fdsapi.EphemerisRequestControllerApi(client).retrieve_all9(),
            'destroy': lambda client: fdsapi.EphemerisRequestControllerApi(client).delete
        },
        Models.RESULT_ORBIT_DETERMINATION: {
            'object': fdsapi.OrbitDeterminationResultDto,
            'retrieve': lambda client: fdsapi.OrbitDeterminationApi(client).get_orbit_determination_result,
            'retrieve_from_use_case': lambda client:
            fdsapi.OrbitDeterminationApi(client).get_orbit_determination_result_by_determination_id
        },
        Models.RESULT_ORBIT_EXTRAPOLATION: {
            'object': fdsapi.OrbitExtrapolationResultDto,
            'retrieve': lambda client: fdsapi.OrbitExtrapolationApi(client).get_orbit_extrapolation_result,
            'retrieve_from_use_case': lambda client:
            fdsapi.OrbitExtrapolationApi(client).get_orbit_extrapolation_result_by_extrapolation_id
        },
        Models.RESULT_MANEUVER_GENERATION: {
            'object': fdsapi.ManeuverGenerationResultDto,
            'retrieve': lambda client: fdsapi.ManeuverGenerationApi(client).get_maneuver_generation_result,
            'retrieve_from_use_case':
                lambda client: fdsapi.ManeuverGenerationApi(
                    client).get_maneuver_generation_result_by_request_id
        },
        Models.RESULT_TLE_EXTRAPOLATION: {
            'object': fdsapi.TleExtrapolationResultDto,
            'retrieve': lambda client: fdsapi.TLESGP4ExtrapolationApi(client).get_tle_extrapolation_result,
            'retrieve_from_use_case':
                lambda client: fdsapi.TLESGP4ExtrapolationApi(
                    client).get_tle_extrapolation_result_by_extrapolation_id
        },
    }

    USE_CASES_MAP = {
        UseCases.ORBIT_EXTRAPOLATION: {
            'command': fdsapi.OrbitExtrapolationInputDto,
            'runner': lambda client: fdsapi.OrbitExtrapolationApi(client).run_orbit_extrapolation,
            'retrieve': lambda client: fdsapi.OrbitExtrapolationApi(client).get_orbit_extrapolation,
        },
        UseCases.ORBIT_DETERMINATION: {
            'command': fdsapi.UkfOrbitDeterminationInputDto,
            'runner': lambda client: fdsapi.OrbitDeterminationApi(client).run_ukf_orbit_determination,
            'retrieve': lambda client: fdsapi.OrbitDeterminationApi(client).get_orbit_determination,
        },
        UseCases.MANEUVER_GENERATION: {
            'command': fdsapi.ManeuverGenerationInputDto,
            'runner': lambda client: fdsapi.ManeuverGenerationApi(client).run_maneuver_generation,
            'retrieve': lambda client: fdsapi.ManeuverGenerationApi(client).get_maneuver_generation,
        },
        UseCases.TLE_EXTRAPOLATION: {
            'command': fdsapi.TleExtrapolationDto,
            'runner': lambda client: fdsapi.TLESGP4ExtrapolationApi(client).extrapolate_tle,
            'retrieve': lambda client: fdsapi.TLESGP4ExtrapolationApi(client).get_tle_extrapolation,
        }
    }

    def __init__(self, fds_api_url, api_key=None, token=None, client_id=None, client_secret=None, proxy=None):
        self._api_config = fdsapi.Configuration(
            host=fds_api_url
        )
        self.api_key = api_key
        self.token = token
        self.client_id = client_id
        self.client_secret = client_secret
        if proxy is not None:
            self.api_config.proxy = proxy

    @property
    def api_config(self):
        return self._api_config

    @property
    def api_url_msg(self):
        return f"Client {self.api_config.host}"

    @classmethod
    def get_client(cls):
        return cls(
            fds_api_url=config.get_api_url(),
            api_key=config.get_api_key(),
            client_id=config.get_client_id(),
            client_secret=config.get_client_secret(),
            token=config.get_token(),
            proxy=config.get_proxy(),
        )

    @staticmethod
    def get_id(obj: object | dict):
        """The following is only needed because objects returned are sometimes classes, sometimes dicts (at the current
        client version, to be fixed in future releases)"""
        try:
            return getattr(obj, 'id')
        except AttributeError:
            return obj['id']

    def get_api_client(self):
        header_name = None
        header_value = None
        if self.api_key is not None and self.api_key != '':
            header_value = self.api_key
            header_name = 'apikey'
        elif self.token is not None and self.token != '':
            header_value = f'Bearer {self.token}'
            header_name = 'Authorization'
        elif self.client_id is not None and self.client_secret is not None:
            credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            header_value = f'Basic {credentials}'
            header_name = 'Authorization'
        return fdsapi.ApiClient(self.api_config, header_name=header_name, header_value=header_value)

    def _object_exists(self, object_type: str, client_id: str, object_map, command='retrieve') -> bool:
        with self.get_api_client() as api_client:
            try:
                object_map[self.Models[object_type]][command](api_client)(client_id)
            except fdsapi.ApiException as e:
                if e.status == 404:
                    return False
                logger.error(f"{self.api_url_msg}: Error while checking if '{object_type}' with client_id {client_id} "
                             f"exists")
                raise e
            else:
                return True

    def model_exists(self, model_type: str, client_id: str):
        return self._object_exists(model_type, client_id, self.MODELS_MAP)

    def use_case_exists(self, use_case_type: str, client_id: str):
        return self._object_exists(use_case_type, client_id, self.USE_CASES_MAP)

    def create_object(self, object_type: str, **kwargs) -> object:
        builder = self.MODELS_MAP[self.Models[object_type]]['object'](**kwargs)
        with self.get_api_client() as api_client:
            try:
                obj = self.MODELS_MAP[self.Models[object_type]]['create'](api_client)(builder)
                if hasattr(obj, 'actual_instance'):  # TODO investigate why this happens in openapi code generation
                    obj = obj.actual_instance
                client_id = self.get_id(obj)
            except fdsapi.ApiException as e:
                logger.error(f"{self.api_url_msg}: Error while creating '{object_type}'")
                raise e
            else:
                # logger.debug(f"{self.api_url_msg}: Created '{object_type}' with client_id: {client_id}")
                return obj

    def destroy_object(self, object_type: str, client_id: str) -> None:
        with self.get_api_client() as api_client:
            try:
                self.MODELS_MAP[self.Models[object_type]]['destroy'](api_client)(client_id)
            except fdsapi.ApiException as e:
                logger.error(f"{self.api_url_msg}: Error while destroying '{object_type}' with client_id: {client_id}")
                raise e
            else:
                pass
                # logger.debug(f"{self.api_url_msg}: Destroyed '{object_type}' with client_id: {client_id}")

    def _retrieve_object(self, object_type: str, client_id: str, object_map: dict, command='retrieve'):
        with self.get_api_client() as api_client:
            try:
                obj = object_map[self.Models[object_type]][command](api_client)(client_id)
            except fdsapi.ApiException as e:
                logger.error(f"{self.api_url_msg}: Error while retrieving '{object_type}' with client_id: {client_id}")
                raise e
            else:
                msg = '' if command == 'retrieve' else 'from use_case '
                # logger.debug(f"{self.api_url_msg}: Retrieving '{object_type}' {msg}with client_id: {client_id}")
                return obj

    def retrieve_model(self, model_type: str, client_id: str):
        return self._retrieve_object(model_type, client_id, self.MODELS_MAP)

    def retrieve_use_case(self, use_case_type: str, client_id: str):
        return self._retrieve_object(use_case_type, client_id, self.USE_CASES_MAP)

    def retrieve_result_from_use_case(self, model_type: str, use_case_client_id: str):
        if model_type not in (self.Models.RESULT_ORBIT_DETERMINATION,
                              self.Models.RESULT_ORBIT_EXTRAPOLATION,
                              self.Models.RESULT_MANEUVER_GENERATION):
            msg = f"Not possible to retrieve '{model_type}' with this method. Only Results can."
            log_and_raise(ValueError, msg)
        return self._retrieve_object(model_type, use_case_client_id, self.MODELS_MAP, 'retrieve_from_use_case')

    def retrieve_all(self, model_type: str):
        with self.get_api_client() as api_client:
            try:
                obj_list = self.MODELS_MAP[self.Models[model_type]]['retrieve_all'](api_client)
            except fdsapi.ApiException as e:
                logger.error(f"{self.api_url_msg}: Error while retrieving all '{model_type}'")
                raise e
            except KeyError:
                msg = f"It is not possible to retrieve all objects of type '{model_type}'."
                log_and_raise(KeyError, msg)
            else:
                # logger.debug(f"{self.api_url_msg}: Retrieving all '{model_type}'")
                return obj_list

    def run_use_case(self, use_case_type: str, **kwargs):
        command = self.USE_CASES_MAP[self.UseCases[use_case_type]]['command'](**kwargs)
        with self.get_api_client() as api_client:
            try:
                # logger.debug(f"{self.api_url_msg}: Running '{use_case_type}'...")
                obj = self.USE_CASES_MAP[self.UseCases[use_case_type]]['runner'](api_client)(command)
            except fdsapi.ApiException as e:
                logger.error(f"{self.api_url_msg}: Error while running '{use_case_type}'")
                raise e
            else:
                # logger.debug(f"{self.api_url_msg}: Finished '{use_case_type}' with client_id {self.get_id(obj)}")
                return obj
