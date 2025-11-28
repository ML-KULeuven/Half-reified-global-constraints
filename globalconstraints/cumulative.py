import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, all_pairs

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal
from cpmpy.solvers.solver_interface import ExitStatus

"""
**WARNING**
The classes below are not a drop-in replacement for cpmpy.Cumulative.
The decompositions implemented are only valid when the global constraint occurs in positive context!
"""

class CustomCumulative(CustomGlobal, cp.Cumulative):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "custom_cumulative"

        assert self.args[2] is None, "end should be None after refactoring, are you on the `no_end_cumulative` branch of CPMpy?"
        self.cpm_global = cp.Cumulative

class NativeCumulative(CustomCumulative, NativeGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_cumulative"

class TaskDecomposedCumulative(CustomCumulative, cp.Cumulative):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "taskd_cumulative"

    def iftrue(self):

        start, dur, end, demand, cap = self.args
        start = list(start)
        dur = list(dur)
        assert end is None, "end should be None after refactoring"

        njobs = len(start)
        cons = []
        
        end = [start[i] + dur[i] for i in range(njobs)]
        # ensure task can only start if no enough capacity left
        for i in range(njobs):
            running_demand = cp.sum([demand[j] * ((start[j] <= start[i]) & (end[j] > start[i])) for j in range(njobs) if i != j])
            cons.append(running_demand + demand[i] <= cap)

        return cons

    def iffalse(self):
        return []

    def toplevel(self):
        return []


class CumulativeAuxHalfReif(AuxGlobal, CustomCumulative):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_cumulative"

        self.to_replace = [0,1,3,4]
        self.cpm_global = cp.Cumulative

class CumulativeAuxHalfReifDummy(CumulativeAuxHalfReif):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_cumulative_dummy"

        self.to_replace = [0,1,3,4]
        self.cpm_global = cp.Cumulative

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if self.sol is None:
            return []

        assert len(self.sol) == len(self.args) == len(self.new_args)
        return flatlist([na == val for na, val in zip(self.new_args, self.sol)])

class CumulativeAuxHalfReifMinimal(AuxGlobal, CustomCumulative):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_cumulative_minimal"

        # start, dur, demand, cap, only replace cap
        self.to_replace = [4]
        self.cpm_global = cp.Cumulative

    def get_aux_vars(self):
        start, dur, end, demand, cap = self.args
        max_demand = sum(get_bounds(demand)[1])
        return [None, None, None, None, cp.intvar(0, max(get_bounds(cap)[1], max_demand))]

class CumulativeAuxHalfReifMinimalDummy(CumulativeAuxHalfReifMinimal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_cumulative_dummy_minimal"

        # start, dur, demand, cap, only replace cap
        self.to_replace = [4]
        self.cpm_global = cp.Cumulative

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if self.sol is None:
            return []
        return [self.sol[-1] == self.new_args[-1]]