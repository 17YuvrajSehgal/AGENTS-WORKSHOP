import hashlib
import numpy as np
import torch

from vesuvius.models.augmentation.transforms.utils.skeleton_transform import MedialSurfaceTransform


def make_seg(rng, shape, n_blobs, label=1):
    seg = np.zeros(shape, dtype=np.float32)
    Z, Y, X = shape
    for _ in range(n_blobs):
        cz, cy, cx = rng.integers(8, Z - 8), rng.integers(30, Y - 30), rng.integers(30, X - 30)
        rz, ry, rx = rng.integers(3, 7), rng.integers(8, 25), rng.integers(4, 15)
        zz, yy, xx = np.ogrid[:Z, :Y, :X]
        m = ((zz - cz) / rz) ** 2 + ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0
        seg[m] = label
    return seg


def main():
    rng = np.random.default_rng(1234)
    shape = (40, 192, 192)
    h = hashlib.sha256()

    tf_plain = MedialSurfaceTransform(do_tube=False, target_keys=["surface"],
                                      ignore_values={"surface": 2})
    tf_tube = MedialSurfaceTransform(do_tube=True, do_open=True, do_close=True)

    samples = []
    for i in range(12):
        seg = make_seg(rng, shape, n_blobs=int(rng.integers(1, 3)))
        # sprinkle ignore label in a small region
        seg[0:2, 0:4, 0:4] = 2
        samples.append(seg)

    # Uncached path (no patch_info): full skeleton computation each call
    for i, seg in enumerate(samples):
        tf = tf_plain if i % 2 == 0 else tf_tube
        dd = {"image": torch.zeros((1,) + shape),
              "surface": torch.from_numpy(seg[None].copy())}
        out = tf(**dd)
        sk = out["surface_skel"].numpy()
        h.update(np.ascontiguousarray(sk).tobytes())

    # Calls carrying patch_info (exercise cache path where present) - repeated
    for rep in range(2):
        for i, seg in enumerate(samples[:4]):
            dd = {"image": torch.zeros((1,) + shape),
                  "surface": torch.from_numpy(seg[None].copy()),
                  "patch_info": {"volume_name": f"vol{i}", "position": [0, 0, i],
                                 "patch_size": list(shape), "scale": 0}}
            out = tf_plain(**dd)
            h.update(np.ascontiguousarray(out["surface_skel"].numpy()).tobytes())

    # Disk-cache-enabled transform where supported (constructor kwargs only in head)
    import inspect, shutil, os
    cache_dir = "/tmp/kt_802/medial_cache"
    shutil.rmtree(cache_dir, ignore_errors=True)
    os.makedirs(cache_dir, exist_ok=True)
    params = inspect.signature(MedialSurfaceTransform.__init__).parameters
    kw = {}
    if "cache_dir" in params:
        kw = dict(cache_dir=cache_dir, enable_disk_cache=True, memory_cache_size=1)
    for inst in range(2):
        tf_disk = MedialSurfaceTransform(do_tube=False, target_keys=["surface"], **kw)
        for i, seg in enumerate(samples[4:7]):
            dd = {"surface": torch.from_numpy(seg[None].copy()),
                  "patch_info": {"volume_name": f"dvol{i}", "position": [i, 0, 0],
                                 "patch_size": list(shape), "scale": 0}}
            out = tf_disk(**dd)
            h.update(np.ascontiguousarray(out["surface_skel"].numpy()).tobytes())

    # 2D segmentation
    seg2d = np.zeros((2, 128, 128), dtype=np.float32)
    seg2d[0, 30:60, 20:90] = 1
    seg2d[1, 70:100, 40:70] = 1
    out = tf_tube(**{"surface": torch.from_numpy(seg2d)})
    h.update(out["surface_skel"].numpy().tobytes())

    # Validation transform factory (behaviour differs; not hashed)
    from vesuvius.models.augmentation.pipelines.training_transforms import create_validation_transforms
    create_validation_transforms(skeleton_targets=["surface"], skeleton_ignore_values={"surface": 2})
    create_validation_transforms(skeleton_targets=None)

    # empty seg
    dd = {"surface": torch.zeros((1, 8, 32, 32))}
    out = tf_plain(**dd)
    h.update(out["surface_skel"].numpy().tobytes())

    print(h.hexdigest())


if __name__ == "__main__":
    main()
