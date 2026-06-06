import pandas as pd


def merge_csvs(recieving: pd.DataFrame, adp: pd.DataFrame):

    merged = pd.merge(
        recieving, adp, on=["player", "team_name", "position"], how="inner"
    )
    merged = merged.drop(columns=["Notes", "Id"])
    merged.to_csv("merged.csv", index=False)


def merge_finish(merged: pd.DataFrame, finish: pd.DataFrame):
    merged = merged.merge(
        finish[
            [
                "player",
                "team_name",
                "position",
                "fantasyPts",
                "ptsPerSnap",
                "ptsPerTouch",
            ]
        ],
        on=["player", "team_name", "position"],
        how="left",
    )
    merged.to_csv("merged_points.csv", index=False)


def clean_data(dataframes: list[pd.DataFrame]):
    for df in dataframes:
        df["player"] = df["player"].str.replace(" Jr.", "", regex=False)
        df["player"] = df["player"].str.replace(".", "", regex=False)


def main():
    recieving = pd.read_csv("pff_recieving/receiving_summary_2024.csv")
    adp = pd.read_csv("preseason_adp/2025ADP.csv")
    finish = pd.read_csv("points_finish/receiving_finish_2025.csv")
    merged = pd.read_csv("merged.csv")
    clean_data([recieving, adp, finish])
    merge_finish(merged, finish)
    return
    # merged = pd.read_csv("merged.csv")
    seen_pff = set()
    seen_underdog = set()
    dups = []
    for row in adp.itertuples():
        seen_underdog.add(row.player)
    for row in recieving.itertuples():
        seen_pff.add(row.player)
    for row in adp.itertuples():
        if row.player not in seen_pff and row.position == "WR":
            dups.append(row.player)
    print(dups)


if __name__ == "__main__":
    main()
