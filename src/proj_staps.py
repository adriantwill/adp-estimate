from typing import Tuple

import nflreadpy as nfl
import polars as pl

from util import normalize_player_name


def main():
    proj_wr_starter("SEA", 2023)


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


def merge_pff_college(df: pl.DataFrame, year: int):
    college_stats = pl.read_csv(f"data/source/pff/pff_college/receiving_{year - 1}.csv")
    df = df.with_columns(
        pl.col("full_name").map_elements(normalize_player_name).alias("normalized_name")
    )
    college_stats = college_stats.with_columns(
        pl.col("player").map_elements(normalize_player_name).alias("normalized_name")
    )
    df = df.join(college_stats, on=["normalized_name"], how="left", coalesce=True)
    # AVOID USING MAP_ELEMENTS
    return df


def proj_wr_starter(team: str, year: int):
    depth = nfl.load_depth_charts(seasons=year)
    output_stats = nfl.load_player_stats(
        seasons=year, summary_level="reg+post"
    )  # maybe just reg
    output_stats = output_stats[["player_id", "target_share"]]
    draft_stats = nfl.load_draft_picks(seasons=year)
    draft_stats = draft_stats[["gsis_id", "pick"]]
    draft_stats = draft_stats.with_columns(pl.lit(1).alias("is_rookie"))
    input_stats = nfl.load_player_stats(seasons=year - 1, summary_level="reg+post")
    wr_depth = depth.filter(
        (pl.col("club_code") == team)
        & (
            (pl.col("position") == "WR")
            | (pl.col("position") == "TE")
            | (pl.col("position") == "RB")
        )
        & (pl.col("week") == 1)
        # & (pl.col("season") == df["year"])
    )
    output_stats = output_stats.rename({"player_id": "gsis_id"})
    input_stats = input_stats.rename({"player_id": "gsis_id"})
    wr_depth = wr_depth.filter(
        (pl.col("depth_position") == "WR")
        | (pl.col("depth_position") == "TE")
        | (pl.col("position") == "RB")
    )
    wr_depth = wr_depth.join(output_stats, on="gsis_id")
    wr_depth = wr_depth.join(draft_stats, on="gsis_id", how="left")
    wr_depth = wr_depth.join(input_stats, on="gsis_id", how="left")
    # wr_depth = wr_depth.filter(
    #     pl.col("recent_team").is_not_null() ^ pl.col("is_rookie") == 1
    # )
    wr_depth = wr_depth[
        [
            "full_name",
            "pick",
            "is_rookie",
            "target_share",
            "racr",
            "receiving_epa",
            "target_share_right",
        ]
    ]
    print(wr_depth)
    print(sum(wr_depth["target_share"]))


if __name__ == "__main__":
    main()
