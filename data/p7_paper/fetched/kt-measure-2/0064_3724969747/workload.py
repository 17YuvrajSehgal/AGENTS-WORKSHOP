import hashlib
import os
os.makedirs("/tmp/kt_13664", exist_ok=True)
os.environ["CACHEDB"] = "/tmp/kt_13664/cache.db"
from tinygrad import Tensor, Variable, Device
from tinygrad.engine.schedule import schedule_cache

Device.DEFAULT = "CPU"
results = []
schedule_cache.clear()
v = Variable('v', 1, 1000)
w = Variable('w', 1, 1000)
x = Tensor.arange(64).float().reshape(8, 8).contiguous().realize()
y = Tensor.ones(8, 8).contiguous().realize()

for i in range(1, 121):
  t1 = (x + Tensor(v.bind(i))).sum()
  results.append(t1.item())
  t2 = ((x * Tensor(v.bind(i))) @ (y + Tensor(w.bind(i * 3 % 997 + 1)))).relu().sum(axis=1)
  results.append(tuple(t2.tolist()))
  t = x + Tensor(v.bind(i % 100 + 1))
  sched, var_vals = t.schedule_with_vars()
  results.append((len(sched), tuple(sorted(var_vals.items()))))

print(len(results))
print(hashlib.sha256(repr(results).encode()).hexdigest())
