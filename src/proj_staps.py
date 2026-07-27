import nflreadpy as nfl
import polars as pl

from util import normalize_player_name


def main():
    for i in range(16):
        year = 2009 + i
        schedules = nfl.load_schedules(seasons=year)
        team_abbreviations = (
            pl.concat([schedules["home_team"], schedules["away_team"]])
            .unique()
            .sort()
            .to_list()
        )
        for i, abv in enumerate(team_abbreviations):
            print(year)
            proj_wr_starter(abv, year, i)


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


def proj_wr_starter(team: str, year: int, team_num: int):
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
        | (pl.col("depth_position") == "RB")
    )
    wr_depth = wr_depth.join(output_stats, on="gsis_id")
    wr_depth = wr_depth.join(draft_stats, on="gsis_id", how="left")
    wr_depth = wr_depth.join(input_stats, on="gsis_id", how="left")
    wr_depth = wr_depth.filter(
        (pl.col("target_share_right").is_not_null()) | (pl.col("is_rookie") == 1)
    )
    wr_depth = wr_depth.with_columns(
        pl.when((pl.col("recent_team") != team) | (pl.col("recent_team").is_null()))
        .then(1)
        .otherwise(0)
        .alias("different_team")
    )
    context_group = ["club_code", "season"]
    previous_target_share = pl.col("target_share_right").fill_null(0.0)
    rookie = pl.col("is_rookie").fill_null(0)
    newcomer = pl.col("different_team").fill_null(0)
    wr_depth = wr_depth.with_columns(
        [
            (
                previous_target_share.sum().over(context_group)
                - previous_target_share
            ).alias("teammate_previous_target_share_sum"),
            previous_target_share.sort(descending=True)
            .get(0)
            .over(context_group)
            .alias("team_top_previous_target_share"),
            previous_target_share.sort(descending=True)
            .get(1, null_on_oob=True)
            .over(context_group)
            .alias("team_second_previous_target_share"),
            previous_target_share.rank("ordinal", descending=True)
            .over(context_group)
            .alias("previous_target_share_rank"),
            (pl.len().over(context_group) - 1).alias("teammate_count"),
            (rookie.sum().over(context_group) - rookie).alias(
                "rookie_teammate_count"
            ),
            (newcomer.sum().over(context_group) - newcomer).alias(
                "newcomer_teammate_count"
            ),
        ]
    )
    wr_depth = wr_depth[
        [
            "different_team",
            "season",
            "pick",
            "is_rookie",
            "target_share",
            "racr",
            "receiving_epa",
            "target_share_right",
            "teammate_previous_target_share_sum",
            "team_top_previous_target_share",
            "team_second_previous_target_share",
            "previous_target_share_rank",
            "teammate_count",
            "rookie_teammate_count",
            "newcomer_teammate_count",
        ]
    ]
    wr_depth = wr_depth.with_columns(pl.lit(team_num).alias("team_num"))
    wr_depth = wr_depth.fill_null(strategy="zero")
    print(wr_depth)


if __name__ == "__main__":
    main()
