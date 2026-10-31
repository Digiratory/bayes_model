import numpy as np
import pandas as pd

from bn_modeller.bayesian_nets.feature_metrics import (
    P_KEY,
    P_VAL_KEY,
    R_KEY,
    extract_feature_metrics,
)


def make_frame(data: np.ndarray, names: list[str]) -> pd.DataFrame:
    return pd.DataFrame(data, index=names, columns=names)


def test_extract_basic_metrics():
    names = ["a", "b", "c"]
    corr = make_frame(
        np.array(
            [
                [1.0, 0.8, -0.6],
                [0.8, 1.0, 0.3],
                [-0.6, 0.3, 1.0],
            ]
        ),
        names,
    )
    pval = make_frame(
        np.array(
            [
                [0.0, 0.01, 0.3],
                [0.01, 0.0, 0.5],
                [0.3, 0.5, 0.0],
            ]
        ),
        names,
    )
    pcorr = make_frame(
        np.array(
            [
                [1.0, 0.7, -0.2],
                [0.7, 1.0, 0.4],
                [-0.2, 0.4, 1.0],
            ]
        ),
        names,
    )

    metrics = extract_feature_metrics(corr, pval, pcorr)

    assert set(metrics) == set(names)
    assert metrics["a"] == {R_KEY: 0.8, P_KEY: 0.7, P_VAL_KEY: 0.01}
    assert metrics["b"] == {R_KEY: 0.8, P_KEY: 0.7, P_VAL_KEY: 0.01}
    assert metrics["c"] == {R_KEY: 0.6, P_KEY: 0.4, P_VAL_KEY: 0.3}


def test_self_pairs_are_excluded():
    names = ["a", "b"]
    corr = make_frame(
        np.array(
            [
                [1.0, 0.2],
                [0.2, 1.0],
            ]
        ),
        names,
    )
    pval = make_frame(
        np.array(
            [
                [0.0, 0.4],
                [0.4, 0.0],
            ]
        ),
        names,
    )
    pcorr = corr.copy()

    metrics = extract_feature_metrics(corr, pval, pcorr)

    # Without the diagonal the only metric source is the 0.2 / 0.4 pair.
    assert metrics["a"][R_KEY] == 0.2
    assert metrics["a"][P_VAL_KEY] == 0.4
    assert metrics["b"][R_KEY] == 0.2
    assert metrics["b"][P_VAL_KEY] == 0.4


def test_matrices_with_mismatched_labels_are_aligned():
    corr = make_frame(
        np.array(
            [
                [1.0, 0.8],
                [0.8, 1.0],
            ]
        ),
        ["a", "b"],
    )
    pval = make_frame(
        np.array(
            [
                [0.0, 0.01],
                [0.01, 0.0],
            ]
        ),
        ["b", "a"],
    )
    pcorr = corr.copy()

    metrics = extract_feature_metrics(corr, pval, pcorr)

    assert metrics["a"] == {R_KEY: 0.8, P_KEY: 0.8, P_VAL_KEY: 0.01}
    assert metrics["b"] == {R_KEY: 0.8, P_KEY: 0.8, P_VAL_KEY: 0.01}


def test_nan_correlation_is_treated_as_zero():
    names = ["a", "b"]
    corr = make_frame(
        np.array(
            [
                [1.0, np.nan],
                [np.nan, 1.0],
            ]
        ),
        names,
    )
    pval = make_frame(
        np.array(
            [
                [0.0, 0.02],
                [0.02, 0.0],
            ]
        ),
        names,
    )
    pcorr = make_frame(
        np.array(
            [
                [1.0, 0.5],
                [0.5, 1.0],
            ]
        ),
        names,
    )

    metrics = extract_feature_metrics(corr, pval, pcorr)

    assert metrics["a"][R_KEY] == 0.0
    assert metrics["b"][R_KEY] == 0.0
    assert metrics["a"][P_KEY] == 0.5


def test_nan_partial_correlation_is_treated_as_zero():
    names = ["a", "b"]
    corr = make_frame(np.eye(2), names)
    pval = make_frame(np.array([[0.0, 0.03], [0.03, 0.0]]), names)
    pcorr = make_frame(
        np.array(
            [
                [1.0, np.nan],
                [np.nan, 1.0],
            ]
        ),
        names,
    )

    metrics = extract_feature_metrics(corr, pval, pcorr)

    assert metrics["a"][P_KEY] == 0.0
    assert metrics["b"][P_KEY] == 0.0
    assert metrics["a"][R_KEY] == 0.0


def test_nan_pvalue_is_treated_as_one():
    names = ["a", "b"]
    corr = make_frame(np.array([[1.0, 0.9], [0.9, 1.0]]), names)
    pval = make_frame(
        np.array(
            [
                [np.nan, np.nan],
                [np.nan, np.nan],
            ]
        ),
        names,
    )
    pcorr = make_frame(np.eye(2), names)

    metrics = extract_feature_metrics(corr, pval, pcorr)

    assert metrics["a"][P_VAL_KEY] == 1.0
    assert metrics["b"][P_VAL_KEY] == 1.0


def test_single_feature_has_neutral_metrics():
    names = ["a"]
    corr = make_frame(np.array([[1.0]]), names)
    pval = make_frame(np.array([[np.nan]]), names)
    pcorr = make_frame(np.array([[1.0]]), names)

    metrics = extract_feature_metrics(corr, pval, pcorr)

    assert metrics["a"] == {R_KEY: 0.0, P_KEY: 0.0, P_VAL_KEY: 1.0}


def test_negative_correlations_use_absolute_value():
    names = ["a", "b"]
    corr = make_frame(np.array([[1.0, -0.95], [-0.95, 1.0]]), names)
    pval = make_frame(np.array([[np.nan, 0.001], [0.001, np.nan]]), names)
    pcorr = make_frame(np.array([[1.0, -0.7], [-0.7, 1.0]]), names)

    metrics = extract_feature_metrics(corr, pval, pcorr)

    assert metrics["a"][R_KEY] == 0.95
    assert metrics["a"][P_KEY] == 0.7
