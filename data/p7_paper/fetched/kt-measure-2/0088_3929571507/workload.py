import hashlib
import importlib.util
import os
import sys
import sysconfig

# Load the `z3` package from this side's source tree (byte-identical to the
# installed copy) so line coverage maps to src/api/python/z3/*.py. The build
# generates z3core.py, z3consts.py and lib/libz3.so only in the installed package,
# so that directory is added to the package search path after the source dir.
_src_z3 = os.path.join(os.path.dirname(sys.prefix), "src", "src", "api", "python", "z3")
_inst_z3 = os.path.join(sysconfig.get_paths()["purelib"], "z3")
if os.path.isfile(os.path.join(_src_z3, "__init__.py")) and os.path.isfile(os.path.join(_inst_z3, "z3core.py")):
    _spec = importlib.util.spec_from_file_location(
        "z3", os.path.join(_src_z3, "__init__.py"),
        submodule_search_locations=[_src_z3, _inst_z3])
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["z3"] = _mod
    _spec.loader.exec_module(_mod)

from z3 import *
from z3.z3num import Numeral

out = []


def rec(x):
    out.append(str(x))


class Prop(UserPropagateBase):
    def __init__(self, s=None, ctx=None):
        UserPropagateBase.__init__(self, s, ctx)

    def push(self):
        pass

    def pop(self, n):
        pass

    def fresh(self, new_ctx):
        return Prop(None, new_ctx)


def noop(*a):
    pass


ROUNDS = 60
for r in range(ROUNDS):
    # RatVal
    for a in range(1, 30):
        rec(RatVal(a + r, a + 3))

    # Goal.__getitem__
    xs = Ints(" ".join("x%d" % i for i in range(20)))
    g = Goal()
    for i, x in enumerate(xs):
        g.add(x > i + r)
    for i in range(len(g)):
        rec(g[i])

    # AstVector.__setitem__
    v = AstVector()
    for x in xs:
        v.push(x)
    for i in range(len(v)):
        v[i] = xs[(i + r) % len(xs)] + 1
    rec(v)

    # ModelRef.__getitem__
    s = Solver()
    f = Function("f", IntSort(), IntSort())
    s.add([x == i + r for i, x in enumerate(xs[:10])])
    s.add(f(xs[0]) == 7)
    s.check()
    m = s.model()
    for i in range(len(m)):
        rec(m[i])

    # ApplyResult.__getitem__
    a, b = Ints("a b")
    gg = Goal()
    gg.add(Or(a == 0, a == 1), Or(b == 0, b == 1), a > b + r % 2 - 1)
    res = Then(Tactic("split-clause"), Tactic("split-clause"))(gg)
    for i in range(len(res)):
        rec(res[i])

    # UserPropagateBase add_* methods
    for k in range(10):
        ps = Solver()
        p = Prop(ps)
        p.add_fixed(noop)
        p.add_created(noop)
        p.add_final(noop)
        p.add_eq(noop)
        p.add_diseq(noop)
        p.add_decide(noop)
        p.add_on_binding(noop)
        for x in xs[:5]:
            p.add(x)
        # re-registering a callback is an error (AssertionError on base,
        # Z3Exception on head); record only that it failed
        for meth in (p.add_fixed, p.add_created, p.add_final, p.add_eq,
                     p.add_diseq, p.add_decide, p.add_on_binding):
            try:
                meth(noop)
                rec("ok")
            except (AssertionError, Z3Exception):
                rec("err")
        rec(k)
        del p

    # z3num Numeral
    for i in range(1, 40):
        n = Numeral("%d/%d" % (i + r, i + 7))
        rec(n.numerator().as_long())
        rec(n.denominator().as_long())
        rec(n.as_fraction())
        rec(Numeral(i * 13 + r).as_long())
    # non-rational / non-integer numerals: error paths
    irr = Numeral(Sqrt(RealVal(2 + r % 5)))
    half = Numeral("%d/2" % (2 * r + 1))
    for fn in (irr.numerator, irr.denominator, irr.as_fraction, half.as_long):
        try:
            fn()
            rec("ok")
        except (AssertionError, Z3Exception):
            rec("err")

h = hashlib.sha256("\n".join(out).encode()).hexdigest()
print(len(out))
print(h)
