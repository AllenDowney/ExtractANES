.PHONY: clean lint format requirements extract_codebook run_extract run_eda run_eda_lgbt_rights run_eda_immigration run_notebooks sync_culturewar sync_culturewar_codebook

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = ExtractANES
PYTHON_VERSION = 3.12

# All Python / jupytext / jupyter targets run inside the ExtractANES conda env.
CONDA_RUN = conda run --no-capture-output -n $(PROJECT_NAME)

CDF_STEM = anes_timeseries_cdf_stata_20260205
ANES_HDF = data/interim/anes_extract_$(CDF_STEM).hdf
ANES_LABELS = data/interim/anes_extract_$(CDF_STEM)_labels.csv
ANES_CDF_MINIMAL = codebook/extracted/anes_cdf_minimal.json
ANES_CDF_SUMMARY = codebook/extracted/anes_cdf_summary.csv
CULTUREWAR_NOTEBOOKS = $(HOME)/CultureWar/notebooks
CULTUREWAR_CODEBOOK = $(HOME)/CultureWar/codebook/extracted


#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python Dependencies (into ExtractANES conda env)
requirements:
	$(CONDA_RUN) python -m pip install -U pip setuptools wheel
	$(CONDA_RUN) python -m pip install -r requirements.txt


## Extract ANES CDF variable metadata (HTML codebook + Stata headers)
extract_codebook:
	$(CONDA_RUN) python codebook/extract_cdf_codebook.py


# Notebooks: source of truth is *.md in notebooks/. Convert one-way with
# `jupytext --to ipynb` (do not use `jupytext --sync`, which pairs files).
NBCONVERT = jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600


## Build ANES CDF extract HDF (notebooks/make_cdf_extract.py)
run_extract:
	cd notebooks && $(CONDA_RUN) python make_cdf_extract.py


## Convert explore_cdf_extract.md to ipynb and execute
run_eda:
	cd notebooks && $(CONDA_RUN) jupytext --to ipynb explore_cdf_extract.md
	cd notebooks && $(CONDA_RUN) $(NBCONVERT) explore_cdf_extract.ipynb


## Convert eda_lgbt_rights.md to ipynb and execute (Task 8)
run_eda_lgbt_rights:
	cd notebooks && $(CONDA_RUN) jupytext --to ipynb eda_lgbt_rights.md
	cd notebooks && $(CONDA_RUN) $(NBCONVERT) eda_lgbt_rights.ipynb


## Convert eda_immigration.md to ipynb and execute (Task 9)
run_eda_immigration:
	cd notebooks && $(CONDA_RUN) jupytext --to ipynb eda_immigration.md
	cd notebooks && $(CONDA_RUN) $(NBCONVERT) eda_immigration.ipynb


## Run extract then EDA notebooks
run_notebooks: run_extract run_eda


## Copy ANES CDF codebook metadata to ~/CultureWar/codebook/extracted/
sync_culturewar_codebook:
	@test -f $(ANES_CDF_MINIMAL) || (echo "Missing $(ANES_CDF_MINIMAL); run: make extract_codebook" && exit 1)
	@test -f $(ANES_CDF_SUMMARY) || (echo "Missing $(ANES_CDF_SUMMARY); run: make extract_codebook" && exit 1)
	@mkdir -p $(CULTUREWAR_CODEBOOK)
	cp $(ANES_CDF_MINIMAL) $(CULTUREWAR_CODEBOOK)/
	cp $(ANES_CDF_SUMMARY) $(CULTUREWAR_CODEBOOK)/
	@echo ">>> Copied $(ANES_CDF_MINIMAL) and $(ANES_CDF_SUMMARY) to $(CULTUREWAR_CODEBOOK)/"


## Rebuild extract and copy HDF, labels, and codebook metadata to CultureWar
sync_culturewar: run_extract sync_culturewar_codebook
	@test -d $(CULTUREWAR_NOTEBOOKS) || (echo "Missing $(CULTUREWAR_NOTEBOOKS)" && exit 1)
	cp $(ANES_HDF) $(CULTUREWAR_NOTEBOOKS)/
	cp $(ANES_LABELS) $(CULTUREWAR_NOTEBOOKS)/
	@echo ">>> Copied $(ANES_HDF) and labels to $(CULTUREWAR_NOTEBOOKS)/"


## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
lint:
	$(CONDA_RUN) flake8 notebooks/*.py
	$(CONDA_RUN) black --check --config pyproject.toml notebooks/*.py


## Format source code with black
format:
	$(CONDA_RUN) black --config pyproject.toml notebooks/*.py




## Set up python interpreter environment
create_environment:
	mamba create --name $(PROJECT_NAME) python=$(PYTHON_VERSION) -c conda-forge -y

	@echo ">>> Environment created. Run make targets without manual activate (uses conda run -n $(PROJECT_NAME))."




#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
