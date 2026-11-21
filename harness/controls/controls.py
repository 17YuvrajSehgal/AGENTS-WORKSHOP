"""Positive controls in Python: variant a has the problem, b has the fix.

Usage: python3 controls.py <control> <a|b>
The expected signal for each control is in controls.json.
"""
import os
import socket
import subprocess
import sys
import threading
import time

DATA = "/tmp/kt_controls_data.txt"


def file_reads(b):
    if b:
        with open(DATA) as f:
            text = f.read()
        return sum(len(text) for _ in range(2000))
    total = 0
    for _ in range(2000):
        with open(DATA) as f:
            total += len(f.read())
    return total


def batch_net(b):
    r, w = socket.socketpair()
    got = []
    t = threading.Thread(target=lambda: got.append(sum(iter(lambda: len(r.recv(65536)), 0))))
    t.start()
    msgs = [b"x" * 64] * 4000
    if b:
        w.sendall(b"".join(msgs))
    else:
        for m in msgs:
            w.send(m)
    w.close()
    t.join()
    return got[0]


def spawn(b):
    if b:
        return sum(len(str(i)) for i in range(100))
    return sum(subprocess.run(["/bin/true"]).returncode for _ in range(100))


def logging(b):
    lines = [f"line {i}\n" for i in range(5000)]
    with open("/tmp/kt_controls_log.txt", "w", buffering=1) as f:  # line buffered
        if b:
            f.write("".join(lines))
        else:
            for line in lines:
                f.write(line)
    return len(lines)


def alloc(b):
    size = 64 * 1024 * 1024
    if b:
        buf = bytearray(size)
        for i in range(50):
            buf[::4096] = bytes([i % 256]) * (size // 4096)
        return len(buf)
    total = 0
    for i in range(50):
        buf = bytearray(size)
        buf[::4096] = bytes([i % 256]) * (size // 4096)
        total += len(buf)
    return total


def algorithmic(b):
    xs = list(range(6000)) + [17]
    if b:
        seen, dup = set(), 0
        for x in xs:
            dup += x in seen
            seen.add(x)
        return dup
    return sum(1 for i, x in enumerate(xs) if x in xs[:i])


def _work(k):
    return sum(i * i for i in range(k * 3_000_000, (k + 1) * 3_000_000))


def parallel(b):
    if b:
        from multiprocessing import Pool
        with Pool(2) as p:
            return sum(p.map(_work, range(4)))
    return sum(_work(k) for k in range(4))


def async_io(b):
    if b:
        ts = [threading.Thread(target=time.sleep, args=(0.05,)) for _ in range(20)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
    else:
        for _ in range(20):
            time.sleep(0.05)
    return 20


def lazy_import(b):
    if not b:
        import asyncio, decimal, email.mime.multipart, http.client, xml.etree.ElementTree  # noqa: F401,E401
        import unittest, argparse, logging as lg, sqlite3, tarfile, zipfile  # noqa: F401,E401
    return 0


def stat_loop(b):
    if b:
        ok = os.path.exists(DATA)
        return sum(ok for _ in range(5000))
    return sum(os.path.exists(DATA) for _ in range(5000))


if __name__ == "__main__":
    if not os.path.exists(DATA):
        with open(DATA, "w") as f:
            f.write("data line\n" * 2000)
    name, variant = sys.argv[1], sys.argv[2]
    print(globals()[name](variant == "b"))
