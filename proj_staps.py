from typing import Tuple

import nflreadpy as nfl
import polars as pl


def main():
    year = 2024
    depth = nfl.load_depth_charts(seasons=year)
    stats = nfl.load_player_stats(
        seasons=year, summary_level="reg+post"
    )  # maybe just reg
    proj_wr_starter(depth, stats, "HOU")


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


def proj_wr_starter(depth: pl.DataFrame, stats: pl.DataFrame, team: str):
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
    wr_depth = wr_depth.join(stats, on="player_id")
    print(wr_depth)
    print(wr_depth.select(["air_yards_share", "target_share", "full_name"]))


if __name__ == "__main__":
    main()
