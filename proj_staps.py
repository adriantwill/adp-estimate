from typing import Tuple

import nflreadpy as nfl
import polars as pl


def main():
    print(player_stats("00-0030035"))
    # stats = nfl.load_player_stats(seasons=[2024], summary_level="reg+post")
    # print(stats)
    # stats.write_csv("stats_TEMP.csv")
    # df = pl.read_csv("depth_TEMP.csv")
    #
    # proj_wr_starter(df, "HOU")


def player_stats(id: str) -> Tuple[str, str] | None:
    stats = nfl.load_player_stats(seasons=[2024], summary_level="reg+post")
    wr = stats.filter(pl.col("player_id") == id)
    row = wr.row(0, named=True) if wr.height > 0 else None
    return (row["air_yards_share"], row["target_share"])


def proj_wr_starter(df: pl.DataFrame, team: str):
    qb = df.filter(
        (pl.col("club_code") == team)
        & (pl.col("position") == "WR")
        # | (pl.col("position") == "TE")
        # | (pl.col("position") == "RB")
        & (pl.col("week") == 1)
        # & (pl.col("season") == df["year"])
    )
    print(qb)
    return qb["full_name"]


if __name__ == "__main__":
    main()
