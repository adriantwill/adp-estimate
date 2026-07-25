import re
from pathlib import Path
from typing import Literal

import nflreadpy as nfl
import pandas as pd
import polars as pl

from src.path import (
    MERGED_QB_CSV,
    MERGED_WR_CSV,
    PASSING_FINISH_DIR,
    PFF_PASSING_DIR,
    PFF_RECEIVING_DIR,
    PROS_BB_ADP_DIR,
    RECEIVING_FINISH_DIR,
)
from util import normalize_player_name

TEAM_CODE_MAP = {
    "BLT": "BAL",
    "CLV": "CLE",
    "HST": "HOU",
    "ARZ": "ARI",
    "LA": "LAR",
    "JAX": "JAC",
}
YEARS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
Position = Literal["QB", "RB", "WR", "TE"]


def main():
    merge_wr_csvs()
    merge_qb_csvs()


def csv_df_list(path: Path) -> list:
    dfs = []
    for file_path in path.iterdir():
        if file_path.suffix != ".csv":
            continue
        df = pd.read_csv(file_path)
        year = re.search(r"\d{4}", file_path.name).group()
        df["year"] = int(year)
        print(str(path))
        match path.name:
            case "pff_recieving":
                max_targets = df["targets"].max()
                df = df[df["targets"] >= max_targets * 0.10]
            case "pff_passing":
                max_attempts = df["attempts"].max()
                df = df[df["attempts"] >= max_attempts * 0.1]
            case "pros_bb_adp":
                df = df[["year", "Player", "AVG", "POS"]]
                df = df.rename(columns={"POS": "position"})
                df["position"] = df["position"].str.replace(r"\d+", "", regex=True)
                df = df.rename(columns={"Player": "player"})
                df["year"] = int(year) - 1
            case "recieving_finish":
                df["year"] = int(year) - 1
            case "passing_finish":
                df["year"] = int(year) - 1
                df["position"] = "QB"
        dfs.append(df)
    return dfs


def merge_wr_csvs():
    pff_dfs = csv_df_list(PFF_RECEIVING_DIR)
    adp_dfs = csv_df_list(PROS_BB_ADP_DIR)
    finish_dfs = csv_df_list(RECEIVING_FINISH_DIR)
    clean_data(pff_dfs + adp_dfs + finish_dfs, "WR")
    adp = pd.concat(adp_dfs, ignore_index=True)
    recieving = pd.concat(pff_dfs, ignore_index=True)
    finish = pd.concat(finish_dfs, ignore_index=True)
    merged = pd.merge(
        recieving,
        adp,
        on=["player", "year", "position"],
        how="inner",
    )
    merged = pd.merge(
        merged,
        finish[
            [
                "player",
                "position",
                "year",
                "fantasyPts",
                "ptsPerSnap",
                "ptsPerTouch",
            ]
        ],
        on=["player", "position", "year"],
        how="inner",
    )
    merged = expected_points(merged)
    merged["team_name"] = merged["team_name"].replace(TEAM_CODE_MAP)
    years = merged["year"].unique().astype(int).tolist()
    stats = nfl.load_depth_charts(seasons=years)
    merged["proj_qb"] = merged.apply(proj_qb_starter, axis=1, args=(stats,))
    print("compelte merge")
    merged.to_csv(MERGED_WR_CSV, index=False)


def proj_qb_starter(row, stats):
    stats = stats[row["year"]]
    team = row["team_name"]
    qb = stats.filter(
        (pl.col("club_code") == team)
        & (pl.col("position") == "QB")
        & (pl.col("depth_team") == "1")
        & (pl.col("week") == 1)
        & (pl.col("season") == row["year"])
    )
    print(qb)
    return qb["full_name"]


def expected_points(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["year", "AVG"]).copy()
    df["bucket"] = df.groupby("year").cumcount() // 6
    expected_points = (
        df[df["year"] < 2024].groupby("bucket")["fantasyPts"].mean().to_frame("mean")
    )
    expected_points["median"] = (
        df[df["year"] < 2024].groupby("bucket")["fantasyPts"].median()
    )
    expected_points["1st_q"] = df.groupby("bucket")["fantasyPts"].quantile(0.25)
    expected_points["3st_q"] = df.groupby("bucket")["fantasyPts"].quantile(0.75)
    df["expected_diff"] = round(
        (df["fantasyPts"] - df["bucket"].map(expected_points["median"])), 3
    )
    return df


def merge_qb_csvs():
    pff_dfs = csv_df_list(PFF_PASSING_DIR)
    adp_dfs = csv_df_list(PROS_BB_ADP_DIR)
    finish_dfs = csv_df_list(PASSING_FINISH_DIR)
    clean_data(pff_dfs + adp_dfs + finish_dfs, "QB")
    adp = pd.concat(adp_dfs, ignore_index=True)
    passing = pd.concat(pff_dfs, ignore_index=True)
    finish = pd.concat(finish_dfs, ignore_index=True)
    merged = pd.merge(
        passing,
        adp,
        on=["player", "year", "position"],
        how="inner",
    )
    merged = pd.merge(
        merged,
        finish[
            [
                "player",
                "position",
                "year",
                "fantasyPts",
                "ptsPerDb",
            ]
        ],
        on=["player", "position", "year"],
        how="inner",
    )
    print("compelte merge")
    merged.to_csv(MERGED_QB_CSV, index=False)


def clean_data(dataframes: list[pd.DataFrame], pos: Position):
    for df in dataframes:
        df["player"] = df["player"].apply(normalize_player_name)
        non_pos_rows = df.index[~df["position"].isin([pos])]
        df = df.drop(index=non_pos_rows)


if __name__ == "__main__":
    main()
