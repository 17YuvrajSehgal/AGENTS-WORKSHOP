import hashlib
import os
import threading

os.environ.pop("OTEL_SDK_DISABLED", None)

# Stand-in for the OTLP network exporter: the real HTTP exporter class, but its
# shutdown fails (simulating a network error while closing the exporter
# session). No spans are emitted, so nothing is ever sent.
import opentelemetry.exporter.otlp.proto.http.trace_exporter as _otlp

_RealExporter = _otlp.OTLPSpanExporter


class FailingShutdownExporter(_RealExporter):
    _failed = False

    def shutdown(self):
        super().shutdown()
        if self._failed:
            return
        self._failed = True
        raise ConnectionError("exporter connection error on shutdown")


_otlp.OTLPSpanExporter = FailingShutdownExporter
from crewai.telemetry import Telemetry

results = []
instances = []

# Sequential creation (e.g. agents/crews created repeatedly in a server)
for i in range(300):
    t = Telemetry()
    results.append((t.ready, t.trace_set))
    instances.append(t)

# Concurrent creation from threads
lock = threading.Lock()
def worker():
    for _ in range(20):
        t = Telemetry()
        with lock:
            results.append((t.ready, t.trace_set))
            instances.append(t)

threads = [threading.Thread(target=worker) for _ in range(10)]
for th in threads:
    th.start()
for th in threads:
    th.join()

# Cleanup: shut down the telemetry provider(s) via the class destructor when
# available (head), otherwise shut the provider down directly (base).
seen = {}
for t in instances:
    seen[id(t)] = t
for t in seen.values():
    d = Telemetry.__dict__.get("__del__")
    if d is not None:
        d(t)
    else:
        try:
            t.provider.shutdown()
        except ConnectionError:
            pass

print("instances created:", len(results))
print("ready count:", sum(1 for r, _ in results if r))
print(hashlib.sha256(repr(sorted(results)).encode()).hexdigest())
