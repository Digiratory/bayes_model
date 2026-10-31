import time
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from PySide6.QtCore import (
    QCoreApplication,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtSql import QSqlDatabase, QSqlIndex, QSqlQuery, QSqlTableModel

from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel

# Fractions (0..1) of the overall import progress reported by
# import_dataframe_to_db. The earlier phases (file reading, value
# normalization) are reported by the import worker.
PROGRESS_FEATURES_START = 0.35
PROGRESS_FEATURES_END = 0.45
PROGRESS_SAMPLES_START = 0.45
PROGRESS_SAMPLES_END = 1.0


@dataclass
class ImportStats:
    """Summary of a completed import run."""

    features: int = 0
    samples: int = 0
    nan_values: int = 0


class ImportCancelled(Exception):
    """Raised by the import when a cancellation was requested."""


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


def read_sheet_dataframe(
    sheet_file_path: str,
    transposed_csv: bool,
    skip_rows: int = 0,
    skip_cols: int = 0,
) -> pd.DataFrame:
    """Read a CSV/Excel sheet file into a dataframe without value normalization.

    Same reading semantics as :func:`sheetfile_to_dataframe`, but the cells
    are returned as-is (strings, numbers or NaN) and the sample-id index is
    not cast to integers.

    Args:
        sheet_file_path (str): The path to the CSV file.
        transposed_csv (bool): True if the CSV file is transposed.
        skip_rows (int): The number of rows to skip at the beginning of the CSV file.
        skip_cols (int): The number of columns to skip at the beginning of the CSV file.
    Returns:
        pandas.DataFrame: A Pandas DataFrame containing the sheet file's contents.
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
        # Delete first skip_cols columns
        data_pd = data_pd.drop(data_pd.columns[:skip_cols], axis=1)
    if transposed_csv:
        # Transpose dataframe
        data_pd = data_pd.T
    return data_pd


def collect_non_numeric_values(data_pd: pd.DataFrame) -> list:
    """Collect the unique cell values that cannot be converted to numbers.

    Numeric cells and empty (NaN) cells are not included. The original
    values are returned in order of first appearance, so they can be shown
    to the user and resolved later via :func:`apply_value_map`.

    Args:
        data_pd (pandas.DataFrame): The dataframe to inspect.
    Returns:
        list: The unique non-numeric cell values.
    """
    values: dict = {}

    def _collect(x):
        try:
            pd.to_numeric(x, errors="raise")
        except (ValueError, TypeError):
            values.setdefault(x, None)
        return x

    data_pd.map(_collect)
    return list(values)


def apply_value_map(data_pd: pd.DataFrame, value_map: dict) -> pd.DataFrame:
    """Convert dataframe cells to numeric values using a user-provided mapping.

    Numeric cells are kept as-is, cells present in *value_map* are replaced
    by their mapped numeric value (which may be NaN), and any remaining
    non-numeric cell becomes NaN. The sample-id index is converted to
    integers.

    Args:
        data_pd (pandas.DataFrame): The dataframe to normalize.
        value_map (dict): Mapping from non-numeric cell values to their
            numeric replacements.
    Returns:
        pandas.DataFrame: A new dataframe with numeric cells and an
        integer sample-id index.
    Raises:
        ValueError: If the index cannot be interpreted as numeric sample ids.
    """

    def _fix(x):
        try:
            return pd.to_numeric(x, errors="raise")
        except (ValueError, TypeError):
            if x in value_map:
                return value_map[x]
            return np.nan

    data_pd = data_pd.map(_fix)

    try:
        data_pd.index = pd.to_numeric(data_pd.index).astype(int)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Sample ID must be numeric: {e}") from e
    return data_pd


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
    data_pd = read_sheet_dataframe(
        sheet_file_path,
        transposed_csv,
        skip_rows=skip_rows,
        skip_cols=skip_cols,
    )

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


def create_project_schema(db: QSqlDatabase) -> None:
    """Create the project tables on *db* if they do not exist yet.

    Intended for worker-thread connections: the GUI thread normally creates
    the schema implicitly by instantiating the SQL table models. All queries
    are executed on the given connection only.

    Args:
        db (QSqlDatabase): An open database connection owned by the caller.
    Raises:
        RuntimeError: If a table cannot be created.
    """
    for create_sql in (
        FeatureSqlTableModel.create_table_sql,
        SampleSqlTableModel.create_table_sql,
    ):
        query = QSqlQuery(db)
        if not query.exec(create_sql):
            raise RuntimeError(
                f"Unable to create the project schema: {query.lastError().text()}"
            )


def _noop_progress(fraction: float, message: str) -> None:
    return None


def _not_cancelled() -> bool:
    return False


class _ProgressThrottle:
    """Time-throttled wrapper around a progress callback.

    Long insert loops must not flood the GUI thread with progress updates:
    emissions are limited to one per ``min_interval`` seconds, except forced
    emissions used for phase boundaries.
    """

    def __init__(
        self,
        callback: Callable[[float, str], None],
        min_interval: float = 0.1,
    ):
        self._callback = callback
        self._min_interval = min_interval
        self._last_emission = 0.0

    def emit(self, fraction: float, message: str, force: bool = False) -> None:
        now = time.monotonic()
        if force or (now - self._last_emission) >= self._min_interval:
            self._last_emission = now
            self._callback(fraction, message)


def _load_feature_ids(db: QSqlDatabase) -> dict[str, int]:
    select = QSqlQuery(db)
    if not select.exec(
        f"SELECT {FeatureSqlTableModel.column_id}, {FeatureSqlTableModel.column_name} "
        f"FROM {FeatureSqlTableModel.table_name}"
    ):
        raise RuntimeError(f"Unable to read features: {select.lastError().text()}")
    feature_ids = {}
    while select.next():
        feature_ids[str(select.value(1))] = int(select.value(0))
    return feature_ids


def _insert_features(db: QSqlDatabase, data_pd: pd.DataFrame, progress, cancel_check):
    feature_ids = _load_feature_ids(db)
    known_names = set(feature_ids)
    new_names = []
    for column in data_pd.columns:
        name = str(column)
        if name not in known_names:
            known_names.add(name)
            new_names.append(name)

    insert = QSqlQuery(db)
    insert.prepare(
        f"INSERT INTO {FeatureSqlTableModel.table_name} ("
        f"{FeatureSqlTableModel.column_name}, "
        f"{FeatureSqlTableModel.column_description}, "
        f"{FeatureSqlTableModel.column_is_active}) VALUES (?, ?, ?)"
    )
    message = QCoreApplication.translate("db_model_handler", "Inserting features...")
    total = len(new_names)
    for position, name in enumerate(new_names):
        if cancel_check():
            raise ImportCancelled()
        insert.addBindValue(name)
        insert.addBindValue("")
        insert.addBindValue(1)
        if not insert.exec():
            raise RuntimeError(
                f"Unable to insert feature '{name}': {insert.lastError().text()}"
            )
        fraction = PROGRESS_FEATURES_START + (position + 1) / total * (
            PROGRESS_FEATURES_END - PROGRESS_FEATURES_START
        )
        progress.emit(fraction, message)
    progress.emit(PROGRESS_FEATURES_END, message, force=True)


def _insert_samples(
    db: QSqlDatabase,
    data_pd: pd.DataFrame,
    stats: ImportStats,
    progress,
    cancel_check,
):
    feature_ids = _load_feature_ids(db)
    insert = QSqlQuery(db)
    insert.prepare(
        f"INSERT INTO {SampleSqlTableModel.table_name} ("
        f"{SampleSqlTableModel.column_sample_id}, "
        f"{SampleSqlTableModel.column_feature_id}, "
        f"{SampleSqlTableModel.column_value}) VALUES (?, ?, ?)"
    )
    message = QCoreApplication.translate("db_model_handler", "Inserting samples...")
    column_names = [str(column) for column in data_pd.columns]
    total_rows = max(len(data_pd.index), 1)
    nan_values = 0
    for row_number, (index, row_pd) in enumerate(data_pd.iterrows()):
        if cancel_check():
            raise ImportCancelled()
        sample_id = int(index)
        for column_name in column_names:
            value = row_pd[column_name]
            if pd.isna(value):
                nan_values += 1
                continue
            insert.addBindValue(sample_id)
            insert.addBindValue(feature_ids[column_name])
            insert.addBindValue(float(value))
            if not insert.exec():
                raise RuntimeError(
                    f"Unable to insert sample {sample_id} / '{column_name}': "
                    f"{insert.lastError().text()}"
                )
        fraction = PROGRESS_SAMPLES_START + (row_number + 1) / total_rows * (
            PROGRESS_SAMPLES_END - PROGRESS_SAMPLES_START
        )
        progress.emit(fraction, message)
    stats.nan_values = nan_values
    progress.emit(PROGRESS_SAMPLES_END, message, force=True)


def import_dataframe_to_db(
    db: QSqlDatabase,
    data_pd: pd.DataFrame,
    progress_callback: Callable[[float, str], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> ImportStats:
    """Import a normalized dataframe into the database behind *db*.

    The dataframe must already contain only numeric or NaN values and an
    integer sample-id index (see :func:`apply_value_map`). Missing features
    are inserted, then every non-NaN cell is stored as a sample value. All
    inserts run inside a single transaction: on cancellation or failure the
    transaction is rolled back and the exception is re-raised.

    Note: unlike the legacy :func:`add_values_from_csv`, this function never
    skips the import when samples already exist; it is meant for importing
    into a fresh project database (the Create New flow of the project
    wizard).

    Args:
        db (QSqlDatabase): An open database connection, used only from the
            thread that owns it.
        data_pd (pandas.DataFrame): Normalized dataframe (numeric/NaN cells,
            integer index).
        progress_callback (Callable): Optional ``callback(fraction, message)``
            with fraction in [0, 1]; emissions are time-throttled.
        cancel_check (Callable): Optional callable polled between inserts;
            return True to abort via :class:`ImportCancelled` after rollback.
    Returns:
        ImportStats: Counts of imported features, samples and skipped NaN cells.
    Raises:
        ImportCancelled: If ``cancel_check`` returned True.
        RuntimeError: On database errors.
    """
    if progress_callback is None:
        progress_callback = _noop_progress
    if cancel_check is None:
        cancel_check = _not_cancelled

    stats = ImportStats(features=len(data_pd.columns), samples=len(data_pd.index))
    if not db.transaction():
        raise RuntimeError(
            f"Unable to start the import transaction: {db.lastError().text()}"
        )
    try:
        progress = _ProgressThrottle(progress_callback)
        _insert_features(db, data_pd, progress, cancel_check)
        _insert_samples(db, data_pd, stats, progress, cancel_check)
        if not db.commit():
            raise RuntimeError(f"Unable to commit the import: {db.lastError().text()}")
    except BaseException:
        db.rollback()
        raise
    return stats
