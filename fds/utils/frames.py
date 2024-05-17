from typing import Sequence

import numpy as np

from fds.utils.enum import EnumFromInput
from fds.utils.geometry import convert_to_numpy_array_and_check_shape, unit_vector

_frame_alias_map = {
    "CIRF": "ECI",
    "ITRF": "ECF",
    "J2000": "EME2000",
    # Add more mappings as needed
}


class Frame(EnumFromInput):
    CIRF = "CIRF"
    ECI = "ECI"
    TEME = "TEME"
    J2000 = "J2000"
    EME2000 = "EME2000"
    GCRF = "GCRF"

    ITRF = "ITRF"
    GTOD = "GTOD"
    ECF = "ECF"

    TNW = "TNW"
    QSW = "QSW"

    @property
    def value_or_alias(self) -> str:
        return _frame_alias_map.get(self.value, self.value)


def transformation_matrix_in_to_tnw(
        state_cart: np.ndarray | Sequence[float]
) -> np.ndarray[float]:
    """
    Compute the transformation matrix from inertial to TNW frame.

    Args:
        state_cart (np.ndarray): state in cartesian coordinates (X, Y, Z, Vx, Vy, Vz) [km, km, km, km/s, km/s, km/s]

    Returns:
        np.ndarray: transformation matrix from inertial to TNW frame

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_fr_tnwMat

    """
    state_cart = convert_to_numpy_array_and_check_shape(state_cart, (6,))

    if state_cart is None:
        raise ValueError("The state must be a 6-element array")

    p = state_cart[:3]
    v = state_cart[3:6]

    u_t = unit_vector(v)
    u_w = unit_vector(np.cross(p, v))
    u_n = np.cross(u_w, u_t)

    return np.array([u_t, u_n, u_w])


def transformation_matrix_in_to_lvlh(
        state_cart: np.ndarray | Sequence[float]
) -> np.ndarray[float]:
    """
    Compute the transformation matrix from inertial to LVLH frame.

    Args:
        state_cart (np.ndarray): state in cartesian coordinates (X, Y, Z, Vx, Vy, Vz) [km, km, km, km/s, km/s, km/s]

    Returns:
        np.ndarray: transformation matrix from inertial to LVLH frame

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_fr_lvlhMat

    """
    state_cart = convert_to_numpy_array_and_check_shape(state_cart, (6,))

    if state_cart is None:
        raise ValueError("The state must be a 6-element array")

    p = state_cart[:3]
    v = state_cart[3:6]

    u_r = -unit_vector(p)
    u_h = -unit_vector(np.cross(p, v))
    u_l = np.cross(u_h, u_r)

    return np.array([u_l, u_h, u_r])


def get_rot_order_axes(r: str) -> np.ndarray:
    """
    Get the rotation order axes.

    Args:
        r (str): rotation order

    Returns:
        np.ndarray: rotation order axes

    """
    if len(r) != 3:
        raise ValueError("The rotation order must contain 3 letters")
    axes = {
        "X": 0,
        "Y": 1,
        "Z": 2
    }
    return np.array([axes[letter] for letter in r.upper()])
