import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from sklearn.preprocessing import add_dummy_feature


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


def numpy_linreg(X_b, y):
    theta = np.linalg.inv(X_b.T @ X_b) @ X_b.T @ y
    mse = 0
    for i in range(len(X_b)):
        mse += (theta.T @ X_b[i] - y[i]) ** 2
    mse /= len(X_b)
    rmse = np.sqrt(mse)
    print(rmse)


def sklearn_linreg(X, y):
    lin_reg = LinearRegression()
    lin_reg.fit(X, y)


def main():
    # recieving = pd.read_csv("pff_recieving/receiving_summary_2024.csv")
    # adp = pd.read_csv("preseason_adp/2025ADP.csv")
    # finish = pd.read_csv("points_finish/receiving_finish_2025.csv")
    # clean_data([recieving, adp, finish])
    # merge_csvs(recieving, adp, finish)
    merged = pd.read_csv("merged.csv")
    nan_cols = merged.columns[merged.isna().any()]
    print(nan_cols.tolist())
    exclude = [
        "player_id",
        "declined_penalties",
        "fantasyPts",
        "ptsPerSnap",
        "ptsPerTouch",
        "franchise_id",
    ]
    exclude.extend(merged.columns[merged.isna().any()].to_list())
    X_df = merged.drop(columns=exclude)
    X_df = X_df.select_dtypes(include="number")
    features = X_df.columns.to_list()
    X = merged[features].to_numpy().reshape(-1, len(features))
    X_b = add_dummy_feature(X)
    y = merged["fantasyPts"].to_numpy().reshape(-1, 1)
    print(y)
    numpy_linreg(X_b, y)
    # sklearn_linreg(X, y)
    # plt.plot(X, y, "b.")
    # plt.show()


if __name__ == "__main__":
    main()
