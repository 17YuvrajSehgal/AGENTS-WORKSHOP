"""Workload for nexus PR 623: cache-first content size + FUSE getattr sizing."""

import hashlib
import logging
import os
import shutil
import tempfile
from datetime import UTC, datetime

logging.disable(logging.CRITICAL)

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from nexus.backends.cache_mixin import CacheConnectorMixin
from nexus.backends.hn_connector import HNConnectorBackend
from nexus.core.metadata import FileMetadata
from nexus.core.permissions import OperationContext
from nexus.fuse.mount import MountMode
from nexus.fuse.operations import NexusFUSEOperations
from nexus.storage.models import Base, FilePathModel

digest = hashlib.sha256()


TMP_BASE = "/dev/shm" if os.path.isdir("/dev/shm") else None


def make_engine(url):
    eng = create_engine(url, poolclass=NullPool)

    @event.listens_for(eng, "connect")
    def _pragmas(dbapi_conn, _rec):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA synchronous=OFF")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()

    return eng


def feed(*items):
    for it in items:
        digest.update(repr(it).encode())


# ----------------------------------------------------------------------------
# Part 1: CacheConnectorMixin writes (single + batch) and cache-first size
# ----------------------------------------------------------------------------
N_FILES = 200
ROUNDS = 2

workdir = tempfile.mkdtemp(prefix="kt_623_", dir=TMP_BASE)
try:
    for rnd in range(ROUNDS):
        CacheConnectorMixin.clear_memory_cache()
        db_path = os.path.join(workdir, f"cache_{rnd}.db")
        engine = make_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

        now = datetime(2025, 1, 1, tzinfo=UTC)
        with SessionLocal() as s:
            for i in range(N_FILES):
                s.add(
                    FilePathModel(
                        path_id=f"pid-{i:05d}",
                        virtual_path=f"/hn/top/item_{i:05d}.md",
                        backend_id="hn",
                        physical_path=f"top/item_{i:05d}.md",
                        size_bytes=0,
                        created_at=now,
                        updated_at=now,
                    )
                )
            s.commit()

        backend = HNConnectorBackend(session_factory=SessionLocal)

        def make_content(i):
            return (f"# Story {i}\n" + ("lorem ipsum dolor " * ((i * 7) % 50 + 1))).encode()

        # Single writes for first half
        half = N_FILES // 2
        for i in range(half):
            e = backend._write_to_cache(
                f"/hn/top/item_{i:05d}.md", make_content(i), backend_version=f"v{i}"
            )
            feed(e.original_size, e.cached_size, e.content_type)
        # Re-write some with different content (existing entry path)
        for i in range(0, half, 5):
            e = backend._write_to_cache(
                f"/hn/top/item_{i:05d}.md", make_content(i) + b"extra", backend_version=f"w{i}"
            )
            feed(e.original_size)

        # Batch writes for second half
        entries = [
            {
                "path": f"/hn/top/item_{i:05d}.md",
                "content": make_content(i),
                "backend_version": f"v{i}",
            }
            for i in range(half, N_FILES)
        ]
        res = backend._batch_write_to_cache(entries)
        feed([(e.original_size, e.cached_size) for e in res])

        # Sizes via get_content_size (cache-first in head, estimate in base)
        sizes = []
        for i in range(N_FILES + 20):
            ctx = OperationContext(
                user="bench",
                groups=[],
                backend_path=f"top/item_{i:05d}.md",
                virtual_path=f"/hn/top/item_{i:05d}.md",
            )
            sizes.append(backend.get_content_size("ignored", ctx))
        feed(sizes)

        with SessionLocal() as s:
            rows = s.execute(
                select(FilePathModel.virtual_path, FilePathModel.size_bytes).order_by(
                    FilePathModel.virtual_path
                )
            ).all()
            feed([tuple(r) for r in rows])
        engine.dispose()
finally:
    shutil.rmtree(workdir, ignore_errors=True)


# ----------------------------------------------------------------------------
# Part 1b: S3 / Gmail connectors get_content_size (cache-first in head)
# ----------------------------------------------------------------------------
import boto3


class _FakeS3Client:
    """In-memory stand-in for the AWS S3 client (no network)."""

    def __init__(self, objects):
        self.objects = objects
        self.head_calls = 0

    def head_bucket(self, Bucket):
        return {}

    def get_bucket_versioning(self, Bucket):
        return {}

    def head_object(self, Bucket, Key):
        self.head_calls += 1
        if Key not in self.objects:
            from botocore.exceptions import ClientError

            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {"ContentLength": len(self.objects[Key])}

    def list_objects_v2(self, Bucket, Prefix, Delimiter="/", **kw):
        contents, prefixes = [], set()
        for key in sorted(self.objects):
            if key.startswith(Prefix):
                rest = key[len(Prefix) :]
                if Delimiter and Delimiter in rest:
                    prefixes.add(Prefix + rest.split(Delimiter)[0] + Delimiter)
                else:
                    contents.append({"Key": key, "Size": len(self.objects[key])})
        return {"Contents": contents, "CommonPrefixes": [{"Prefix": p} for p in sorted(prefixes)]}


class _FakeS3Resource:
    def Bucket(self, name):
        return object()


def _seed_paths(SessionLocal, vpaths):
    t = datetime(2025, 1, 1, tzinfo=UTC)
    with SessionLocal() as s:
        for k, vp in enumerate(vpaths):
            s.add(
                FilePathModel(
                    path_id=f"p-{k:05d}",
                    virtual_path=vp,
                    backend_id="conn",
                    physical_path=vp,
                    size_bytes=0,
                    created_at=t,
                    updated_at=t,
                )
            )
        s.commit()


workdir = tempfile.mkdtemp(prefix="kt_623b_", dir=TMP_BASE)
try:
    from nexus.backends.gmail_connector import GmailConnectorBackend
    from nexus.backends.s3_connector import S3ConnectorBackend

    for rnd in range(ROUNDS):
        CacheConnectorMixin.clear_memory_cache()
        engine = make_engine(f"sqlite:///{workdir}/conn_{rnd}.db")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

        # --- S3 ---
        N_S3 = 200
        objects = {
            f"data/obj_{i:04d}.txt": (f"object {i} " * (i % 30 + 1)).encode() for i in range(N_S3)
        }
        fake_client = _FakeS3Client(objects)
        _orig_client, _orig_resource = boto3.client, boto3.resource
        boto3.client = lambda *a, **k: fake_client
        boto3.resource = lambda *a, **k: _FakeS3Resource()
        try:
            s3 = S3ConnectorBackend(
                bucket_name="bench",
                prefix="data",
                access_key_id="x",
                secret_access_key="y",
                session_factory=SessionLocal,
            )
        finally:
            boto3.client, boto3.resource = _orig_client, _orig_resource
        s3_vpaths = [f"/mnt/s3/obj_{i:04d}.txt" for i in range(N_S3)]
        _seed_paths(SessionLocal, s3_vpaths)
        # cache 3/4 of the objects
        res = s3._batch_write_to_cache(
            [
                {"path": s3_vpaths[i], "content": objects[f"data/obj_{i:04d}.txt"]}
                for i in range(N_S3)
                if i % 4 != 0
            ]
        )
        feed(len(res))
        s3_sizes = []
        for i in range(N_S3):
            ctx = OperationContext(
                user="bench",
                groups=[],
                backend_path=f"obj_{i:04d}.txt",
                virtual_path=s3_vpaths[i],
            )
            s3_sizes.append(s3.get_content_size("ignored", ctx))
        feed(s3_sizes)

        # --- Gmail (all entries cached, so no API access is needed) ---
        gm = GmailConnectorBackend(
            token_manager_db=f"{workdir}/tokens_{rnd}.db",
            user_email="bench@example.invalid",
            session_factory=SessionLocal,
        )
        N_GM = 150
        gm_vpaths = [f"/mnt/gmail/INBOX/thr{i:04d}-msg{i:04d}.yaml" for i in range(N_GM)]
        t = datetime(2025, 1, 1, tzinfo=UTC)
        with SessionLocal() as s:
            for i, vp in enumerate(gm_vpaths):
                s.add(
                    FilePathModel(
                        path_id=f"g-{i:05d}",
                        virtual_path=vp,
                        backend_id="gmail",
                        physical_path=vp,
                        size_bytes=0,
                        created_at=t,
                        updated_at=t,
                    )
                )
            s.commit()
        for i, vp in enumerate(gm_vpaths):
            body = f"subject: Message {i}\nbody: |\n  " + ("hello world " * (i % 40 + 1))
            gm._write_to_cache(vp, body.encode(), backend_version="immutable")
        gm_sizes = []
        for i, vp in enumerate(gm_vpaths):
            ctx = OperationContext(
                user="bench",
                groups=[],
                backend_path=f"INBOX/thr{i:04d}-msg{i:04d}.yaml",
                virtual_path=vp,
            )
            gm_sizes.append(gm.get_content_size("ignored", ctx))
        feed(gm_sizes)

        with SessionLocal() as s:
            rows = s.execute(
                select(FilePathModel.virtual_path, FilePathModel.size_bytes).order_by(
                    FilePathModel.virtual_path
                )
            ).all()
            feed([tuple(r) for r in rows])
        engine.dispose()
finally:
    shutil.rmtree(workdir, ignore_errors=True)


# ----------------------------------------------------------------------------
# Part 1c: NexusFS.sync_mount of an S3 connector mount (metadata sync sizes)
# ----------------------------------------------------------------------------
import nexus

workdir = tempfile.mkdtemp(prefix="kt_623c_", dir=TMP_BASE)
try:
    nfs = nexus.connect(
        config={"mode": "embedded", "data_dir": workdir, "enforce_permissions": False}
    )
    objects = {}
    for i in range(120):
        objects[f"bucket/obj_{i:04d}.txt"] = (f"payload {i} " * (i % 25 + 1)).encode()
    for i in range(40):
        objects[f"bucket/sub{i % 4}/nested_{i:04d}.txt"] = (f"nested {i} " * (i + 1)).encode()
    fake_client = _FakeS3Client(objects)
    _orig_client, _orig_resource = boto3.client, boto3.resource
    boto3.client = lambda *a, **k: fake_client
    boto3.resource = lambda *a, **k: _FakeS3Resource()
    try:
        s3m = S3ConnectorBackend(
            bucket_name="bench",
            prefix="bucket",
            access_key_id="x",
            secret_access_key="y",
            session_factory=nfs.metadata.SessionLocal,
        )
    finally:
        boto3.client, boto3.resource = _orig_client, _orig_resource
    nfs.router.add_mount("/mnt/s3", s3m)

    # Single-file sync of files not yet known
    for i in (3, 17, 42):
        r = nfs.sync_mount("/mnt/s3", path=f"obj_{i:04d}.txt", sync_content=False)
        feed(sorted((k, v) for k, v in r.items() if k != "errors"))
    # Full recursive sync
    r = nfs.sync_mount("/mnt/s3", sync_content=False)
    feed(sorted((k, v) for k, v in r.items() if k != "errors"))
    synced = []
    for key in sorted(objects):
        vp = "/mnt/s3/" + key[len("bucket/") :]
        m = nfs.metadata.get(vp)
        synced.append((vp, None if m is None else m.size))
    feed(synced)
    nfs.close()
finally:
    shutil.rmtree(workdir, ignore_errors=True)


# ----------------------------------------------------------------------------
# Part 2: FUSE getattr on files (metadata size vs. content read)
# ----------------------------------------------------------------------------
class InMemoryMetadataStore:
    def __init__(self):
        self._d = {}

    def get(self, path):
        return self._d.get(path)

    def put(self, meta):
        self._d[meta.path] = meta


class InMemoryNexusFS:
    """Minimal in-memory filesystem stand-in exposing the interface FUSE uses."""

    def __init__(self):
        self.files = {}
        self.metadata = InMemoryMetadataStore()
        self.reads = 0

    def add(self, path, content, record_size=True):
        self.files[path] = content
        t = datetime(2025, 1, 1)
        meta = FileMetadata(
            path=path,
            backend_name="mem",
            physical_path=hashlib.sha256(content).hexdigest(),
            size=len(content) if record_size else 0,
            etag=None,
            created_at=t,
            modified_at=t,
            version=1,
        )
        # Permission fields consumed by FUSE getattr
        meta.mode = 0o640
        meta.owner = None
        meta.group = None
        self.metadata.put(meta)

    def is_directory(self, path):
        return False

    def exists(self, path):
        return path in self.files

    def read(self, path, *a, **k):
        self.reads += 1
        return self.files[path]


fs = InMemoryNexusFS()
N_FUSE = 3000
for i in range(N_FUSE):
    content = (f"line {i}\n" * (i % 200 + 1)).encode()
    fs.add(f"/workspace/f{i:05d}.txt", content, record_size=(i % 4 != 0))

attrs_out = []
for rep in range(2):
    ops = NexusFUSEOperations(fs, MountMode.BINARY, cache_config={"attr_cache_size": 16})
    for i in range(N_FUSE):
        a = ops.getattr(f"/workspace/f{i:05d}.txt")
        attrs_out.append((a["st_mode"], a["st_size"], a["st_nlink"]))
    # Also a parsed view path (.txt) for some files in smart mode
    ops2 = NexusFUSEOperations(fs, MountMode.SMART, cache_config={"attr_cache_size": 16})
    for i in range(0, N_FUSE, 10):
        a = ops2.getattr(f"/workspace/f{i:05d}.txt")
        attrs_out.append((a["st_mode"], a["st_size"]))
feed(attrs_out)
print("fuse attrs:", len(attrs_out))
print(digest.hexdigest())
