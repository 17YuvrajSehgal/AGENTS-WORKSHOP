import hashlib, logging, os, shutil, sys, tempfile
from typing import Any, Dict, Iterator, Sequence
import numpy as np

logging.basicConfig(level=logging.WARNING)
from levanter.data import BatchProcessor, ShardedDataSource
from levanter.store.cache import CacheOptions, build_or_load_cache
from levanter.distributed import auto_ray_cluster
import ray


class Proc(BatchProcessor[Sequence[int], dict[str, np.ndarray]]):
    def __call__(self, batch):
        return [{"test": np.asarray(x, dtype=np.int64)} for x in batch]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {}

    @property
    def output_exemplar(self):
        return {"test": np.array([0], dtype=np.int64)}

    @property
    def num_cpus(self) -> int:
        return 1


class Src(ShardedDataSource[list[int]]):
    def __init__(self, num_shards, rows):
        self._n = num_shards
        self._rows = rows

    @property
    def shard_names(self):
        return [f"shard_{i}" for i in range(self._n)]

    def open_shard_at_row(self, shard_name, row) -> Iterator[list[int]]:
        s = int(shard_name.split("_")[1])
        return ([s * 1000 + i] * ((i % 7) + 3) for i in range(row, self._rows))


def main():
    # deferred in head, immediate in base
    auto_ray_cluster(address="local", num_cpus=4, include_dashboard=False)
    h = hashlib.sha256()
    root = tempfile.mkdtemp(prefix="kt_1189_")
    try:
        for k in range(3):
            d = os.path.join(root, f"c{k}")
            cache = build_or_load_cache(
                d,
                Src(num_shards=6 + k, rows=40),
                Proc(),
                await_finished=True,
                options=CacheOptions(num_shard_groups=3, batch_size=8),
            )
            cache.await_finished()
            n = len(cache)
            h.update(str(n).encode())
            rows = sorted(tuple(cache[i]["test"].tolist()) for i in range(n))
            h.update(repr(rows).encode())
            print(k, n)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(h.hexdigest())


if __name__ == "__main__":
    main()
