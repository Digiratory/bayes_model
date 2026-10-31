"""Feature roles model for the Prediction page.

A single :class:`FeatureSelectionTableModel` holds every feature with its
per-criterion metrics and an output flag. Features start as inputs (all
features are observable initially); marking a feature as output moves it
to the prediction targets. Two filter proxies provide the panel views:
the left panel shows input features that pass the threshold, the right
panel shows the outputs to predict. Because both panels read from one
source of truth, exclusivity between panels holds by construction.
"""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt

from bn_modeller.bayesian_nets.feature_metrics import (
    P_VAL_KEY,
    R_KEY,
    extract_feature_metrics,
)
from bn_modeller.models.dependency_sqltable_model import (
    CorrelationSQLProxyModel,
    PairTableSQLProxyModel,
)
from bn_modeller.utils.model_adapters import tablemodel_to_dataframe


def feature_metrics_from_correlation_model(
    model: CorrelationSQLProxyModel,
) -> dict[str, dict[str, float]]:
    """Extract per-feature selection metrics from a CorrelationSQLProxyModel.

    Uses the Spearman rank correlation roles, matching the correlation
    family the Bayesian network is built on, plus the partial correlation
    role for the ``P`` criterion.
    """
    if model.rowCount() < 2:
        # The partial correlation matrix is undefined for fewer than two
        # features and its data() access would fail.
        return {}
    spearman_corr = tablemodel_to_dataframe(
        model, role=PairTableSQLProxyModel.SpearmanCorrRole
    )
    spearman_pvalue = tablemodel_to_dataframe(
        model, role=PairTableSQLProxyModel.SpearmanPValueRole
    )
    partial_corr = tablemodel_to_dataframe(
        model, role=CorrelationSQLProxyModel.PartialCorrRole
    )
    return extract_feature_metrics(spearman_corr, spearman_pvalue, partial_corr)


def merge_preserving_outputs(
    old_rows: list[dict], metrics: dict[str, dict[str, float]]
) -> list[dict]:
    """Build model rows from a fresh metric extraction, keeping roles.

    Features that remain present keep their ``is_output`` role by name;
    features that are no longer selected are dropped; newly appearing
    features start as inputs. Duplicate names collapse (last wins), which
    is acceptable because the underlying DB can hold duplicated feature
    names only as an anomaly.
    """
    preserved_outputs = {row["name"]: row["is_output"] for row in old_rows}
    return [
        {
            "name": name,
            "metrics": dict(feature_metrics),
            "is_output": preserved_outputs.get(name, False),
        }
        for name, feature_metrics in metrics.items()
    ]


class FeatureSelectionTableModel(QAbstractTableModel):
    """Table of features with selection metrics and an output flag.

    Columns: Feature | Value. The Value column shows the metric of the
    current criterion. Criterion and threshold are part of the model state
    so that all panel views filter consistently.
    """

    _COLUMN_FEATURE = 0
    _COLUMN_VALUE = 1
    _COLUMN_COUNT = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[dict] = []
        self._criterion: str = R_KEY
        self._threshold: float = 0.0

    def setMetrics(self, metrics: dict[str, dict[str, float]]):
        """Replace the features with a fresh metric extraction.

        Expects the metric dicts produced by
        :func:`extract_feature_metrics`: every feature must provide all
        criterion keys with non-NaN values. Features keep their output
        role by name from the previous rows, so the roles survive a
        re-extraction after the Dependency selection changed; features
        that are no longer selected are dropped and new features start
        as inputs.
        """
        self.beginResetModel()
        self._rows = merge_preserving_outputs(self._rows, metrics)
        self.endResetModel()

    def setCriterionThreshold(self, criterion: str, threshold: float):
        """Set criterion and threshold atomically with a single refresh."""
        changed = criterion != self._criterion or threshold != self._threshold
        self._criterion = criterion
        self._threshold = threshold
        if changed:
            self._refreshAll()

    def metric(self, row: int) -> float:
        return self._rows[row]["metrics"][self._criterion]

    def passesThreshold(self, row: int) -> bool:
        value = self.metric(row)
        if self._criterion == P_VAL_KEY:
            return value <= self._threshold
        return value >= self._threshold

    def isOutput(self, row: int) -> bool:
        return self._rows[row]["is_output"]

    def setOutput(self, rows, is_output: bool):
        """Set the output flag for the given source rows."""
        for row in rows:
            if self._rows[row]["is_output"] == is_output:
                continue
            self._rows[row]["is_output"] = is_output
            self.dataChanged.emit(
                self.index(row, self._COLUMN_FEATURE),
                self.index(row, self._COLUMN_VALUE),
                [Qt.ItemDataRole.DisplayRole],
            )

    def inputNames(self) -> list[str]:
        return [row["name"] for row in self._rows if not row["is_output"]]

    def outputNames(self) -> list[str]:
        return [row["name"] for row in self._rows if row["is_output"]]

    def _refreshAll(self):
        if not self._rows:
            return
        self.dataChanged.emit(
            self.index(0, self._COLUMN_FEATURE),
            self.index(len(self._rows) - 1, self._COLUMN_VALUE),
            [Qt.ItemDataRole.DisplayRole],
        )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._COLUMN_COUNT

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            row = self._rows[index.row()]
            if index.column() == self._COLUMN_FEATURE:
                return row["name"]
            if index.column() == self._COLUMN_VALUE:
                return self._formatValue(row["metrics"][self._criterion])
        return None

    def _formatValue(self, value: float) -> str:
        if self._criterion == P_VAL_KEY:
            return f"{value:.4f}"
        return f"{value:.3f}"

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            if section == self._COLUMN_FEATURE:
                return "Feature"
            if section == self._COLUMN_VALUE:
                return "Value"
        return super().headerData(section, orientation, role)


class InputFeaturesProxyModel(QSortFilterProxyModel):
    """Left panel view: input features passing the threshold."""

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_parent.isValid():
            return False
        model = self.sourceModel()
        return not model.isOutput(source_row) and model.passesThreshold(source_row)


class OutputFeaturesProxyModel(QSortFilterProxyModel):
    """Right panel view: features marked for prediction."""

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_parent.isValid():
            return False
        return self.sourceModel().isOutput(source_row)
