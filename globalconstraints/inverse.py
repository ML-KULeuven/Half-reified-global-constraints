import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, all_pairs

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal


class CustomInverse(CustomGlobal, cp.Inverse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "custom_inverse"

        self.cpm_global = cp.Inverse

class NativeInverse(CustomInverse, NativeGlobal):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_inverse"

class DecomposedInverse(CustomInverse):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "decomposed_inverse"

    def iftrue(self):
        fwd, rev = self.args
        rev = cp.cpm_array(rev)
        return [all(rev[x] == i for i, x in enumerate(fwd))] + \
               [all(fwd[y] == j for j, y in enumerate(rev))]

    def iffalse(self):
        return []

    def toplevel(self):
        return []

class InverseAuxHalfReif(AuxGlobal, CustomInverse):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_inverse"

        self.to_replace = [0,1]
        self.cpm_global = cp.Inverse

class InverseAuxHalfReifDummy(InverseAuxHalfReif):

    def iffalse(self):
        if self.sol is None:
            return []
        assert len(self.sol)  == len(self.new_args)
        lst = []
        for i, (arg, s) in enumerate(zip(self.new_args, self.sol)):
            if i in self.to_replace:
                lst.append(arg == s)
        return flatlist(lst)

