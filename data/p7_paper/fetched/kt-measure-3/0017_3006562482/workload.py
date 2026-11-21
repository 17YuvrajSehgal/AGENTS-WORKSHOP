import atexit, contextlib, hashlib, io, os, sys
import bpy


def _skip_bpy_teardown():
    # bpy-as-module segfaults during interpreter teardown after an add-on is
    # registered; exit cleanly once all output (and coverage data) is written.
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(0)


atexit.register(_skip_bpy_teardown)
from mathutils import Vector
import io_scene_vrm
from io_scene_vrm.common import ops, version
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup, get_armature_extension)

import addon_utils
addon_utils.enable("io_scene_vrm", default_set=True)
src = io_scene_vrm.__file__.rsplit("/src/io_scene_vrm", 1)[0]
sys.path.insert(0, src + "/tests")
import blender_test_spring_bone as t

ctx = bpy.context
h = hashlib.sha256()

# 1) repository tests for VRM1 spring bones
with contextlib.redirect_stdout(io.StringIO()):
    for f in t.FUNCTIONS:
        f(ctx)
        h.update(f.__name__.encode())

# 2) scaled scene: many spring chains on one armature
N_CHAINS, CHAIN_LEN, STEPS = 16, 10, 400
with contextlib.redirect_stdout(io.StringIO()):
    t.clean_scene(ctx)
bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
arm = ctx.object
ext = get_armature_extension(arm.data)
ext.addon_version = version.get_addon_version()
ext.spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1
ext.spring_bone1.enable_animation = True
bpy.ops.object.mode_set(mode="EDIT")
root = arm.data.edit_bones.new("root")
root.head = Vector((0, 0, 0)); root.tail = Vector((0, 0, 1))
for c in range(N_CHAINS):
    parent = root
    x = c * 0.5
    for j in range(CHAIN_LEN):
        b = arm.data.edit_bones.new(f"c{c}_j{j}")
        b.parent = parent
        b.head = Vector((x, j * 0.3, 1)); b.tail = Vector((x, (j + 1) * 0.3, 1))
        parent = b
bpy.ops.object.mode_set(mode="OBJECT")
for c in range(N_CHAINS):
    assert ops.vrm.add_spring_bone1_spring(armature_object_name=arm.name) == {"FINISHED"}
    for j in range(CHAIN_LEN):
        assert ops.vrm.add_spring_bone1_spring_joint(
            armature_object_name=arm.name, spring_index=c) == {"FINISHED"}
    joints = ext.spring_bone1.springs[c].joints
    for j in range(CHAIN_LEN):
        joints[j].node.bone_name = f"c{c}_j{j}"
        joints[j].gravity_power = 0.5 + 0.05 * c
        joints[j].drag_force = 0.3
        joints[j].stiffness = 0.2 + 0.02 * j
ctx.view_layer.update()
for s in range(STEPS):
    arm.location = (0, 0, 0.01 * (s % 7))
    ctx.view_layer.update()
    ops.vrm.update_spring_bone1_animation(delta_time=1 / 30)
    ctx.view_layer.update()
    for pb in arm.pose.bones:
        h.update(("%s %.4f %.4f %.4f\n" % (pb.name, *pb.head)).encode())
print(h.hexdigest())
