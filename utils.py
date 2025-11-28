from natsort import natsorted
import copy

import cpmpy as cp
from cpmpy.transformations.get_variables import get_variables
from cpmpy.transformations.normalize import toplevel_list
from cpmpy.expressions.globalconstraints import GlobalConstraint
from cpmpy.expressions.core import Operator

from globalconstraints import *

def decompose_globals(list_of_cons, solver, solver_kwargs=dict()):
    """
        Rewrite/Decompose half-reified global constraints.
         Anytime we encounter bv -> Global, we rewrite this as:
            global.toplevel() /\ bv -> global.iftrue() /\ ~bv -> global.iffalse()

        AuxGlobal global constraints need to call a solver here, so we set the `solver_kwargs` argument.
        For the experiments, we use the same solver as we use for actually solving the "main" model (e.g., maxcsp)
    """
    newlist = []
    for cons in toplevel_list(list_of_cons):

        if isinstance(cons, Operator) and cons.name == "->":
            bv, expr = cons.args
            if isinstance(expr, CustomGlobal):
                expr.solver_kwargs = dict(solver=solver, **solver_kwargs)
                # bv -> expr.iftrue()
                newlist.append(bv.implies(cp.all(expr.iftrue())))
                # ~bv -> expr.iffalse()
                newlist.append((~bv).implies(cp.all(expr.iffalse())))
                # expr.toplevel()
                newlist.append(expr.toplevel())
            elif isinstance(expr, GlobalConstraint):
                print(f"Warning: found 'normal' CPMpy global constraint in half-reification: \n {cons}")
                newlist.append(cons)
            else:
                newlist.append(cons)
        else:
            newlist.append(cons)

    return newlist


def init_solver_with_search_order(model, solver, bvs, search_order, **solver_kwargs):

    d_model = copy.copy(model)
    d_model.constraints = decompose_globals(model.constraints, solver=solver, solver_kwargs=solver_kwargs)

    # search order
    orig = natsorted(set(get_variables(model.constraints)) - set(bvs), key=str) # original variables
    aux = natsorted(set(get_variables(d_model.constraints)) - set(orig) - set(bvs), key=str) # auxiliary variables
    bvs = natsorted(bvs, key=str)

    assert set(orig) & set(aux) == set()
    assert set(orig) & set(bvs) == set()
    assert set(aux) & set(bvs) == set()

    if search_order == "default":
        order = []
    elif search_order == "orig-bv-aux":
        order = orig + bvs + aux
    elif search_order == "bv-orig-aux":
        order = bvs + orig + aux
    else:
        raise ValueError(f"Invalid search order: {search_order}")

    s = cp.SolverLookup.get(solver)
    s.solver_vars(order) # ensure insertion-order is respected
    s += d_model.constraints
    if d_model.objective_ is not None:
        s.objective(d_model.objective_, d_model.objective_is_min)

    # solvers have different ways of setting search order
    if search_order == "default":
        pass
    elif solver == "choco":
        s.chc_solver = s.native_model.get_solver()
        s.chc_solver.set_input_order_ub_search(s.solver_vars(order))
    else:
        raise ValueError(f"Cannot set search order {search_order} for solver {solver}")

    return s


def plot_results(df, **kwargs):

    import seaborn as sns
    import matplotlib.pyplot as plt

    df['total_time'] = df[[col for col in df.columns if "time" in col]].sum(axis=1)
    ax = sns.ecdfplot(
        data = df[df['status'] != 'timeout'],
        x = "total_time",
        hue = "constraint",
        stat="count"
    )

    ax.set_title("\n".join(f"{key} = {val}" for key, val in kwargs.items()))
    plt.show()
