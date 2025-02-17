from typing import Callable

import numpy as np
import pandas as pd
from PySide6.QtCore import (
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtSql import QSqlIndex, QSqlTableModel

from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel


class SampleFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._sampleId = None

    def enableFilter(self, sampleId):
        self._sampleId = sampleId
        self.invalidateFilter()

    def disableFilter(self):
        self._sampleId = None
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ):
        index = self.sourceModel().index(
            source_row,
            self.sourceModel().record().indexOf(SampleSqlTableModel.column_sample_id),
            source_parent,
        )
        if self._sampleId is not None:
            data = self.sourceModel().data(index)
            return data == self._sampleId

        return super().filterAcceptsRow(source_row, source_parent)


def to_numeric_with_callback(data: str | None, callback: Callable[[str], float]):
    """Convert a string to numeric value with a callback function for user correction.
    Args:
        data (str | None): The string to be converted.
        callback (Callable[[str], float]): A function that takes a string as input and returns a numeric value.
    Returns:
        float | None: A numeric value or None if an error occurred during conversion.
    """
    try:
        return pd.to_numeric(data, errors="raise")
    except ValueError as e:
        return callback(data)


def sheetfile_to_dataframe(
    sheet_file_path: str,
    transposed_csv: bool,
    skip_rows: int = 0,
    skip_cols: int = 0,
    value_fixer_callback: Callable[[str], float] | None = None,
):
    """Convert a CSV file to a Pandas DataFrame.
    Args:
        csv_file_path (str): The path to the CSV file.
        transposed_csv (bool): True if the CSV file is transposed.
        skip_rows (int): The number of rows to skip at the beginning of the CSV file.
        skip_cols (int): The number of columns to skip at the beginning of the CSV file.
    Returns:
        pandas.DataFrame: A Pandas DataFrame containing the CSV file's contents.
    """
    if sheet_file_path.endswith(".xlsx") or sheet_file_path.endswith(".xls"):
        data_pd = pd.read_excel(
            sheet_file_path, index_col=skip_cols, skiprows=skip_rows
        )
    elif sheet_file_path.endswith(".csv"):
        data_pd = pd.read_csv(sheet_file_path, index_col=skip_cols, skiprows=skip_rows)
    else:
        raise ValueError(f"Unsupported file format for {sheet_file_path}")

    if skip_cols > 0:
        # Delete first skip_rows rows
        data_pd = data_pd.drop(data_pd.columns[:skip_cols], axis=1)
    if transposed_csv:
        # Transpose dataframe
        data_pd = data_pd.T

    # Curate values in the dataframe to be numeric
    # TODO: ask user for correct errors
    # data_pd = data_pd.map(pd.to_numeric, errors='coerce')

    def _value_fixer(x: str):
        x_fixed = np.nan
        try:
            x_fixed = pd.to_numeric(x, errors="raise")
        except ValueError:
            if value_fixer_callback is not None:
                x_fixed = value_fixer_callback(x)
        return x_fixed

    data_pd = data_pd.map(_value_fixer)

    data_pd.index = data_pd.index.map(pd.to_numeric)
    data_pd.index = data_pd.index.astype(int)
    return data_pd


def add_values_from_csv(
    csv_file_path: str,
    transposed_csv: bool,
    featureSqlTableModel: FeatureSqlTableModel,
    sampleSqlTableModel: SampleSqlTableModel,
    skip_rows: int = 0,
    skip_cols: int = 0,
    value_fixer_callback=None,
):
    """Add values from a CSV file to the database.

    Args:
        csv_file_path (str): The path to the CSV file.
        transposed_csv (bool): True if the CSV file is transposed.
        featureSqlTableModel (FeatureSqlTableModel): The target data model for the features.
        sampleSqlTableModel (SampleSqlTableModel): The target data model for the samples.
        skip_rows (int): The number of rows to skip at the beginning of the CSV file. Default is 0.
        skip_cols (int): The number of columns to skip at the beginning of the CSV file. Default is 0.
    """
    data_pd = sheetfile_to_dataframe(
        csv_file_path,
        transposed_csv=transposed_csv,
        skip_rows=skip_rows,
        skip_cols=skip_cols,
        value_fixer_callback=value_fixer_callback,
    )

    feature_proxy = QSortFilterProxyModel()
    feature_proxy.setSourceModel(featureSqlTableModel)
    feature_proxy.setFilterKeyColumn(
        featureSqlTableModel.fieldIndex(featureSqlTableModel.column_name)
    )

    new_features = []
    for col_candidate in data_pd.columns:
        feature_proxy.setFilterFixedString(col_candidate)
        if feature_proxy.rowCount() == 0:
            new_features.append(col_candidate)

    for new_feature in new_features:
        rowRecord = featureSqlTableModel.record()
        rowRecord.remove(rowRecord.indexOf(FeatureSqlTableModel.column_id))
        rowRecord.setValue(FeatureSqlTableModel.column_name, new_feature)
        rowRecord.setValue(FeatureSqlTableModel.column_is_active, 1)
        rowRecord.setValue(FeatureSqlTableModel.column_description, "")
        featureSqlTableModel.insertRecord(-1, rowRecord)
    featureSqlTableModel.submitAll()

    # sample_proxy = SampleFilterProxyModel()
    # sample_proxy.setSourceModel(sampleSqlTableModel)
    # new_samples = []
    # for sample_candidate in data_pd.index:
    #     sample_proxy.enableFilter(sample_candidate)
    #     if sample_proxy.rowCount() == 0:
    #         new_samples.append(sample_candidate)
    # Logic with searching dublication is extremelly slow, ignore DB update as a temporal solution.
    # TODO: reimplement with raw sql query.
    if sampleSqlTableModel.rowCount() > 0:
        return

    # for new_sample in new_samples:
    # row_pd = data_pd.loc[new_sample]
    for index, row_pd in data_pd.iterrows():
        for col in data_pd.columns:
            if not np.isnan(row_pd[col]):
                rowRecord = sampleSqlTableModel.record()
                rowRecord.remove(rowRecord.indexOf(SampleSqlTableModel.column_id))

                feature_proxy.setFilterFixedString(col)

                rowRecord.setValue(
                    SampleSqlTableModel.column_feature_id,
                    feature_proxy.index(
                        0,
                        featureSqlTableModel.fieldIndex(FeatureSqlTableModel.column_id),
                    ).data(),
                )
                rowRecord.setValue(SampleSqlTableModel.column_sample_id, int(index))
                rowRecord.setValue(SampleSqlTableModel.column_value, float(row_pd[col]))
                sampleSqlTableModel.insertRecord(-1, rowRecord)
    sampleSqlTableModel.submitAll()
    # for index, row in data_pd.iterrows():
