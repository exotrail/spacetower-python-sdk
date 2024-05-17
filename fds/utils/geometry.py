from typing import Sequence

import numpy as np

from fds.utils.log import log_and_raise


def unit_vector(v: np.ndarray) -> np.ndarray:
    """
    Return the unit vector of the input vector.

    Args:
        v (np.ndarray): input vector

    Returns:
        np.ndarray: unit vector
    """
    unit_v = v / np.linalg.norm(v)
    return unit_v


def check_vector_shape(v: np.ndarray, shape: tuple):
    """
    Check if the input vector has the correct shape.

    Args:
        v (np.ndarray): input vector
        shape (tuple): expected shape

    Raises:
        ValueError: if the input vector has a different length than expected
    """
    if v.shape != shape:
        msg = f"Input vector has shape {v.shape} while {shape} was expected."
        log_and_raise(ValueError, msg)


def convert_to_numpy_array_and_check_shape(v: Sequence, shape: tuple) -> np.ndarray:
    """
    Convert a list to a numpy array and check if the length is correct.

    Args:
        v (list): input list
        shape (tuple): expected shape

    Returns:
        np.ndarray: input list as numpy array

    Raises:
        ValueError: if the input vector has a different length than expected
    """
    v = np.array(v)
    check_vector_shape(v, tuple(shape))
    return v


def angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Computes the angle in radians between two vectors v1 and v2.

    Parameters:
        v1 (np.ndarray): A NumPy array representing the first vector.
        v2 (np.ndarray): A NumPy array representing the second vector.

    Returns:
        float: The angle in radians between the two vectors.

    Raises:
        ValueError: If v1 or v2 are zero vectors or if their dimensions don't match.
    """
    return np.arccos(np.dot(unit_vector(v1), unit_vector(v2)))
