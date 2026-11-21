import hashlib, warnings
warnings.filterwarnings("ignore")
import numpy as np
import cvxpy as cp
import torch
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from cvxpylayers.torch import CvxpyLayer as TorchLayer
from cvxpylayers.jax import CvxpyLayer as JaxLayer

torch.manual_seed(0)
rng = np.random.default_rng(0)
torch.set_default_dtype(torch.float64)

n, m = 8, 12
x = cp.Variable(n)
A = cp.Parameter((m, n))
b = cp.Parameter(m)
prob = cp.Problem(cp.Minimize(cp.sum_squares(A @ x - b) + 0.1 * cp.sum_squares(x)), [x >= -1, x <= 1])
assert prob.is_dpp()

tl = TorchLayer(prob, parameters=[A, b], variables=[x], solver="DIFFCP")
jl = JaxLayer(prob, parameters=[A, b], variables=[x], solver="DIFFCP")

c = cp.Parameter(n)
lp = cp.Problem(cp.Minimize(c @ x), [x >= 0, x <= 1])
ml = TorchLayer(lp, parameters=[c], variables=[x], solver="MPAX")

h = hashlib.sha256()
def add(arr):
    h.update(np.round(np.asarray(arr, dtype=np.float64), 4).tobytes())

for it in range(12):
    A_t = torch.randn(m, n, requires_grad=True)
    b_t = torch.randn(m, requires_grad=True)
    (sol,) = tl(A_t, b_t, solver_args={"eps": 1e-9})
    sol.sum().backward()
    add(sol.detach().numpy()); add(A_t.grad.numpy()); add(b_t.grad.numpy())

    Ab = torch.randn(4, m, n, requires_grad=True)
    bb = torch.randn(4, m, requires_grad=True)
    (solb,) = tl(Ab, bb, solver_args={"eps": 1e-9})
    (solb ** 2).sum().backward()
    add(solb.detach().numpy()); add(Ab.grad.numpy()); add(bb.grad.numpy())

    Aj = jnp.asarray(rng.standard_normal((m, n)))
    bj = jnp.asarray(rng.standard_normal(m))
    (solj,) = jl(Aj, bj, solver_args={"eps": 1e-9})
    add(solj)
    g = jax.grad(lambda a, bb_: jl(a, bb_, solver_args={"eps": 1e-9})[0].sum(), argnums=1)(Aj, bj)
    add(g)

for it in range(5):
    (sm,) = ml(torch.randn(n))
    add(np.round(sm.detach().numpy().astype(np.float64), 2))
print(h.hexdigest())
