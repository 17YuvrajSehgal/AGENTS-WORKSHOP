"""Workload: LogStore ingest + query (adapted from lib/iris/scripts/benchmark_log_store.py)."""

import hashlib
import shutil
from pathlib import Path

from iris.cluster.log_store import LogStore, task_log_key
from iris.cluster.types import JobName, TaskAttempt
from iris.rpc import logging_pb2

ROOT = Path("/tmp/kt_3840/run")
NUM_JOBS = 16
NUM_TASKS = 20
LINES = 250
H = hashlib.sha256()


def _make_entries(count, prefix, start_ms=0):
    out = []
    for i in range(count):
        level = 20 if i % 50 == 0 else 0
        e = logging_pb2.LogEntry(source="stdout", data=f"{prefix} line {i}", level=level)
        e.timestamp.epoch_ms = start_ms + i
        out.append(e)
    return out


def _job_name(j):
    return f"/user/bench-job-{j:04d}"


def _task_key(j, t, attempt=0):
    job = JobName.from_wire(f"{_job_name(j)}/task/{t}")
    return task_log_key(TaskAttempt(task_id=job, attempt_id=attempt))


def record(tag, res):
    H.update(tag.encode())
    H.update(str(res.cursor).encode())
    for e in res.entries:
        H.update(e.SerializeToString(deterministic=True))
    return len(res.entries)


def queries(store, round_id):
    total = 0
    for mj in (1, NUM_JOBS // 2, NUM_JOBS - 1):
        mt = NUM_TASKS // 2
        key = _task_key(mj, mt)
        total += record("a", store.get_logs(key))
        total += record("b", store.get_logs(key, max_lines=100))
        total += record("c", store.get_logs(key, max_lines=100, tail=True))
        first = store.get_logs(key, max_lines=120)
        total += record("d", store.get_logs(key, cursor=first.cursor, max_lines=100))
        total += record("e", store.get_logs(key, substring_filter="line 42"))
        total += record("f", store.get_logs(key, min_level="WARNING"))
        since = mj * 1_000_000 + mt * 10_000 + LINES // 2
        total += record("g", store.get_logs(key, since_ms=since))
        prefix = f"{_job_name(mj)}/"
        total += record("h", store.get_logs_by_prefix(prefix, max_lines=100))
        total += record("i", store.get_logs_by_prefix(prefix))
        total += record("j", store.get_logs_by_prefix(prefix, max_lines=100, tail=True))
        total += record("k", store.get_logs_by_prefix(prefix, substring_filter="line 199"))
        pr = store.get_logs_by_prefix(prefix, max_lines=300)
        total += record("l", store.get_logs_by_prefix(prefix, cursor=pr.cursor, max_lines=100))
        total += record("m", store.get_logs(key, cursor=first.cursor, since_ms=since, substring_filter="line"))
        H.update(str(store.has_logs(key)).encode())
    total += record("n", store.get_logs_by_prefix("/user/", max_lines=100))
    total += record("o", store.get_logs_by_prefix("/user/", max_lines=100, tail=True))
    H.update(str(store.has_logs(_task_key(NUM_JOBS + 5, 0))).encode())
    H.update(f"round{round_id}:{total}".encode())
    return total


def main():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    log_dir = ROOT / "logs"
    store = LogStore(
        log_dir=log_dir,
        flush_interval_sec=1e9,
        segment_target_bytes=256 * 15_000,
    )
    try:
        for j in range(NUM_JOBS):
            batch = []
            for t in range(NUM_TASKS):
                key = _task_key(j, t)
                entries = _make_entries(LINES, f"[job={j} task={t}]", start_ms=j * 1_000_000 + t * 10_000)
                if t % 7 == 0:
                    # small single-key appends
                    for k in range(0, LINES, 25):
                        store.append(key, entries[k : k + 25])
                    continue
                batch.append((key, entries))
                if len(batch) >= 5:
                    store.append_batch(batch)
                    batch = []
            if batch:
                store.append_batch(batch)
            if j % 4 == 3:
                queries(store, j)
        n = queries(store, 99)
        print("final query entries", n)
    finally:
        store.close()
    shutil.rmtree(ROOT, ignore_errors=True)
    print(H.hexdigest())


if __name__ == "__main__":
    main()
