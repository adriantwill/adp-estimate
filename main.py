from pathlib import Path
import re

import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from sklearn.preprocessing import add_dummy_feature


def merge_csvs():
    pff_path = Path("pff_recieving")
    adp_path = Path("preseason_adp")
    finish_path = Path("points_finish")
    pff_dfs = []
    adp_dfs = []
    finish_dfs = []

    for file_path in pff_path.iterdir():
        if file_path.suffix != ".csv":
            continue
        df = pd.read_csv(file_path)
        year = re.search(r"\d{4}", file_path.name).group()
        df["year"] = int(year)
        pff_dfs.append(df)
    for file_path in adp_path.iterdir():
        print(file_path)
        if file_path.suffix != ".csv":
            continue
        df = pd.read_csv(file_path)
        year = re.search(r"\d{4}", file_path.name).group()
        df["year"] = int(year)
        df = df.rename(columns={"Pos": "position"})
        df = df.rename(columns={"Player": "player"})
        df = df.rename(columns={"Name": "player"})
        # chaange
        adp_dfs.append(df)
    for file_path in finish_path.iterdir():
        if file_path.suffix != ".csv":
            continue
        df = pd.read_csv(file_path)
        year = re.search(r"\d{4}", file_path.name).group()
        df["year"] = int(year)
        finish_dfs.append(df)
    clean_data(pff_dfs + adp_dfs + finish_dfs)
    recieving = pd.concat(pff_dfs, ignore_index=True)
    adp = pd.concat(adp_dfs, ignore_index=True)
    finish = pd.concat(finish_dfs, ignore_index=True)
    merged = pd.merge(
        recieving,
        adp,
        on=["player", "position", "year"],
        how="inner",
    )
    merged = merged.drop(columns=["Notes", "Id"])
    merged = merged.merge(
        finish[
            [
                "player",
                "position",
                "year",
                "fantasyPts",
                "ptsPerSnap",
                "ptsPerTouch",
            ]
        ],
        on=["player", "position", "year"],
        how="inner",
    )
    print("compelte merge")
    merged.to_csv("merged_new.csv", index=False)


def clean_data(dataframes: list[pd.DataFrame]):
    for df in dataframes:
        print(df)
        df["player"] = df["player"].str.replace(" Jr.", "", regex=False)
        df["player"] = df["player"].str.replace(".", "", regex=False)
        non_wr_rows = df.index[df["position"] != "WR"]
        df.drop(index=non_wr_rows, inplace=True)


def check_data():
    recieving = pd.read_csv("pff_recieving/receiving_summary_2024.csv")
    adp = pd.read_csv("preseason_adp/2025ADP.csv")
    finish = pd.read_csv("points_finish/receiving_finish_2025.csv")
    merged = pd.read_csv("merged.csv")
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


def numpy_linreg(
    X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray
):
    X_train = add_dummy_feature(X_train)
    X_test = add_dummy_feature(X_test)
    theta = np.linalg.inv(X_train.T @ X_train) @ X_train.T @ y_train
    mse = 0
    for i in range(len(X_test)):
        mse += (theta.T @ X_test[i] - y_test[i]) ** 2
    mse /= len(X_test)
    rmse = np.sqrt(mse)
    print(rmse)


def sklearn_linreg(
    X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray
):
    lin_reg = LinearRegression()
    lin_reg.fit(X_train, y_train)
    y_pred = lin_reg.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    print(rmse)


def prepare_data(merged: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
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
    features = [
        "ADP",
    ]
    X = merged[features].to_numpy().reshape(-1, len(features))
    y = merged["fantasyPts"].to_numpy().reshape(-1, 1)
    return X, y


def main():
    merge_csvs()
    # merged = pd.read_csv("merged.csv")
    # X, y = prepare_data(merged)
    # X_train, X_test, y_train, y_test = train_test_split(
    #     X, y, test_size=0.2, random_state=42
    # )
    # sklearn_linreg(X_train, X_test, y_train, y_test)
    # plt.plot(X, y, "b.")
    # plt.show()


if __name__ == "__main__":
    main()
