import asyncio, hashlib, warnings, logging
warnings.filterwarnings("ignore")
import azure.cognitiveservices.speech as speechsdk
from bolna.synthesizer import azure_synthesizer as az
logging.disable(logging.CRITICAL)

N_MESSAGES = 10
N_CHUNKS = 16
CHUNK = 320


class _Signal:
    def __init__(self):
        self.handlers = []

    def connect(self, fn):
        self.handlers.append(fn)

    def fire(self, evt):
        for h in list(self.handlers):
            h(evt)


class _Res:
    def __init__(self, data):
        self.audio_data = data


class _Evt:
    def __init__(self, data):
        self.result = _Res(data)


class _Future:
    def __init__(self, t):
        self._t = t

    def get(self):
        return None


class FakeSpeechSynthesizer:
    """Local stand-in for the Azure cloud TTS client: streams deterministic
    PCM chunks from a background thread like the real SDK does."""

    def __init__(self, speech_config=None, audio_config=None):
        self.synthesizing = _Signal()
        self.synthesis_completed = _Signal()

    def _run(self, text):
        seed = hashlib.sha256(text.encode()).digest()
        for i in range(N_CHUNKS):
            data = (hashlib.sha256(seed + bytes([i])).digest() * (CHUNK // 32 + 1))[:CHUNK]
            self.synthesizing.fire(_Evt(data))
        self.synthesis_completed.fire(_Evt(b""))

    def speak_text_async(self, text):
        # Events are delivered before the call returns (deterministic ordering);
        # the code under test still marshals them via run_coroutine_threadsafe.
        self._run(text)
        return _Future(None)

    speak_ssml_async = speak_text_async


speechsdk.SpeechSynthesizer = FakeSpeechSynthesizer


class TM:
    def is_sequence_id_in_current_ids(self, sid):
        return True


N_CALLS = 150


async def run_call(call_idx, h):
    synth = az.AzureSynthesizer("JennyNeural", "en-US", model="", stream=True,
                                caching=True, synthesizer_key="dummy", region="eastus",
                                speed=(1.2 if call_idx % 3 == 0 else None),
                                task_manager_instance=TM())
    synth.loop = asyncio.get_running_loop()
    texts = [f"Call {call_idx} sentence {i}, hello there." for i in range(N_MESSAGES)]
    texts.append(texts[0])  # cache hit path
    packets = []

    async def consume():
        async for p in synth.generate():
            packets.append(p)

    task = asyncio.create_task(consume())
    done_chars = 0
    for i, t in enumerate(texts):
        await synth.push({"meta_info": {"sequence_id": 1, "end_of_llm_stream": (i % 4 == 3)}, "data": t})
        if i < N_MESSAGES:
            done_chars += len(t)
        while synth.synthesized_characters < done_chars or synth.internal_queue.qsize():
            if task.done():
                task.result()
            await asyncio.sleep(0)
    for _ in range(5):
        await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await synth.cleanup()

    per_text = {}
    for p in packets:
        lst = per_text.setdefault(p["meta_info"]["text"], [])
        if p["data"] not in lst:
            lst.append(p["data"])
    for t in texts[:N_MESSAGES]:
        h.update(t.encode())
        for c in sorted(per_text.get(t, [])):
            h.update(c)
    return len(per_text), synth.synthesized_characters


async def main():
    h = hashlib.sha256()
    nt = nc = 0
    for c in range(N_CALLS):
        a, b = await run_call(c, h)
        nt += a
        nc += b
    print("texts:", nt, "chars:", nc)
    print(h.hexdigest())


asyncio.run(main())
