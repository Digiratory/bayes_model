from bn_modeller.bayesian_nets.prediction_results import (
    PREDICTED_PREFIX,
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
