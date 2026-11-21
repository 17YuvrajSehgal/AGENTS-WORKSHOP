import hashlib
import numpy as np
import mlx.core as mx
from mlx_vlm.models.base import scaled_dot_product_attention
from mlx_vlm.models.cache import KVCache
from mlx_vlm import turboquant as tq

mx.random.seed(0)
h = hashlib.sha256()


def rec(a):
    a = np.array(a.astype(mx.float32))
    h.update(np.round(a, 3).tobytes())


def unit(shape):
    v = mx.random.normal(shape)
    return v / mx.linalg.norm(v, axis=-1, keepdims=True)


for rep in range(3):
    for dim in (64, 128):
        vecs = mx.random.normal((1, 4, 256, dim))
        qs = mx.random.normal((1, 4, 2, 2, dim))
        for bits in (1, 2, 3, 4):
            c = tq._TurboQuantMSECodec(dim, bits, seed=rep)
            st = c.quantize(vecs)
            rec(c.dequantize(st))
            sc = c.score(qs, st)
            rec(sc)
            w = mx.softmax(sc, axis=-1)
            rec(c.weighted_sum(w, st))
            rec(c.weighted_sum_from_scores(sc, st))
            p = tq._TurboQuantProdCodec(dim, bits, seed=rep)
            sp = p.quantize(vecs)
            rec(p.dequantize(sp))
            rec(p.score(qs, sp))
        for bits in (4,):
            pp = tq._TurboQuantPolarProdCodec(dim, bits, seed=rep)
            sp = pp.quantize(vecs)
            rec(pp.dequantize(sp))
            rec(pp.score(qs, sp))

    # KV cache attention paths (fractional + integer bits)
    for bits in (3.5, 3.0, 4.0):
        keys = mx.random.normal((1, 2, 128, 64))
        values = mx.random.normal((1, 2, 128, 64))
        fp = KVCache()
        fp.update_and_fetch(keys, values)
        tc = tq.TurboQuantKVCache.from_cache(fp, bits=bits)
        tk, tv = tc.state
        for qlen in (1, 8):
            q = mx.random.normal((1, 4, qlen, 64))
            out = scaled_dot_product_attention(q, tk, tv, tc, scale=64 ** -0.5,
                                               mask=None)
            rec(out)
        dk, dv = tc.dequantize(tk, tv)
        rec(dk)
        rec(dv)
        tc.update_and_fetch(mx.random.normal((1, 2, 1, 64)),
                            mx.random.normal((1, 2, 1, 64)))
        tk, tv = tc.state
        out = scaled_dot_product_attention(mx.random.normal((1, 4, 1, 64)), tk,
                                           tv, tc, scale=64 ** -0.5, mask=None)
        rec(out)

print(h.hexdigest())
