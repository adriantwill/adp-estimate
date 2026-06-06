import pandas as pd


def merge_csvs(recieving: pd.DataFrame, adp: pd.DataFrame):

    merged = pd.merge(
        recieving, adp, on=["player", "team_name", "position"], how="inner"
    )
    merged.drop(columns=["Notes", "Id"])
    merged.to_csv("merged.csv", index=False)


def main():
    recieving = pd.read_csv("pff_recieving/receiving_summary_2024.csv")
    adp = pd.read_csv("preseason_adp/2025ADP.csv")
    recieving["player"] = recieving["player"].str.replace(" Jr.", "", regex=False)
    adp["player"] = adp["player"].str.replace(" Jr.", "", regex=False)
    recieving["player"] = recieving["player"].str.replace(".", "", regex=False)
    adp["player"] = adp["player"].str.replace(".", "", regex=False)
    # merge_csvs(recieving, adp)
    # return
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
