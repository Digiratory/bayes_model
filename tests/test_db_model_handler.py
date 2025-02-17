import os

import numpy as np
import pandas as pd
import pytest

from bn_modeller.utils.db_model_handler import sheetfile_to_dataframe


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
