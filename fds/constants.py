STUDIO_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# NMEA sentences format regex
RMC = (r"(\$GPRMC,\d{6}\.\d+,A,\d{4}\.\d+,[NS],\d{5}\.\d+,[EW],\d+\.\d+,\d{1,3}\.\d+,\d{6},\d*\.\d*,([EW],)?[ADE]"
       r"\*[0-9A-Fa-f]{2})")
GGA = (r"(\$GPGGA,\d{6}\.\d+,\d{4}\.\d+,[NS],\d{5}\.\d+,[EW],\d,\d{2},\d{1,3}\.\d+,\d+.\d+,M,[+-]\d+.\d+,M,[\d{2}]?,"
       r"\*[0-9A-Fa-f]{2})")

EARTH_GRAV_CONSTANT = 398600.4418
EARTH_RADIUS = 6378.137e3  # meters
STANDARD_GRAVITY = 9.80665  # m/s²
