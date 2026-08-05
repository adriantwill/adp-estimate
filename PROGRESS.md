# Project Progress

## Current Goal

Build a model that identifies wide receivers likely to outperform or underperform
their fantasy-football ADP using only information available before the predicted
season.

## Progress So Far

- Built the historical data pipeline for joining PFF receiving statistics, ADP,
  and next-season fantasy results.
- Created an ADP-relative target, `expected_diff`, so the main model predicts
  performance above or below draft-slot expectations instead of raw fantasy
  points.
- Kept model evaluation chronological, with earlier seasons used for training and
  later seasons used for testing.
- Built a projected target-share model in `src/proj_staps.py` using prior-season
  player production and preseason depth-chart information.
- Added player-context features for team changes, rookies, newcomers, teammate
  target-share totals, top teammate shares, prior target-share rank, and position-room
  size.
- Tested ElasticNet and other model options for projected target share.
- Reached approximately `0.02` projected target-share MSE, compared with an
  approximately `0.03` baseline MSE.
- Prepared the projected target-share work for eventual integration into the main
  ADP-value model.

## Validation Work Before Full Integration

- Construct prediction rows from preseason depth charts without requiring actual
  target-season statistics. Actual target share should be joined only as the
  training or evaluation label.
- Generate expanding-window predictions: train on seasons before a target year,
  then predict that target year. This prevents in-sample stacking leakage when
  projected target share becomes a `main.py` feature.
- Preserve a stable player identifier, normalized player name, team, and target
  season in the projected-target-share output.
- Join seasons carefully: a `main.py` row containing 2024 player statistics predicts
  2025 performance and therefore needs projected 2025 target share.
- Compare the same player cohort across three models: ADP baseline, ADP plus PFF
  features, and ADP plus PFF features plus projected target share.
- Apply the top-150 ADP filter consistently to training and test data.
- Standardize features before fitting ElasticNet and report MSE and RMSE with clear,
  consistent labels.
- Prefer regular-season statistics over combined regular-season and postseason
  statistics.

## Next Step

Collect historical college-player statistics from a college-football API. Use these
statistics to build rookie features, since rookies do not have prior NFL production.
Important candidate features include college target share, dominator rating,
receiving efficiency, breakout age, draft capital, and age or experience.

After college data collection, produce leakage-safe projected target-share features
and measure whether they improve unseen-season performance in `main.py`.
