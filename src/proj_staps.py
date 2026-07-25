from typing import Tuple

import nflreadpy as nfl
import polars as pl

from util import normalize_player_name


def main():
    year = 2023
    depth = nfl.load_depth_charts(seasons=year)
    stats = nfl.load_player_stats(
        seasons=year, summary_level="reg+post"
    )  # maybe just reg
    proj_wr_starter(depth, stats, "SEA", year)


def player_stats(df: pl.DataFrame) -> Tuple[str, str]:
    year = df["season"].item()
    id = df["player_id"].item()
    stats = nfl.load_player_stats(
        seasons=year, summary_level="reg+post"
    )  # maybe just reg
    wr = stats.filter(pl.col("player_id") == id)
    row = (
        (
            wr.row(0, named=True)["air_yards_share"],
            wr.row(0, named=True)["target_share"],
        )
        if wr.height > 0
        else None
    )
    print(row)
    return row


def proj_wr_starter(depth: pl.DataFrame, stats: pl.DataFrame, team: str, year: int):
    college_stats = pl.read_csv(f"data/source/pff/pff_college/receiving_{year - 1}.csv")
    input_stats = nfl.load_player_stats(
        seasons=year - 1, summary_level="reg+post"
    )  # mayb
    wr_depth = depth.filter(
        (pl.col("club_code") == team)
        & (pl.col("position") == "WR")
        # | (pl.col("position") == "TE")
        # | (pl.col("position") == "RB")
        & (pl.col("week") == 1)
        # & (pl.col("season") == df["year"])
    )
    wr_depth = wr_depth.rename({"gsis_id": "player_id"})
    wr_depth = wr_depth.unique(subset=["player_id"], keep="first")
    y_wr_depth = wr_depth.join(stats, on="player_id")
    x_wr_depth = wr_depth.select(["full_name", "player_id"]).join(
        input_stats,
        on=[
            "player_id",
        ],
        how="left",
    )
    print(x_wr_depth["full_name"])
    x_wr_depth = x_wr_depth.with_columns(
        pl.col("full_name").map_elements(normalize_player_name).alias("normalized_name")
    )
    college_stats = college_stats.with_columns(
        pl.col("player").map_elements(normalize_player_name).alias("normalized_name")
    )
    x_wr_depth = x_wr_depth.join(college_stats, on=["normalized_name"], how="left")
    print(
        x_wr_depth[
            ["player_id", "player_name", "recent_team", "full_name", "team_name"]
        ]
    )
    y = y_wr_depth.select(["target_share", "full_name"])


if __name__ == "__main__":
    main()
