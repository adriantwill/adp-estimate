from pathlib import Path
import re
from numpy.random import rand
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
import matplotlib.pyplot as plt
from sklearn.preprocessing import add_dummy_feature


def csv_df_list(path: Path) -> list:
    dfs = []
    for file_path in path.iterdir():
        if file_path.suffix != ".csv":
            continue
        df = pd.read_csv(file_path)
        year = re.search(r"\d{4}", file_path.name).group()
        df["year"] = int(year)
        print(str(path))
        match str(path):
            case "pff_recieving":
                max_targets = df["targets"].max()
                df = df[df["targets"] >= max_targets * 0.1]
            case "pros_bb_adp":
                df = df[["year", "Player", "AVG", "POS"]]
                df = df.rename(columns={"POS": "position"})
                df["position"] = df["position"].str.replace(r"\d+", "", regex=True)
                df = df.rename(columns={"Player": "player"})
                df["year"] = int(year) - 1
            case "points_finish":
                df["year"] = int(year) - 1
        dfs.append(df)
    return dfs


def merge_csvs():
    pff_dfs = csv_df_list(Path("pff_recieving"))
    adp_dfs = csv_df_list(Path("pros_bb_adp"))
    finish_dfs = csv_df_list(Path("points_finish"))
    clean_data(pff_dfs + adp_dfs + finish_dfs)
    adp = pd.concat(adp_dfs, ignore_index=True)
    recieving = pd.concat(pff_dfs, ignore_index=True)
    finish = pd.concat(finish_dfs, ignore_index=True)
    merged = pd.merge(
        recieving,
        adp,
        on=["player", "year", "position"],
        how="inner",
    )
    merged = pd.merge(
        merged,
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
    merged.to_csv("merged_wr.csv", index=False)


def clean_data(dataframes: list[pd.DataFrame]):
    for df in dataframes:
        df["player"] = df["player"].str.replace(" Jr.", "", regex=False)
        df["player"] = df["player"].str.replace(".", "", regex=False)
        non_wr_rows = df.index[~df["position"].isin(["WR", "TE"])]
        df.drop(index=non_wr_rows, inplace=True)


def merge_avg_player(df: pd.DataFrame):
    df = df.sort_values(["player", "year"])
    exclude = [
        "player_id",
        "declined_penalties",
        "fantasyPts",
        "ptsPerSnap",
        "ptsPerTouch",
        "franchise_id",
        "year",
    ]
    cols = (
        df.drop(columns=exclude, errors="ignore")
        .select_dtypes(include="number")
        .dropna(axis=1)
        .columns.tolist()
    )
    for col in cols:
        curr = df.groupby("player")[col].shift(0)
        prev1 = df.groupby("player")[col].shift(1)
        prev2 = df.groupby("player")[col].shift(2)
        weighted_sum = (
            curr.fillna(0) * 1.0 + prev1.fillna(0) * 0.5 + prev2.fillna(0) * 0.25
        )
        weight_total = (
            curr.notna().astype(float) * 1.0
            + prev1.notna().astype(float) * 0.5
            + prev2.notna().astype(float) * 0.25
        )

        df[col] = round(weighted_sum / weight_total, 3)
    df.to_csv("average.csv", index=False)


def normal_linreg(
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


def linreg_gd(
    X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray
):
    X_train = add_dummy_feature(X_train)
    X_test = add_dummy_feature(X_test)
    thetas = [np.random.rand(0, 100), np.random.rand(0, 100)]
    gradient = []
    for theta in thetas:
        prediction = X_train @ thetas
        error = prediction - y_train
        d_theta = (2 / len(X_train)) * np.sum(error * X_train[:, 0])
        gradient.append(d_theta)


def sklearn_linreg(
    X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray
):
    lin_reg = Ridge(alpha=10)
    lin_reg.fit(X_train, y_train)
    y_pred = lin_reg.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    print(rmse)


def prepare_data(
    merged: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    exclude = [
        "player_id",
        "declined_penalties",
        "fantasyPts",
        "ptsPerSnap",
        "ptsPerTouch",
        "franchise_id",
        "year",
    ]
    exclude.extend(
        merged.columns[merged.isna().any()].to_list()
    )  # EDIT this, removes all NAN
    X_df = merged.drop(columns=exclude)
    X_df = X_df.select_dtypes(include="number")
    features = X_df.columns.to_list()
    train = merged[merged["year"] < 2024]
    test = merged[merged["year"] == 2024]
    features = ["AVG"]
    X_train = train[features].to_numpy().reshape(-1, len(features))
    X_test = test[features].to_numpy().reshape(-1, len(features))
    y_train = train["fantasyPts"].to_numpy().reshape(-1, 1)
    y_test = test["fantasyPts"].to_numpy().reshape(-1, 1)
    return X_train, X_test, y_train, y_test


def main():
    df = pd.read_csv("merged_new_test.csv")
    X_train, X_test, y_train, y_test = prepare_data(df)
    sklearn_linreg(X_train, X_test, y_train, y_test)
    return
    # merged = pd.read_csv("average.csv")
    # # merge_avg_player(pd.read_csv("merged_new.csv"))
    # X_train, X_test, y_train, y_test = prepare_data(merged)
    # sklearn_linreg(X_train, X_test, y_train, y_test)
    # plt.plot(X, y, "b.")
    # plt.show()


if __name__ == "__main__":
    main()
