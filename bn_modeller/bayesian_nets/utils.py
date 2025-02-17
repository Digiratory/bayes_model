import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import erfcinv

F = -1 / (2 ** (1 / 2) * erfcinv(3 / 2))


def check_non_select_table(df):
    k = []
    for i in df.columns:
        k.append((df[i] == 0).all())
    return np.all(k)


def find_zero_columns(df):
    """
    Для нахождения столбцов, где все значения пусты
    :param df:
    :return: список столбцов
    """
    return df.loc[:, df.isna().all()].columns


def to_mad_scale(x, m):
    return abs(x - m)


def get_index_outliers(df) -> set:
    """
    Повторяет функцию rmoutliers (median) из MATLAB
    :param df:
    :return: номера индексов выбросов
    """
    outliers_index = []
    for column in df.columns:
        m = df[column].median()
        x = df[column].apply(to_mad_scale, m=m)
        res = F * x.median()

        down = m - res * 3
        up = m + res * 3

        outliers_index.extend(
            list(df.loc[(df[column] >= up) | (df[column] <= down)].index)
        )

    return set(outliers_index)


def get_outliers_cooks(df):
    """
    Нахождение выбросов на основе расстояния Кука
    """
    # storing dependant values
    y = df.iloc[:, 1]

    # storing independent values
    x = df.iloc[:, 0]

    # add bias
    x = sm.add_constant(x)

    # create and train linear regression model
    sm_model = sm.regression.linear_model.OLS(y, x).fit()
    influence = sm_model.get_influence()

    influence_list = influence.cooks_distance[0]
    influence_df = pd.DataFrame(influence_list, columns=["influence"], index=df.index)

    original_length = len(df)

    cooks_df = df.join(influence_df)
    cooks_threshold = 4 / original_length
    cooks_outliers = cooks_df[cooks_df["influence"] > cooks_threshold]

    return set(cooks_outliers.index)
