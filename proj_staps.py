import polars as pl


def main():
    df = pl.read_csv("depth_TEMP.csv")
    proj_wr_starter(df, "HOU")


def proj_wr_starter(df: pl.DataFrame, team: str):
    qb = df.filter(
        (pl.col("club_code") == team)
        & (
            (pl.col("position") == "WR")
            | (pl.col("position") == "TE")
            | (pl.col("position") == "RB")
        )
        & (pl.col("week") == 1)
        # & (pl.col("season") == df["year"])
    )
    print(qb)
    return qb["full_name"]


if __name__ == "__main__":
    main()
