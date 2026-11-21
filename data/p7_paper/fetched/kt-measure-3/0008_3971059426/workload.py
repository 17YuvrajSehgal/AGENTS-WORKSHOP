import hashlib
import warnings
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyarrow as pa

warnings.filterwarnings("ignore")

from feast import Entity, FeatureView, Field, FileSource, PushSource, RequestSource
from feast.data_format import AvroFormat
from feast.data_source import KafkaSource
from feast.on_demand_feature_view import on_demand_feature_view
from feast.stream_feature_view import StreamFeatureView
from feast.type_map import python_values_to_proto_values
from feast.types import Array, Bool, Float32, Float64, Int32, Int64, String, UnixTimestamp
from feast.utils import _convert_arrow_to_proto
from feast.value_type import ValueType

h = hashlib.sha256()
rng = np.random.default_rng(42)
N = 2000

# ---------- type_map conversions ----------
base_ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
cases = [
    (ValueType.INT64, [int(x) for x in rng.integers(0, 1000, N)]),
    (ValueType.INT32, [np.int32(x) for x in rng.integers(0, 1000, N)]),
    (ValueType.DOUBLE, list(rng.random(N)) + [None]),
    (ValueType.FLOAT, [float(x) for x in rng.random(N)]),
    (ValueType.STRING, [f"s{i}" for i in range(N)] + [None]),
    (ValueType.BYTES, [f"b{i}".encode() for i in range(N)]),
    (ValueType.BOOL, [np.bool_(i % 2) for i in range(N)] + [None]),
    (ValueType.UNIX_TIMESTAMP, [base_ts + timedelta(seconds=i) for i in range(N)]),
    (ValueType.INT64, [None] * 50),
    (ValueType.INT64_LIST, [list(range(i % 7)) for i in range(N)] + [None]),
    (ValueType.INT32_LIST, [[1, 2, 3]] * N),
    (ValueType.DOUBLE_LIST, [rng.random(4) for _ in range(N)]),
    (ValueType.FLOAT_LIST, [[1.5, 2.5]] * N),
    (ValueType.STRING_LIST, [["a", "b", str(i)] for i in range(N)]),
    (ValueType.BOOL_LIST, [[True, False, np.bool_(1)] for _ in range(N)] + [None]),
    (ValueType.UNIX_TIMESTAMP_LIST, [[base_ts, base_ts + timedelta(days=1)]] * N + [None]),
    (ValueType.INT64_LIST, [b"[1,2,3]"] * N),
    (ValueType.BOOL_LIST, [b"[1,0,1]"] * N),
    (ValueType.INT64_SET, [{1, 2, i % 10} for i in range(N)] + [None]),
    (ValueType.STRING_SET, [["a", "b", "a"]] * N),
    (ValueType.BOOL_SET, [{True, False}] * N + [None]),
    (ValueType.UNIX_TIMESTAMP_SET, [{base_ts, base_ts + timedelta(hours=1)}] * N),
    (ValueType.DOUBLE_SET, [b"[1.0,2.0]"] * N),
    (ValueType.MAP, [{"k": i, "v": "x"} for i in range(200)]),
]
for _ in range(3):
    for vt, vals in cases:
        out = python_values_to_proto_values(vals, vt)
        h.update(vt.name.encode())
        for p in out:
            kind = p.WhichOneof("val")
            if kind and kind.endswith("_set_val"):
                h.update(kind.encode() + repr(sorted(getattr(p, kind).val)).encode())
            else:
                h.update(p.SerializeToString(deterministic=True))

# error paths
for vt, vals in [
    (ValueType.INT64_LIST, [[1.5, float("nan")]]),
    (ValueType.INT64_SET, [[1.5, 2.0]]),
    (ValueType.BYTES_LIST, [b"[1]"]),
]:
    try:
        python_values_to_proto_values(vals, vt)
        h.update(b"noerr")
    except Exception as e:
        h.update(type(e).__name__.encode())

# ---------- feature views / to_proto ----------
driver = Entity(name="driver", join_keys=["driver_id"])
src = FileSource(name="src", path="/tmp/kt_5998/x.parquet", timestamp_field="event_timestamp",
                 created_timestamp_column="created")
push = PushSource(name="push", batch_source=src)
fv = FeatureView(
    name="fv",
    entities=[driver],
    ttl=timedelta(days=1),
    schema=[Field(name="driver_id", dtype=Int64), Field(name="conv", dtype=Float32),
            Field(name="acc", dtype=Float64), Field(name="cnt", dtype=Int64),
            Field(name="tags", dtype=Array(String))],
    source=push,
)
kafka = KafkaSource(
    name="kafka", kafka_bootstrap_servers="localhost:9092", topic="t",
    timestamp_field="event_timestamp", batch_source=src,
    message_format=AvroFormat(""),
)
sfv = StreamFeatureView(
    name="sfv", entities=[driver], ttl=timedelta(days=1),
    schema=[Field(name="driver_id", dtype=Int64), Field(name="conv", dtype=Float32)],
    source=kafka, mode="spark", timestamp_field="event_timestamp",
)
req = RequestSource(name="req", schema=[Field(name="val", dtype=Int64)])


@on_demand_feature_view(
    sources=[fv, req],
    schema=[Field(name="out1", dtype=Float64), Field(name="out2", dtype=Int64),
            Field(name="missing_f", dtype=Float64)],
    mode="python",
    write_to_online_store=True,
)
def odfv(inputs):
    return {"out1": [c * 2.0 for c in inputs["conv"]], "out2": inputs["val"],
            "missing_f": [None] * len(inputs["val"])}


@on_demand_feature_view(
    sources=[fv, req],
    schema=[Field(name="pout", dtype=Float64)],
    mode="pandas",
)
def odfv_pd(df):
    out = pd.DataFrame()
    out["pout"] = df["conv"] * 3.0
    return out


def _scrub(msg):
    for fd, val in list(msg.ListFields()):
        if fd.message_type is None:
            continue
        if fd.message_type.full_name == "google.protobuf.Timestamp" and "timestamp" in fd.name and fd.name != "timestamp_field":
            msg.ClearField(fd.name)
            continue
        if fd.label == fd.LABEL_REPEATED:
            if fd.message_type.GetOptions().map_entry:
                if fd.message_type.fields_by_name["value"].message_type is not None:
                    for k in val:
                        _scrub(val[k])
                continue
            for v in val:
                _scrub(v)
            if fd.name in ("features", "entity_columns", "feature_columns"):
                items = sorted((v.name, v.SerializeToString(deterministic=True)) for v in val)
                msg.ClearField(fd.name)
                for _, b in items:
                    getattr(msg, fd.name).add().ParseFromString(b)
        else:
            _scrub(val)
    return msg


for _ in range(200):
    for obj in (fv, sfv, odfv, odfv_pd):
        h.update(_scrub(obj.to_proto().spec).SerializeToString(deterministic=True))

# ---------- arrow -> proto ----------
M = 3000
ts = pd.Timestamp("2024-01-01", tz="UTC")
table = pa.Table.from_pandas(pd.DataFrame({
    "driver_id": np.arange(M, dtype=np.int64),
    "conv": rng.random(M).astype(np.float32),
    "acc": rng.random(M),
    "cnt": rng.integers(0, 100, M),
    "tags": [["a", "b"] for _ in range(M)],
    "event_timestamp": [ts + pd.Timedelta(seconds=i) for i in range(M)],
    "created": [ts] * M,
}))
for _ in range(3):
    rows = _convert_arrow_to_proto(table, fv, {"driver_id": ValueType.INT64})
    for ek, feats, et, ct in rows:
        h.update(ek.SerializeToString(deterministic=True))
        for k in sorted(feats):
            h.update(k.encode() + feats[k].SerializeToString(deterministic=True))
        h.update(str(et).encode() + str(ct).encode())

odtable = pa.RecordBatch.from_pandas(pd.DataFrame({
    "driver_id": np.arange(M, dtype=np.int64),
    "out1": rng.random(M),
    "out2": rng.integers(0, 100, M),
    "conv": rng.random(M),
}), preserve_index=False)
for jk in ({"driver_id": ValueType.INT64}, {"other_id": ValueType.STRING}):
    for _ in range(3):
        rows = _convert_arrow_to_proto(odtable, odfv, jk)
        for ek, feats, et, ct in rows:
            h.update(ek.SerializeToString(deterministic=True))
            for k in sorted(feats):
                h.update(k.encode() + feats[k].SerializeToString(deterministic=True))
        h.update(str(len(rows)).encode())

print(h.hexdigest())
