import copy

import cpmpy as cp
import numpy as np

from cpmpy.expressions.utils import flatlist

from globalconstraints import *

def get_rcpsp_model(duration, precedence, resources, capacities, horizon, Cumulative, **kwargs):

    n_jobs = len(duration)
    start = cp.intvar(0, horizon, shape=n_jobs, name="s")
    
    model = cp.Model()
    
    for t1, t2 in precedence:
        model += (start[t1]+duration[t1]) <= start[t2]

    for machine_id, cap in enumerate(capacities):
        # find which task to schedule on machine m
        taskmask = resources.T[machine_id] != 0
        task_idx = np.argwhere(taskmask)
        demand = resources.T[machine_id][taskmask]
        # add cumulative to model
        model += Cumulative(start=start[task_idx],
                           duration=duration[task_idx],
                           demand=demand,
                           capacity=cap)

    model.minimize(cp.max([s+d for s,d in zip(start, duration)]))
    return model

#######################################################

def get_set_model(cards, size_of_set, global_type):

    if global_type == "decomp":
        AllDifferent = BinaryDecomposedAllDifferent
    elif global_type == "aux":
        AllDifferent = AllDifferentAuxHalfReif
    elif global_type == "native":
        AllDifferent = NativeAllDifferent
    elif global_type == "auxdummy":
        AllDifferent = AllDifferentAuxHalfReifDummySol
    else:
        raise ValueError("Unexpected global type", global_type)

    winning_cards = cp.intvar(0, len(cards)-1, shape=size_of_set, name="cards")
    n_attr = len(cards[0])
    model = cp.Model()

    model += cp.AllDifferent(winning_cards) # cannot have duplicates obviously...
    model += cp.IncreasingStrict(winning_cards) # break symmetries

    cards = cp.cpm_array(cards)

    for attr in range(n_attr):
        # hack to get around CPMpy annoyngness with 2d-element
        attr_vals = cp.intvar(0, max(cards[:, attr]), shape=size_of_set, name=f"attr {attr}")
        model += [val == cards[:, attr][wc] for val, wc in zip(attr_vals, winning_cards)]
        is_all_diff = cp.boolvar(name=f"IMPL_diff_{attr}")
        is_all_equal = cp.boolvar(name=f"IMPL_equal_{attr}")
        model += is_all_equal.implies(cp.all(flatlist(cp.AllEqual(attr_vals).decompose()))) # some solvers do not support AllEqual
        model += is_all_diff.implies(AllDifferent(attr_vals))
        model += is_all_diff | is_all_equal   

    return model

#######################################################

def get_random_gcc_model(lb, ub, n_vars, subsets, values, counts, GlobalCardinalityCount):
    vars = cp.intvar(lb,ub, shape=n_vars, name="X")

    model = cp.Model()
    for idxes, vals, cnts in zip(subsets, values, counts):
        model += GlobalCardinalityCount(vars[idxes], vals, cnts)

    return model

def get_random_alldiff_model(n_vars, subsets, AllDifferent=cp.AllDifferent):

    model = cp.Model()
    vars = cp.intvar(0, n_vars//2, shape=n_vars, name="X")
    for subset in subsets:
        model += AllDifferent(vars[subset])

    return model

def get_random_cumulative_model(lb, ub, n_tasks, subsets, durations, demands, capacities, Cumulative):

    start = cp.intvar(lb, ub, shape=n_tasks, name="start")

    model = cp.Model()
    for subset, capa in zip(subsets, capacities):
        model += Cumulative(start=start[subset], 
                            duration=durations[subset], 
                            demand=demands[subset], 
                            capacity=capa)
    return model

#######################################################

def get_xcsp3_model(path, global_type=None):

    if global_type == "decomp":
        global_constraints = dict(AllDifferent=BinaryDecomposedAllDifferent,
                                  Cumulative=TaskDecomposedCumulative,
                                  NoOverlap=BinaryDecomposedNoOverlap,
                                  NonReifiedTable=DecomposedTable,
                                  NonReifiedNegativeTable=DecomposedNegativeTable,
                                  Regular=DecomposedRegular,
                                  Inverse=DecomposedInverse
                                  )
    
    elif global_type == "aux":
        global_constraints = dict(AllDifferent=AllDifferentAuxHalfReif,
                                  Cumulative=CumulativeAuxHalfReif,
                                  NoOverlap=NoOverlapAuxHalfReif,
                                  NonReifiedTable=TableAuxHalfReif,
                                  NonReifiedNegativeTable=NegativeTableAuxHalfReif,
                                  Regular=RegularAuxHalfReif,
                                  Inverse=InverseAuxHalfReif
                                  )
        
    elif global_type == "auxminimal":
        global_constraints = dict(AllDifferent=AllDifferentAuxHalfReif,
                                  Cumulative=CumulativeAuxHalfReifMinimal,
                                  NoOverlap=NoOverlapAuxHalfReif,
                                  NonReifiedTable=TableAuxHalfReif,
                                  NonReifiedNegativeTable=NegativeTableAuxHalfReifMinimal,
                                  Regular=RegularAuxHalfReifMinimal,
                                  Inverse=InverseAuxHalfReif
                                  )
    elif global_type == "auxdummy":
        global_constraints = dict(AllDifferent=AllDifferentAuxHalfReifDummySol,
                                  Cumulative=CumulativeAuxHalfReifDummy,
                                  NoOverlap=NoOverlapAuxHalfReifDummy,
                                  NonReifiedTable=TableAuxHalfReifDummy,
                                  NonReifiedNegativeTable=NegativeTableAuxHalfReifDummy,
                                  Regular=RegularAuxHalfReifDummy,
                                  Inverse=InverseAuxHalfReifDummy
                                  )
    elif global_type == "auxminimaldummy":
        global_constraints = dict(AllDifferent=AllDifferentAuxHalfReifDummySol,
                                  Cumulative=CumulativeAuxHalfReifMinimalDummy,
                                  NoOverlap=NoOverlapAuxHalfReifDummy,
                                  NonReifiedTable=TableAuxHalfReifDummy,
                                  NonReifiedNegativeTable=NegativeTableAuxHalfReifDummy,
                                  Regular=RegularAuxHalfReifDummy,
                                  Inverse=InverseAuxHalfReifDummy
                                )
    else:
        raise ValueError(f"Unexpected value for global type, got {global_type}")

    from cpmpy.transformations.normalize import toplevel_list
    from cpmpy.transformations.decompose_global import decompose_in_tree
    from cpmpy.expressions.globalconstraints import GlobalConstraint
    from cpmpy.tools.xcsp3 import read_xcsp3

    print("Reading", path)
    model = read_xcsp3(path)

    model = copy.copy(model)
    model.constraints = toplevel_list(model.constraints, merge_and=False)
    num_glob = 0
    for i, cons in enumerate(list(model.constraints)):
        if isinstance(cons, GlobalConstraint):
            # check if in map
            if type(cons).__name__ in global_constraints:
                CLS = global_constraints[type(cons).__name__]
                model.constraints[i] = CLS(*cons.args)
                num_glob += 1
            else:
                model.constraints[i] = cp.all(decompose_in_tree([cons])) # decompose
                # x,y = cons.decompose()
                # decomposed = toplevel_list(x) + toplevel_list(y)
                # changes = True
                # while changes:
                #     print("Decomposing nested globals")
                #     changes = False
                #     new_decomposed = []
                #     for c in decomposed:
                #         if isinstance(c, GlobalConstraint):
                #             new_decomposed += toplevel_list(c.decompose())
                #             changes = True
                #         else:
                #             new_decomposed.append(c)
                #     decomposed = new_decomposed
                #
                # model.constraints[i] = cp.all(decomposed)

    print("Solving model with", num_glob, "custom global constraints")
    return model
