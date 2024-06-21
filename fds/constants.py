STUDIO_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# NMEA sentences format regex
# RMC = (r"(\$GPRMC,\d{6}\.\d+,A,\d{4}\.\d+,[NS],\d{5}\.\d+,[EW],\d+\.\d+,\d{1,3}\.\d+,\d{6},\d*\.\d*,([EW],)?[ADE]"
#        r"\*[0-9A-Fa-f]{2})")
RMC_REGEX = (r"(\$GPRMC,\d{6}\.\d+,A,\d{4}\.\d+,[NS],\d{5}\.\d+,[EW],\d+\.\d+,\d{1,3}\.\d+,\d{6},(\d+\.\d+)?,([EW])?,"
             r"[ADE]*\*[0-9A-Fa-f]{2})")  # https://docs.novatel.com/OEM7/Content/Logs/GPRMC.htm
# GGA = (r"(\$GPGGA,\d{6}\.\d+,\d{4}\.\d+,[NS],\d{5}\.\d+,[EW],\d,\d{2},\d{1,3}\.\d+,\d+.\d+,M,[+-]\d+.\d+,M,[\d{2}]?,"
#        r"\*[0-9A-Fa-f]{2})")
GGA_REGEX = (r"(\$GPGGA,\d{6}\.\d+,\d{4}\.\d+,[NS],\d{5}\.\d+,[EW],\d,\d{1,2},\d+\.\d+,\d+\.\d+,M,([+-]\d+\.\d+)?,M?,"
             r"(\d{1,2})?,(.{4})?\*[0-9A-Fa-f]{2}$)")  # https://docs.novatel.com/OEM7/Content/Logs/GPGGA.htm

EARTH_GRAV_CONSTANT = 398600.4418
EARTH_RADIUS = 6378.137e3  # meters
STANDARD_GRAVITY = 9.80665  # m/s²

# UNIT CONVERSIONS
KN_TO_MPS = 0.514444
