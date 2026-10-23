"""Extraction of per-feature metrics from correlation matrices.

The Prediction page ranks features by a single criterion:
- ``R``: maximum absolute Spearman rank correlation with any other feature;
- ``P``: maximum absolute partial correlation with any other feature;
- ``P_val``: minimum Spearman correlation p-value against any other feature.

All matrices are expected to be square pandas DataFrames with feature names
on both axes. Diagonal (self-pair) entries are excluded.

NaN handling: a feature with a NaN metric is treated as 0.0 for ``R``/``P``
(so it passes a zero threshold) and as 1.0 for ``P_val`` (so it fails the
default threshold). This keeps every feature visible when the page opens.
"""

import numpy as np
import pandas as pd

R_KEY = "R"
P_KEY = "P"
P_VAL_KEY = "P_val"


def _abs_max(series: pd.Series) -> float:
    """Maximum absolute value of a series, ignoring NaN.

    Returns NaN when the series is empty or all-NaN.
    """
    if series.empty:
        return float("nan")
    return float(series.abs().max(skipna=True))


def _min(series: pd.Series) -> float:
    """Minimum value of a series, ignoring NaN.

    Returns NaN when the series is empty or all-NaN.
    """
    if series.empty:
        return float("nan")
    return float(series.min(skipna=True))


def extract_feature_metrics(
    spearman_corr: pd.DataFrame,
    spearman_pvalue: pd.DataFrame,
    partial_corr: pd.DataFrame,
) -> dict[str, dict[str, float]]:
    """Compute per-feature selection metrics from correlation matrices.

    Args:
        spearman_corr: Square DataFrame of Spearman rank correlations.
        spearman_pvalue: Square DataFrame of Spearman p-values.
        partial_corr: Square DataFrame of partial correlations.

    Returns:
        Mapping of feature name to a dict with ``R``, ``P`` and ``P_val``
        metrics. NaN metrics are normalized: 0.0 for ``R``/``P`` and 1.0
        for ``P_val``.
    """
    names = list(spearman_corr.columns)
    corr = spearman_corr.reindex(index=names, columns=names).astype(float)
    pval = spearman_pvalue.reindex(index=names, columns=names).astype(float)
    pcorr = partial_corr.reindex(index=names, columns=names).astype(float)

    metrics: dict[str, dict[str, float]] = {}
    for name in names:
        others = [other for other in names if other != name]
        corr_series = corr.loc[name, others]
        pval_series = pval.loc[name, others]
        pcorr_series = pcorr.loc[name, others]

        r = _abs_max(corr_series)
        p = _abs_max(pcorr_series)
        p_value = _min(pval_series)

        metrics[name] = {
            R_KEY: 0.0 if np.isnan(r) else r,
            P_KEY: 0.0 if np.isnan(p) else p,
            P_VAL_KEY: 1.0 if np.isnan(p_value) else p_value,
        }
    return metrics
