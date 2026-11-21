import hashlib, os
import numpy as np
from ikpy.chain import Chain

URDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base/src/resources/poppy_torso/poppy_torso.URDF")
arm = Chain.from_urdf_file(
    URDF,
    base_elements=["base", "abs_z", "spine", "bust_y", "bust_motors", "bust_x", "chest", "r_shoulder_y"],
    last_link_vector=[0, 0.18, 0],
    active_links_mask=[False, False, False, False, True, True, True, True, True],
)
rng = np.random.RandomState(0)
h = hashlib.sha256()
n = len(arm.links)
for i in range(60):
    target = np.array([0.1, -0.2, 0.1]) + rng.uniform(-0.05, 0.05, 3)
    ik = arm.inverse_kinematics(target_position=target, initial_position=[0] * n)
    h.update(np.round(ik, 6).tobytes())
for i in range(3000):
    joints = rng.uniform(-1, 1, n)
    fk = arm.forward_kinematics(joints)
    full = arm.forward_kinematics(joints, full_kinematics=True)
    h.update(np.round(fk, 8).tobytes()); h.update(np.round(full[-1], 8).tobytes())
print(h.hexdigest())
