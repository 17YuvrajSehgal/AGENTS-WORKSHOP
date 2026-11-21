import asyncio, hashlib, json, logging
import numpy as np
try:
    from sleeper_detection.probes.probe_detector import ProbeDetector
except ImportError:  # head installs the package as packages.sleeper_detection
    from packages.sleeper_detection.probes.probe_detector import ProbeDetector

logging.disable(logging.CRITICAL)


def make_data(rng, n, d, shift):
    direction = rng.standard_normal(d)
    direction /= np.linalg.norm(direction)
    pos = rng.standard_normal((n, d)) + shift * direction
    neg = rng.standard_normal((n, d)) - shift * direction
    return pos, neg


async def main():
    rng = np.random.default_rng(1234)
    det = ProbeDetector(model=None)
    out = []
    for i in range(16):
        layer = det.config["ensemble_layers"][i % 4]
        pos, neg = make_data(rng, 300, 256, 0.15 + 0.02 * (i % 5))
        probe = await det.train_probe(f"feat_{i}", pos, neg, layer, "synthetic")
        out.append((probe.probe_id, round(probe.auc_score, 6), round(probe.threshold, 6),
                    round(probe.true_positive_rate, 6), round(probe.false_positive_rate, 6)))
        test = rng.standard_normal((20, 256))
        for v in test:
            ds = await det.detect(v, layer)
            out.append([(d.probe_id, round(d.confidence, 6), bool(d.detected)) for d in ds][:3])
    stats = det.get_probe_statistics()
    out.append(json.loads(json.dumps(stats, default=str)))
    print(len(det.probes), "probes")
    print(hashlib.sha256(json.dumps(out, sort_keys=True, default=str).encode()).hexdigest())


asyncio.run(main())
