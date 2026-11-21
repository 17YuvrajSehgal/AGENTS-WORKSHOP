import asyncio, hashlib, os, socket, sys, pickle
here = os.path.dirname(os.path.abspath(sys.executable))
src = os.path.join(os.path.dirname(os.path.dirname(here)), "src", "server", "python")
sys.path.insert(0, src)
import rpc_reader
from rpc_reader import RpcFileTransport, prepare_peer_readloop, RpcStreamTransport, RpcPickleStreamTransport


class Service:
    def echo(self, x, n):
        return [x, n * 2]

    def bytes_op(self, b):
        return bytes(reversed(b))


async def run_pair(transport_cls, n_calls):
    loop = asyncio.get_running_loop()
    writers = []
    if transport_cls is RpcFileTransport:
        a_r, b_w = os.pipe()
        b_r, a_w = os.pipe()
        ta, tb = RpcFileTransport(a_r, a_w), RpcFileTransport(b_r, b_w)
    else:
        s1, s2 = socket.socketpair()
        r1, w1 = await asyncio.open_connection(sock=s1)
        r2, w2 = await asyncio.open_connection(sock=s2)
        writers = [w1, w2]
        ta, tb = transport_cls(r1, w1), transport_cls(r2, w2)
    peerA, readA = await prepare_peer_readloop(loop, ta)
    peerB, readB = await prepare_peer_readloop(loop, tb)
    peerA.params["svc"] = Service()
    tA = asyncio.ensure_future(readA())
    tB = asyncio.ensure_future(readB())
    svc = await peerB.getParam("svc")
    h = hashlib.sha256()
    for batch in range(n_calls // 50):
        coros = []
        for i in range(50):
            k = batch * 50 + i
            if k % 3 == 0:
                coros.append(svc.bytes_op(bytes([(k + j) % 256 for j in range(64)])))
            else:
                coros.append(svc.echo({"k": k, "s": "x" * (k % 17)}, k))
        res = await asyncio.gather(*coros)
        for r in res:
            h.update(repr(r).encode() if not isinstance(r, (bytes, bytearray)) else bytes(r))
    for t in (tA, tB):
        t.cancel()
    for w in writers:
        w.close()
    if transport_cls is RpcFileTransport:
        os.close(a_w); os.close(b_w)
    await asyncio.gather(tA, tB, return_exceptions=True)
    return h.hexdigest()


async def main():
    out = []
    for cls in (RpcStreamTransport, RpcPickleStreamTransport):
        out.append(await run_pair(cls, 10000))
    out.append(await run_pair(RpcFileTransport, 2000))
    return out


res = asyncio.run(main())
for r in res:
    print(r)
print(hashlib.sha256("".join(res).encode()).hexdigest())
