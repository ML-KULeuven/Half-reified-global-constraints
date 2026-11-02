"""
Load experiment JSON results into a DataFrame and plot ECDFs.

Expects RESULTS/<dataset>/.../*.json (one subfolder per dataset).
One figure per (dataset, experiment_type, solver), with a line per constraint.
"""
import json
from glob import glob
from os import listdir, makedirs
from os.path import isdir, join

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_ecdf(df, ax):
    """ECDF of total runtime, one curve per constraint. Uses only non-timeout runs."""
    plot_df = df.copy()
    plot_df["total_time"] = plot_df["init_time"] + plot_df["solve_time"]
    sns.ecdfplot(
        data=plot_df[plot_df["status"] != "timeout"],
        x="total_time",
        hue="constraint",
        stat="count",
        ax=ax,
    )
    return ax


def load_dataset(results_dir, dataset):
    """Load all JSON results for one dataset into a DataFrame."""
    paths = sorted(glob(join(results_dir, dataset, "**", "*.json"), recursive=True))
    if not paths:
        return pd.DataFrame()

    rows = []
    for path_ in paths:
        with open(path_) as f:
            data = json.load(f)
        row = dict(data["instance"])
        for key, val in data.items():
            if key != "instance":
                row[key] = val
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot ECDFs from experiment JSON results")
    parser.add_argument("--results", default="results", help="Root results directory (dataset subfolders)")
    parser.add_argument("--output", default="plots", help="Directory for saved figures")
    parser.add_argument("--dataset", default=None, help="Only plot this dataset (default: all under --results)")
    args = parser.parse_args()

    if args.dataset is not None:
        datasets = [args.dataset]
    else:
        datasets = sorted(name for name in listdir(args.results) if isdir(join(args.results, name)))

    if not datasets:
        raise SystemExit(f"No dataset subfolders under {args.results}")

    for dataset in datasets:
        df = load_dataset(args.results, dataset)
        if df.empty:
            print(f"Skipping {dataset}: no JSON results")
            continue

        for (experiment_type, solver), group in df.groupby(["experiment_type", "solver"]):
            out_dir = join(args.output, dataset)
            makedirs(out_dir, exist_ok=True)
            out_path = join(out_dir, f"{solver}-{experiment_type}.png")

            fig, ax = plt.subplots(figsize=(8, 5))
            plot_ecdf(group, ax)
            ax.set_title(f"{dataset} | {solver} | {experiment_type}")
            ax.set_xlabel("Runtime (s)")
            ax.set_ylabel("Number of instances solved")
            fig.savefig(out_path, bbox_inches="tight")
            plt.close(fig)
            print(f"Wrote {out_path}")
