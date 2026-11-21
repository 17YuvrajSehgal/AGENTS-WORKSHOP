import hashlib, math, os, sys

import bpy
import io_scene_vrm

io_scene_vrm.register()

from mathutils import Vector
from io_scene_vrm.common import ops, version
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)

# repo tests
sys.path.insert(0, os.path.join(os.path.dirname(io_scene_vrm.__file__), "..", "..", "tests"))
import blender_test_spring_bone as t  # noqa: E402

ctx = bpy.context
digest = hashlib.sha256()

for f in t.FUNCTIONS:
    f(ctx)
    digest.update(f.__name__.encode())


def build(index, n_joints):
    bpy.ops.object.add(type="ARMATURE", location=(index * 3.0, 0, 0),
                       rotation=(0.1 * index, 0, 0.3 * index))
    arm = ctx.object
    ext = get_armature_extension(arm.data)
    ext.addon_version = version.get_addon_version()
    ext.spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1
    ext.spring_bone1.enable_animation = True
    bpy.ops.object.mode_set(mode="EDIT")
    root = arm.data.edit_bones.new("root")
    root.head = Vector((0, 0, 0))
    root.tail = Vector((0, 0.5, 0))
    parent = root
    for i in range(n_joints):
        b = arm.data.edit_bones.new(f"j{i}")
        b.parent = parent
        b.head = Vector((0, 0.5 + 0.5 * i, 0.05 * (i % 3)))
        b.tail = Vector((0, 1.0 + 0.5 * i, 0.05 * ((i + 1) % 3)))
        b.roll = 0.2 * i
        parent = b
    bpy.ops.object.mode_set(mode="OBJECT")

    name = arm.name
    sb = ext.spring_bone1
    # colliders
    for k in range(3):
        assert ops.vrm.add_spring_bone1_collider(armature_object_name=name) == {"FINISHED"}
        c = sb.colliders[-1]
        c.node.bone_name = "root"
        c.shape.sphere.offset = (0.0, 1.5 + 1.5 * k, -1.2)
        c.shape.sphere.radius = 0.6
    assert ops.vrm.add_spring_bone1_collider_group(armature_object_name=name) == {"FINISHED"}
    for k in range(3):
        assert ops.vrm.add_spring_bone1_collider_group_collider(
            armature_object_name=name, collider_group_index=0) == {"FINISHED"}
        sb.collider_groups[0].colliders[k].collider_name = sb.colliders[k].name
    assert ops.vrm.add_spring_bone1_spring(armature_object_name=name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_collider_group(
        armature_object_name=name, spring_index=0) == {"FINISHED"}
    sb.springs[0].collider_groups[0].collider_group_name = sb.collider_groups[0].name
    for i in range(n_joints):
        assert ops.vrm.add_spring_bone1_spring_joint(
            armature_object_name=name, spring_index=0) == {"FINISHED"}
        j = sb.springs[0].joints[-1]
        j.node.bone_name = f"j{i}"
        j.gravity_power = 1.0
        j.drag_force = 0.3
        j.stiffness = 0.5 + 0.1 * (i % 4)
        j.hit_radius = 0.1
    return arm


t.clean_scene(ctx)
arms = [build(i, 12) for i in range(4)]
ctx.view_layer.update()

for step in range(1000):
    for a_i, arm in enumerate(arms):
        arm.location = (a_i * 3.0 + 0.5 * math.sin(step * 0.1), 0.3 * math.cos(step * 0.07), 0)
    ctx.view_layer.update()
    ops.vrm.update_spring_bone1_animation(delta_time=1.0 / 30.0)
    ctx.view_layer.update()
    if step % 50 == 49:
        for arm in arms:
            for pb in arm.pose.bones:
                digest.update(("%s %.4f %.4f %.4f\n" % ((pb.name,) + tuple(pb.head))).encode())

for arm in arms:
    pb = arm.pose.bones["j11"]
    print(arm.name, "%.4f %.4f %.4f" % tuple(pb.head))
print(digest.hexdigest())
