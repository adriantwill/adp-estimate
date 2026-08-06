"""Leakage-safe experiment for beating wide-receiver ADP.

Each row in ``merged_wr.csv`` uses season ``year`` information to predict the
following season.  The experiment treats ADP as a strong prior, then predicts
where football context should move that prior up or down.

Run with::

    .venv/bin/python test_codex.py

NFLverse downloads require an internet connection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import nflreadpy as nfl
import numpy as np
import polars as pl
from sklearn.base import RegressorMixin
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

WR_DATA = Path("data/clean/merged_wr.csv")
FIRST_YEAR = 2017
FINAL_HOLDOUT_YEAR = 2024
ADP_CUTOFF = 150.0
SKILL_POSITIONS = ["WR", "TE", "RB", "FB"]
ACTIVE_STATUSES = ["ACT", "INA"]

TEAM_CODE_MAP = {
    "ARZ": "ARI",
    "BLT": "BAL",
    "CLV": "CLE",
    "HST": "HOU",
    "JAX": "JAC",
    "LA": "LAR",
    "OAK": "LV",
    "SD": "LAC",
    "STL": "LAR",
    "WAS": "WAS",
}

ADP_FEATURES = ["log_adp", "inverse_sqrt_adp", "adp_top_36", "adp_top_72"]

WR_FEATURES = [
    "age",
    "age_squared",
    "age_over_29",
    "years_exp",
    "draft_number",
    "player_game_count",
    "routes_per_game",
    "targets_per_game",
    "targets_per_route",
    "receptions_per_game",
    "yards_per_game",
    "touchdowns_per_game",
    "prior_ppr_per_game",
    "first_downs_per_target",
    "epa_per_target",
    "avg_depth_of_target",
    "caught_percent",
    "drop_rate",
    "grades_offense",
    "grades_pass_route",
    "positive_epa_percent",
    "targeted_qb_rating",
    "yards_after_catch_per_reception",
    "yards_per_reception",
    "yprr",
    "last_year_fantasy_points",
    "last_year_adp",
    "two_year_targets_per_game",
    "two_year_yards_per_game",
    "two_year_yprr",
    "targets_per_game_change",
    "yards_per_game_change",
    "yprr_change",
]

TARGET_SHARE_FEATURES = [
    "prior_target_share",
    "prior_air_yards_share",
    "prior_wopr",
    "projected_target_share",
    "roster_prior_target_share",
    "returning_target_share",
    "vacated_target_share",
    "top_roster_target_share",
    "competitor_target_share",
    "skill_player_count",
    "newcomer_count",
    "rookie_count",
    "changed_team",
    "on_active_week_one_roster",
]

QB_FEATURES = [
    "qb_attempts_per_game",
    "qb_yards_per_attempt",
    "qb_touchdown_rate",
    "qb_interception_rate",
    "qb_epa_per_attempt",
    "qb_cpoe",
    "qb_fantasy_points_per_game",
    "qb_continuity",
    "qb_has_prior_stats",
]

TEAM_FEATURES = [
    "team_attempts_per_game",
    "team_yards_per_attempt",
    "team_touchdown_rate",
    "team_interception_rate",
    "team_epa_per_attempt",
    "team_cpoe",
    "team_sack_rate",
    "team_receiving_yac_per_catch",
    "team_rushing_epa_per_carry",
]

CONTEXT_FEATURES = (
    WR_FEATURES + TARGET_SHARE_FEATURES + QB_FEATURES + TEAM_FEATURES
)


@dataclass(frozen=True)
class Candidate:
    """One residual-model option selected without seeing final holdout."""

    name: str
    model_kind: str
    feature_group: str
    residual_weight: float


@dataclass(frozen=True)
class Metrics:
    """Prediction quality on one or more chronological folds."""

    rmse: float
    mae: float
    rank_correlation: float


def normalize_name(value: str | None) -> str:
    """Return stable join key for PFF and NFLverse player names."""

    name = str(value or "").lower()
    name = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", name)
    return re.sub(r"[^a-z0-9]+", "", name)


def safe_ratio(numerator: str, denominator: str, alias: str) -> pl.Expr:
    """Build division expression that leaves bad denominators missing."""

    return (
        pl.when(pl.col(denominator).fill_null(0) > 0)
        .then(pl.col(numerator) / pl.col(denominator))
        .otherwise(None)
        .alias(alias)
    )


def load_nflverse_data() -> tuple[
    pl.DataFrame,
    pl.DataFrame,
    pl.DataFrame,
    pl.DataFrame,
]:
    """Load only seasons needed for historical features and roster context."""

    prior_seasons = list(range(FIRST_YEAR, FINAL_HOLDOUT_YEAR + 1))
    prediction_seasons = list(range(FIRST_YEAR + 1, FINAL_HOLDOUT_YEAR + 2))
    player_stats = nfl.load_player_stats(
        seasons=prior_seasons,
        summary_level="reg",
    )
    team_stats = nfl.load_team_stats(
        seasons=prior_seasons,
        summary_level="reg",
    )
    weekly_rosters = nfl.load_rosters_weekly(seasons=prediction_seasons)
    schedules = nfl.load_schedules(seasons=prediction_seasons)
    return player_stats, team_stats, weekly_rosters, schedules


def prepare_player_stats(player_stats: pl.DataFrame) -> pl.DataFrame:
    """Create prior-season player rates used by WR roster and QB joins."""

    return (
        player_stats.with_columns(
            pl.col("season").cast(pl.Int64),
            pl.col("recent_team").replace(TEAM_CODE_MAP),
            pl.col("player_display_name")
            .map_elements(normalize_name, return_dtype=pl.String)
            .alias("player_key"),
        )
        .with_columns(
            safe_ratio("targets", "games", "nfl_targets_per_game"),
            safe_ratio("attempts", "games", "qb_attempts_per_game"),
            safe_ratio("passing_yards", "attempts", "qb_yards_per_attempt"),
            safe_ratio("passing_tds", "attempts", "qb_touchdown_rate"),
            safe_ratio(
                "passing_interceptions", "attempts", "qb_interception_rate"
            ),
            safe_ratio("passing_epa", "attempts", "qb_epa_per_attempt"),
            safe_ratio(
                "fantasy_points", "games", "qb_fantasy_points_per_game"
            ),
        )
    )


def prepare_week_one_rosters(rosters: pl.DataFrame) -> pl.DataFrame:
    """Keep best Week-1 roster record per player and season."""

    status_priority = (
        pl.when(pl.col("status") == "ACT")
        .then(0)
        .when(pl.col("status") == "INA")
        .then(1)
        .when(pl.col("status").is_in(["RES", "PUP", "NFI"]))
        .then(2)
        .otherwise(3)
        .alias("status_priority")
    )
    return (
        rosters.filter(pl.col("week") == 1)
        .with_columns(
            pl.col("season").cast(pl.Int64),
            pl.col("team").replace(TEAM_CODE_MAP),
            pl.col("full_name")
            .map_elements(normalize_name, return_dtype=pl.String)
            .alias("player_key"),
            status_priority,
        )
        .sort(["season", "gsis_id", "status_priority"])
        .unique(["season", "gsis_id"], keep="first")
    )


def build_roster_context(
    rosters: pl.DataFrame,
    player_stats: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build projected target competition from Week-1 roster and prior stats."""

    prior_opportunity = player_stats.select(
        pl.col("season").alias("prior_season"),
        "player_id",
        pl.col("recent_team").alias("prior_team"),
        pl.col("target_share").alias("prior_target_share"),
        pl.col("air_yards_share").alias("prior_air_yards_share"),
        pl.col("wopr").alias("prior_wopr"),
        "nfl_targets_per_game",
    )
    skill_roster = (
        rosters.filter(
            pl.col("position").is_in(SKILL_POSITIONS)
            & pl.col("status").is_in(ACTIVE_STATUSES)
        )
        .with_columns((pl.col("season") - 1).alias("prior_season"))
        .join(
            prior_opportunity,
            left_on=["prior_season", "gsis_id"],
            right_on=["prior_season", "player_id"],
            how="left",
        )
        .with_columns(
            (pl.col("prior_team") == pl.col("team"))
            .fill_null(False)
            .cast(pl.Int8)
            .alias("returning_player"),
            pl.col("prior_target_share").fill_null(0.0),
            pl.col("prior_air_yards_share").fill_null(0.0),
            pl.col("prior_wopr").fill_null(0.0),
            pl.col("nfl_targets_per_game").fill_null(0.0),
            (pl.col("rookie_year") == pl.col("season"))
            .fill_null(False)
            .cast(pl.Int8)
            .alias("rookie"),
        )
        .with_columns(
            pl.when(pl.col("prior_target_share") > 0)
            .then(pl.col("prior_target_share"))
            .when(
                (pl.col("position") == "WR")
                & (pl.col("draft_number").fill_null(999) <= 100)
            )
            .then(0.12)
            .when(pl.col("position") == "WR")
            .then(0.04)
            .when(pl.col("position") == "TE")
            .then(0.035)
            .otherwise(0.025)
            .alias("opportunity_score")
        )
    )

    team_context = (
        skill_roster.group_by(["season", "team"])
        .agg(
            pl.col("opportunity_score").sum().alias("team_opportunity_score"),
            pl.col("prior_target_share").sum().alias("roster_prior_target_share"),
            pl.when(pl.col("returning_player") == 1)
            .then(pl.col("prior_target_share"))
            .otherwise(0.0)
            .sum()
            .alias("returning_target_share"),
            pl.col("prior_target_share").max().alias("top_roster_target_share"),
            pl.len().alias("skill_player_count"),
            (pl.col("returning_player") == 0).sum().alias("newcomer_count"),
            pl.col("rookie").sum().alias("rookie_count"),
        )
        .with_columns(
            (1.0 - pl.col("returning_target_share"))
            .clip(0.0, 1.0)
            .alias("vacated_target_share")
        )
    )

    player_context = skill_roster.select(
        "season",
        "team",
        "gsis_id",
        "prior_target_share",
        "prior_air_yards_share",
        "prior_wopr",
        "opportunity_score",
    )
    return player_context, team_context


def build_qb_context(
    schedules: pl.DataFrame,
    player_stats: pl.DataFrame,
) -> pl.DataFrame:
    """Use Week-1 starter as preseason projected-QB proxy, then add prior stats."""

    week_one = schedules.filter(
        (pl.col("week") == 1) & (pl.col("game_type") == "REG")
    )
    home = week_one.select(
        pl.col("season").cast(pl.Int64),
        pl.col("home_team").replace(TEAM_CODE_MAP).alias("team"),
        pl.col("home_qb_id").alias("qb_id"),
    )
    away = week_one.select(
        pl.col("season").cast(pl.Int64),
        pl.col("away_team").replace(TEAM_CODE_MAP).alias("team"),
        pl.col("away_qb_id").alias("qb_id"),
    )
    qb_prior = player_stats.select(
        pl.col("season").alias("prior_season"),
        pl.col("player_id").alias("qb_id"),
        pl.col("recent_team").alias("qb_prior_team"),
        "qb_attempts_per_game",
        "qb_yards_per_attempt",
        "qb_touchdown_rate",
        "qb_interception_rate",
        "qb_epa_per_attempt",
        pl.col("passing_cpoe").alias("qb_cpoe"),
        "qb_fantasy_points_per_game",
    )
    return (
        pl.concat([home, away])
        .unique(["season", "team"])
        .with_columns((pl.col("season") - 1).alias("prior_season"))
        .join(qb_prior, on=["prior_season", "qb_id"], how="left")
        .with_columns(
            (pl.col("qb_prior_team") == pl.col("team"))
            .fill_null(False)
            .cast(pl.Int8)
            .alias("qb_continuity"),
            pl.col("qb_attempts_per_game")
            .is_not_null()
            .cast(pl.Int8)
            .alias("qb_has_prior_stats"),
        )
        .drop("prior_season")
    )


def build_team_context(team_stats: pl.DataFrame) -> pl.DataFrame:
    """Create previous-team offensive volume and efficiency rates."""

    return (
        team_stats.with_columns(
            pl.col("season").cast(pl.Int64).alias("year"),
            pl.col("team").replace(TEAM_CODE_MAP),
        )
        .with_columns(
            safe_ratio("attempts", "games", "team_attempts_per_game"),
            safe_ratio("passing_yards", "attempts", "team_yards_per_attempt"),
            safe_ratio("passing_tds", "attempts", "team_touchdown_rate"),
            safe_ratio(
                "passing_interceptions", "attempts", "team_interception_rate"
            ),
            safe_ratio("passing_epa", "attempts", "team_epa_per_attempt"),
            safe_ratio("sacks_suffered", "attempts", "team_sack_rate"),
            safe_ratio(
                "receiving_yards_after_catch",
                "receptions",
                "team_receiving_yac_per_catch",
            ),
            safe_ratio("rushing_epa", "carries", "team_rushing_epa_per_carry"),
            pl.col("passing_cpoe").alias("team_cpoe"),
        )
        .select("year", "team", *TEAM_FEATURES)
    )


def build_modeling_frame() -> pl.DataFrame:
    """Join local PFF history to preseason-safe NFLverse context."""

    player_stats, team_stats, raw_rosters, schedules = load_nflverse_data()
    player_stats = prepare_player_stats(player_stats)
    rosters = prepare_week_one_rosters(raw_rosters)
    player_roster_context, team_roster_context = build_roster_context(
        rosters,
        player_stats,
    )
    qb_context = build_qb_context(schedules, player_stats)
    team_context = build_team_context(team_stats)

    roster_map = rosters.select(
        "season",
        "player_key",
        "team",
        "gsis_id",
        "status",
        "birth_date",
        "years_exp",
        "draft_number",
    )
    raw_wr = pl.read_csv(WR_DATA, infer_schema_length=10_000).with_columns(
        pl.col("year").cast(pl.Int64),
        pl.col("player")
        .map_elements(normalize_name, return_dtype=pl.String)
        .alias("player_key"),
        safe_ratio("targets", "player_game_count", "history_targets_per_game"),
        safe_ratio("yards", "player_game_count", "history_yards_per_game"),
    )
    previous_wr_season = raw_wr.select(
        (pl.col("year") + 1).alias("year"),
        "player_key",
        pl.col("fantasyPts").alias("last_year_fantasy_points"),
        pl.col("AVG").alias("last_year_adp"),
        pl.col("history_targets_per_game").alias("two_year_targets_per_game"),
        pl.col("history_yards_per_game").alias("two_year_yards_per_game"),
        pl.col("yprr").alias("two_year_yprr"),
    )
    wr = (
        raw_wr
        .filter(pl.col("AVG") <= ADP_CUTOFF)
        .with_columns(
            pl.col("year").cast(pl.Int64),
            (pl.col("year") + 1).alias("season"),
            pl.col("team_name").replace(TEAM_CODE_MAP).alias("prior_team"),
            pl.col("AVG").alias("adp"),
            pl.col("AVG").log1p().alias("log_adp"),
            (1.0 / pl.col("AVG").sqrt()).alias("inverse_sqrt_adp"),
            (pl.col("AVG") <= 36).cast(pl.Int8).alias("adp_top_36"),
            (pl.col("AVG") <= 72).cast(pl.Int8).alias("adp_top_72"),
        )
        .join(previous_wr_season, on=["year", "player_key"], how="left")
        .join(roster_map, on=["season", "player_key"], how="left")
        .with_columns(
            pl.col("team").fill_null(pl.col("prior_team")),
            pl.col("birth_date")
            .cast(pl.Date, strict=False)
            .dt.year()
            .alias("birth_year"),
            pl.col("status")
            .is_in(ACTIVE_STATUSES)
            .fill_null(False)
            .cast(pl.Int8)
            .alias("on_active_week_one_roster"),
            (pl.col("team").fill_null(pl.col("prior_team")) != pl.col("prior_team"))
            .cast(pl.Int8)
            .alias("changed_team"),
        )
        .with_columns(
            (pl.col("season") - pl.col("birth_year")).alias("age"),
            safe_ratio("routes", "player_game_count", "routes_per_game"),
            safe_ratio("targets", "player_game_count", "targets_per_game"),
            safe_ratio("targets", "routes", "targets_per_route"),
            safe_ratio("receptions", "player_game_count", "receptions_per_game"),
            safe_ratio("yards", "player_game_count", "yards_per_game"),
            safe_ratio("touchdowns", "player_game_count", "touchdowns_per_game"),
            safe_ratio("first_downs", "targets", "first_downs_per_target"),
            safe_ratio("epa", "targets", "epa_per_target"),
            (
                (pl.col("receptions") + pl.col("yards") / 10 + 6 * pl.col("touchdowns"))
                / pl.col("player_game_count")
            ).alias("prior_ppr_per_game"),
        )
        .with_columns(
            pl.col("age").pow(2).alias("age_squared"),
            (pl.col("age") > 29).cast(pl.Int8).alias("age_over_29"),
            (pl.col("targets_per_game") - pl.col("two_year_targets_per_game")).alias(
                "targets_per_game_change"
            ),
            (pl.col("yards_per_game") - pl.col("two_year_yards_per_game")).alias(
                "yards_per_game_change"
            ),
            (pl.col("yprr") - pl.col("two_year_yprr")).alias("yprr_change"),
        )
        .join(
            player_roster_context,
            on=["season", "team", "gsis_id"],
            how="left",
        )
        .join(team_roster_context, on=["season", "team"], how="left")
        .with_columns(
            pl.when(pl.col("team_opportunity_score") > 0)
            .then(pl.col("opportunity_score") / pl.col("team_opportunity_score"))
            .otherwise(None)
            .alias("projected_target_share"),
            (
                pl.col("roster_prior_target_share")
                - pl.col("prior_target_share").fill_null(0.0)
            )
            .clip(0.0, None)
            .alias("competitor_target_share"),
        )
        .join(qb_context, on=["season", "team"], how="left")
        .join(team_context, on=["year", "team"], how="left")
        .with_columns(
            (
                pl.col("adp").rank("average", descending=True).over("year")
                / pl.len().over("year")
            ).alias("adp_rank_score"),
            (
                pl.col("fantasyPts").rank("average").over("year")
                / pl.len().over("year")
            ).alias("fantasy_rank_score"),
        )
    )
    return wr


def make_baseline_model() -> IsotonicRegression:
    """Return monotonic ADP-to-points calibration curve."""

    return IsotonicRegression(increasing=False, out_of_bounds="clip")


def make_residual_model(kind: str) -> RegressorMixin:
    """Build regularized model for football-context correction."""

    if kind == "ridge":
        return make_pipeline(
            SimpleImputer(add_indicator=True),
            StandardScaler(),
            Ridge(alpha=100.0),
        )
    if kind == "hist_small":
        return HistGradientBoostingRegressor(
            learning_rate=0.035,
            max_iter=250,
            max_leaf_nodes=7,
            min_samples_leaf=25,
            l2_regularization=25.0,
            random_state=42,
        )
    raise ValueError(f"Unknown model kind: {kind}")


def feature_names(group: str) -> list[str]:
    """Return feature set named by candidate configuration."""

    if group == "wr":
        return WR_FEATURES
    if group == "wr_and_targets":
        return WR_FEATURES + TARGET_SHARE_FEATURES
    if group == "all_context":
        return CONTEXT_FEATURES
    if group == "all_plus_adp":
        return ADP_FEATURES + CONTEXT_FEATURES
    raise ValueError(f"Unknown feature group: {group}")


def matrix(frame: pl.DataFrame, columns: list[str]) -> np.ndarray:
    """Convert selected numeric Polars columns to sklearn matrix."""

    return frame.select(columns).cast(pl.Float64).to_numpy()


def predict_fold(
    train: pl.DataFrame,
    test: pl.DataFrame,
    candidate: Candidate | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit ADP prior and optional residual correction for one time split."""

    y_train = train["fantasyPts"].to_numpy()
    y_test = test["fantasyPts"].to_numpy()
    baseline = make_baseline_model()
    baseline.fit(train["adp"].to_numpy(), y_train)
    train_prior = baseline.predict(train["adp"].to_numpy())
    test_prior = baseline.predict(test["adp"].to_numpy())
    if candidate is None:
        return y_test, test_prior

    features = feature_names(candidate.feature_group)
    residual_model = make_residual_model(candidate.model_kind)
    residual_model.fit(matrix(train, features), y_train - train_prior)
    correction = residual_model.predict(matrix(test, features))
    prediction = test_prior + candidate.residual_weight * correction
    return y_test, prediction


def predict_rank_fold(
    train: pl.DataFrame,
    test: pl.DataFrame,
    candidate: Candidate | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Predict within-season finish percentile as correction to ADP percentile."""

    actual = test["fantasy_rank_score"].to_numpy()
    test_prior = test["adp_rank_score"].to_numpy()
    if candidate is None:
        return actual, test_prior

    train_actual = train["fantasy_rank_score"].to_numpy()
    train_prior = train["adp_rank_score"].to_numpy()
    features = feature_names(candidate.feature_group)
    residual_model = make_residual_model(candidate.model_kind)
    residual_model.fit(matrix(train, features), train_actual - train_prior)
    correction = residual_model.predict(matrix(test, features))
    prediction = test_prior + candidate.residual_weight * correction
    return actual, prediction


def rank_correlation(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculate Spearman correlation without adding SciPy dependency."""

    actual_rank = np.argsort(np.argsort(actual, kind="stable"), kind="stable")
    predicted_rank = np.argsort(np.argsort(predicted, kind="stable"), kind="stable")
    return float(np.corrcoef(actual_rank, predicted_rank)[0, 1])


def score(actual: np.ndarray, predicted: np.ndarray) -> Metrics:
    """Calculate point and ranking metrics."""

    return Metrics(
        rmse=float(root_mean_squared_error(actual, predicted)),
        mae=float(mean_absolute_error(actual, predicted)),
        rank_correlation=rank_correlation(actual, predicted),
    )


def validation_predictions(
    frame: pl.DataFrame,
    candidate: Candidate | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Pool expanding-window predictions for model selection years."""

    actual_parts: list[np.ndarray] = []
    prediction_parts: list[np.ndarray] = []
    for test_year in range(2020, FINAL_HOLDOUT_YEAR):
        train = frame.filter(pl.col("year") < test_year)
        test = frame.filter(pl.col("year") == test_year)
        actual, prediction = predict_fold(train, test, candidate)
        actual_parts.append(actual)
        prediction_parts.append(prediction)
    return np.concatenate(actual_parts), np.concatenate(prediction_parts)


def rank_validation_predictions(
    frame: pl.DataFrame,
    candidate: Candidate | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Pool expanding-window rank predictions for model selection years."""

    actual_parts: list[np.ndarray] = []
    prediction_parts: list[np.ndarray] = []
    for test_year in range(2020, FINAL_HOLDOUT_YEAR):
        train = frame.filter(pl.col("year") < test_year)
        test = frame.filter(pl.col("year") == test_year)
        actual, prediction = predict_rank_fold(train, test, candidate)
        actual_parts.append(actual)
        prediction_parts.append(prediction)
    return np.concatenate(actual_parts), np.concatenate(prediction_parts)


def candidates() -> list[Candidate]:
    """Return modest search space; final holdout never chooses among these."""

    options: list[Candidate] = []
    for kind in ["ridge", "hist_small"]:
        for group in ["wr_and_targets", "all_context", "all_plus_adp"]:
            for weight in [0.1, 0.25, 0.5, 0.75]:
                options.append(
                    Candidate(f"{kind}/{group}/{weight}", kind, group, weight)
                )
    return options


def print_metrics(label: str, metrics: Metrics) -> None:
    """Print compact comparable score line."""

    print(
        f"{label:<34} RMSE={metrics.rmse:6.2f}  "
        f"MAE={metrics.mae:6.2f}  rank_r={metrics.rank_correlation:5.3f}"
    )


def main() -> None:
    """Select context correction chronologically, then score final holdout once."""

    frame = build_modeling_frame().sort(["year", "adp"])
    print(
        f"Rows={frame.height}; seasons={frame['year'].min()}-{frame['year'].max()}; "
        f"ADP<={ADP_CUTOFF:.0f}"
    )
    print(
        "Roster matches="
        f"{frame['gsis_id'].is_not_null().sum()}/{frame.height}; "
        "projected target shares="
        f"{frame['projected_target_share'].is_not_null().sum()}/{frame.height}"
    )

    validation_actual, validation_adp = validation_predictions(frame, None)
    validation_adp_metrics = score(validation_actual, validation_adp)
    scored_candidates: list[tuple[float, Candidate, Metrics]] = []
    for candidate in candidates():
        actual, prediction = validation_predictions(frame, candidate)
        metrics = score(actual, prediction)
        scored_candidates.append((metrics.rmse, candidate, metrics))
    scored_candidates.sort(key=lambda item: item[0])
    best = scored_candidates[0][1]

    validation_rank_actual, validation_adp_rank = rank_validation_predictions(
        frame,
        None,
    )
    scored_rank_candidates: list[tuple[float, Candidate]] = []
    for candidate in candidates():
        actual, prediction = rank_validation_predictions(frame, candidate)
        correlation = rank_correlation(actual, prediction)
        scored_rank_candidates.append((correlation, candidate))
    scored_rank_candidates.sort(key=lambda item: item[0], reverse=True)
    best_rank = scored_rank_candidates[0][1]

    print("\nWalk-forward model selection: base seasons 2020-2023")
    print_metrics("ADP only", validation_adp_metrics)
    for _, candidate, metrics in scored_candidates[:5]:
        print_metrics(candidate.name, metrics)
    print(
        "Rank-specific validation: "
        f"ADP={rank_correlation(validation_rank_actual, validation_adp_rank):.3f}; "
        f"{best_rank.name}={scored_rank_candidates[0][0]:.3f}"
    )

    train = frame.filter(pl.col("year") < FINAL_HOLDOUT_YEAR)
    holdout = frame.filter(pl.col("year") == FINAL_HOLDOUT_YEAR)
    holdout_actual, holdout_adp = predict_fold(train, holdout, None)
    _, holdout_model = predict_fold(train, holdout, best)
    adp_metrics = score(holdout_actual, holdout_adp)
    model_metrics = score(holdout_actual, holdout_model)
    holdout_rank_actual, holdout_adp_rank = predict_rank_fold(train, holdout, None)
    _, holdout_model_rank = predict_rank_fold(train, holdout, best_rank)

    print("\nUntouched final holdout: 2024 inputs -> 2025 fantasy points")
    print_metrics("ADP only", adp_metrics)
    print_metrics(best.name, model_metrics)
    improvement = 100 * (adp_metrics.rmse - model_metrics.rmse) / adp_metrics.rmse
    print(f"RMSE improvement over ADP: {improvement:+.2f}%")
    print(
        "Rank-specific model: "
        f"ADP rank_r={rank_correlation(holdout_rank_actual, holdout_adp_rank):.3f}; "
        f"{best_rank.name} rank_r="
        f"{rank_correlation(holdout_rank_actual, holdout_model_rank):.3f}"
    )

    results = holdout.select("player", "adp", "fantasyPts").with_columns(
        pl.Series("adp_prediction", holdout_adp),
        pl.Series("model_prediction", holdout_model),
    )
    results = results.with_columns(
        (pl.col("model_prediction") - pl.col("adp_prediction")).alias(
            "model_adjustment"
        ),
        (pl.col("fantasyPts") - pl.col("adp_prediction")).alias("actual_vs_adp"),
    )
    print("\nLargest model upgrades")
    print(
        results.sort("model_adjustment", descending=True)
        .select(
            "player",
            "adp",
            "model_adjustment",
            "actual_vs_adp",
        )
        .head(10)
    )


if __name__ == "__main__":
    main()
