import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import add_dummy_feature
from sklearn.utils.validation import np


def merge_csvs(recieving: pd.DataFrame, adp: pd.DataFrame, finish: pd.DataFrame):
    merged = pd.merge(recieving, adp, on=["player", "position"], how="inner")
    merged = merged.drop(columns=["Notes", "Id"])
    merged = merged.merge(
        finish[
            [
                "player",
                "position",
                "fantasyPts",
                "ptsPerSnap",
                "ptsPerTouch",
            ]
        ],
        on=["player", "position"],
        how="inner",
    )
    merged.to_csv("merged.csv", index=False)


def clean_data(dataframes: list[pd.DataFrame]):
    for df in dataframes:
        df["player"] = df["player"].str.replace(" Jr.", "", regex=False)
        df["player"] = df["player"].str.replace(".", "", regex=False)
        non_wr_rows = df.index[df["position"] != "WR"]
        df.drop(index=non_wr_rows, inplace=True)


def check_data(
    recieving: pd.DataFrame,
    adp: pd.DataFrame,
    finish: pd.DataFrame,
    merged: pd.DataFrame,
):
    seen_pff = set()
    seen_underdog = set()
    dups = []
    for row in merged.itertuples():
        seen_underdog.add(row.player)
    for row in recieving.itertuples():
        if row.player in seen_pff:
            dups.append(row.player)
        seen_pff.add(row.player)
    for row in recieving.itertuples():
        if row.player not in seen_underdog and row.position == "WR":
            dups.append(row.player)
    print(dups)


def main():
    # recieving = pd.read_csv("pff_recieving/receiving_summary_2024.csv")
    # adp = pd.read_csv("preseason_adp/2025ADP.csv")
    # finish = pd.read_csv("points_finish/receiving_finish_2025.csv")
    # clean_data([recieving, adp, finish])
    # merge_csvs(recieving, adp, finish)
    merged = pd.read_csv("merged.csv")
    X = merged["ADP"].to_numpy()
    X = X.reshape(-1, 1)
    X_b = add_dummy_feature(X)
    y = merged["fantasyPts"].to_numpy()
    y = y.reshape(-1, 1)
    print(y)
    theta = np.linalg.inv(X_b.T @ X_b) @ X_b.T @ y
    plt.plot(X, y, "b.")
    plt.show()
    print(theta)


if __name__ == "__main__":
    main()
