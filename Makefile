# Usage:
#   make experiments                  # all datasets
#   make experiments <dataset>
#   make experiments SOLVER=ortools
#   make plots                        # all datasets
#   make plots <dataset>
#
# Optional: SOLVER EXPERIMENT_TYPE SEARCH_ORDER TIMEOUT NUM_EXPERIMENTS
#           RESULTS PLOTS PYTHON
# Results land in RESULTS/<dataset>/. Existing JSON files are skipped.

PYTHON          ?= python3
DATASETS        := random-alldiff random-gcc random-cumulative set rcpsp xcsp3

TIMEOUT         ?= 3600
NUM_EXPERIMENTS ?= -1
SEARCH_ORDER    ?= default
RESULTS         ?= results
PLOTS           ?= plots

EXTRA_GOALS := $(filter-out experiments plots help clean,$(MAKECMDGOALS))
DATASET_FROM_GOAL := $(filter $(DATASETS),$(EXTRA_GOALS))
ifneq ($(DATASET_FROM_GOAL),)
  DATASET := $(DATASET_FROM_GOAL)
endif

# Which datasets to run: the one given, or all of them
RUN_DATASETS := $(if $(DATASET),$(DATASET),$(DATASETS))

.PHONY: experiments plots help clean $(DATASETS)

help:
	@echo "make experiments [<dataset>] [SOLVER=...] [EXPERIMENT_TYPE=...] [RESULTS=results]"
	@echo "make plots [<dataset>] [RESULTS=results] [PLOTS=plots]"

experiments:
	@for d in $(RUN_DATASETS); do \
		echo "=== $$d ==="; \
		$(PYTHON) experiments.py \
			--dataset $$d \
			--output-dir $(RESULTS)/$$d \
			--timeout $(TIMEOUT) \
			--num-experiments $(NUM_EXPERIMENTS) \
			--search-order $(SEARCH_ORDER) \
			$(if $(SOLVER),--solver $(SOLVER)) \
			$(if $(EXPERIMENT_TYPE),--experiment-type $(EXPERIMENT_TYPE)); \
	done

plots:
	$(PYTHON) plot_results.py \
		--results $(RESULTS) \
		--output $(PLOTS) \
		$(if $(DATASET),--dataset $(DATASET))

$(DATASETS):
	@:

clean:
ifdef DATASET
	rm -rf $(RESULTS)/$(DATASET) $(PLOTS)/$(DATASET)
else
	rm -rf $(RESULTS) $(PLOTS)
endif
