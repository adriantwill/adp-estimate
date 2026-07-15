from typing import Tuple

import nflreadpy as nfl
import polars as pl


def main():
    df = nfl.load_depth_charts(seasons=2024)
    proj_wr_starter(df, "HOU", 2022)


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


def proj_wr_starter(df: pl.DataFrame, team: str, year: int):
    qb = df.filter(
        (pl.col("club_code") == team)
        & (pl.col("position") == "WR")
        # | (pl.col("position") == "TE")
        # | (pl.col("position") == "RB")
        & (pl.col("week") == 1)
        # & (pl.col("season") == df["year"])
    )
    stats = nfl.load_player_stats(
        seasons=year, summary_level="reg+post"
    )  # maybe just reg
    qb = qb.rename({"gsis_id": "player_id"})
    qb = qb.join(stats, on="player_id")
    print(qb)
    print(qb.select(["air_yards_share", "target_share", "full_name"]))


if __name__ == "__main__":
    main()
