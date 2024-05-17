import numpy as np


def pmodulo(x: float, modulo: float) -> float:
    """
    Modulo with positive result

    Source:
        SciLab (v 2023.1.0), https://atoms.scilab.org pmodulo
    """

    return x - abs(modulo) * np.floor(x / abs(modulo))


def modulo_with_range(x: float, x_min: float, x_max: float, x_min_atol: float = 1E-10,
                      x_max_atol: float = 1E-10) -> float:
    """
    Modulo with result in range [x_min, x_max)

    Args:
        x: The value to be modulated
        x_min: The minimum value of the range
        x_max: The maximum value of the range
        x_min_atol: The tolerance for the minimum value (to avoid floating point errors)
        x_max_atol: The tolerance for the maximum value (to avoid floating point errors)

    Source:
        Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_rMod
    """
    delta = x_max - x_min
    x = x_min if abs(x - x_min) < x_min_atol else x
    nrev = np.floor((x - x_min) / delta)
    res = x - nrev * delta
    return x_min if abs(res - x_max) < x_max_atol else res
