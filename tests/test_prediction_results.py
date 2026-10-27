from bn_modeller.bayesian_nets.prediction_results import (
    PREDICTED_PREFIX,
    find_predicted_name_conflicts,
)


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
