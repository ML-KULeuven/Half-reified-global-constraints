import cpmpy as cp
from cpmpy.expressions.utils import get_bounds, all_pairs

from .superclass import AuxGlobal, flatlist, NativeGlobal, CustomGlobal
from cpmpy.solvers.solver_interface import ExitStatus

class CustomTable(CustomGlobal, cp.Table):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "custom_table"

class NativeTable(CustomTable, NativeGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_table"

class DecomposedTable(CustomTable, cp.Table):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "decomposed_table"
        vars, table = self.args
        self.row_is_sat = cp.boolvar(shape=(len(table),))

    def iftrue(self):
        return [cp.any(self.row_is_sat)]

    def toplevel(self):
        vars, table = self.args
        vars = cp.cpm_array(vars)
        return [self.row_is_sat[i].implies(cp.all(row == vars)) for i,row in enumerate(table)]

    def iffalse(self):
        return []


class TableAuxHalfReif(AuxGlobal, CustomTable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_table"

        self.cpm_global = cp.Table
        self.to_replace = [0]


class TableAuxHalfReifDummy(TableAuxHalfReif):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_table_dummy"

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if self.sol is None:
            return []
        return flatlist(cp.cpm_array(self.args[0]) == self.sol[0])





