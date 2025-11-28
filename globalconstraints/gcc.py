import warnings

import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, argval, argvals

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal
from cpmpy.solvers.solver_interface import ExitStatus


class CustomGCC(CustomGlobal, cp.GlobalCardinalityCount):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "custom_gcc"

        self.cpm_global = cp.GlobalCardinalityCount

class NativeGCC(CustomGCC, NativeGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_gcc"

class BooleanDecomposedGCC(CustomGCC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "boolean_gcc"

        vars, vals, occ = self.args
        lbs, ubs = get_bounds(vars)
        lb, ub = min(lbs), max(ubs) + 1
        self.val_range = list(range(lb, ub))
        for v in vals:
            assert isinstance(v, int)
        self.bv = cp.boolvar(shape=(len(vars), len(self.val_range)))

    def toplevel(self):
        vars, vals, occ = self.args
        defining = [cp.sum(row) == 1 for row in self.bv]  # each variable has exactly one value
        defining += [cp.sum(bvs * self.val_range) == var for bvs, var in
                     zip(self.bv, vars)]  # link bvs to values of vars
        return defining

    def iftrue(self):

        vars, vals, occ = self.args
        cons = []
        for val, cnt in zip(vals, occ):
            idx = self.val_range.index(val)
            cons += [cp.sum(self.bv[:, idx]) == cnt]  # count is correct

        if self.closed:
            for idx, var_val in enumerate(self.val_range):
                if var_val not in vals:
                    cons += cp.sum(self.bv[:, idx]) == 0

        return cons

    def iffalse(self):
        return []


class GCCAuxHalfReif(AuxGlobal, CustomGCC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_gcc"
        self.to_replace = [0, 2]
        self.cpm_global = cp.GlobalCardinalityCount

class GCCAuxHalfReifDummy(GCCAuxHalfReif):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_gcc_dummy"

        self.to_replace = [0, 2]
        self.cpm_global = cp.GlobalCardinalityCount

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if self.sol is None:
            return []
        assert len(self.sol)  == len(self.new_args)
        lst = []
        for i, (arg, s) in enumerate(zip(self.new_args, self.sol)):
            if i in self.to_replace:
                lst.append(arg == s)
        return flatlist(lst)


class GCCAuxHalfReifMinimal(AuxGlobal, CustomGCC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_gcc_minimal"
        self.to_replace = [2]
        # self.cpm_global = cp.GlobalCardinalityCount

    def get_aux_vars(self):
        vars, vals, occ = self.args
        # just replace occ
        return [None, None, cp.intvar(0, len(vars), shape=len(vals))]