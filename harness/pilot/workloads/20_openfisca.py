# openfisca-core #1367 "perf(as_of): fix quadratic reconstruction in forward
# simulations". Pilot workload (hand-written, experimenter has read the PR):
# an as_of variable for 50,000 people over 240 months; each month 1% of
# values change; set_input then get_array (forward-sequential), using the
# same minimal fixtures as the PR's tests. Last line = SHA-256 of all reads.
import hashlib

import numpy

from openfisca_core.entities import Entity
from openfisca_core.holders import Holder
from openfisca_core.periods import DateUnit, period
from openfisca_core.populations import Population
from openfisca_core.variables import Variable

_entity = Entity("person", "persons", "", "")


class AsOfVar(Variable):
    entity = _entity
    definition_period = DateUnit.MONTH
    value_type = int
    as_of = "start"


N, MONTHS = 50_000, 240
population = Population(_entity)
population.simulation = None
population.count = N
holder = Holder(AsOfVar(), population)

rng = numpy.random.default_rng(42)
values = rng.integers(0, 1000, N)
h = hashlib.sha256()
for m in range(MONTHS):
    p = period(f"{2000 + m // 12}-{m % 12 + 1:02d}")
    idx = rng.choice(N, N // 100, replace=False)
    values = values.copy()
    values[idx] = rng.integers(0, 1000, idx.size)
    holder.set_input(p, values)
    h.update(holder.get_array(p).tobytes())
print(MONTHS)
print(h.hexdigest())
