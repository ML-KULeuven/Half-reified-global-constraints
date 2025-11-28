import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, all_pairs

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal

class CustomNoOverlap(CustomGlobal, cp.NoOverlap):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "custom_nooverlap"

        assert self.args[2] is None, "end should be None after refactoring, are you on the `no_end_cumulative` branch of CPMpy?"
        self.cpm_global = cp.NoOverlap

class NativeNoOverlap(AuxGlobal, NativeGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_nooverlap"

class BinaryDecomposedNoOverlap(CustomNoOverlap):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "timed_nooverlap"

    def iftrue(self):
        start, dur, end = self.args
        assert end is None, f"end should be None after refactoring, but got {end}"
        start = list(start)
        dur = list(dur)
        njobs = len(start)

        cons = []

        end = [start[i] + dur[i] for i in range(njobs)]
        for i,j in all_pairs(list(range(len(start)))):
            cons.append((end[i] <= start[j]) | (end[j] <= start[i]))
    
        return cons

    def iffalse(self):
        return []
    def toplevel(self):
        return []

class NoOverlapAuxHalfReif(AuxGlobal, CustomNoOverlap):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_nooverlap"

        self.to_replace = [0,1]

class NoOverlapAuxHalfReifDummy(NoOverlapAuxHalfReif):

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if self.sol is None:
            return []
        self.check_if_sat()
        if self.sol is None:
            return []

        new_start, new_dur = self.new_args
        return flatlist([cp.cpm_array(new_start) == self.sol[0],
                         cp.cpm_array(new_dur) == self.sol[1]])