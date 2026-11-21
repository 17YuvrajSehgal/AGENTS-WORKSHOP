import glob, hashlib, json, os, shutil, sys

KT = "/tmp/kt_233"
# Use a local DuckDB home with the spatial extension pre-installed (no network needed)
_ext = os.path.join(KT, ".duckdb", "extensions", "v1.4.4", "linux_amd64")
if not os.path.exists(os.path.join(_ext, "spatial.duckdb_extension")):
    src_ext = os.path.expanduser("~/.duckdb/extensions/v1.4.4/linux_amd64")
    os.makedirs(_ext, exist_ok=True)
    for fn in os.listdir(src_ext):
        shutil.copy(os.path.join(src_ext, fn), _ext)
os.environ["HOME"] = KT

import pyarrow as pa
import pyarrow.parquet as pq
import geoparquet_io
from geoparquet_io.core import duckdb_metadata as dm
from geoparquet_io.core.common import detect_geoparquet_file_type, get_duckdb_connection

src = os.path.dirname(os.path.dirname(geoparquet_io.__file__))
data = os.path.join(src, "tests", "data")
names = ["buildings_test.parquet", "fields_gpq2_5070_brotli.parquet"]
files = [os.path.join(data, n) for n in names]

# Synthetic files with GeoArrow extension metadata and struct columns
gen = os.path.join(KT, "gen")
os.makedirs(gen, exist_ok=True)
wkb_pt = bytes.fromhex("0101000000000000000000F03F0000000000000040")
projjson = {"type": "GeographicCRS", "name": "WGS 84",
            "id": {"authority": "OGC", "code": "CRS84"}}
variants = {
    "ext_str": json.dumps({"crs": "OGC:CRS84"}),
    "ext_dict": json.dumps({"crs": projjson}),
    "ext_bad": "{not json",
}
synth = []
for key, meta in variants.items():
    p = os.path.join(gen, f"{key}.parquet")
    fmeta = {b"ARROW:extension:name": b"geoarrow.wkb"}
    if meta is not None:
        fmeta[b"ARROW:extension:metadata"] = meta.encode()
    schema = pa.schema([
        pa.field("id", pa.int64(), nullable=False),
        pa.field("geometry", pa.binary(), metadata=fmeta),
        pa.field("bbox", pa.struct([("xmin", pa.float64()), ("ymin", pa.float64())])),
    ])
    t = pa.table({"id": list(range(10)), "geometry": [wkb_pt] * 10,
                  "bbox": [{"xmin": 1.0, "ymin": 2.0}] * 10}, schema=schema)
    if not os.path.exists(p):
        pq.write_table(t, p)
    synth.append(p)
bad = os.path.join(gen, "not_parquet.parquet")
with open(bad, "w") as fh:
    fh.write("this is not parquet " * 10)

h = hashlib.sha256()
def add(x):
    h.update(json.dumps(x, sort_keys=True, default=repr).encode())

def run_all(fs, con=None):
    for f in fs:
        name = os.path.basename(f)
        kv = dm.get_kv_metadata(f, con=con)
        add([name, sorted((k.decode(errors="replace"), len(v)) for k, v in kv.items())])
        add([name, dm.get_geo_metadata(f, con=con)])
        fm = dm.get_file_metadata(f, con=con)
        add([name, fm.get("num_rows"), fm.get("num_row_groups")])
        si = dm.get_schema_info(f, con=con)
        add([name, [(c.get("name"), c.get("logical_type")) for c in si]])

run_all(files)
for f in files:
    add([os.path.basename(f), detect_geoparquet_file_type(f)])
run_all(synth)
part = os.path.join(data, "country_partition")
run_all([part])
for fn in (dm.get_kv_metadata, dm.get_geo_metadata, dm.get_file_metadata, dm.get_schema_info):
    try:
        fn(bad)
        add("noerr")
    except Exception as e:
        add(type(e).__name__)

con = get_duckdb_connection(load_spatial=False)
run_all(files[:1], con=con)
con.close()

# With geoarrow-pyarrow extension types registered
try:
    import geoarrow.pyarrow  # noqa: F401
    for f in synth:
        try:
            si = dm.get_schema_info(f)
            add([os.path.basename(f), [(c.get("name"), c.get("logical_type")) for c in si]])
        except Exception as e:
            add(type(e).__name__)
except ImportError:
    add("no-geoarrow")
print(h.hexdigest())
