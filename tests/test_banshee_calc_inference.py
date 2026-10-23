import numpy as np
import pandas as pd
import pytest

from bn_modeller.bayesian_nets.pyBansheeCalculation import BansheeCalc
from bn_modeller.bayesian_nets.utils import rescale_feature


def make_dataset(n_samples: int = 30) -> pd.DataFrame:
    """Synthetic dataset: two inputs, one small- and one large-scale target."""
    rng = np.random.default_rng(42)
    x1 = rng.uniform(0.0, 10.0, n_samples)
    x2 = 0.6 * x1 + rng.normal(0.0, 3.0, n_samples)
    y_small = 2.0 * x1 + 1.0 * x2 + rng.normal(0.0, 0.1, n_samples)
    y_large = 200.0 * x1 - 100.0 * x2 + rng.normal(0.0, 1.0, n_samples)
    return pd.DataFrame({"x1": x1, "x2": x2, "y_small": y_small, "y_large": y_large})


def make_calc(df: pd.DataFrame) -> BansheeCalc:
    node_list = [0, 1, 2, 3]
    edge_list = [(0, 2), (1, 2), (0, 3), (1, 3)]
    return BansheeCalc(node_list, edge_list, df)


def test_get_target_features():
    calc = BansheeCalc.__new__(BansheeCalc)
    calc.columns_data = ["x1", "x2", "y_small", "y_large"]

    assert calc.getTargetFeatures(["x1", "x2"]) == ["y_small", "y_large"]
    assert calc.getTargetFeatures(["y_small"]) == ["x1", "x2", "y_large"]
    assert calc.getTargetFeatures([]) == ["x1", "x2", "y_small", "y_large"]


def test_get_inference_predictions_track_targets():
    np.random.seed(0)
    df = make_dataset()
    calc = make_calc(df)
    assert calc.getRankCorr() is not None

    input_features = ["x1", "x2"]
    values = df[input_features].to_numpy()

    predictions = calc.getInference(input_features, values)

    assert isinstance(predictions, pd.DataFrame)
    # Target ordering must follow the dataset column order
    assert list(predictions.columns) == ["y_small", "y_large"]
    assert predictions.shape == (len(df), 2)

    # The two targets differ by two orders of magnitude; a column mix-up
    # would swap their scales.
    small_range = float(np.ptp(predictions["y_small"]))
    large_range = float(np.ptp(predictions["y_large"]))
    assert small_range < 200
    assert large_range > 1000

    for target in ["y_small", "y_large"]:
        corr = np.corrcoef(predictions[target], df[target])[0, 1]
        assert corr > 0.8, target


def test_get_inference_accepts_single_sample_row():
    np.random.seed(0)
    df = make_dataset()
    calc = make_calc(df)

    values = df[["x1", "x2"]].iloc[0].to_numpy()
    predictions = calc.getInference(["x1", "x2"], values)

    assert predictions.shape == (1, 2)


def test_get_inference_unknown_input_feature():
    df = make_dataset()
    calc = make_calc(df)

    with pytest.raises(ValueError, match="nope"):
        calc.getInference(["x1", "nope"], df[["x1", "x2"]].to_numpy())


def test_get_inference_value_width_mismatch():
    df = make_dataset()
    calc = make_calc(df)

    values = df[["x1", "x2"]].to_numpy()
    with pytest.raises(ValueError, match="value columns"):
        calc.getInference(["x1"], values)


def test_rescale_feature():
    vector = np.array([1.0, 2.0, 3.0])
    rescaled = rescale_feature(vector, 10.0, 20.0)

    assert rescaled[0] == pytest.approx(10.0)
    assert rescaled[1] == pytest.approx(15.0)
    assert rescaled[2] == pytest.approx(20.0)


def test_rescale_feature_constant_vector_does_not_divide_by_zero():
    # A constant predicted vector (e.g. a single valid sample row) must not
    # produce all-NaN output; it maps to the lower bound instead.
    rescaled = rescale_feature(np.array([5.0, 5.0, 5.0]), 10.0, 20.0)

    assert rescaled == [10.0, 10.0, 10.0]


def test_get_inference_quantified_on_complete_rows_handles_nan_targets():
    # Regression: py-banshee normalizes its ECDF by the full row count, so
    # NaN rows in the quantification data shrink the interpolation range
    # below 1.0 and inference crashes with "above the interpolation range's
    # maximum value". Quantifying on complete rows only (page behavior)
    # must allow predicting every sample with complete inputs, including
    # rows whose targets are missing.
    np.random.seed(0)
    df = make_dataset()
    df.loc[5, "y_small"] = np.nan

    calc = make_calc(df.dropna())
    assert calc.getRankCorr() is not None

    input_features = ["x1", "x2"]
    predictions = calc.getInference(input_features, df[input_features].to_numpy())

    assert predictions.shape == (len(df), 2)
    assert list(predictions.columns) == ["y_small", "y_large"]
    # The prediction for the row with the NaN target is still produced and
    # tracks the target scale.
    assert predictions["y_small"].corr(df["y_small"].dropna()) > 0.8
