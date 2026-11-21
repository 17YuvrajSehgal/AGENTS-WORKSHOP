import hashlib
import numpy as np
import mbi
from mbi import Domain, Factor, CliqueVector, MarkovRandomField

np.random.seed(0)
domain_dict = {f"a{i}": s for i, s in enumerate([3, 40, 12, 15, 2, 30, 5, 8, 11, 8, 2, 3, 20, 14, 17, 6, 2, 13, 6, 10])}
cliques = [("a0", "a1"), ("a1", "a2"), ("a2", "a3"), ("a1", "a4"), ("a4", "a5"),
           ("a5", "a6"), ("a6", "a7"), ("a5", "a8"), ("a8", "a9"), ("a9", "a10"),
           ("a10", "a11"), ("a11", "a12"), ("a12", "a13"), ("a13", "a14"), ("a3", "a15"),
           ("a15", "a16"), ("a16", "a17"), ("a17", "a18"), ("a18", "a19"), ("a7", "a19")]
domain = Domain.fromdict(domain_dict)
# Build tree-consistent marginals in numpy (root a0, edges parent->child).
# Note: ("a7","a19") closes a cycle, so drop it to keep a tree.
cliques = cliques[:-1]
probs = {"a0": np.random.dirichlet(np.ones(domain_dict["a0"]))}
arrays = {}
for p, c in cliques:
    cond = np.random.dirichlet(np.ones(domain_dict[c]), size=domain_dict[p])
    joint = probs[p][:, None] * cond
    probs[c] = joint.sum(axis=0)
    arrays[(p, c)] = Factor(domain.project((p, c)), joint)
marginals = CliqueVector(domain, cliques, arrays)
potentials = marginals
model = MarkovRandomField(potentials=potentials, marginals=marginals, total=1)

h = hashlib.sha256()
for method in ["round", "sample"]:
    for N in [1000, 20000, 100000]:
        np.random.seed(N)
        syn = model.synthetic_data(rows=N, method=method)
        for cl in [(c,) for c in domain.attributes] + cliques:
            v = np.asarray(syn.project(cl).datavector())
            h.update(v.astype(np.int64).tobytes())
        print(method, N, int(np.asarray(syn.project(cliques[0]).datavector()).sum()))

# repo test
dom = Domain(['A', 'B'], [10, 10])
np.random.seed(1)
f = Factor.random(dom).normalize(1.0)
m = CliqueVector(dom, [('A', 'B')], {('A', 'B'): f})
mdl = MarkovRandomField(potentials=m, marginals=m, total=1000)
s = mdl.synthetic_data(rows=1000, method="round")
h.update(np.asarray(s.project(('A', 'B')).datavector()).astype(np.int64).tobytes())
print(h.hexdigest())
