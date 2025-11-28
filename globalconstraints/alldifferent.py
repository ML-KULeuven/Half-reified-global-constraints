import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, all_pairs

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal
from cpmpy.solvers.solver_interface import ExitStatus

"""
**WARNING**
The classes below are not a drop-in replacement for cpmpy.AllDifferent.
The decompositions implemented are only valid when the global constraint occurs in positive context!
"""
class CustomAllDifferent(CustomGlobal, cp.AllDifferent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "custom_alldifferent"

        self.cpm_global = cp.AllDifferent

class NativeAllDifferent(CustomAllDifferent, NativeGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_alldifferent"

class BinaryDecomposedAllDifferent(CustomAllDifferent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "binary_alldifferent"

    def toplevel(self):
        return []

    def iftrue(self):
        return [x != y for x,y in all_pairs(self.args)]

    def iffalse(self):
        return []

class AllDifferentAuxHalfReif(AuxGlobal, CustomAllDifferent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_alldifferent"

        self.to_replace = list(range(len(self.args)))
        self.cpm_global = cp.AllDifferent

class AllDifferentAuxHalfReifDummySol(AllDifferentAuxHalfReif):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_alldifferent_dummy"

        self.to_replace = list(range(len(self.args)))
        self.cpm_global = cp.AllDifferent

    def iffalse(self):
        if self.sol is None:
            return []
        assert len(self.sol)  == len(self.new_args)
        lst = []
        for i, (arg, s) in enumerate(zip(self.new_args, self.sol)):
            if i in self.to_replace:
                lst.append(arg == s)
        return flatlist(lst)

if __name__ == "__main__":

    x = cp.intvar(0,10, shape=3, name="X")

    print(AllDifferentAuxHalfReifDummySol(x).iffalse())