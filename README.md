# Efficient Reformulations of Half-reified Global Constraints

This repository contains the code for replicating the experiments for the following paper, submitted to the Journal of Artificial Intelligence Research (JAIR)
>
> 



## Getting started
To run the experiments, you will need to install the following packages:
- CPMpy on branch `no_end_cumulative`
- OR-Tools
- PyChoco
- PyCSP3
- CP-Optimizer
- Pandas
- Seaborn
- natsort

```bash
$ git+https://github.com/CPMpy/cpmpy@no_end_cumulative
$ pip install ortools pychoco docplex pycsp3 pandas seaborn, natsort
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
├── benchmarks 
│   ├── generated.py          # generated benchmarks with alldifferent, gcc and cumulative constraints
│   ├── rcpsp.py              # code for loading rcpsp instances
│   ├── rcpsp_j60             # rcpsp instances downloaded from psplib.com
│   ├── xcsp3_instances       # xcsp3 instances used in the experiments
│   └── xcsp3_overview.csv    # metadata about the xcsp3 instances
├── experiments.py            # experiment runner script
├── globalconstraints         # main implementation of the global constraints
│   ├── __init__.py
│   ├── alldifferent.py
│   ├── cumulative.py
│   ├── gcc.py
│   ├── inverse.py
│   ├── negative_table.py
│   ├── nooverlap.py
│   ├── regular.py
│   ├── superclass.py
│   └── table.py
├── models.py                  # CPMpy model generation functions
└── utils.py                   # utilities
```