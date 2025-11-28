from math import floor
from os import listdir
from os.path import join
from time import time

import cpmpy as cp
from cpmpy.expressions.globalconstraints import GlobalConstraint
from cpmpy.tools.xcsp3 import read_xcsp3

from cpmpy.expressions.core import Operator
from cpmpy.transformations.normalize import toplevel_list
from cpmpy.transformations.get_variables import get_variables
from cpmpy.solvers.solver_interface import ExitStatus
from natsort import natsorted
from tqdm import tqdm

from benchmarks.rcpsp import read_rcpsp
from globalconstraints import *
from utils import init_solver_with_search_order, plot_results


def setup_maxcsp_experiment(model_func, data, global_name, global_cls):
    """
        Setup a Max-CSP experiment.
        Computes the soft and hard constraints of the model, and determines the weights for the soft constraints.
    """
    if global_name != "global_type":
        cpm_global = eval(f"cp.{global_name}")
    else:
        cpm_global = global_cls

    is_xcsp3 = "path" in data and "xcsp3" in data["path"]

    cpm_model = model_func(**data, **{global_name : cpm_global})

    # get weights for function,
    # ensure it is equal no matter what global constraint is used,
    # so just use the CPMpy version of the constraint
    cpm_soft = toplevel_list(cpm_model.constraints, merge_and=False)
    weights = [len(str(cons)) for cons in cpm_soft]

    # now get the actual model we will solve
    model = model_func(**data, **{global_name : global_cls})
    soft = toplevel_list(model.constraints, merge_and=False)
    hard = []
    if "optimal" in data:
        assert model.objective_ is not None
        hard = [model.objective_ <= floor(0.7 * data["optimal"])]
        if is_xcsp3:
            hard = [model.objective_ < data["optimal"]]

    return soft, hard, weights

def compute_maxcsp(soft, hard, weights, solver, search_order="default", **solver_kwargs):

    model, soft, assump = make_assump_model(soft=soft, hard=hard)
    model.maximize(cp.sum(weights * assump))

    timings = dict()
    try: # catch potential timeout
        start = time()
        solver = init_solver_with_search_order(model, solver, assump, search_order, **solver_kwargs)
        timings['init_time'] = time() - start
    except TimeoutError:
        return dict(status = "timeout in decompose", **timings)

    res = solver.solve(**solver_kwargs) # solve the model
    timings['solve_time'] = solver.status().runtime

    status = solver.status().exitstatus
    if status == ExitStatus.OPTIMAL:
        return dict(status = "optimal", **timings, objective = solver.objective_value(),)
    if status == ExitStatus.UNSATISFIABLE:
        return dict(status = "unsatisfiable", **timings)
    if status in {ExitStatus.UNKNOWN, ExitStatus.FEASIBLE}:
        return dict(status = "timeout", **timings)

    raise ValueError(f"Unknown exit status {model.status().exitstatus}")

def justsolve(model, solver, search_order, **solver_kwargs):

    bvs = [v for v in get_variables(model.constraints) if v.name.startswith("IMPL_")]

    timings = dict()
    try:  # catch potential timeout
        start = time()
        solver = init_solver_with_search_order(model, solver, bvs, search_order, **solver_kwargs)
        timings['init_time'] = time() - start
    except TimeoutError:
        return dict(status="timeout in decompose", **timings)

    res = solver.solve(**solver_kwargs)
    timings['solve_time'] = solver.status().runtime

    status = solver.status().exitstatus
    if status == ExitStatus.OPTIMAL:
        return dict(objective=solver.objective_value(),
                    status="optimal", **timings)
    if status == ExitStatus.FEASIBLE:
        return dict(status="feasible", **timings)
    if status == ExitStatus.UNSATISFIABLE:
        return dict(status="unsatisfiable", **timings)
    if status == ExitStatus.UNKNOWN:
        return dict(status="timeout", **timings)

    raise ValueError(f"Unknown exit status {model.status().exitstatus}")

def get_solver_core(soft, hard, solver, search_order="default", weights=None, **solver_kwargs):

    model, soft, assump = make_assump_model(soft=soft, hard=hard)

    timings = dict()
    try:  # catch potential timeout
        start = time()
        solver = init_solver_with_search_order(model, solver, assump, search_order, **solver_kwargs)
        timings['init_time'] = time() - start
    except TimeoutError:
        return dict(status="timeout in decompose", **timings)

    res = solver.solve(assumptions=assump, **solver_kwargs)  # solve the model under assumptions
    timings['solve_time'] = solver.status().runtime

    status = solver.status().exitstatus
    if status == ExitStatus.UNSATISFIABLE:
        return dict(status="unsatisfiable", core_size=len(solver.get_core()), **timings)
    if status == ExitStatus.FEASIBLE:
        return dict(status="feasible", **timings)
    if status in {ExitStatus.UNKNOWN, ExitStatus.FEASIBLE}:
        return dict(status="timeout", **timings)

    raise ValueError(f"Unknown exit status {solver.status().exitstatus}")

###############################################
#       Getting the experiment configs        #
###############################################

def get_random_alldiff_configs(solver, num_experiments):

    classes = [BinaryDecomposedAllDifferent, AllDifferentAuxHalfReif, AllDifferentAuxHalfReifDummySol]
    if solver in ["cpo", "choco"]:
        classes += [NativeAllDifferent]
    i = 0
    for n_vars in [10, 20, 30, 40, 50]:
        for n_cons in [10, 12, 14, 16, 18, 20]:
            for seed in range(10):
                if i == num_experiments:
                    return
                i += 1

                data = generate_random_alldiffs(n_vars, n_cons, seed=seed)

                for cls in classes:
                    soft, hard, weights = setup_maxcsp_experiment(model_func=get_random_alldiff_model,
                                                                  data=data,
                                                                  global_name="AllDifferent",
                                                                  global_cls=cls)
                    yield dict(soft=soft, hard=hard, weights=weights), \
                          dict(solver=solver, constraint=cls.__name__,
                               n_vars=n_vars, n_cons=n_cons, seed=seed)

def get_random_gcc_configs(solver, num_experiments):

    classes = [BooleanDecomposedGCC, GCCAuxHalfReif, GCCAuxHalfReifMinimal, GCCAuxHalfReifDummy]
    if solver == "choco":
        classes += [NativeGCC]
    i = 0
    n_vars = 15
    for n_cons in [2,4,5]:
        for seed in range(50):
            if i == num_experiments:
                return
            i += 1

            data = generate_random_gcc(n_vars, n_cons, lb=0, ub=15,p=0.5, seed=seed)

            for cls in classes:
                soft, hard, weights = setup_maxcsp_experiment(model_func=get_random_gcc_model,
                                                              data=data,
                                                              global_name="GlobalCardinalityCount",
                                                              global_cls=cls)
                yield dict(soft=soft, hard=hard, weights=weights), \
                      dict(solver=solver, constraint=cls.__name__,
                           n_vars=n_vars, n_cons=n_cons, seed=seed)

def get_random_cumulative_configs(solver, num_experiments):

    classes = [TaskDecomposedCumulative, CumulativeAuxHalfReif, CumulativeAuxHalfReifMinimal,
               CumulativeAuxHalfReifDummy, CumulativeAuxHalfReifMinimalDummy]
    if solver == "choco":
        classes += [NativeCumulative]
    i = 0
    for n_tasks in [20,30,40,50,60]:
        for n_cons in [4,6,8,10,12,14,16,18,20]:
            for seed in range(7):
                if i == num_experiments:
                    return
                i += 1

                data = generate_random_cumulatives(n_tasks, n_cons, lb=0, ub=50, p=0.5)

                for cls in classes:
                    soft, hard, weights = setup_maxcsp_experiment(model_func=get_random_cumulative_model,
                                                                 data=data,
                                                                 global_name="Cumulative",
                                                                 global_cls=cls)
                    yield dict(soft=soft, hard=hard, weights=weights), \
                          dict(solver=solver, constraint=cls.__name__,
                               n_tasks=n_tasks, n_cons=n_cons, seed=seed)

def get_set_configs(solver, num_experiments):

    classes = ["decomp", "aux", "auxdummy"]
    if solver in {"cpo", "choco"}:
        classes += ["native"]
    i = 0
    for n_cards in range(9,200,10):
        for size_of_set in range(3,100,3):
            seed = 0
            if i == num_experiments:
                return
            i += 1

            data = generate_set_instance(n_cards, size_of_set=size_of_set, seed=seed)
            for cls in classes:
                model = get_set_model(**data,global_type=cls)

                yield  dict(model=model),\
                       dict(solver=solver, constraint=cls,
                            n_cards=n_cards, size_of_set=size_of_set, seed=seed)

def get_rcpsp_configs(solver, num_experiments):

    classes = [TaskDecomposedCumulative, CumulativeAuxHalfReif, CumulativeAuxHalfReifMinimal,
               CumulativeAuxHalfReifDummy, CumulativeAuxHalfReifMinimalDummy]
    if solver == "choco":
        classes += [NativeCumulative]
    i = 0

    dirname = "benchmarks/rcpsp_j60"
    for fname in natsorted(listdir(dirname)):
        if i == num_experiments:
            return
        i += 1

        data = read_rcpsp(join(dirname,fname))
        for cls in classes:
            soft, hard, weights = setup_maxcsp_experiment(model_func=get_rcpsp_model,
                                                          data=data,
                                                          global_name="Cumulative",
                                                          global_cls=cls)

            yield dict(soft=soft, hard=hard, weights=weights), \
                  dict(solver=solver, constraint=cls.__name__, fname=fname)

def get_xcsp3_configs(solver, num_experiments):

    classes = ["decomp", "aux", "auxdummy", "auxminimal", "auxminimaldummy"]

    xcsp3_overview = pd.read_csv("benchmarks/xcsp3_overview.csv")

    dirname = "benchmarks/xcsp3_instances"
    i = 0
    for fname in natsorted(listdir(dirname)):
        if i == num_experiments:
            return
        i += 1

        obj_val = xcsp3_overview[xcsp3_overview['fname']==fname].iloc[0]['objective_value']
        print("Objective value for ", fname, " is ", obj_val)

        data = dict(path = join(dirname,fname))
        if not pd.isna(obj_val):
            data['optimal'] = int(obj_val)

        for cls in classes:
            print(solver, cls)
            soft, hard, weights = setup_maxcsp_experiment(model_func = get_xcsp3_model,
                                                          data=dict(path=join(dirname,fname)),
                                                          global_name="global_type",
                                                          global_cls=cls)

            yield dict(soft=soft, hard=hard, weights=weights), \
                dict(solver=solver, constraint=cls, fname=fname)


if __name__ == "__main__":
    from models import get_random_alldiff_model, get_random_gcc_model, get_random_cumulative_model, get_set_model, \
    get_rcpsp_model, get_xcsp3_model
    from benchmarks.generated import generate_random_alldiffs, generate_random_gcc, generate_random_cumulatives, \
    generate_set_instance

    import pandas as pd
    from cpmpy.tools.explain.utils import make_assump_model

    do_plot = True

    configs = []

    # SETUP EXPERIMENT CONFIG HERE
    num_experiments = 50 # change to -1 for running all experiments.
    benchmark = "random-alldiff"
    solver = "ortools"
    experiment_type = "maxcsp"
    search_order="default"
    TIMEOUT = 60 # change to 3600s for full experiment run

    solver_kwargs = dict(time_limit=TIMEOUT)
    if solver == "ortools":
        solver_kwargs['num_workers'] = 1
    if solver == "cpo":
        solver_kwargs['Workers'] = 1

    if benchmark == "random-alldiff":
        configs = get_random_alldiff_configs(solver, num_experiments)
    elif benchmark == "random-gcc":
        configs = get_random_gcc_configs(solver, num_experiments)
    elif benchmark == "random-cumulative":
        configs = get_random_cumulative_configs(solver, num_experiments)
    elif benchmark == "set":
        configs = get_set_configs(solver, num_experiments)
    elif benchmark == "rcpsp":
        configs = get_rcpsp_configs(solver, num_experiments)
    elif benchmark == "xcsp3":
        configs = get_xcsp3_configs(solver, num_experiments)
    else:
        raise ValueError(f"Unknown benchmark {benchmark}")


    results = []
    for i, (experiment_params, config) in enumerate(tqdm(configs)):
        if experiment_type == "maxcsp":
            result  = compute_maxcsp(solver=solver, search_order=search_order, **experiment_params, **solver_kwargs)
        elif experiment_type == "assump":
            result = get_solver_core(solver=solver, search_order=search_order, **experiment_params, **solver_kwargs)
        elif experiment_type == "justsolve":
            result  = justsolve(solver=solver, search_order=search_order, **experiment_params, **solver_kwargs)
        else:
            raise ValueError(f"Unknown experiment type {experiment_type}")

        result.update(config)
        results.append(result)

    df = pd.DataFrame(results)
    df.to_pickle(f"results/{benchmark}-{solver}-{experiment_type}-{search_order}.df")

    if do_plot:
        plot_results(df, solver=solver, benchmark=benchmark, experiment_type=experiment_type, search_order=search_order)

    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)

    print(df)





