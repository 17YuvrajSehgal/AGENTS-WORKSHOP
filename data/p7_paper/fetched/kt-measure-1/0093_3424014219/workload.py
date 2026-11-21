import hashlib, io, os, sys, contextlib, random

SRC = os.path.join(os.path.dirname(os.path.abspath(sys.prefix)), "src")
sys.path.insert(0, SRC)

from scripts.helper_classes import GeoJSON
from scripts.timezone_data import TimezoneData
from scripts.shortcuts import compile_h3_map, all_res_candidates, optimise_shortcut_ordering

rng = random.Random(12345)


def make_geojson(n_zones):
    feats = []
    for z in range(n_zones):
        polys = []
        for p in range(rng.randint(1, 4)):
            cx = rng.uniform(-170, 170)
            cy = rng.uniform(-75, 75)
            w = rng.uniform(2, 25)
            h = rng.uniform(2, 15)
            n = rng.randint(4, 30)
            ring = []
            for k in range(n):
                t = k / n
                if t < 0.25:
                    x, y = cx - w + 8 * w * t, cy - h
                elif t < 0.5:
                    x, y = cx + w, cy - h + 8 * h * (t - 0.25)
                elif t < 0.75:
                    x, y = cx + w - 8 * w * (t - 0.5), cy + h
                else:
                    x, y = cx - w, cy + h - 8 * h * (t - 0.75)
                ring.append([round(max(-179.9, min(179.9, x)), 4), round(max(-89, min(89, y)), 4)])
            ring.append(ring[0])
            polys.append([ring])
        feats.append({"type": "Feature", "properties": {"tzid": f"Zone/{z}"},
                      "geometry": {"type": "MultiPolygon", "coordinates": polys}})
    return {"type": "FeatureCollection", "features": feats}


out = []
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    gj = GeoJSON.model_validate(make_geojson(400))
    data = TimezoneData.from_geojson(gj)
    for res in (0, 1):
        cands = sorted(all_res_candidates(res))
        mapping = compile_h3_map(data, set(cands))
        for h in sorted(mapping):
            out.append((res, int(h), [int(x) for x in mapping[h]]))
    # direct ordering calls on larger lists
    n = data.nr_of_polygons
    for i in range(8000):
        ids = rng.sample(range(n), rng.randint(0, min(n, 60)))
        out.append(("ord", [int(x) for x in optimise_shortcut_ordering(data, ids)]))
    # repeated access of cached candidates
    tot = 0
    for h in sorted(data.hex_cache):
        tot += len(data.get_hex(h).poly_candidates)
    out.append(("cand", tot))

print(len(out))
print(hashlib.sha256(repr(out).encode()).hexdigest())
