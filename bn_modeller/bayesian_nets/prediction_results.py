"""Pure helpers for the prediction result table.

The prediction worker, the validation on the page and the results dialog
share these helpers so the result-table conventions (the leading
``Sample Id`` column and the ``Predicted <feature>`` columns) are defined
in one Qt-free place.
"""

import numpy as np
import pandas as pd

PREDICTED_PREFIX = "Predicted "
SAMPLE_ID_COLUMN = "Sample Id"


def find_predicted_name_conflicts(
    target_features: list[str],
) -> list[tuple[str, str]]:
    """Find prediction targets whose predicted column name is a target too.

    The result frame keeps the observed values of every target next to the
    ``Predicted <target>`` columns, so a pair of targets satisfying
    ``"Predicted " + t1 == t2`` would make the predicted column of ``t1``
    overwrite the observed values of ``t2``.

    Args:
        target_features: Names of the features marked for prediction.

    Returns:
        list[tuple[str, str]]: Conflicting ``(t1, t2)`` name pairs.
    """
    names = list(target_features)
    return [
        (name, PREDICTED_PREFIX + name)
        for name in names
        if PREDICTED_PREFIX + name in names
    ]


def assemble_prediction_results(
    samples: pd.DataFrame,
    valid_mask: np.ndarray,
    target_features: list[str],
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble the result frame shown in the results dialog and CSV.

    One row per sample passing ``valid_mask``, with the original sample
    ids (the index of ``samples``) in the leading ``Sample Id`` column,
    the observed values of the target features, and the predicted values
    in the ``Predicted <target>`` columns.

    Args:
        samples: Feature samples indexed by the original sample id.
        valid_mask: Positional boolean mask of the samples to report.
        target_features: Names of the features marked for prediction.
        predictions: Predicted values with one column per target, aligned
            row-wise with the samples selected by ``valid_mask``.

    Returns:
        pd.DataFrame: The assembled result table with a fresh positional
        index.

    Raises:
        ValueError: When a target name would collide with a result
            column: the reserved ``Sample Id`` column or the predicted
            column of another target (see
            :func:`find_predicted_name_conflicts`).
    """
    if SAMPLE_ID_COLUMN in target_features:
        raise ValueError(
            f"Feature name '{SAMPLE_ID_COLUMN}' collides with the reserved "
            "result column; rename the feature or exclude it from prediction"
        )
    if find_predicted_name_conflicts(target_features):
        raise ValueError(
            "A feature name collides with the predicted column of another "
            "feature; rename the feature or exclude it from prediction"
        )

    observed = samples.loc[valid_mask, target_features]
    columns = {SAMPLE_ID_COLUMN: observed.index.to_numpy()}
    for target in target_features:
        columns[target] = observed[target].to_numpy()
    for target in target_features:
        columns[PREDICTED_PREFIX + target] = predictions[target].to_numpy()
    return pd.DataFrame(columns)
