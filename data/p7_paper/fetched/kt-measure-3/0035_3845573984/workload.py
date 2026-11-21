import hashlib, logging, os, struct, wave, math
import numpy as np
import chirp.audio_feedback as af_mod
from chirp.audio_feedback import AudioFeedback

D = "/tmp/kt_21"
os.makedirs(D, exist_ok=True)

def make_wav(path, n, ch, rate, seed):
    rng = np.random.default_rng(seed)
    data = (rng.standard_normal(n * ch) * 3000).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(ch); wf.setsampwidth(2); wf.setframerate(rate)
        wf.writeframes(data.tobytes())

paths = []
for i in range(8):
    p = os.path.join(D, f"s{i}.wav")
    if not os.path.exists(p):
        make_wav(p, 20000 + 1000 * i, 1 + (i % 2), 16000 + 8000 * (i % 3), i)
    paths.append(p)

# Stand-in for audio hardware (sounddevice): records what would be played
class FakeSD:
    def __init__(self):
        self.h = hashlib.sha256(); self.n = 0
    def play(self, data, rate):
        self.n += 1
        self.h.update(str((data.shape, int(data.sum()), rate)).encode())

class FakeWinsound:
    SND_FILENAME = 0x20000; SND_ASYNC = 0x1; SND_MEMORY = 0x4; MB_ICONHAND = 0x10
    def __init__(self):
        self.n = 0
    def PlaySound(self, data, flags):
        self.n += 1
    def MessageBeep(self, t):
        self.n += 1

logger = logging.getLogger("kt"); logger.addHandler(logging.NullHandler()); logger.propagate = False

sd = FakeSD()
af_mod.sd = sd
af_mod.winsound = None
a = AudioFeedback(logger=logger, enabled=True)
for r in range(1200):
    a.play_start(); a.play_stop()
    for p in paths:
        a.play_start(p)
        a.play_error(p)
    a.play_error(os.path.join(D, "missing.wav"))
    a.play_stop(os.path.join(D, "missing.wav"))

ws = FakeWinsound()
af_mod.sd = None
af_mod.winsound = ws
b = AudioFeedback(logger=logger, enabled=True)
for r in range(600):
    b.play_start(); b.play_stop()
    for p in paths:
        b.play_start(p)
        b.play_error(p)

print("sd plays", sd.n, "winsound calls", ws.n)
print(hashlib.sha256((sd.h.hexdigest() + str(ws.n)).encode()).hexdigest())
