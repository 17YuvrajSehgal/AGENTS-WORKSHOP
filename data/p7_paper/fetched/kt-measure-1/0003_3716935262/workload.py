import hashlib, json, logging, shutil, sys, tempfile
from pathlib import Path
from unittest.mock import Mock

logging.disable(logging.CRITICAL)

from nexus import LocalBackend, NexusFS
from nexus.backends.backend import Backend
from nexus.core.permissions import OperationContext
from nexus.storage.models import FilePathModel
from nexus.fuse.mount import MountMode
from nexus.fuse.operations import NexusFUSEOperations

N_FILES = 300


class DynConnector(Backend):
    def __init__(self, names):
        super().__init__()
        self.token_manager = Mock()
        self._names = names

    @property
    def name(self):
        return "mock_dynamic_connector"

    @property
    def user_scoped(self):
        return True

    def list_dir(self, path, context=None):
        return list(self._names)

    def read_content(self, path, context=None):
        return b"Mock content"

    def write_content(self, path, content, context=None):
        pass

    def delete_content(self, path, context=None):
        pass

    def content_exists(self, path, context=None):
        return True

    def is_directory(self, path, context=None):
        return False

    def mkdir(self, path, context=None):
        pass

    def rmdir(self, path, context=None):
        pass

    def get_content_size(self, path, context=None):
        return 12

    def get_ref_count(self, content_hash):
        return 1


def run_list():
    d = Path(tempfile.mkdtemp(prefix="kt624_"))
    out = []
    try:
        nx = NexusFS(backend=LocalBackend(d), db_path=d / "metadata.db",
                     auto_parse=False, enforce_permissions=False)
        names = [f"file{i:04d}.txt" for i in range(N_FILES)]
        mount = "/mnt/conn"
        nx.router.add_mount(mount, DynConnector(names), priority=10)
        s = nx.metadata.SessionLocal()
        try:
            for i, n in enumerate(names):
                if i % 4 == 3:
                    continue  # some unsynced files without metadata
                s.add(FilePathModel(path_id=f"{mount}/{n}", virtual_path=f"{mount}/{n}",
                                    backend_id="mock_connector", physical_path=f"/{n}",
                                    size_bytes=100 + i * 7, tenant_id="default"))
            s.commit()
        finally:
            s.close()
        for _ in range(5):
            files = nx.list(mount, recursive=False, details=True)
            out.append([(f["path"], f["size"]) for f in files])
            out.append(nx.list(mount, recursive=False, details=False))
        nx.close()
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return out


class RemoteFSStandIn:
    """Stand-in for a remote (RPC) Nexus filesystem client."""

    def __init__(self):
        self.reads = 0

    def get_metadata(self, path):
        i = int(path.rsplit("_", 1)[1].split(".")[0])
        d = {"path": path, "owner": None, "group": None, "mode": 0o644, "is_directory": False}
        if i % 3:
            d["size"] = (i % 5) * 1000
        return d

    def is_directory(self, path, context=None):
        return False

    def exists(self, path, context=None):
        return True

    def read(self, path, context=None):
        self.reads += 1
        return b"x" * 17


def run_fuse():
    out = []
    fs = RemoteFSStandIn()
    ops = NexusFUSEOperations(fs, MountMode.BINARY, cache_config={})
    for i in range(3000):
        p = f"/ws/f_{i}.bin"
        m = ops._get_metadata(p)
        out.append((m.path, getattr(m, "size", "absent"), m.mode))
        a = ops.getattr(p)
        out.append(a["st_size"])
    out.append(fs.reads)
    return out


res = {"list": run_list(), "fuse": run_fuse()}
print(len(res["list"]), len(res["fuse"]))
print(hashlib.sha256(json.dumps(res, sort_keys=True, default=str).encode()).hexdigest())
