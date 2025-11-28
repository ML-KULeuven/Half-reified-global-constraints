import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, all_pairs

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal
from cpmpy.solvers.solver_interface import ExitStatus

class CustomRegular(CustomGlobal, cp.Regular):

    def __init__(self, *args, **kwargs):
        super.__init__(*args, **kwargs)
        self.name = "custom_regular"

class NativeRegular(CustomRegular, NativeGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "native_regular"

class DecomposedRegular(CustomRegular, cp.Regular):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "decomposed_regular"

        self.cpm_regular = cp.Regular(*args, **kwargs)
        self.constraining, self.defining = self.cpm_regular.decompose()

    def iftrue(self):
        return self.constraining

    def toplevel(self):
        return self.defining

class RegularAuxHalfReif(AuxGlobal, CustomRegular):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "aux_regular"
        self.cpm_global = cp.Regular
        self.to_replace = [0]

class RegularAuxHalfReifDummy(RegularAuxHalfReif):

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if self.sol is None:
            return []
        return [cp.all(cp.cpm_array(self.args[0]) == self.sol)]

RegularAuxHalfReifMinimal = RegularAuxHalfReif


