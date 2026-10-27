"""Pure helpers for the prediction result table.

The prediction worker, the validation on the page and the results dialog
share these helpers so the result-table conventions (the
``Predicted <feature>`` columns) are defined in one Qt-free place.
"""

PREDICTED_PREFIX = "Predicted "


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
