# Efficient Reformulations of Half-reified Global Constraints

This repository contains the code for replicating the experiments for the following paper, submitted to the Journal of Artificial Intelligence Research (JAIR)
>
>



## Getting started
To run the experiments, you will need to install the following packages:
- CPMpy (>= 1.0, with Cumulative/NoOverlap without end variables)
- OR-Tools
- PyChoco
- PyCSP3
- CP-Optimizer
- Pandas
- Seaborn
- natsort

```bash
$ pip install cpmpy ortools pychoco docplex pycsp3 pandas seaborn natsort
```

CP-optimizer requires a licence to be installed.
For more information, please refer to the [CP-Optimizer website](https://www.ibm.com/products/ilog-cplex-optimization-studio/cplex-cp-optimizer).

## Short overview of the method
This repository contains the implementation for an efficient reformulation of the half-reified global constraints.
Our reformulation avoids decomposing the global constraint, and instead uses a set of freshly introduced auxiliary variables to rewrite the constraint.

For example, take the constraint `bv -> AllDifferent(x,y,z)`.
This constraint is rewritten using our method to `AllDifferent(x',y',z') & bv -> (x = x' & y = y' & z = z')`.
This reformulation allows us to post the reified global constraint to any solver that supports the global constraint at the top-level of the constraint model.

While our implementation is generic, this repository implements it for the constraints: AllDifferent, Cumulative, GCC, Inverse, Table, NegativeTable, NoOverlap and Regular.

## Structure of the repository

```
├── README.md
├── Makefile              # make experiments <dataset>
├── run_model.py          # one instance → one JSON
├── experiments.py        # solvers + grid expansion for the Makefile
├── benchmarks/
├── globalconstraints/
├── models.py
└── utils.py
```

## Running the experiments

Use-cases: `justsolve`, `maxcsp`, `assump`.

```bash
make experiments random-alldiff
make experiments random-alldiff SOLVER=ortools
make experiments set TIMEOUT=10 NUM_EXPERIMENTS=2
```

Results go to `results/<dataset>/` (override with `OUTPUT=`). Already-finished
JSON files are skipped.

`run_model.py` runs a single instance from CLI args (instance keys like `--n-vars` /
`--seed` for alldiff, `--fname` for rcpsp) and rejects unavailable combinations
(e.g. GCC+ortools, fixed search on ortools/cpo):

```bash
python run_model.py --dataset random-alldiff --solver ortools --experiment-type maxcsp \
  --constraint AllDifferentAuxHalfReif --n-vars 10 --n-cons 10 --seed 0 \
  --output out.json
```

Each JSON has `"instance"` (the input params) plus result keys (`status`, `init_time`,
`solve_time`, …). Paper defaults: `NUM_EXPERIMENTS=-1`, `TIMEOUT=3600`.
