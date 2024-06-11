DEFAULT_CONFIG = {
    "SPACECRAFT_SPHERE": {
        "nametag": None,  # str
        "platform_mass": None,  # float, (kg)
        "drag_coefficient": None,  # float, (-)
        "reflectivity_coefficient": None,  # float, (-)
        "cross_section": None,  # float, (m²)
    },
    "SPACECRAFT_BOX": {
        "nametag": None,  # str
        "platform_mass": None,  # float, (kg)
        "drag_coefficient": None,  # float, (-)
        "reflectivity_coefficient": None,  # float, (-)
        "max_angular_acceleration": None,  # float, (deg/s²)
        "max_angular_velocity": None,  # float, (deg/s)
        "length_x": None,  # float, (m)
        "length_y": None,  # float, (m)
        "length_z": None,  # float, (m)
    },
    "BATTERY": {
        "nametag": None,  # str
        "depth_of_discharge": None,  # float,(0<x<1)
        "nominal_capacity": None,  # float,(W)
        "minimum_charge_for_firing": None,  # float,(0<x<1)
        "initial_charge": None,  # float,(0<x<1)
    },
    "SOLAR_ARRAY": {
        "nametag": None,  # str
        "kind": None,  # str, (values: BODY, DEPLOYABLE_FIXED, DEPLOYABLE_ROTATING, NONE)
        "initialisation_kind": None,  # str, (values: MAXIMUM_POWER, SURFACE, SURFACE_AND_POWER)
        "efficiency": None,  # float, (0<x<1)
        "normal_in_satellite_frame": [None, None, None],  # list[float, float, float], 3-elements unit vector
        "maximum_power": None,  # float, (W)
        "surface": None,  # float, (m²).
        "axis_in_satellite_frame": [None, None, None],  # Iterable[float], 3-elements unit vector
        "satellite_faces": None,  # Iterable[str], (values: PLUS_X, MINUS_X, PLUS_Y, MINUS_Y, PLUS_Z, MINUS_Z)
    },
    "THRUSTER_ELECTRICAL": {
        "nametag": None,  # str
        "impulse": None,  # float, (Ns)
        "maximum_thrust_duration": None,  # float, (s)
        "propellant_mass": None,  # float, (kg)
        "thrust": None,  # float, (N)
        "axis_in_satellite_frame": [None, None, None],  # list[float, float, float], 3-elements unit vector
        "isp": None,  # float, (s)
        "wet_mass": None,  # float, (kg)
        "warm_up_duration": None,  # float, (s)
        "power": None,  # float, (W)
        "stand_by_power": None,  # float, (W)
        "warm_up_power": None,  # float, (W)
    },
    "THRUSTER_CHEMICAL": {
        "nametag": None,  # str
        "impulse": None,  # float, (Ns)
        "maximum_thrust_duration": None,  # float, (s)
        "propellant_mass": None,  # float, (kg)
        "thrust": None,  # float, (N)
        "axis_in_satellite_frame": [None, None, None],  # list[float, float, float], 3-elements unit vector
        "isp": None,  # float, (s)
        "wet_mass": None,  # float, (kg)
        "warm_up_duration": None,  # float, (s)
    },
    "PROPAGATION_CONTEXT": {
        "nametag": None,
        "integrator_min_step": None,  # float, (s)
        "integrator_max_step": None,  # float, (s)
        "integrator_kind": None,
        # str, (values: 'DORMAND_PRINCE_853', 'DORMAND_PRINCE_54', 'ADAMS_MOULTON', 'RUNGE_KUTTA')
        "model_perturbations": None,
        # Iterable[str], Perturbations included in the model (values: EARTH_POTENTIAL, SRP, THIRD_BODY, DRAG, CONSTANT_THRUST, IMPULSIVE_THRUST)
        "model_solar_flux": None,  # float, Solar flux (SFU).
        "model_earth_potential_deg": None,  # int, Earth potential degree (-)
        "model_earth_potential_ord": None,  # int, Earth potential order (-)
        "model_atmosphere_kind": None,  # str, (values: 'HARRIS_PRIESTER', 'NRL_MSISE00')
    },
    "MANEUVER_STRATEGY": {
        "nametag": None,  # str
        "thrust_arcs_position": None,
        # str, (values: ASCENDING_AND_DESCENDING_NODES, ASCENDING_NODE, CUSTOM, DESCENDING_NODE, APOGEE_AND_PERIGEE, APOGEE, PERIGEE, ASCENDING_AND_DESCENDING_ANTINODES, ASCENDING_ANTINODE, DESCENDING_ANTINODE, MEAN_LONGITUDE)
        "thrust_arcs_number": None,  # str, (values: ONE or TWO)
        "thrust_arc_initialisation_kind": None,  # str, (values: DUTY_CYCLE, THRUST_DURATION)
        "number_of_thrust_orbits": None,  # int
        "number_of_rest_orbits": None,  # int
        "number_of_shift_orbits": None,  # int
        "orbital_duty_cycle": None,  # float, (0<x<1)
        "thrust_arc_duration": None,  # float, (s)
        "stop_thrust_at_eclipse": None,  # bool
    },
    "ORBIT_DETERMINATION_CONFIG": {
        "nametag": None,
        "tuning_alpha": None,  # float
        "tuning_beta": None,  # float
        "tuning_kappa": None,  # float
        "outliers_manager_scale": None,  # float
        "outliers_manager_warmup": None,  # int
        "noise_provider_kind": None,  # str, (values: 'BASIC', 'SNC', 'DMC', 'EDB_CD')
    },
    "TELEMETRY_GPS_NMEA": {
        "nametag": None,
        "standard_deviation_ground_speed": None,  # float
        "standard_deviation_latitude": None,  # float
        "standard_deviation_longitude": None,  # float
        "standard_deviation_altitude": None,  # float
    },
    "TELEMETRY_GPS_NMEA_RAW": {
        "nametag": None,
        "standard_deviation_ground_speed": None,  # float
        "standard_deviation_latitude": None,  # float
        "standard_deviation_longitude": None,  # float
        "standard_deviation_altitude": None,  # float
    },
    "TELEMETRY_GPS_PV": {
        "nametag": None,
        "standard_deviation_position": None,  # float
        "standard_deviation_velocity": None,  # float
    },
    "TELEMETRY_RADAR": {
        "nametag": None,
        "two_way_measurement": None,  # bool
        "standard_deviation_azimuth": None,  # float
        "standard_deviation_elevation": None,  # float
        "standard_deviation_range": None,  # float
        "standard_deviation_range_rate": None,  # float
    },
    "TELEMETRY_OPTICAL": {
        "nametag": None,
        "standard_deviation_azimuth": None,  # float
        "standard_deviation_elevation": None,  # float
    },
    "OEM_REQUEST": {
        "nametag": None,  # str
        "creator": None,  # str
        "ephemerides_step": None,  # float
        "frame": None,  # str
        "object_id": None,  # str
        "object_name": None,  # str
        "write_acceleration": None,  # bool
        "write_covariance": None,  # bool
    },

    "version": 1.3,
}
