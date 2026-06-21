from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_PBP_GROUP_COLS = ("season", "posteam")
DEFAULT_PLAYER_GROUP_COLS = ("season", "recent_team")
DEFAULT_FTN_GROUP_COLS = ("season", "posteam")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


def _group_columns(df: pd.DataFrame, group_cols: tuple[str, ...]) -> list[str]:
    cols = [col for col in group_cols if col in df.columns]
    if not cols:
        raise KeyError(f"None of the grouping columns exist: {group_cols}")
    return cols


def _require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def _numeric_flag(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(0, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(0)


def filter_offensive_pbp(pbp: pd.DataFrame) -> pd.DataFrame:
    # Returns filtered offensive plays plus _pass_attempt, _rush_attempt, _offensive_play.
    _require_columns(pbp, ["posteam", "play_type"])

    mask = pbp["posteam"].notna() & pbp["play_type"].isin(["pass", "run"])

    if "season_type" in pbp.columns:
        mask &= pbp["season_type"].eq("REG")
    if "play_deleted" in pbp.columns:
        mask &= _numeric_flag(pbp, "play_deleted").ne(1)
    if "qb_kneel" in pbp.columns:
        mask &= _numeric_flag(pbp, "qb_kneel").ne(1)
    if "qb_spike" in pbp.columns:
        mask &= _numeric_flag(pbp, "qb_spike").ne(1)

    plays = pbp.loc[mask].copy()
    plays["_pass_attempt"] = (
        _numeric_flag(plays, "pass_attempt")
        if "pass_attempt" in plays.columns
        else plays["play_type"].eq("pass").astype(float)
    )
    plays["_rush_attempt"] = (
        _numeric_flag(plays, "rush_attempt")
        if "rush_attempt" in plays.columns
        else plays["play_type"].eq("run").astype(float)
    )
    plays["_offensive_play"] = 1.0
    return plays


def add_pace_seconds_per_play(
    plays: pd.DataFrame, group_cols: tuple[str, ...] = DEFAULT_PBP_GROUP_COLS
) -> pd.Series:
    required = ["game_id", "play_id", "game_seconds_remaining"]
    if any(col not in plays.columns for col in required):
        groups = _group_columns(plays, group_cols)
        return pd.Series(np.nan, index=plays.groupby(groups).size().index)

    groups = _group_columns(plays, group_cols)
    sort_cols = groups + ["game_id", "play_id"]
    pace = plays.sort_values(sort_cols).copy()
    pace["_prev_game_seconds_remaining"] = pace.groupby(groups + ["game_id"])[
        "game_seconds_remaining"
    ].shift(1)
    pace["_seconds_since_prev_play"] = (
        pace["_prev_game_seconds_remaining"] - pace["game_seconds_remaining"]
    )
    valid = pace["_seconds_since_prev_play"].between(1, 120)
    return pace.loc[valid].groupby(groups)["_seconds_since_prev_play"].mean()


def calculate_team_pbp_stats(
    pbp: pd.DataFrame, group_cols: tuple[str, ...] = DEFAULT_PBP_GROUP_COLS
) -> pd.DataFrame:
    # Returns offensive plays, pass/rush attempts, pass rates, pace, red-zone rates,
    # EPA, success rates, touchdown rate, red-zone trips, and points per game.
    # Rush includes qb scrambles
    plays = filter_offensive_pbp(pbp)
    groups = _group_columns(plays, group_cols)
    grouped = plays.groupby(groups, dropna=False)

    out = grouped.size().rename("offensive_plays").to_frame()
    out["pass_attempts"] = grouped["_pass_attempt"].sum()
    out["rush_attempts"] = grouped["_rush_attempt"].sum()
    out["pass_rate"] = _safe_divide(
        out["pass_attempts"], out["pass_attempts"] + out["rush_attempts"]
    )

    if {"qtr", "score_differential", "down"}.issubset(plays.columns):
        neutral = (
            plays["qtr"].le(3)
            & plays["score_differential"].abs().le(8)
            & plays["down"].isin([1, 2])
        )
        plays["_neutral_play"] = neutral.astype(float)
        plays["_neutral_pass"] = (neutral & plays["_pass_attempt"].eq(1)).astype(float)
        neutral_grouped = plays.groupby(groups, dropna=False)
        out["neutral_pass_rate"] = _safe_divide(
            neutral_grouped["_neutral_pass"].sum(),
            neutral_grouped["_neutral_play"].sum(),
        )
    else:
        out["neutral_pass_rate"] = np.nan

    if "game_id" in plays.columns:
        games = grouped["game_id"].nunique()
        out["plays_per_game"] = _safe_divide(out["offensive_plays"], games)
    else:
        games = pd.Series(np.nan, index=out.index)
        out["plays_per_game"] = np.nan

    out["pace_seconds_per_play"] = add_pace_seconds_per_play(plays, group_cols)

    if "yardline_100" in plays.columns:
        plays["_red_zone_play"] = plays["yardline_100"].le(20).astype(float)
        plays["_red_zone_pass"] = (
            plays["yardline_100"].le(20) & plays["_pass_attempt"].eq(1)
        ).astype(float)
        rz_grouped = plays.groupby(groups, dropna=False)
        out["red_zone_rate"] = _safe_divide(
            rz_grouped["_red_zone_play"].sum(), out["offensive_plays"]
        )
        out["red_zone_pass_rate"] = _safe_divide(
            rz_grouped["_red_zone_pass"].sum(), rz_grouped["_red_zone_play"].sum()
        )

        if {"game_id", "drive"}.issubset(plays.columns):
            rz_drives = (
                plays.loc[plays["_red_zone_play"].eq(1), groups + ["game_id", "drive"]]
                .drop_duplicates()
                .groupby(groups, dropna=False)
                .size()
            )
            out["red_zone_trips_per_game"] = _safe_divide(rz_drives, games)
        else:
            out["red_zone_trips_per_game"] = np.nan
    else:
        out["red_zone_rate"] = np.nan
        out["red_zone_pass_rate"] = np.nan
        out["red_zone_trips_per_game"] = np.nan

    if "down" in plays.columns:
        plays["_first_down_play"] = plays["down"].eq(1).astype(float)
        plays["_first_down_pass"] = (
            plays["down"].eq(1) & plays["_pass_attempt"].eq(1)
        ).astype(float)
        down_grouped = plays.groupby(groups, dropna=False)
        out["first_down_pass_rate"] = _safe_divide(
            down_grouped["_first_down_pass"].sum(),
            down_grouped["_first_down_play"].sum(),
        )
    else:
        out["first_down_pass_rate"] = np.nan

    out["pass_oe"] = grouped["pass_oe"].mean() if "pass_oe" in plays.columns else np.nan

    if "epa" in plays.columns:
        out["offensive_epa_per_play"] = grouped["epa"].mean()
        out["epa_per_play"] = grouped["epa"].mean()
        plays["_dropback_epa"] = plays["epa"].where(
            _numeric_flag(plays, "qb_dropback").eq(1)
        )
        plays["_rush_epa"] = plays["epa"].where(plays["_rush_attempt"].eq(1))
        epa_grouped = plays.groupby(groups, dropna=False)
        out["dropback_epa"] = epa_grouped["_dropback_epa"].mean()
        out["rush_epa"] = epa_grouped["_rush_epa"].mean()
    else:
        out["offensive_epa_per_play"] = np.nan
        out["epa_per_play"] = np.nan
        out["dropback_epa"] = np.nan
        out["rush_epa"] = np.nan

    if "success" in plays.columns:
        out["success_rate"] = grouped["success"].mean()
        plays["_dropback_success"] = plays["success"].where(
            _numeric_flag(plays, "qb_dropback").eq(1)
        )
        plays["_rush_success"] = plays["success"].where(plays["_rush_attempt"].eq(1))
        success_grouped = plays.groupby(groups, dropna=False)
        out["dropback_success_rate"] = success_grouped["_dropback_success"].mean()
        out["rush_success_rate"] = success_grouped["_rush_success"].mean()
    else:
        out["success_rate"] = np.nan
        out["dropback_success_rate"] = np.nan
        out["rush_success_rate"] = np.nan

    if {"pass_touchdown", "rush_touchdown"}.issubset(plays.columns):
        plays["_offensive_touchdown"] = (
            _numeric_flag(plays, "pass_touchdown").eq(1)
            | _numeric_flag(plays, "rush_touchdown").eq(1)
        ).astype(float)
    elif {"touchdown", "td_team", "posteam"}.issubset(plays.columns):
        plays["_offensive_touchdown"] = (
            _numeric_flag(plays, "touchdown").eq(1)
            & plays["td_team"].eq(plays["posteam"])
        ).astype(float)
    else:
        plays["_offensive_touchdown"] = np.nan
    out["touchdown_rate"] = plays.groupby(groups, dropna=False)[
        "_offensive_touchdown"
    ].mean()

    score_col = None
    for candidate in ["posteam_score_post", "posteam_score"]:
        if candidate in plays.columns:
            score_col = candidate
            break
    if score_col and "game_id" in plays.columns:
        game_points = plays.groupby(groups + ["game_id"], dropna=False)[score_col].max()
        out["points_per_game"] = game_points.groupby(
            level=list(range(len(groups)))
        ).mean()
    else:
        out["points_per_game"] = np.nan

    return out.reset_index()


def calculate_target_concentration(
    stats_player: pd.DataFrame,
    group_cols: tuple[str, ...] = DEFAULT_PLAYER_GROUP_COLS,
) -> pd.DataFrame:
    # Returns top WR target shares, WR/TE target share, and top-2 WR WOPR share.
    _require_columns(stats_player, ["position"])
    groups = _group_columns(stats_player, group_cols)
    df = stats_player.copy()
    df["position"] = df["position"].astype(str).str.upper()

    if "target_share" not in df.columns:
        _require_columns(df, ["targets"])
        team_targets = df.groupby(groups, dropna=False)["targets"].transform("sum")
        df["target_share"] = _safe_divide(df["targets"], team_targets)

    base = df[groups].drop_duplicates().set_index(groups)

    def top_sum(position: str, column: str, n: int) -> pd.Series:
        if column not in df.columns:
            return pd.Series(np.nan, index=base.index)
        subset = df[df["position"].eq(position)].sort_values(groups + [column])
        top = subset.groupby(groups, dropna=False).tail(n)
        return top.groupby(groups, dropna=False)[column].sum()

    out = base.copy()
    out["top_1_wr_target_share"] = top_sum("WR", "target_share", 1)
    out["top_2_wr_target_share"] = top_sum("WR", "target_share", 2)
    out["top_3_wr_target_share"] = top_sum("WR", "target_share", 3)
    out["wr_target_share"] = (
        df[df["position"].eq("WR")].groupby(groups, dropna=False)["target_share"].sum()
    )
    out["te_target_share"] = (
        df[df["position"].eq("TE")].groupby(groups, dropna=False)["target_share"].sum()
    )
    out["wopr_concentration"] = top_sum("WR", "wopr", 2)
    return out.reset_index().fillna(0)


def calculate_ftn_team_scheme_stats(
    ftn_charting: pd.DataFrame,
    group_cols: tuple[str, ...] = DEFAULT_FTN_GROUP_COLS,
) -> pd.DataFrame:
    # Returns FTN play count, scheme rates, average backfield count, and average box count.
    df = ftn_charting.copy()
    if "posteam" not in df.columns and "team" in df.columns:
        df = df.rename(columns={"team": "posteam"})

    groups = _group_columns(df, group_cols)
    grouped = df.groupby(groups, dropna=False)
    out = grouped.size().rename("ftn_plays").to_frame()

    rate_cols = {
        "motion_rate": "is_motion",
        "play_action_rate": "is_play_action",
        "screen_rate": "is_screen_pass",
        "rpo_rate": "is_rpo",
        "no_huddle_rate": "is_no_huddle",
        "trick_play_rate": "is_trick_play",
        "qb_out_of_pocket_rate": "is_qb_out_of_pocket",
    }
    for output_col, source_col in rate_cols.items():
        out[output_col] = (
            grouped[source_col].mean() if source_col in df.columns else np.nan
        )

    structure_cols = {
        "avg_offense_backfield": "n_offense_backfield",
        "avg_defense_box": "n_defense_box",
    }
    for output_col, source_col in structure_cols.items():
        out[output_col] = (
            grouped[source_col].mean() if source_col in df.columns else np.nan
        )

    return out.reset_index()
