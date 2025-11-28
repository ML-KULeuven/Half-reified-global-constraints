import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, all_pairs

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal
from cpmpy.solvers.solver_interface import ExitStatus

class CustomNegativeTable(CustomGlobal, cp.NegativeTable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "custom_negtable"

class NativeNegativeTable(CustomNegativeTable, NativeGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_negtable"

class DecomposedNegativeTable(CustomNegativeTable, cp.NegativeTable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "decomposed_negtable"
        vars, table = self.args
        self.row_is_sat = cp.boolvar(shape=(len(table),))

    def toplevel(self):
        vars, table = self.args
        vars = cp.cpm_array(vars)
        return [cp.all(row == vars).implies(self.row_is_sat[i]) for i, row in enumerate(table)]

    def iftrue(self):
        return [~cp.any(self.row_is_sat)]

class NegativeTableAuxHalfReif(AuxGlobal, CustomNegativeTable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_negtable"

        self.cpm_global = cp.NegativeTable
        self.to_replace = [0]

class NegativeTableAuxHalfReifDummy(NegativeTableAuxHalfReif):

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if self.sol is None:
            return []
        return [cp.all(cp.cpm_array(self.args[0]) == self.sol)]

NegativeTableAuxHalfReifMinimal = NegativeTableAuxHalfReif
NegativeTableAuxHalfReifMinimalDummy = NegativeTableAuxHalfReifDummy

