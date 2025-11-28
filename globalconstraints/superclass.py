from cpmpy.expressions.globalconstraints import GlobalConstraint
from cpmpy.solvers.solver_interface import ExitStatus

import cpmpy as cp
from cpmpy.expressions.utils import argvals, flatlist, is_any_list, is_num, get_bounds
from cpmpy.expressions.variables import _BoolVarImpl, _NumVarImpl

class CustomGlobal(GlobalConstraint):

    def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         self.name = "custom_global"

    def decompose(self):
        raise NotImplementedError("This global constraint cannot be decomposed!!\n"
                                  "You should use the `toplevel`, `iftrue` and `iffalse` methods instead.")

    def toplevel(self):
        raise NotImplementedError()
    def iftrue(self):
        raise NotImplementedError()
    def iffalse(self):
        raise NotImplementedError()

class NativeGlobal(CustomGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "native_global"

        self.cpm_global = None

    def toplevel(self):
        return []

    def iftrue(self):
        return [self.cpm_global(*self.args)]

    def iffalse(self):
        return []

class AuxGlobal(CustomGlobal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "aux_global"

        self.to_replace = list(range(len(self.args)))
        self.cpm_global = None

    def make_new_vars(self, expr):
        if is_any_list(expr):
            return [self.make_new_vars(e) for e in expr]
        if isinstance(expr, _BoolVarImpl):
            return cp.boolvar()
        if isinstance(expr, _NumVarImpl) or is_num(expr):
            return cp.intvar(*get_bounds(expr))
        raise ValueError(f"Unexpected expression to make a new variable for: {expr}")

    def get_aux_vars(self):
        aux_vars = []
        for i, arg in enumerate(self.args):
            if i in self.to_replace:
                new_arg = self.make_new_vars(arg)
                if is_any_list(arg):
                    new_arg = cp.cpm_array(new_arg)
                aux_vars.append(new_arg)
            else:
                aux_vars.append(None) # None will fail in CPMpy, so it's a safe placeholder
        return aux_vars

    def check_if_sat(self):

        model = cp.Model(self.cpm_global(*self.args))
        res = model.solve(**self.solver_kwargs)
        if model.status().exitstatus == ExitStatus.UNKNOWN:
            raise TimeoutError(f"Timeout during intialization of {self}")
        if res is True:
            self.sol = argvals(self.args)
            self.new_args = self.get_aux_vars()
        else:
            self.sol = None

    def toplevel(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if "aux" not in self.name:
            raise ValueError(f"{self} is not an AuxGlobal (maybe a decomposition?), you probably need to override this method.")
        if self.sol is not None:
            args = [self.new_args[i] if i  in self.to_replace else self.args[i] for i in range(len(self.args))]
            return self.cpm_global(*args)
        return []

    def iftrue(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if "aux" not in self.name:
            raise ValueError(f"{self} is not an AuxGlobal (maybe a decomposition?), you probably need to override this method.")
        if self.sol is None:
            return [cp.BoolVal(False)]
        cons = []
        for i, arg in enumerate(self.args):
            if i in self.to_replace:
                cons += [self.new_args[i] == arg]
        return flatlist(cons)

    def iffalse(self):
        if not hasattr(self, "sol"): self.check_if_sat()
        if "aux" not in self.name:
            raise ValueError(f"{self} is not an AuxGlobal (maybe a decomposition?), you probably need to override this method.")
        # should be overloaded by "DummySol" variants
        return []
