import atexit
import hashlib
import json
import struct
import os
import sys
from pathlib import Path

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.editor.extension import get_armature_extension

SEGMENTS = int(os.environ.get("KT_SEGMENTS", "24"))
RINGS = int(os.environ.get("KT_RINGS", "16"))
N_KEYS = 3

out_dir = Path("/tmp/kt_1069")
out_dir.mkdir(parents=True, exist_ok=True)

bpy.ops.preferences.addon_enable(module="io_scene_vrm")
assert "io_scene_vrm" in bpy.context.preferences.addons
os.environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"


def build_scene():
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=False)
    assert ops.icyp.make_basic_armature() == {"FINISHED"}
    armature_obj = bpy.context.view_layer.objects.active
    ext = get_armature_extension(armature_obj.data)
    ext.spec_version = ext.SPEC_VERSION_VRM0

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=SEGMENTS, ring_count=RINGS, radius=0.3, location=(0, 0, 1.2)
    )
    mesh_obj = bpy.context.view_layer.objects.active
    mesh_obj.name = "Body"
    # flat shading: split normals are per-face and deterministic
    for i, poly in enumerate(mesh_obj.data.polygons):
        poly.use_smooth = False

    mat = bpy.data.materials.new("Skin")
    mat.use_nodes = True
    mesh_obj.data.materials.append(mat)

    mesh_obj.shape_key_add(name="Basis")
    verts = mesh_obj.data.vertices
    for k in range(N_KEYS):
        key = mesh_obj.shape_key_add(name=f"Key{k}")
        for i, v in enumerate(key.data):
            co = verts[i].co
            f = 0.05 * (k + 1) * (((i * 7 + k * 13) % 11) / 11.0)
            axis = k % 3
            new = list(co)
            new[axis] += f * (1.0 if co[axis] >= 0 else -1.0)
            v.co = new

    mesh_obj.parent = armature_obj
    bpy.ops.object.select_all(action="DESELECT")
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj


COMPONENT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_accessor(gltf, binary, index):
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    n = NCOMP[acc["type"]]
    fmt = COMPONENT[acc["componentType"]]
    size = struct.calcsize(fmt)
    stride = view.get("byteStride", size * n)
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    out = []
    for i in range(acc["count"]):
        vals = struct.unpack_from("<" + fmt * n, binary, base + i * stride)
        if fmt == "f":
            # float noise (~1e-7) varies between runs; quantize off-grid
            vals = tuple(round(v + 3.7e-5, 3) + 0.0 for v in vals)
        out.append(vals)
    return out


def canonical_digest(data):
    # The exporter's vertex ordering is not stable between runs, so hash an
    # order-independent form: JSON without buffer layout + sorted triangles
    # made of full per-vertex attribute tuples (incl. morph targets).
    json_len = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20 : 20 + json_len])
    bin_off = 20 + json_len
    bin_len = struct.unpack_from("<I", data, bin_off)[0]
    binary = data[bin_off + 8 : bin_off + 8 + bin_len]

    tris_all = []
    for mesh in gltf.get("meshes", []):
        for prim in mesh["primitives"]:
            attrs = sorted(prim["attributes"].items())
            cols = [read_accessor(gltf, binary, a) for _, a in attrs]
            for target in prim.get("targets", []):
                for _, a in sorted(target.items()):
                    cols.append(read_accessor(gltf, binary, a))
            verts = list(zip(*cols))
            idx = [i[0] for i in read_accessor(gltf, binary, prim["indices"])]
            tris = []
            for t in range(0, len(idx), 3):
                tri = [verts[idx[t]], verts[idx[t + 1]], verts[idx[t + 2]]]
                r = tri.index(min(tri))
                tris.append(tuple(tri[r:] + tri[:r]))
            tris.sort()
            tris_all.append((mesh.get("name"), prim.get("material"), tris))

    skeleton = {k: v for k, v in gltf.items() if k not in ("accessors", "bufferViews", "buffers")}
    h = hashlib.sha256()
    h.update(json.dumps(skeleton, sort_keys=True).encode())
    h.update(repr(tris_all).encode())
    return h.hexdigest(), sum(len(t[2]) for t in tris_all)


build_scene()

digest = hashlib.sha256()
for n in range(2):
    path = out_dir / f"out{n}.vrm"
    if path.exists():
        path.unlink()
    assert ops.export_scene.vrm(filepath=str(path)) == {"FINISHED"}
    data = path.read_bytes()
    d, ntri = canonical_digest(data)
    digest.update(d.encode())
    print(f"export {n}: {ntri} triangles {d[:16]}")

print(digest.hexdigest())
sys.stdout.flush()


def _finish():
    # Blender's bpy module prints a memory leak report to stdout during
    # interpreter teardown, which would hide the digest line. Save coverage
    # data (if measured) and exit without running Blender's teardown.
    try:
        import coverage

        cov = coverage.Coverage.current()
        if cov is not None:
            cov.stop()
            cov.save()
    except ImportError:
        pass
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


atexit.register(_finish)
