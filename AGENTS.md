# Repository Guidelines

## Project Structure & Module Organization

- `main.py` loads cleaned player data and trains the current `ElasticNet` model.
- `src/merged_csv.py` cleans and joins historical PFF, ADP, and fantasy-finish CSVs.
- `src/path.py` is the single source of truth for repository data paths.
- `stats_functions/` contains reusable feature-engineering helpers.
- `proj_staps.py` contains depth-chart and projected-starter experiments.
- `data/source/` holds input datasets; `data/clean/` holds generated merged datasets.

Keep reusable pipeline logic in `src/`. Do not duplicate path constants or data-cleaning rules in entry-point scripts.

## Current Modeling Focus

Current work studies expected fantasy performance from ADP and trains models against the difference between expected and actual results. Prioritize identifying shared traits among players who significantly outperform or underperform ADP. Preserve chronological validation and use only information available before the predicted season.

## Build, Test, and Development Commands

This repository is a Python project without a packaging or build configuration. Use the checked-in virtual environment for all commands:

```bash
.venv/bin/python main.py
.venv/bin/python -m src.merged_csv
.venv/bin/python -m compileall main.py src stats_functions
```

The first command trains and evaluates the model. The second rebuilds merged CSV files and may fetch NFL data. The third performs a basic syntax check. Install packages only through `.venv/bin/python -m pip`; never use bare `pip`.

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation. Use `snake_case` for modules, functions, and variables; use `UPPER_CASE` for constants such as `MERGED_WR_CSV`. Group imports as standard library, third-party packages, then local modules. Add type hints to public functions and prefer `pathlib.Path` over string paths.

No formatter or linter is configured. Keep changes focused and avoid unrelated formatting.

## Testing Guidelines

No automated test suite or coverage threshold currently exists. For new tests, use `tests/test_<module>.py` and name cases `test_<behavior>`. Prefer `pytest`, run with:

```bash
.venv/bin/python -m pytest
```

For data-pipeline changes, verify row counts, required columns, year alignment, and absence of target leakage.

## Commit & Pull Request Guidelines

Recent commits use short, lowercase, imperative summaries, such as `organize files` and `add function for getting projected qb starter`. Keep each commit limited to one logical change.

Pull requests should explain purpose, affected datasets, validation commands, and results. Call out schema changes, generated CSV changes, network-dependent steps, and any modeling assumptions. Link relevant issues when available.
