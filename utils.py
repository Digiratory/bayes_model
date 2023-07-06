def find_zero_columns(df):
    """
    Для нахождения столбцов, где все значения пусты
    :param df:
    :return: список столбцов
    """
    return df.loc[:, df.isna().all()].columns