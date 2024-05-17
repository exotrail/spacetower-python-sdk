import numpy as np

from fds.constants import EARTH_GRAV_CONSTANT, STANDARD_GRAVITY
from fds.utils import math
from fds.utils.frames import transformation_matrix_in_to_tnw


class OrbitalElements:
    def __init__(
            self,
            SMA: float,
            ECC: float,
            INC: float,
            AOP: float,
            RAAN: float,
            TA: float
    ):
        """
        Args:
            SMA (float): semi-major axis [km]
            ECC (float): eccentricity [-]
            INC (float): inclination [deg]
            AOP (float): argument of periapsis [deg]
            RAAN (float): right ascension of the ascending node [deg]
            TA (float): true anomaly [deg]
        """
        self._SMA = SMA
        self._ECC = ECC
        self._INC = math.modulo_with_range(INC, 0, 180)
        self._AOP = math.modulo_with_range(AOP, 0, 360)
        self._RAAN = math.modulo_with_range(RAAN, -180, 180)
        self._TA = math.modulo_with_range(TA, 0, 360)
        self._MA = math.modulo_with_range(
            float(np.rad2deg(mean_anomaly_from_true_anomaly(self.ECC, np.deg2rad(self.TA)))), 0, 360
        )

    @property
    def SMA(self) -> float:
        return self._SMA

    @property
    def ECC(self) -> float:
        return self._ECC

    @property
    def INC(self) -> float:
        return self._INC

    @property
    def AOP(self) -> float:
        return self._AOP

    @property
    def RAAN(self) -> float:
        return self._RAAN

    @property
    def TA(self) -> float:
        return self._TA

    @property
    def MA(self) -> float:
        return self._MA

    def as_array(self, with_mean_anomaly: bool = True, radians: bool = False) -> np.ndarray:
        an = self.MA if with_mean_anomaly else self.TA

        if radians:
            return np.array([self.SMA, self.ECC, np.deg2rad(self.INC), np.deg2rad(self.AOP), np.deg2rad(self.RAAN),
                             np.deg2rad(an)])
        return np.array([self.SMA, self.ECC, self.INC, self.AOP, self.RAAN, an])

    @classmethod
    def with_mean_anomaly(
            cls,
            SMA: float,
            ECC: float,
            INC: float,
            AOP: float,
            RAAN: float,
            MA: float
    ) -> 'OrbitalElements':
        """
            Args:
                SMA (float): semi-major axis [km]
                ECC (float): eccentricity [-]
                INC (float): inclination [deg]
                AOP (float): argument of periapsis [deg]
                RAAN (float): right ascension of the ascending node [deg]
                MA (float): mean anomaly [deg]
        """
        true_anomaly = true_anomaly_from_mean_anomaly(ECC, np.deg2rad(MA))
        return cls(SMA, ECC, INC, AOP, RAAN, np.rad2deg(true_anomaly))


def mean_anomaly_from_true_anomaly(
        eccentricity: float,
        true_anomaly: float
) -> float:
    """
    Compute the mean anomaly from the true anomaly.

    Args:
        eccentricity: eccentricity [-]
        true_anomaly: true anomaly [rad]

    Returns:
        float: mean anomaly [rad]
    """
    eccentric_anomaly = eccentric_anomaly_from_true_anomaly(eccentricity, true_anomaly)
    return mean_anomaly_from_eccentric_anomaly(eccentricity, eccentric_anomaly)


def mean_anomaly_from_eccentric_anomaly(
        eccentricity: float,
        eccentric_anomaly: float
) -> float:
    """
    Compute the mean anomaly from the eccentric anomaly.

    Args:
        eccentricity: eccentricity [-]
        eccentric_anomaly: eccentric anomaly [rad]

    Returns:
        float: mean anomaly [rad]

    Source:
        Curtis, Orbital Mechanics for Engineering Students, eq 3.11
    """
    return eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly)


def eccentric_anomaly_from_true_anomaly(
        eccentricity: float,
        true_anomaly: float
) -> float:
    """
    Compute the eccentric anomaly from the true anomaly.

    Args:
        eccentricity: eccentricity [-]
        true_anomaly: true anomaly [rad] in the range [-pi, pi]

    Returns:
        float: eccentric anomaly [rad]

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_kp_v2E
    """
    true_anomaly = math.modulo_with_range(true_anomaly, -np.pi, np.pi)
    beta = eccentricity / (1 + np.sqrt(1 - eccentricity ** 2))
    return true_anomaly - 2 * np.arctan2(beta * np.sin(true_anomaly), 1 + beta * np.cos(true_anomaly))


def eccentric_anomaly_from_mean_anomaly_newton_rhapson(
        eccentricity: float,
        mean_anomaly: float,
        step_tol: float = 1E-15
) -> float:
    """
    Compute the eccentric anomaly from the mean anomaly using the Newton-Raphson method.

    Args:
        eccentricity: eccentricity [-]
        mean_anomaly: mean anomaly [rad]
        step_tol: tolerance for the Newton-Raphson method

    Returns:
        float: eccentric anomaly [rad]

    Source:
        Curtis, Orbital Mechanics for Engineering Students, eq 3.14
    """
    # Newton-Raphson method
    # Initial guess
    if eccentricity < 0.8:
        eccentric_anomaly = mean_anomaly
    else:
        eccentric_anomaly = np.pi

    # Iteration
    f = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly) - mean_anomaly
    f_prime = 1 - eccentricity * np.cos(eccentric_anomaly)
    while abs(f / f_prime) > step_tol:
        eccentric_anomaly = eccentric_anomaly - f / f_prime
        f = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly) - mean_anomaly
        f_prime = 1 - eccentricity * np.cos(eccentric_anomaly)

    return eccentric_anomaly


def eccentric_anomaly_from_mean_anomaly(
        eccentricity: float,
        mean_anomaly: float,
) -> float:
    """
    Compute the eccentric anomaly from the mean anomaly using one Halley step and one Newton-Raphson step.

    Args:
        eccentricity: eccentricity [-]
        mean_anomaly: mean anomaly [rad]

    Returns:
        float: eccentric anomaly [rad]

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL__kp_M2Eell
    """

    def initial_guess_odell_gooding(ecc: float, reduced_ma: float) -> float:
        k1 = 3 * np.pi + 2
        k2 = np.pi - 1
        k3 = 6 * np.pi - 1
        a = 3 * k2 ** 2 / k1
        b = k3 ** 2 / (6 * k1)
        ecc_a = 0
        if abs(reduced_ma) < 1 / 6:
            ecc_a = reduced_ma + ecc * (np.cbrt(6 * reduced_ma) - reduced_ma)
        elif abs(reduced_ma) >= 1 / 6:
            if reduced_ma < 0:
                w = np.pi + reduced_ma
                ecc_a = reduced_ma + ecc_a * (a * w / (b - w) - np.pi - reduced_ma)
            else:  # reduced_ma >= 0
                w = np.pi - reduced_ma
                ecc_a = reduced_ma + ecc_a * (np.pi - a * w / (b - w) - reduced_ma)
        return ecc_a

    # Reduced mean anomaly
    reduced_mean_anomaly = math.modulo_with_range(mean_anomaly, -np.pi, np.pi)

    eccentric_anomaly = initial_guess_odell_gooding(eccentricity, reduced_mean_anomaly)

    no_cancellation_risk = (1 - eccentricity + eccentric_anomaly ** 2 / 6) >= 0.1

    # Perform 2 iterations
    for _ in range(2):
        # Halley step
        fdd = eccentricity * np.sin(eccentric_anomaly)
        fddd = eccentricity * np.cos(eccentric_anomaly)

        if no_cancellation_risk:
            f = eccentric_anomaly - fdd - reduced_mean_anomaly
            fd = 1 - fddd
        else:
            f = mean_anomaly_from_eccentric_anomaly(eccentricity, eccentric_anomaly) - reduced_mean_anomaly
            fd = 1 - eccentricity + 2 * eccentricity * np.sin(eccentric_anomaly * .5) ** 2

        dee = f * fd / (0.5 * f * fdd - fd ** 2)

        ww = fd + 0.5 * dee * (fdd + dee * fddd / 3)
        fd = fd + dee * (fdd + 0.5 * dee * fddd)
        eccentric_anomaly = eccentric_anomaly - (f - dee * (fd - ww)) / fd

    return eccentric_anomaly + (mean_anomaly - reduced_mean_anomaly)


def true_anomaly_from_eccentric_anomaly(
        eccentricity: float,
        eccentric_anomaly: float
) -> float:
    """
    Compute the true anomaly from the eccentric anomaly.

    Args:
        eccentricity: eccentricity [-]
        eccentric_anomaly: eccentric anomaly [rad]

    Returns:
        float: true anomaly [rad]

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_kp_E2v
    """
    beta = eccentricity / (1 + np.sqrt(1 - eccentricity ** 2))
    return eccentric_anomaly + 2 * np.arctan2(beta * np.sin(eccentric_anomaly), 1 - beta * np.cos(eccentric_anomaly))


def true_anomaly_from_mean_anomaly(
        eccentricity: float,
        mean_anomaly: float,
) -> float:
    """
    Compute the true anomaly from the mean anomaly.

    Args:
        eccentricity: eccentricity [-]
        mean_anomaly: mean anomaly [rad]

    Returns:
        float: true anomaly [rad]

    Source:
        Curtis, Orbital Mechanics for Engineering Students
    """
    eccentric_anomaly = eccentric_anomaly_from_mean_anomaly(eccentricity, mean_anomaly)
    return true_anomaly_from_eccentric_anomaly(eccentricity, eccentric_anomaly)


def check_kep_validity(
        sma: float,
        ecc: float,
):
    if sma <= 0:
        raise ValueError("Semi-major axis must be greater than 0")
    if ecc < 0 or ecc >= 1:
        raise ValueError("Eccentricity must be in the range [0, 1)")


def kep_to_car(
        sma: float,
        ecc: float,
        inc: float,
        aop: float,
        raan: float,
        ma: float
) -> np.ndarray:
    """
    Convert Keplerian to Cartesian elements.

    Args:
        sma (float): semi-major axis [km]
        ecc (float): eccentricity [-]
        inc (float): inclination [rad]
        aop (float): argument of perigee [rad]
        raan (float): right ascension of the ascending node [rad]
        ma (float): mean anomaly [rad]

    Returns:
        np.ndarray: cartesian elements (X, Y, Z, Vx, Vy, Vz) [km, km, km, km/s, km/s, km/s]

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_oe_kep2car
    """

    check_kep_validity(sma, ecc)

    eccentric_anomaly = eccentric_anomaly_from_mean_anomaly(ecc, ma)

    r = sma * (1 - ecc * np.cos(eccentric_anomaly))
    n = np.sqrt(EARTH_GRAV_CONSTANT / sma ** 3)
    eta = np.sqrt(1 - ecc ** 2)

    x = sma * (np.cos(eccentric_anomaly) - ecc)
    y = sma * eta * np.sin(eccentric_anomaly)

    vx = -n * sma ** 2 / r * np.sin(eccentric_anomaly)
    vy = n * sma ** 2 / r * eta * np.cos(eccentric_anomaly)

    c_aop, s_aop = np.cos(aop), np.sin(aop)
    c_raan, s_raan = np.cos(raan), np.sin(raan)
    c_inc, s_inc = np.cos(inc), np.sin(inc)

    first_column = np.array([
        c_aop * c_raan - s_aop * s_raan * c_inc,
        c_aop * s_raan + s_aop * c_raan * c_inc,
        s_aop * s_inc
    ])
    second_column = np.array([
        -s_aop * c_raan - c_aop * s_raan * c_inc,
        -s_aop * s_raan + c_aop * c_raan * c_inc,
        c_aop * s_inc
    ])

    pos = first_column * x + second_column * y
    vel = first_column * vx + second_column * vy

    return np.array([pos[0], pos[1], pos[2], vel[0], vel[1], vel[2]])


def keplerian_period(semi_major_axis: float, mu: float = EARTH_GRAV_CONSTANT) -> float:
    return 2 * np.pi * np.sqrt(semi_major_axis ** 3 / mu)


def get_delta_cartesian_tnw_between_two_keplerian_states(
        sma_ref: float,
        ecc_ref: float,
        inc_ref: float,
        aop_ref: float,
        raan_ref: float,
        ma_ref: float,
        sma_target: float,
        ecc_target: float,
        inc_target: float,
        aop_target: float,
        raan_target: float,
        ma_target: float
) -> np.ndarray:
    """
    Get the cartesian delta between two keplerian states in the TNW frame.

    Args:
        sma_ref (float): semi-major axis of the first orbit [km]
        ecc_ref (float): eccentricity of the first orbit
        inc_ref (float): inclination of the first orbit [rad]
        aop_ref (float): argument of perigee of the first orbit [rad]
        raan_ref (float): right ascension of the ascending node of the first orbit [rad]
        ma_ref (float): mean anomaly of the first orbit [rad]
        sma_target (float): semi-major axis of the second orbit [km]
        ecc_target (float): eccentricity of the second orbit
        inc_target (float): inclination of the second orbit [rad]
        aop_target (float): argument of perigee of the second orbit [rad]
        raan_target (float): right ascension of the ascending node of the second orbit [rad]
        ma_target (float): mean anomaly of the second orbit [rad]

    Returns:
        np.ndarray: cartesian delta between two keplerian states in the TNW frame [km, km, km, km/s, km/s, km/s]

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_op_orbGapLof
    """

    oe_ref = (sma_ref, ecc_ref, inc_ref, aop_ref, raan_ref, ma_ref)
    oe_target = (sma_target, ecc_target, inc_target, aop_target, raan_target, ma_target)

    state_cart_in_ref = kep_to_car(*oe_ref)
    state_cart_in_target = kep_to_car(*oe_target)

    rot_in2tnw = transformation_matrix_in_to_tnw(state_cart_in_ref)

    dstate_in = state_cart_in_target - state_cart_in_ref

    dpos_tnw = np.dot(rot_in2tnw, dstate_in[:3])
    dvel_tnw = np.dot(rot_in2tnw, dstate_in[3:])

    return np.concatenate((dpos_tnw, dvel_tnw))


def compute_delta_v_with_rocket_equation(
        specific_impulse: float,
        initial_mass: float,
        final_mass: float,
) -> float:
    """
    Compute the delta-v required to perform a maneuver with the rocket equation.

    Args:
        specific_impulse (float): specific impulse [s]
        initial_mass (float): initial mass [kg]
        final_mass (float): final mass [kg]

    Returns:
        float: delta-v [m/s]

    Source:
        Curtis, Orbital Mechanics for Engineering Students, eq 6.21
    """
    return specific_impulse * STANDARD_GRAVITY * np.log(initial_mass / final_mass)
