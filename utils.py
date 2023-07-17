from scipy.special import erfcinv

F = -1 / (2 ** (1 / 2) * erfcinv(3 / 2))


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

        outliers_index.extend(list(df.loc[(df[column] >= up) | (df[column] <= down)].index))

    return set(outliers_index)

