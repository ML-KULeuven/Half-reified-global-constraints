"""
Run one experiment instance from CLI args, write a JSON result.

Example:
  python run_model.py --dataset random-alldiff --solver ortools --experiment-type maxcsp \
      --constraint AllDifferentAuxHalfReif --n-vars 10 --n-cons 10 --seed 0 \
      --output out.json
"""
import json
import os

import globalconstraints as gc
from benchmarks.generated import (
    generate_random_alldiffs,
    generate_random_cumulatives,
    generate_random_gcc,
    generate_set_instance,
)
from benchmarks.rcpsp import read_rcpsp
from experiments import compute_maxcsp, get_solver_core, justsolve, setup_maxcsp_experiment
from models import (
    get_random_alldiff_model,
    get_random_cumulative_model,
    get_random_gcc_model,
    get_rcpsp_model,
    get_set_model,
    get_xcsp3_model,
)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--solver", required=True)
    parser.add_argument("--experiment-type", required=True, choices=["maxcsp", "assump", "justsolve"])
    parser.add_argument("--search-order", default="default")
    parser.add_argument("--constraint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--n-vars", type=int)
    parser.add_argument("--n-cons", type=int)
    parser.add_argument("--n-tasks", type=int)
    parser.add_argument("--n-cards", type=int)
    parser.add_argument("--size-of-set", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--fname")
    args = parser.parse_args()

    if args.dataset == "random-gcc" and args.solver == "ortools":
        raise SystemExit("Rejected: GCC experiments are not available for OR-Tools")
    if args.search_order != "default" and args.solver in ("ortools", "cpo"):
        raise SystemExit(f"Rejected: fixed search order only supported for choco, not {args.solver}")

    solver_kwargs = dict(time_limit=args.timeout)
    if args.solver == "ortools":
        solver_kwargs["num_workers"] = 1
    if args.solver == "cpo":
        solver_kwargs["Workers"] = 1

    # instance params echoed into the JSON
    instance = {k: v for k, v in vars(args).items() if v is not None and k != "output"}

    if args.dataset == "random-alldiff":
        data = generate_random_alldiffs(args.n_vars, args.n_cons, seed=args.seed)
        soft, hard, weights = setup_maxcsp_experiment(
            get_random_alldiff_model, data, "AllDifferent", getattr(gc, args.constraint)
        )
        experiment_params = dict(soft=soft, hard=hard, weights=weights)

    elif args.dataset == "random-gcc":
        data = generate_random_gcc(args.n_vars, args.n_cons, lb=0, ub=15, p=0.5, seed=args.seed)
        soft, hard, weights = setup_maxcsp_experiment(
            get_random_gcc_model, data, "GlobalCardinalityCount", getattr(gc, args.constraint)
        )
        experiment_params = dict(soft=soft, hard=hard, weights=weights)

    elif args.dataset == "random-cumulative":
        data = generate_random_cumulatives(args.n_tasks, args.n_cons, lb=0, ub=50, p=0.5)
        soft, hard, weights = setup_maxcsp_experiment(
            get_random_cumulative_model, data, "Cumulative", getattr(gc, args.constraint)
        )
        experiment_params = dict(soft=soft, hard=hard, weights=weights)

    elif args.dataset == "set":
        data = generate_set_instance(args.n_cards, size_of_set=args.size_of_set, seed=args.seed)
        experiment_params = dict(model=get_set_model(**data, global_type=args.constraint))

    elif args.dataset == "rcpsp":
        data = read_rcpsp(os.path.join("benchmarks/rcpsp_j60", args.fname))
        soft, hard, weights = setup_maxcsp_experiment(
            get_rcpsp_model, data, "Cumulative", getattr(gc, args.constraint)
        )
        experiment_params = dict(soft=soft, hard=hard, weights=weights)

    elif args.dataset == "xcsp3":
        import pandas as pd
        overview = pd.read_csv("benchmarks/xcsp3_overview.csv")
        obj_val = overview[overview["fname"] == args.fname].iloc[0]["objective_value"]
        data = dict(path=os.path.join("benchmarks/xcsp3_instances", args.fname))
        if not pd.isna(obj_val):
            data["optimal"] = int(obj_val)
        soft, hard, weights = setup_maxcsp_experiment(
            get_xcsp3_model, data, "global_type", args.constraint
        )
        experiment_params = dict(soft=soft, hard=hard, weights=weights)

    else:
        raise SystemExit(f"Unknown dataset {args.dataset!r}")

    if args.experiment_type == "maxcsp":
        result = compute_maxcsp(solver=args.solver, search_order=args.search_order,
                                **experiment_params, **solver_kwargs)
    elif args.experiment_type == "assump":
        result = get_solver_core(solver=args.solver, search_order=args.search_order,
                                 **experiment_params, **solver_kwargs)
    elif args.experiment_type == "justsolve":
        result = justsolve(solver=args.solver, search_order=args.search_order,
                           **experiment_params, **solver_kwargs)
    else:
        raise SystemExit(f"Unknown experiment type {args.experiment_type!r}")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({"instance": instance, **result}, f, indent=2)
        f.write("\n")
