from math import floor
from os import listdir
from os.path import join
from time import time

import cpmpy as cp
from cpmpy.solvers.solver_interface import ExitStatus
from cpmpy.tools.explain.utils import make_assump_model
from cpmpy.transformations.get_variables import get_variables
from cpmpy.transformations.normalize import toplevel_list
from natsort import natsorted

from globalconstraints import *
from utils import init_solver_with_search_order


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
#       Instance grids (params only)          #
###############################################

DATASET_TYPES = {
    "random-alldiff": ("maxcsp", "assump"),
    "random-gcc": ("maxcsp", "assump"),
    "random-cumulative": ("maxcsp", "assump"),
    "set": ("justsolve",),
    "rcpsp": ("maxcsp",),
    "xcsp3": ("maxcsp", "assump"),
}


def iter_instances(dataset, solver, num_experiments=-1):
    """Yield dicts of CLI kwargs identifying one instance (no models built)."""
    if dataset == "random-alldiff":
        classes = ["BinaryDecomposedAllDifferent", "AllDifferentAuxHalfReif", "AllDifferentAuxHalfReifDummySol"]
        if solver in ("cpo", "choco"):
            classes.append("NativeAllDifferent")
        i = 0
        for n_vars in [10, 20, 30, 40, 50]:
            for n_cons in [10, 12, 14, 16, 18, 20]:
                for seed in range(10):
                    if i == num_experiments:
                        return
                    i += 1
                    for constraint in classes:
                        yield dict(n_vars=n_vars, n_cons=n_cons, seed=seed, constraint=constraint)

    elif dataset == "random-gcc":
        classes = ["BooleanDecomposedGCC", "GCCAuxHalfReif", "GCCAuxHalfReifMinimal", "GCCAuxHalfReifDummy"]
        if solver == "choco":
            classes.append("NativeGCC")
        i = 0
        for n_cons in [2, 4, 5]:
            for seed in range(50):
                if i == num_experiments:
                    return
                i += 1
                for constraint in classes:
                    yield dict(n_vars=15, n_cons=n_cons, seed=seed, constraint=constraint)

    elif dataset == "random-cumulative":
        classes = ["TaskDecomposedCumulative", "CumulativeAuxHalfReif", "CumulativeAuxHalfReifMinimal",
                   "CumulativeAuxHalfReifDummy", "CumulativeAuxHalfReifMinimalDummy"]
        if solver == "choco":
            classes.append("NativeCumulative")
        i = 0
        for n_tasks in [20, 30, 40, 50, 60]:
            for n_cons in [4, 6, 8, 10, 12, 14, 16, 18, 20]:
                for seed in range(7):
                    if i == num_experiments:
                        return
                    i += 1
                    for constraint in classes:
                        yield dict(n_tasks=n_tasks, n_cons=n_cons, seed=seed, constraint=constraint)

    elif dataset == "set":
        classes = ["decomp", "aux", "auxdummy"]
        if solver in ("cpo", "choco"):
            classes.append("native")
        i = 0
        for n_cards in range(9, 200, 10):
            for size_of_set in range(3, 100, 3):
                if i == num_experiments:
                    return
                i += 1
                for constraint in classes:
                    yield dict(n_cards=n_cards, size_of_set=size_of_set, seed=0, constraint=constraint)

    elif dataset == "rcpsp":
        classes = ["TaskDecomposedCumulative", "CumulativeAuxHalfReif", "CumulativeAuxHalfReifMinimal",
                   "CumulativeAuxHalfReifDummy", "CumulativeAuxHalfReifMinimalDummy"]
        if solver == "choco":
            classes.append("NativeCumulative")
        i = 0
        for fname in natsorted(listdir("benchmarks/rcpsp_j60")):
            if i == num_experiments:
                return
            i += 1
            for constraint in classes:
                yield dict(fname=fname, constraint=constraint)

    elif dataset == "xcsp3":
        classes = ["decomp", "aux", "auxdummy", "auxminimal", "auxminimaldummy"]
        i = 0
        for fname in natsorted(listdir("benchmarks/xcsp3_instances")):
            if i == num_experiments:
                return
            i += 1
            for constraint in classes:
                yield dict(fname=fname, constraint=constraint)

    else:
        raise ValueError(f"Unknown dataset {dataset}")


def output_name(inst):
    """Flat filename for one instance JSON."""
    c = inst["constraint"]
    if "fname" in inst:
        return f"{c}-{inst['fname']}.json"
    if "n_tasks" in inst:
        return f"{c}-t{inst['n_tasks']}-c{inst['n_cons']}-s{inst['seed']}.json"
    if "n_cards" in inst:
        return f"{c}-n{inst['n_cards']}-z{inst['size_of_set']}-s{inst['seed']}.json"
    return f"{c}-v{inst['n_vars']}-c{inst['n_cons']}-s{inst['seed']}.json"


if __name__ == "__main__":
    # Batch driver used by the Makefile: expand the grid, skip existing outputs,
    # shell out to run_model.py for each missing instance.
    import argparse
    import os
    import subprocess
    import sys

    parser = argparse.ArgumentParser(description="Expand experiment grid and run missing instances")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--solver", action="append", dest="solvers",
                        help="Repeatable; default: ortools choco cpo")
    parser.add_argument("--experiment-type", action="append", dest="types",
                        help="Repeatable; default: types for the dataset")
    parser.add_argument("--search-order", default="default")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--num-experiments", type=int, default=-1)
    args = parser.parse_args()

    solvers = args.solvers or ["ortools", "choco", "cpo"]
    types = args.types or list(DATASET_TYPES[args.dataset])
    os.makedirs(args.output_dir, exist_ok=True)

    for solver in solvers:
        for experiment_type in types:
            for inst in iter_instances(args.dataset, solver, args.num_experiments):
                out_dir = join(args.output_dir, solver, experiment_type, args.search_order)
                out = join(out_dir, output_name(inst))
                if os.path.exists(out):
                    continue

                cmd = [
                    sys.executable, "run_model.py",
                    "--dataset", args.dataset,
                    "--solver", solver,
                    "--experiment-type", experiment_type,
                    "--search-order", args.search_order,
                    "--constraint", inst["constraint"],
                    "--output", out,
                    "--timeout", str(args.timeout),
                ]
                for key in ("n_vars", "n_cons", "n_tasks", "n_cards", "size_of_set", "seed", "fname"):
                    if key in inst:
                        cmd += [f"--{key.replace('_', '-')}", str(inst[key])]

                print(" ".join(cmd))
                subprocess.check_call(cmd)
