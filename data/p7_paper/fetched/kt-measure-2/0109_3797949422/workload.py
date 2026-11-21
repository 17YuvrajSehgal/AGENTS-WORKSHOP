import hashlib, itertools
import numpy as np
import jax.numpy as jnp
from mbi.domain import Domain
from mbi.dataset import JaxDataset

np.random.seed(0)
attrs = ["a", "b", "c", "d", "e", "f"]
shape = [3, 4, 5, 2, 6, 7]
dom = Domain(attrs, shape)
h = hashlib.sha256()
import jax
mesh = jax.sharding.Mesh(np.array(jax.devices()[:1]), ("x",))


def columns(ds):
    # version-neutral view of the stored data (2D array in base, dict in head)
    if isinstance(ds.data, dict):
        return [np.asarray(ds.data[a]) for a in ds.domain.attrs]
    arr = np.asarray(ds.data)
    return [arr[:, i] for i in range(arr.shape[1])]


def proj(ds, cols):
    try:
        v = np.asarray(ds.project(cols).datavector(), dtype=np.float64)
        return np.round(v, 3).tobytes()
    except Exception as e:  # base project() is broken with this jax version
        return type(e).__name__.encode()


for rep in range(30):
    ds = JaxDataset.synthetic(dom, 50000)
    h.update(str(ds.records).encode())
    for c in columns(ds):
        h.update(c.astype(np.int64).tobytes())
    for k in (1, 2):
        for cols in itertools.combinations(attrs, k):
            h.update(proj(ds, list(cols)))
    h.update(proj(ds, "a"))
    h.update(proj(ds, []))
    h.update(proj(wds_prev, []) if rep else b"")
    wds = JaxDataset(ds.data, dom, jnp.asarray(np.random.rand(50000)))
    h.update(proj(wds, ["c", "e", "f"]))
    wds_prev = wds
    try:
        sh = wds.apply_sharding(mesh)
        h.update(proj(sh, ["a", "b"]))
    except Exception as e:
        h.update(type(e).__name__.encode())
    try:
        h.update(str(JaxDataset({}, dom).records).encode())
    except Exception as e:
        h.update(type(e).__name__.encode())
print(h.hexdigest())
