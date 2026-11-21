import base64
import copy
import hashlib
import random
from io import BytesIO

from PIL import Image

from prime_rl.orchestrator import trajectories as T

rng = random.Random(1234)


def make_b64(i):
    img = Image.new("RGB", (48, 48), (i * 7 % 256, i * 13 % 256, i * 29 % 256))
    px = img.load()
    for _ in range(40):
        px[rng.randrange(48), rng.randrange(48)] = (rng.randrange(256), rng.randrange(256), rng.randrange(256))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


IMAGES = [make_b64(i) for i in range(64)]

import os
FILE_DIR = "/tmp/kt_2006/assets/images"
os.makedirs(FILE_DIR, exist_ok=True)
FILE_URLS = []
for i in range(0, 64, 4):
    path = os.path.join(FILE_DIR, f"img{i}.png")
    data = base64.b64decode(IMAGES[i])
    if not os.path.exists(path) or open(path, "rb").read() != data:
        with open(path, "wb") as f:
            f.write(data)
    FILE_URLS.append("file://" + path)


def make_rollouts(n_rollouts, steps):
    rollouts = []
    for r in range(n_rollouts):
        traj = []
        for s in range(steps):
            content = [{"type": "text", "text": f"rollout {r} step {s}"}]
            for k in range(1 + (r + s) % 3):
                idx = (r * 5 + s * 3 + k) % len(IMAGES)
                content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{IMAGES[idx]}"}})
            if (r + s) % 2 == 0:
                content.append({"type": "image_url", "image_url": {"url": FILE_URLS[(r + s) % len(FILE_URLS)]}})
            # a non-image url and a plain text message
            content.append({"type": "image_url", "image_url": {"url": "http://example.invalid/x.png"}})
            prompt = [{"role": "system", "content": "sys"}, {"role": "user", "content": content}]
            traj.append({"prompt": prompt, "completion": []})
        rollouts.append({"example_id": r // 2, "trajectory": traj})
    return rollouts


h = hashlib.sha256()
template = make_rollouts(40, 6)

for it in range(25):
    rollouts = copy.deepcopy(template)
    examples = list(enumerate(rollouts))
    all_images, per_ex = T._extract_images_from_examples(examples)
    h.update(str(len(all_images)).encode())
    for img in all_images:
        h.update(img.convert("RGB").tobytes())
    h.update(repr(sorted(per_ex.items())).encode())
    # stripped placeholders
    for _, out in examples:
        for step in out["trajectory"]:
            for msg in step["prompt"]:
                if isinstance(msg["content"], list):
                    for item in msg["content"]:
                        if item.get("type") == "image_url":
                            h.update(item["image_url"]["url"].encode())

    # small example below parallel threshold
    small = copy.deepcopy(make_rollouts(1, 1)) if it == 0 else None
    if small:
        imgs, idx = T._extract_images_from_examples(list(enumerate(small)))
        h.update(repr(idx).encode())

    # per-message extraction
    for step in template[it % len(template)]["trajectory"]:
        pairs = T._extract_images_from_messages(step["prompt"])
        for img, key in pairs:
            h.update(img.convert("RGB").tobytes())
            h.update(hashlib.sha256(key.encode()).digest())

print(h.hexdigest())
