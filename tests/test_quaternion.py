import unittest

import numpy as np

from fds.models.quaternion import Quaternion


class TestQuaternion(unittest.TestCase):

    def setUp(self):
        self.rot_mat_in_to_tnw_test = np.array([
            [-1.0, 5.3028761936245346E-17, 3.0616169978683824E-17],
            [-6.123233995736767E-17, -0.8660254037844388, -0.5],
            [-4.009074440407614E-33, -0.5, 0.8660254037844388]
        ])
        self.q_test = Quaternion(2.957E-17, 7.924E-18, -0.2588190, 0.9659258)

    def test_quaternion_conjugate(self):
        q = Quaternion(1, 2, 3, 4)
        q_conj = q.conjugate()
        self.assertTrue(q_conj == Quaternion(1, -2, -3, -4))

    def test_quaternion_norm(self):
        q = Quaternion(1, 2, 3, 4)
        norm = np.sqrt(1 + 4 + 9 + 16)
        self.assertTrue(np.isclose(q.norm(), norm))

    def test_quaternion_unit(self):
        q = Quaternion(1, 2, 3, 4)
        q_unit = q.unit()
        self.assertTrue(np.isclose(q_unit.norm(), 1))

    def test_quaternion_mul(self):
        q1 = Quaternion(1, 2, 3, 4)
        q2 = Quaternion(5, 6, 7, 8)
        q = q1 * q2
        self.assertTrue(q == Quaternion(-60, 12, 30, 24))

    def test_quaternion_repr(self):
        q = Quaternion(1, 2, 3, 4)
        self.assertTrue(repr(q) == "Quaternion(1, 2, 3, 4)")

    def test_quaternion_str(self):
        q = Quaternion(1, 2, 3, 4)
        self.assertTrue(str(q) == "Quaternion(1, 2, 3, 4)")

    def test_quaternion_add(self):
        q1 = Quaternion(1, 2, 3, 4)
        q2 = Quaternion(5, 6, 7, 8)
        q = q1 + q2
        self.assertTrue(q == Quaternion(6, 8, 10, 12))

    def test_quaternion_sub(self):
        q1 = Quaternion(1, 2, 3, 4)
        q2 = Quaternion(5, 6, 7, 8)
        q = q1 - q2
        self.assertTrue(q == Quaternion(-4, -4, -4, -4))

    def test_quaternion_eq(self):
        q1 = Quaternion(1, 2, 3, 4)
        q2 = Quaternion(1, 2, 3, 4)
        self.assertTrue(q1 == q2)

    def test_quaternion_ne(self):
        q1 = Quaternion(1, 2, 3, 4)
        q2 = Quaternion(5, 6, 7, 8)
        self.assertTrue(q1 != q2)

    def test_quaternion_real(self):
        q = Quaternion(1, 2, 3, 4)
        self.assertTrue(q.real == 1)

    def test_quaternion_imag(self):
        q = Quaternion(1, 2, 3, 4)
        self.assertTrue(np.allclose(q.imag(), np.array([2, 3, 4]), rtol=1e-4))

    def test_quaternion_from_angle_axis(self):
        alpha = np.pi / 2
        q = Quaternion.from_angle_axis(alpha, np.array([1, 0, 0]))
        self.assertTrue(q == Quaternion(np.cos(alpha / 2), np.sin(alpha / 2), 0, 0))

        q = Quaternion.from_angle_axis(np.pi / 4, np.array([10, 45, 77]))
        q_celestlab = Quaternion(0.9238795, 0.0426416, 0.1918874, 0.3283406)
        self.assertTrue(q == q_celestlab)

    def test_rot_matrix_to_quaternion(self):
        q = Quaternion.from_rotation_matrix(self.rot_mat_in_to_tnw_test)
        self.assertTrue(q == self.q_test)

    def test_quaternion_to_rotation_matrix(self):
        rot_mat = self.q_test.to_rotation_matrix()
        self.assertTrue(np.allclose(rot_mat, self.rot_mat_in_to_tnw_test, rtol=1e-4))

    def test_rot_matrix_to_quaternion_elementary(self):
        q = Quaternion.from_rotation_matrix(np.eye(3))
        self.assertTrue(q == Quaternion(1, 0, 0, 0))

        theta = np.random.rand() * 2 * np.pi
        rot_x = np.array([
            [1, 0, 0],
            [0, np.cos(theta), -np.sin(theta)],
            [0, np.sin(theta), np.cos(theta)]
        ]).T
        q_rot_x = Quaternion.from_rotation_matrix(rot_x)
        mat_rot_x = q_rot_x.to_rotation_matrix()
        self.assertTrue(np.allclose(rot_x, mat_rot_x, rtol=1e-4))

        rot_y = np.array([
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)]
        ]).T

        q_rot_y = Quaternion.from_rotation_matrix(rot_y)
        mat_rot_y = q_rot_y.to_rotation_matrix()
        self.assertTrue(np.allclose(rot_y, mat_rot_y, rtol=1e-4))

        rot_z = np.array([
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1]
        ]).T
        q_rot_z = Quaternion.from_rotation_matrix(rot_z)
        mat_rot_z = q_rot_z.to_rotation_matrix()
        self.assertTrue(np.allclose(rot_z, mat_rot_z, rtol=1e-4))

    def test_back_and_forth(self):
        m_x = np.array([
            [1, 0, 0],
            [0, 0, -1],
            [0, 1, 0]
        ]).T
        q_from_m = Quaternion.from_rotation_matrix(m_x)
        m_x_from_q_m = q_from_m.to_rotation_matrix()
        q_from_ax = Quaternion.from_angle_axis(np.pi / 2, np.array([1, 0, 0]))
        m_x_from_q_ax = q_from_ax.to_rotation_matrix()
        self.assertTrue(np.allclose(m_x, m_x_from_q_m, rtol=1e-4))
        self.assertTrue(np.allclose(m_x, m_x_from_q_ax, rtol=1e-4))
        self.assertTrue(q_from_m == q_from_ax)

    def test_vector_rotation(self):
        v = np.array([1, 0, 0])
        q = Quaternion.from_angle_axis(np.pi / 2, np.array([0, 0, 1]))
        v_image = q.rotate(v)
        self.assertTrue(np.allclose(v_image, np.array([0, 1, 0]), rtol=1e-4))
        q_conj = q.conjugate()
        v_rotated = q_conj.rotate(v)
        self.assertTrue(np.allclose(v_rotated, np.array([0, -1, 0]), rtol=1e-4))

    def test_quaternion_to_euler_angles(self):
        pi2 = np.pi / 2
        q = Quaternion.from_angle_axis(pi2, np.array([1, 0, 0]))
        angles, angles_alt = q.to_angles("zxz")

        angles_test = np.array([0, pi2, 0])
        angles_alt_test = np.array([-np.pi, -pi2, -np.pi])

        self.assertTrue(np.allclose(angles, angles_test, rtol=1e-4))
        self.assertTrue(np.allclose(angles_alt, angles_alt_test, rtol=1e-4))

    def test_quaternion_to_euler_angles_2(self):
        pi2 = np.pi / 2
        q = Quaternion.from_angle_axis(pi2, np.array([0, 1, 0]))
        angles, angles_alt = q.to_angles("zxz")

        angles_test = np.array([pi2, pi2, -pi2])
        angles_alt_test = np.array([-pi2, -pi2, pi2])

        self.assertTrue(np.allclose(angles, angles_test, rtol=1e-4))
        self.assertTrue(np.allclose(angles_alt, angles_alt_test, rtol=1e-4))

    def test_quaternion_to_euler_angles_3(self):
        pi2 = np.pi / 2
        q = Quaternion.from_angle_axis(pi2, np.array([0, 0, 1]))
        angles, angles_alt = q.to_angles("zxz")

        angles_test = np.array([pi2, 0, 0])
        angles_alt_test = np.array([-pi2, 0, -np.pi])

        self.assertTrue(np.allclose(angles, angles_test, rtol=1e-4))
        self.assertTrue(np.allclose(angles_alt, angles_alt_test, rtol=1e-4))

    def test_quaternion_to_cardan_angles_xyz(self):
        q = Quaternion.from_angle_axis(np.pi / 4, np.array([10, 45, 77]))
        angles, angles_alt = q.to_angles("xyz")
        angles_test = np.array([-0.051127215025036025, 0.39256933951356465, 0.6931113779446509])
        angles_alt_test = np.array([3.090465438564757, 2.7490233140762284, -2.4484812756451424])
        self.assertTrue(np.allclose(angles, angles_test, rtol=1e-4))
        self.assertTrue(np.allclose(angles_alt, angles_alt_test, rtol=1e-4))

    def test_quaternion_to_angles_back_and_forth(self):
        q = Quaternion.from_angle_axis(np.pi / 4, np.array([10, 45, 77]))
        angles, angles_alt = q.to_angles("xyz")
        q_from_angles = Quaternion.from_angles(angles, "xyz")
        q_from_angles_alt = Quaternion.from_angles(angles_alt, "xyz")
        self.assertTrue(q == q_from_angles)
        self.assertTrue(q == q_from_angles_alt)

    def test_quaternion_to_angle_axis(self):
        angle, axis = self.q_test.to_angle_axis()
        q = Quaternion.from_angle_axis(angle, axis)
        self.assertTrue(q == self.q_test)

        angle_test = np.deg2rad(90)
        axis_test = [1, 0, 0]
        q = Quaternion.from_angle_axis(angle_test, axis_test)

        angle_q, axis_q = q.to_angle_axis()
        self.assertTrue(np.isclose(angle_q, angle_test))
        self.assertTrue(np.allclose(axis_q, axis_test))
