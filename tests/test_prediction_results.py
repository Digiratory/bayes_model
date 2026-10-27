import numpy as np
import pandas as pd
import pytest

from bn_modeller.bayesian_nets.prediction_results import (
    PREDICTED_PREFIX,
    SAMPLE_ID_COLUMN,
    assemble_prediction_results,
    find_predicted_name_conflicts,
)
from bn_modeller.models.feature_selection_model import merge_preserving_outputs


def test_find_predicted_name_conflicts_detects_collision():
    # Regression: if the features 'y' and 'Predicted y' are both marked for
    # prediction, the result column 'Predicted y' used to overwrite the
    # observed values of the feature 'Predicted y'.
    assert find_predicted_name_conflicts(["y", "Predicted y"]) == [("y", "Predicted y")]


def test_find_predicted_name_conflicts_is_order_independent():
    assert find_predicted_name_conflicts(["Predicted y", "y"]) == [("y", "Predicted y")]


def test_find_predicted_name_conflicts_without_collision():
    assert find_predicted_name_conflicts(["y"]) == []
    assert find_predicted_name_conflicts(["y", "z", "Predicted z"]) == [
        ("z", PREDICTED_PREFIX + "z")
    ]
    assert find_predicted_name_conflicts([]) == []


def test_merge_preserves_output_roles_for_surviving_names():
    # Regression: the prediction feature list was extracted once at project
    # load, so features moved to 'Features to Predict' lost their role on
    # every re-extraction after the Dependency selection changed.
    old_rows = [
        {"name": "x1", "metrics": {"R": 0.5}, "is_output": False},
        {"name": "y", "metrics": {"R": 0.9}, "is_output": True},
    ]
    metrics = {"x1": {"R": 0.6}, "y": {"R": 0.8}}

    rows = merge_preserving_outputs(old_rows, metrics)

    assert [row["name"] for row in rows] == ["x1", "y"]
    assert [row["is_output"] for row in rows] == [False, True]
    # Fresh metrics win over the stale ones.
    assert rows[0]["metrics"] == {"R": 0.6}
    assert rows[1]["metrics"] == {"R": 0.8}


def test_merge_drops_absent_and_defaults_new_features_to_input():
    old_rows = [
        {"name": "gone", "metrics": {"R": 0.5}, "is_output": True},
        {"name": "kept", "metrics": {"R": 0.4}, "is_output": False},
    ]
    metrics = {"kept": {"R": 0.4}, "new": {"R": 0.7}}

    rows = merge_preserving_outputs(old_rows, metrics)

    assert rows == [
        {"name": "kept", "metrics": {"R": 0.4}, "is_output": False},
        {"name": "new", "metrics": {"R": 0.7}, "is_output": False},
    ]


def make_samples() -> pd.DataFrame:
    return pd.DataFrame(
        {"x1": [1.0, 2.0, 3.0], "y": [10.0, np.nan, 30.0]},
        index=pd.Index([7, 42, 105], name="sampleId"),
    )


def test_assemble_keeps_sample_ids_through_validity_mask():
    # Regression: rows dropped by the validity mask used to be renumbered,
    # so exported predictions could not be matched to the source samples.
    valid_mask = np.array([True, False, True])
    predictions = pd.DataFrame({"y": [11.0, 31.0]})

    result = assemble_prediction_results(make_samples(), valid_mask, ["y"], predictions)

    assert list(result.columns) == [SAMPLE_ID_COLUMN, "y", PREDICTED_PREFIX + "y"]
    assert result[SAMPLE_ID_COLUMN].tolist() == [7, 105]
    assert result["y"].tolist() == [10.0, 30.0]
    assert result["Predicted y"].tolist() == [11.0, 31.0]


def test_assemble_never_overwrites_observed_column():
    # Regression: a target named 'Predicted y' let the predicted column of
    # the target 'y' overwrite the observed values of 'Predicted y'.
    samples = pd.DataFrame(
        {"x1": [1.0, 2.0], "y": [10.0, 20.0], "Predicted y": [100.0, 200.0]},
        index=pd.Index([1, 2]),
    )
    predictions = pd.DataFrame({"y": [11.0, 21.0], "Predicted y": [12.0, 22.0]})

    with pytest.raises(ValueError):
        assemble_prediction_results(
            samples, np.array([True, True]), ["y", "Predicted y"], predictions
        )


def test_assemble_rejects_reserved_sample_id_target():
    with pytest.raises(ValueError):
        assemble_prediction_results(
            make_samples(),
            np.array([True, True, True]),
            [SAMPLE_ID_COLUMN],
            pd.DataFrame({SAMPLE_ID_COLUMN: [1.0, 2.0, 3.0]}),
        )
