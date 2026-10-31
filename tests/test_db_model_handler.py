import os

import numpy as np
import pandas as pd
import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.utils.db_model_handler import (
    PROGRESS_FEATURES_END,
    PROGRESS_FEATURES_START,
    PROGRESS_SAMPLES_END,
    PROGRESS_SAMPLES_START,
    ImportCancelled,
    apply_value_map,
    collect_non_numeric_values,
    create_project_schema,
    import_dataframe_to_db,
    sheetfile_to_dataframe,
)


def test_csv_to_dataframes():
    """Test method bn_modeller.utils.db_model_handler.csv_to_dataframe
    with a sample CSV file with samples in rows and float or emply
    values of features
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "sample_csv.csv"
    )
    print(csv_path)
    df = sheetfile_to_dataframe(csv_path, transposed_csv=False)
    print(df.columns, len(df))
    assert list(df.columns) == [
        "Feature 1",
        "Feature 2",
        "Feature 3",
        "Feature 4",
        "Feature 5",
        "Feature 6",
    ]
    assert len(df) == 15
    assert np.isnan(df["Feature 1"].iloc[0])
    assert np.isnan(df["Feature 2"].iloc[0])
    assert df["Feature 3"].iloc[0] == 35.0
    assert df["Feature 4"].iloc[0] == 40.0
    assert df["Feature 5"].iloc[0] == 55.0
    assert df["Feature 6"].iloc[0] == 70.0


def test_csv_to_dataframe_transposed():
    """Test method bn_modeller.utils.db_model_handler.csv_to_dataframe
    with a transposed sample CSV file with samples in columns and float or emply
    values of features
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets",
        "sample_transposed_csv.csv",
    )
    print(csv_path)
    df = sheetfile_to_dataframe(csv_path, transposed_csv=True)
    print(df.columns, len(df))
    assert list(df.columns) == [
        "Feature 1",
        "Feature 2",
        "Feature 3",
        "Feature 4",
        "Feature 5",
        "Feature 6",
    ]
    assert len(df) == 15
    assert np.isnan(df["Feature 1"].iloc[0])
    assert np.isnan(df["Feature 2"].iloc[0])
    assert df["Feature 3"].iloc[0] == 35.0
    assert df["Feature 4"].iloc[0] == 40.0
    assert df["Feature 5"].iloc[0] == 55.0
    assert df["Feature 6"].iloc[0] == 70.0


def test_csv_to_dataframe_with_empty_columns():
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "sample_empty_column.csv"
    )
    df = sheetfile_to_dataframe(csv_path, transposed_csv=False, skip_cols=1)
    assert list(df.columns) == [
        "Feature 1",
        "Feature 2",
        "Feature 3",
        "Feature 4",
        "Feature 5",
        "Feature 6",
    ]
    assert len(df) == 15
    assert np.isnan(df["Feature 1"].iloc[0])
    assert np.isnan(df["Feature 2"].iloc[0])
    assert df["Feature 3"].iloc[0] == 35.0
    assert df["Feature 4"].iloc[0] == 40.0
    assert df["Feature 5"].iloc[0] == 55.0
    assert df["Feature 6"].iloc[0] == 70.0


def test_csv_to_dataframe_with_empty_rows():
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "sample_empty_row.csv"
    )
    df = sheetfile_to_dataframe(csv_path, transposed_csv=False, skip_rows=1)
    assert list(df.columns) == [
        "Feature 1",
        "Feature 2",
        "Feature 3",
        "Feature 4",
        "Feature 5",
        "Feature 6",
    ]
    assert len(df) == 15
    assert np.isnan(df["Feature 1"].iloc[0])
    assert np.isnan(df["Feature 2"].iloc[0])
    assert df["Feature 3"].iloc[0] == 35.0
    assert df["Feature 4"].iloc[0] == 40.0
    assert df["Feature 5"].iloc[0] == 55.0
    assert df["Feature 6"].iloc[0] == 70.0


def test_collect_non_numeric_values():
    data = pd.DataFrame(
        {
            "A": ["1.5", "bad", "3", "bad", "also bad"],
            "B": [1, 2, 3, 4, np.nan],
        }
    )
    values = collect_non_numeric_values(data)
    assert values == ["bad", "also bad"]


def test_collect_non_numeric_values_transposed():
    data = pd.DataFrame(
        {"s1": [1.0, "x"], "s2": [2.0, np.nan], "s3": ["y", 3.0]},
        index=["Feature A", "Feature B"],
    ).T
    values = collect_non_numeric_values(data)
    # Unique values in order of first appearance (columns traversed first).
    assert values == ["y", "x"]


def test_apply_value_map():
    data = pd.DataFrame(
        {"A": ["1.5", "bad", "x"], "B": [1, 2, 3]},
        index=["10", "20", "30"],
    )
    fixed = apply_value_map(data, {"bad": 0.5, "x": np.nan})
    assert fixed["A"].iloc[0] == 1.5
    assert fixed["A"].iloc[1] == 0.5
    assert np.isnan(fixed["A"].iloc[2])
    assert fixed["B"].tolist() == [1, 2, 3]
    assert list(fixed.index) == [10, 20, 30]
    assert fixed.index.dtype == np.dtype("int64")


def test_apply_value_map_without_mapping():
    data = pd.DataFrame({"A": ["1", "junk"]}, index=["1", "2"])
    fixed = apply_value_map(data, {})
    assert fixed["A"].iloc[0] == 1
    assert np.isnan(fixed["A"].iloc[1])


def test_apply_value_map_with_non_numeric_index():
    data = pd.DataFrame({"A": [1.0]}, index=["abc"])
    with pytest.raises(ValueError, match="Sample ID must be numeric"):
        apply_value_map(data, {})


@pytest.fixture(scope="module")
def qcore_app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


@pytest.fixture()
def project_db(qcore_app, tmp_path):
    db = QSqlDatabase.addDatabase("QSQLITE", "test_import_conn")
    db.setDatabaseName(str(tmp_path / "project.sqlite"))
    assert db.open()
    create_project_schema(db)
    yield db
    db.close()
    db = None
    QSqlDatabase.removeDatabase("test_import_conn")


def _count_rows(db, table):
    query = QSqlQuery(db)
    assert query.exec(f"SELECT COUNT(*) FROM {table}")
    query.next()
    return query.value(0)


def test_import_dataframe_to_db(project_db):
    data = pd.DataFrame(
        {
            "Feature 1": [1.0, 2.0, np.nan],
            "Feature 2": [np.nan, 5.0, 6.0],
        },
        index=pd.Index([10, 20, 30], dtype=int),
    )
    stats = import_dataframe_to_db(project_db, data)

    assert stats.features == 2
    assert stats.samples == 3
    assert stats.nan_values == 2

    query = QSqlQuery(project_db)
    assert query.exec(
        f"SELECT {FeatureSqlTableModel.column_name} "
        f"FROM {FeatureSqlTableModel.table_name} "
        f"ORDER BY {FeatureSqlTableModel.column_name}"
    )
    names = []
    while query.next():
        names.append(query.value(0))
    assert names == ["Feature 1", "Feature 2"]

    assert query.exec(
        f"SELECT {SampleSqlTableModel.column_sample_id}, "
        f"{SampleSqlTableModel.column_value} "
        f"FROM {SampleSqlTableModel.table_name} "
        f"ORDER BY {SampleSqlTableModel.column_sample_id}, {SampleSqlTableModel.column_value}"
    )
    rows = []
    while query.next():
        rows.append((query.value(0), query.value(1)))
    assert rows == [(10, 1.0), (20, 2.0), (20, 5.0), (30, 6.0)]


def test_import_dataframe_to_db_progress(project_db):
    data = pd.DataFrame(
        {f"Feature {i}": [float(i)] * 25 for i in range(4)},
        index=pd.Index(range(25), dtype=int),
    )
    emissions = []
    stats = import_dataframe_to_db(
        project_db,
        data,
        progress_callback=lambda fraction, message: emissions.append(
            (fraction, message)
        ),
    )

    assert stats.samples == 25
    fractions = [fraction for fraction, _ in emissions]
    # Monotonic (non-decreasing) and covering all import phases.
    assert fractions == sorted(fractions)
    assert fractions[0] >= PROGRESS_FEATURES_START
    assert any(
        PROGRESS_FEATURES_START <= fraction < PROGRESS_FEATURES_END
        for fraction in fractions
    )
    assert any(
        PROGRESS_SAMPLES_START <= fraction < PROGRESS_SAMPLES_END
        for fraction in fractions
    )
    assert fractions[-1] == PROGRESS_SAMPLES_END
    assert all(isinstance(message, str) and message for _, message in emissions)


def test_import_dataframe_to_db_cancel(project_db):
    data = pd.DataFrame(
        {"Feature 1": [1.0, 2.0, 3.0]},
        index=pd.Index([1, 2, 3], dtype=int),
    )
    checks = {"count": 0}

    def cancel_after_first_row():
        checks["count"] += 1
        return checks["count"] > 1

    with pytest.raises(ImportCancelled):
        import_dataframe_to_db(project_db, data, cancel_check=cancel_after_first_row)

    # The transaction was rolled back: nothing persisted, and the connection
    # remains usable.
    assert _count_rows(project_db, FeatureSqlTableModel.table_name) == 0
    assert _count_rows(project_db, SampleSqlTableModel.table_name) == 0
