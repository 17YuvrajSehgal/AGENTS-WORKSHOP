import asyncio, base64, hashlib, json, logging, os
os.environ.setdefault("CARTESIA_API_KEY", "dummy")
import websockets
import websockets.protocol
import websockets.exceptions
from websockets.frames import Close
from bolna.synthesizer.cartesia_synthesizer import CartesiaSynthesizer
logging.disable(logging.CRITICAL)


class FakeCartesiaWS:
    """In-process stand-in for the Cartesia TTS websocket (external service)."""
    def __init__(self):
        self.q = asyncio.Queue()
        self.state = websockets.protocol.State.OPEN
        self.sent = 0

    async def send(self, msg):
        p = json.loads(msg)
        self.sent += 1
        t = p.get("transcript", "")
        ctx = p.get("context_id")
        if t:
            raw = hashlib.sha256(t.encode()).digest() * 8
            for i in range(0, len(raw), 64):
                await self.q.put(json.dumps({"context_id": ctx, "data": base64.b64encode(raw[i:i+64]).decode()}))
        else:
            await self.q.put(json.dumps({"context_id": ctx, "done": True}))

    async def recv(self):
        m = await self.q.get()
        if m is None:
            raise websockets.exceptions.ConnectionClosedOK(Close(1000, ""), Close(1000, ""), True)
        return m

    async def close(self):
        self.state = websockets.protocol.State.CLOSED


class TM:
    def is_sequence_id_in_current_ids(self, sid):
        return True


async def run_once(n_turns, seqs_per_turn, h):
    s = CartesiaSynthesizer("voice", None, task_manager_instance=TM())
    ws = FakeCartesiaWS()
    s.websocket_holder["websocket"] = ws
    # unsolicited audio before any push (meta_info is None)
    await ws.q.put(json.dumps({"context_id": "pre", "data": base64.b64encode(b"\x7f" * 32).decode()}))
    out = []

    async def consume():
        async for pkt in s.generate():
            m = pkt["meta_info"] or {}
            out.append((len(pkt["data"]), m.get("sequence_id"), m.get("is_first_chunk"),
                        m.get("end_of_synthesizer_stream"), m.get("format")))

    ctask = asyncio.create_task(consume())
    ctx_changes = 0
    for turn in range(n_turns):
        for seq in range(seqs_per_turn):
            prev = s.context_id
            for k in range(3):
                await s.push({"meta_info": {"turn_id": turn, "sequence_id": turn * 100 + seq,
                                            "end_of_llm_stream": k == 2},
                              "data": f"turn {turn} seq {seq} part {k} hello world."})
                await s.sender_task
            if s.context_id != prev:
                ctx_changes += 1
    await ws.q.put(None)
    await ctask
    h.update(repr((ctx_changes, ws.sent, s.synthesized_characters, out)).encode())
    return ctx_changes, len(out)


async def main():
    h = hashlib.sha256()
    for r in range(40):
        res = await run_once(10, 10, h)
    print("last run:", res)
    print(h.hexdigest())

asyncio.run(main())
