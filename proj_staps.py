from typing import Tuple
import nflreadpy as nfl
import polars as pl
#remove code below wthis
import ssl
import requests
ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()
original_send = requests.Session.send
def unverified_send(self, request, **kwargs):
    kwargs['verify'] = False
    return original_send(self, request, **kwargs)
requests.Session.send = unverified_send
#remove code above this

def main():
    proj_wr_starter( "HOU", 2022)
    proj_wr_starter( "HOU", 2024)




def proj_wr_starter(team: str, year: int):
    df = nfl.load_depth_charts(seasons=year)
    qb = df.filter(
        (pl.col("club_code") == team)
        & (pl.col("position") == "WR")
        # | (pl.col("position") == "TE")
        # | (pl.col("position") == "RB")
        & (pl.col("week") == 1)
        # & (pl.col("season") == df["year"])
    )
    stats = nfl.load_player_stats(
        seasons=year-1, summary_level="reg+post"
    )  # maybe just reg
    qb = qb.rename({"gsis_id": "player_id"})
    stats= stats.rename({"season": "stats_season"})
    qb = qb.join(stats, on="player_id")
    qb = qb.unique(subset='player_id')
    print(qb.select(["recent_team","club_code", "air_yards_share", "target_share", "full_name","season","stats_season"]))


if __name__ == "__main__":
    main()
