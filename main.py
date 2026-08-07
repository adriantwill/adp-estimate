import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error

from src.path import MERGED_WR_CSV


def sklearn_linreg(
    X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray
):
    lin_reg = ElasticNet()
    lin_reg.fit(X_train, y_train)
    y_pred = lin_reg.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    print(rmse)


def prepare_data(
    merged: pd.DataFrame, adp: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    exclude = [
        "player_id",
        "declined_penalties",
        "fantasyPts",
        "ptsPerSnap",
        "ptsPerTouch",
        "franchise_id",
        "year",
        "expected_diff",
        "bucket",
        "grades_pass_block",
    ]
    X_df = merged.drop(columns=exclude)
    X_df = X_df.select_dtypes(include="number")
    features = X_df.columns.to_list()
    train = merged[merged["year"] < 2024]
    test = merged[merged["year"] == 2024]
    test = test[test["AVG"] <= 150]
    if adp:
        features = ["AVG"]
    X_train = train[features].to_numpy().reshape(-1, len(features))
    X_test = test[features].to_numpy().reshape(-1, len(features))
    y_train = train["expected_diff"].to_numpy().reshape(-1, 1)
    y_test = test["expected_diff"].to_numpy().reshape(-1, 1)
    # remove y_test
    return X_train, X_test, y_train, y_test


def main():
    df = pd.read_csv(MERGED_WR_CSV)
    X_train, X_test, y_train, y_test = prepare_data(df, False)
    sklearn_linreg(X_train, X_test, y_train, y_test)


if __name__ == "__main__":
    main()
