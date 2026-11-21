import hashlib, io, os, pickle, types
import numpy as np
from PIL import Image
from tapnet.tapvid import evaluation_datasets as ed

D = '/tmp/kt_153'
os.makedirs(D, exist_ok=True)
rng = np.random.RandomState(0)

def make_example(nf, h, w, npts, jpeg):
  video = rng.randint(0, 256, size=(nf, h, w, 3)).astype(np.uint8)
  if jpeg:
    fr = []
    for f in video:
      b = io.BytesIO(); Image.fromarray(f).save(b, format='JPEG', quality=90)
      fr.append(b.getvalue())
    video = fr
  pts = rng.rand(npts, nf, 2).astype(np.float32)
  occ = rng.rand(npts, nf) < 0.3
  return {'video': video, 'points': pts, 'occluded': occ}

davis_path = os.path.join(D, 'davis.pkl')
if not os.path.exists(davis_path):
  davis = {f'vid{i}': make_example(24, 120, 160, 60, False) for i in range(6)}
  with open(davis_path, 'wb') as f: pickle.dump(davis, f)
kin_dir = os.path.join(D, 'kinetics'); os.makedirs(kin_dir, exist_ok=True)
kin_path = os.path.join(kin_dir, '0000_of_0010.pkl')
if not os.path.exists(kin_path):
  data = [make_example(24, 120, 160, 60, True) for _ in range(5)] + [make_example(2, 120, 160, 20, True)]
  with open(kin_path, 'wb') as f: pickle.dump(data, f)

csv_dir = os.path.join(D, 'csv'); os.makedirs(csv_dir, exist_ok=True)
csv_path = os.path.join(csv_dir, 'ann.csv')
if not os.path.exists(csv_path):
  import mediapy as media
  rows = []
  for i in range(3):
    t = np.linspace(0, 1, 20)[:, None, None]
    yy, xx = np.mgrid[0:96, 0:128]
    v = ((np.sin(xx / 9.0 + 6 * t + i) * 0.5 + 0.5) * 255)[..., None].repeat(3, -1).astype(np.uint8)
    v = np.broadcast_to(v, (20, 96, 128, 3)).copy()
    media.write_video(os.path.join(csv_dir, f'v{i}.mp4'), v, fps=10)
    for p in range(15):
      vals = []
      for fi in range(20):
        vals += [f'{rng.rand():.4f}', f'{rng.rand():.4f}', str(int(rng.rand() < 0.3))]
      rows.append(','.join([f'v{i}'] + vals))
  with open(csv_path, 'w') as f: f.write('\n'.join(rows) + '\n')

h = hashlib.sha256()
def add(el):
  for k, v in sorted(el.items()):
    for kk, vv in sorted(v.items()):
      a = np.asarray(vv)
      h.update(f'{k}/{kk}{a.shape}'.encode())
      h.update(np.round(a.astype(np.float64), 4).tobytes())

for rep in range(2):
 for qm in ('strided', 'first'):
  for el in ed.create_davis_dataset(davis_path, query_mode=qm, resolution=(128, 128)):
    add(el)
  for el in ed.create_kinetics_dataset(kin_dir, query_mode=qm, resolution=(128, 128)):
    add(el)

  for el in ed.create_csv_dataset('robotap', csv_path, csv_dir, query_mode=qm, resolution=(64, 64)):
    add(el)

for _ in range(3):
  v = rng.randint(0, 256, size=(16, 100, 140, 3)).astype(np.uint8)
  h.update(ed.resize_video(v, (64, 64)).tobytes())
print(h.hexdigest())
