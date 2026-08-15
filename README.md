ExtractANES
==============================

Code for making extracts of ANES data

## Notebooks

Source notebooks live as Markdown in `notebooks/*.md`. To convert and run:

```bash
conda activate ExtractANES
make run_notebooks   # extract + EDA
make run_extract     # make_cdf_extract only
make run_eda         # explore_cdf_extract only
```

Convert md → ipynb one-way with `jupytext --to ipynb` — **do not** use `jupytext --sync`.

--------

<p><small>Project organization based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
