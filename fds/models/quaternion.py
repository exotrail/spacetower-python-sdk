from datetime import datetime
from typing import Self, Sequence, Collection

import numpy as np

from fds.utils import frames
from fds.utils import geometry as geom
from fds.utils import math
from fds.utils.dates import get_datetime
from fds.utils.log import log_and_raise


class Quaternion:
    """
    This class is used to represent a rotation through a quaternion description.
    """
    def __init__(
            self,
            real: float,
            i: float,
            j: float,
            k: float,
            date: datetime | str = None,
            frame_1: str = None,
            frame_2: str = None
    ):
        self._date = get_datetime(date)
        for val in [real, i, j, k]:
            if not isinstance(val, (int, float)):
                msg = f"The quaternion components must be numbers (int or float)"
                log_and_raise(ValueError, msg)

        self._real = real
        self._i, self._j, self._k = i, j, k
        self._frame_1 = frame_1
        self._frame_2 = frame_2

    @property
    def date(self) -> datetime | None:
        """
        The date at which the quaternion is defined (if any).
        """
        return self._date

    @property
    def real(self) -> float:
        """
        Real component of the quaternion.
        """
        return self._real

    @property
    def i(self) -> float:
        """
        Component of the quaternion on the i axis.
        """
        return self._i

    @property
    def j(self) -> float:
        """
        Component of the quaternion on the j axis.
        """
        return self._j

    @property
    def k(self) -> float:
        """
        Component of the quaternion on the k axis.
        """
        return self._k

    @property
    def frame_1(self) -> str | None:
        """
        Name of the frame from which the rotation starts (if any).
        """
        return self._frame_1

    @property
    def frame_2(self) -> str | None:
        """
        Name of the frame to which the rotation ends (if any).
        """
        return self._frame_2

    def __eq__(self, other):
        return np.allclose([self.real, self.i, self.j, self.k], [other.real, other.i, other.j, other.k],
                           rtol=1e-4)

    def __repr__(self):
        r = f"Quaternion({self.real}, {self.i}, {self.j}, {self.k}"
        if self.date is not None:
            r += f", date={self.date}"
        if self.frame_1 is not None and self.frame_2 is not None:
            r += f", {self.frame_1}->{self.frame_2}"
        r += ")"
        return r

    def __str__(self):
        return self.__repr__()

    def __add__(self, other):
        return Quaternion(self.real + other.real, self.i + other.i, self.j + other.j, self.k + other.k)

    def __sub__(self, other):
        return Quaternion(self.real - other.real, self.i - other.i, self.j - other.j, self.k - other.k)

    def __mul__(self, other):
        return Quaternion(
            self.real * other.real - self.i * other.i - self.j * other.j - self.k * other.k,
            self.real * other.i + self.i * other.real + self.j * other.k - self.k * other.j,
            self.real * other.j - self.i * other.k + self.j * other.real + self.k * other.i,
            self.real * other.k + self.i * other.j - self.j * other.i + self.k * other.real
        )

    def imag(self) -> np.ndarray:
        """
        Get the imaginary part of the quaternion.

        Returns:
            an array with the components on the i, j and k axis of the quaternion.
        """
        return np.array([self.i, self.j, self.k])

    def conjugate(self) -> Self:
        """
        Computes the conjugate of the quaternion.

        Returns:
            a new Quaternion instance representing the conjugate of this quaternion.
        """
        return Quaternion(self.real, -self.i, -self.j, -self.k)

    def norm(self) -> float:
        """
        Compute the norm of the quaternion.
        """
        return np.sqrt(self.real ** 2 + self.i ** 2 + self.j ** 2 + self.k ** 2)

    def unit(self) -> Self:
        """
        Normalizes the quaternion.
        """
        norm = self.norm()
        return Quaternion(self.real / norm, self.i / norm, self.j / norm, self.k / norm)

    def to_rotation_matrix(self) -> np.ndarray:
        """
        Convert the quaternion to a rotation matrix R that rotates a vector v to v' = Rv. The result of this operation
        is a vector v expressed in the new frame.

        Returns:
            np.ndarray: rotation matrix 3x3

        Source:
            Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_rot_quat2matrix
        """
        q = self.unit()
        q4, q1, q2, q3 = q.real, q.i, q.j, q.k

        rot_mat = np.array([
            [q1 ** 2 - q2 ** 2 - q3 ** 2 + q4 ** 2, 2 * (q1 * q2 - q3 * q4), 2 * (q1 * q3 + q2 * q4)],
            [2 * (q1 * q2 + q3 * q4), (-q1 ** 2 + q2 ** 2 - q3 ** 2 + q4 ** 2), 2 * (q2 * q3 - q1 * q4)],
            [2 * (q1 * q3 - q2 * q4), 2 * (q2 * q3 + q1 * q4), (-q1 ** 2 - q2 ** 2 + q3 ** 2 + q4 ** 2)]
        ]).T  # Transpose to have the correct rotation matrix

        # Round to 10 decimal places to avoid floating point errors
        rot_mat = np.round(rot_mat, 10)

        return rot_mat

    def to_angle_axis(self) -> tuple[float, np.ndarray]:
        """
        Convert a quaternion to angle-axis representation.

        Returns:
            angle: float
                Angle of rotation in radians.
            axis: np.ndarray
                Axis of rotation as a NumPy array.
        """
        angle = 2 * np.arccos(self.real)
        axis = self.imag() / np.sqrt(1 - self.real ** 2)
        return angle, axis

    @classmethod
    def from_angle_axis(
            cls,
            angle: float,
            axis: Sequence[float] | np.ndarray,
            date: datetime | str = None,
            frame_1: str = None,
            frame_2: str = None
    ) -> Self:
        """
        Convert an angle and an axis to a quaternion.

        Args:
            angle (float): angle [rad]
            axis (np.ndarray | Sequence[float]): axis [3x1]
            date (datetime | str): date of the quaternion (default: None)
            frame_1 (str): name of the starting frame (default: None)
            frame_2 (str): name of the ending frame (default: None)

        Returns:
            quaternion (Quaternion): quaternion

        Source:
            Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_rot_axAng2quat
        """
        axis = geom.convert_to_numpy_array_and_check_shape(axis, (3,))
        q_real = np.cos(angle / 2)
        q_i, q_j, q_k = np.sin(angle / 2) * axis / np.linalg.norm(axis)
        return cls(
            real=q_real,
            i=q_i,
            j=q_j,
            k=q_k,
            date=date,
            frame_1=frame_1,
            frame_2=frame_2
        )

    @classmethod
    def from_rotation_matrix(
            cls,
            rot_mat: np.ndarray,
            date: datetime | str = None,
            frame_1: str = None,
            frame_2: str = None
    ) -> Self:
        """
            Convert a rotation matrix to a quaternion.

            Args:
                rot_mat: rotation matrix 3x3
                date (datetime | str): date of the quaternion (default: None)
                frame_1 (str): name of the starting frame (default: None)
                frame_2 (str): name of the ending frame (default: None)

            Returns:
                quaternion (Quaternion): quaternion

            Source:
                Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_rot_matrix2quat
            """

        if rot_mat.shape != (3, 3):
            msg = "The rotation matrix must be 3x3"
            log_and_raise(ValueError, msg)

        a11, a12, a13 = rot_mat[0, :]
        a21, a22, a23 = rot_mat[1, :]
        a31, a32, a33 = rot_mat[2, :]
        ccc = [a11 - a22 - a33, a22 - a33 - a11, a33 - a11 - a22, a11 + a22 + a33]

        v = np.real(np.sqrt(1 + np.array(ccc)))

        j_max = np.argmax(v)

        v_max = v[j_max]

        if j_max == 0:
            q1 = v_max * 0.5
            q2 = (a12 + a21) / (2 * v_max)
            q3 = (a13 + a31) / (2 * v_max)
            q4 = (a23 - a32) / (2 * v_max)
        elif j_max == 1:
            q1 = (a12 + a21) / (2 * v_max)
            q2 = v_max * 0.5
            q3 = (a23 + a32) / (2 * v_max)
            q4 = (a31 - a13) / (2 * v_max)
        elif j_max == 2:
            q1 = (a13 + a31) / (2 * v_max)
            q2 = (a23 + a32) / (2 * v_max)
            q3 = v_max * 0.5
            q4 = (a12 - a21) / (2 * v_max)
        elif j_max == 3:
            q1 = (a23 - a32) / (2 * v_max)
            q2 = (a31 - a13) / (2 * v_max)
            q3 = (a12 - a21) / (2 * v_max)
            q4 = v_max * 0.5
        elif v_max == 0:
            q4, q1, q2, q3 = 1, 0, 0, 0
        else:
            log_and_raise(ValueError, "Error in quaternion computation")

        return cls(
            real=q4,
            i=q1,
            j=q2,
            k=q3,
            date=date,
            frame_1=frame_1,
            frame_2=frame_2
        )

    def rotate(self, vector: np.ndarray | Sequence[float]) -> np.ndarray:
        """
        Rotate a vector using the quaternion with the formula v' = qvq*. The result of this operation is the image of
        v in the starting frame. To obtain the vector in the new frame, use the conjugate of the quaternion.

        Args:
            vector (np.ndarray | Sequence[float]): vector to rotate [3x1]

        Returns:
            np.ndarray: rotated vector in the starting frame

        Source:
            Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_rot_rotVect
        """
        vector = geom.convert_to_numpy_array_and_check_shape(vector, (3,))

        q = self.unit()
        v = Quaternion(real=0, i=float(vector[0]), j=float(vector[1]), k=float(vector[2]))
        rotated_vector = (q * v * q.conjugate()).imag()
        return np.round(rotated_vector, 10)

    def to_angles(
            self,
            rot_order: str = "XYZ"
    ) -> tuple[np.ndarray, np.ndarray]:
        """
            Convert the quaternion to angles set in the order given by rot_order:
            - 6 Cardan rotations (for which all axes are different): XYZ, XZY, YXZ, YZX, ZXY and ZYX
            - 6 Euler rotations (for which 2 axes are the same): XYX, XZX, YXY, YZY, ZXZ and ZYZ

            Returns:
                np.ndarray: 3 Angles [rad]
                np.ndarray: 3 Alternative angles [rad]

            Source:
                Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_rot_quat2angles
        """

        def get_cardan_angles():
            def alternative_solution(ang: np.ndarray):
                sgn = np.ones(3)
                neg_angles = ang < 0
                sgn[neg_angles] = -1
                return np.array([
                    -sgn[0] * (np.pi - abs(ang[0])),
                    sgn[1] * (np.pi - abs(ang[1])),
                    -sgn[2] * (np.pi - abs(ang[2]))
                ])

            n1 = int(rot_order[0])
            n2 = int(rot_order[1])
            n3 = int(rot_order[2])
            sign = np.sign(math.modulo_with_range(n2 - n1, -1.5, 1.5))

            x_3_image = self.rotate(identiy[:, n3])
            cond_ok = np.abs(x_3_image[n1]) < v_max

            if cond_ok:
                x_1_rot = self.conjugate().rotate(identiy[:, n1])
                theta_1 = np.arctan2(-sign * x_3_image[n2], x_3_image[n3])
                theta_2 = np.arcsin(sign * x_3_image[n1])
                theta_3 = np.arctan2(-sign * x_1_rot[n2], x_1_rot[n1])
            else:
                x_2_image = self.rotate(identiy[:, n2])
                theta_3 = 0
                theta_2 = np.arcsin(sign * x_3_image[n1])
                theta_1 = np.arctan2(sign * x_2_image[n3], x_2_image[n2])

            angles = np.array([theta_1, theta_2, theta_3])
            alternative = alternative_solution(angles)
            return angles, alternative

        def get_euler_angles():
            def alternative_solution(ang: np.ndarray):
                sgn = np.ones(3)
                neg_angles = ang < 0
                sgn[neg_angles] = -1
                return np.array([
                    -sgn[0] * (np.pi - abs(ang[0])),
                    -ang[1],
                    -sgn[2] * (np.pi - abs(ang[2]))
                ])

            n1 = int(rot_order[0])
            n2 = int(rot_order[1])
            n3 = int(math.pmodulo(n2 + (n2 - n1) - 1, 3) + 1)
            sign = np.sign(math.modulo_with_range(n2 - n1, -1.5, 1.5))

            x_1_image = self.rotate(identiy[:, n1])

            cond_ok = np.abs(x_1_image[n1]) < v_max

            if cond_ok:
                x_1_rot = self.conjugate().rotate(identiy[:, n1])
                theta_1 = np.arctan2(x_1_image[n2], -sign * x_1_image[n3])
                theta_2 = np.arccos(x_1_image[n1])
                theta_3 = np.arctan2(x_1_rot[n2], sign * x_1_rot[n3])
            else:
                x_2_image = self.rotate(identiy[:, n2])
                theta_3 = 0
                theta_2 = np.arccos(x_1_image[n1])
                theta_1 = np.arctan2(sign * x_2_image[n3], x_2_image[n2])

            angles = np.array([theta_1, theta_2, theta_3])
            alternative = alternative_solution(angles)
            return angles, alternative

        rot_order = frames.get_rot_order_axes(rot_order)

        v_max = 1 - 1E-10  # Avoid floating point errors
        identiy = np.eye(3)

        # If rot_oder elements are unique, the rotation is a Cardan rotation
        if len(set(rot_order)) == 3:
            return get_cardan_angles()

        if rot_order[0] == rot_order[2] and rot_order[1] != rot_order[0]:  # Euler rotation
            return get_euler_angles()

        log_and_raise(ValueError, "The rotation order is not valid")

    @classmethod
    def from_angles(
            cls,
            angles: np.ndarray | Sequence[float],
            rot_order: str = "XYZ",
            date: datetime | str = None,
            frame_1: str = None,
            frame_2: str = None
    ) -> Self:
        """
            Convert angles to a quaternion.

            Args:
                angles (np.ndarray | Sequence[float]): angles [rad]
                rot_order (str): rotation order
                date (datetime | str): date of the quaternion (default: None)
                frame_1 (str): name of the starting frame (default: None)
                frame_2 (str): name of the ending frame (default: None)

            Returns:
                quaternion (Quaternion): quaternion

            Source:
                Celestlab (v 3.4.2), https://atoms.scilab.org/toolboxes/celestlab, CL_rot_angles2quat
        """
        angles = geom.convert_to_numpy_array_and_check_shape(angles, (3,))
        rot_order = frames.get_rot_order_axes(rot_order)

        identity = np.eye(3)

        quaternion = Quaternion.from_angle_axis(float(angles[0]), identity[:, rot_order[0]], date, frame_1, frame_2)
        for i in range(1, 3):
            quaternion = quaternion * Quaternion.from_angle_axis(float(angles[i]), identity[:, rot_order[i]])

        return quaternion

    @classmethod
    def from_collection(cls, data: Collection[float], date: datetime | str = None,
                        frame_1: str = None, frame_2: str = None) -> Self:
        """
        Create a Quaternion object from an iterable with 4 elements.

        Args:
            data (list[float]): list with 4 elements (real, i, j, k)
            date (datetime | str): date of the quaternion (default: None)
            frame_1 (str): name of the starting frame (default: None)
            frame_2 (str): name of the ending frame (default: None)

        Returns:
            quaternion (Quaternion): quaternion
        """
        data = list(data)
        if len(data) != 4:
            msg = f"Invalid input {data} for Quaternion. Must be an iterable with 4 elements."
            log_and_raise(ValueError, msg)
        return cls(*data, date=date, frame_1=frame_1, frame_2=frame_2)

    @classmethod
    def from_collections(cls, data: Collection[Collection[float]], dates: Collection[datetime | str] = None,
                         frame_1: str = None, frame_2: str = None) \
            -> list[Self]:
        """
        Create a list of Quaternion objects from a list of iterables with 4 elements.

        Args:
            data (list[list[float]]): list of list with 4 elements (real, i, j, k)
            dates (list[list | str]): list of dates of the quaternions (default: None)
            frame_1 (str): name of the starting frame (default: None)
            frame_2 (str): name of the ending frame (default: None)

        Returns:
            list[Quaternion]: list of quaternions
        """
        no_dates = dates is None or len(dates) == 0
        if no_dates:
            dates = [None] * len(data)
        else:
            dates = list(dates)
        data = list(data)
        # check if same length
        if len(data) != len(dates):
            msg = f"Invalid input for Quaternion. 'data' and 'dates' must have the same length."
            log_and_raise(ValueError, msg)
        quaternions = [cls.from_collection(d, date, frame_1, frame_2) for d, date in zip(data, dates)]

        if not no_dates:
            return sorted(quaternions, key=lambda x: x.date)
        return quaternions


def get_univoque_list_of_dated_quaternions(
        quaternions: Collection['Quaternion'],
        ignore_different_quaternions_at_same_date: bool = False
) -> list['Quaternion']:
    """
    This method takes a list of dated quaternions and returns a list of dated quaternions without duplicates. If two
    quaternions have the same date and they are the same, only one is kept. If two quaternions have the same date but
    they are different, an exception is raised if ignore_different_quaternions_at_same_date is False, otherwise no
    quaternion is kept. The list is then sorted by date.

    Args:
        quaternions (list[Quaternion]): list of dated quaternions
        ignore_different_quaternions_at_same_date (bool): if False, an exception is raised if two quaternions have the
            same date but they are different (default: False)
    """
    if not all(q.date is not None for q in quaternions):
        msg = "All quaternions must have a date to delete duplicates."
        log_and_raise(ValueError, msg)

    date_map = {}
    for q in quaternions:
        date_map.setdefault(q.date, []).append(q)
    quaternions = []
    for date, qs in date_map.items():
        if len(qs) == 1 or (len(qs) == 2 and qs[0] == qs[1]):
            quaternions.append(qs[0])
        elif not ignore_different_quaternions_at_same_date:
            msg = f"Two different quaternions at the same date {date}"
            log_and_raise(ValueError, msg)
    return sorted(quaternions, key=lambda _q: _q.date)
