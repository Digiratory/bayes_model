from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from bn_modeller.models import CorrelationSQLProxyModel
from bn_modeller.models.feature_selection_model import (
    FeatureSelectionTableModel,
    InputFeaturesProxyModel,
    OutputFeaturesProxyModel,
    feature_metrics_from_correlation_model,
)
from bn_modeller.widgets.threshold_control_widget import ThresholdControlWidget
from bn_modeller.widgets.transfer_button_panel import TransferButtonPanel


class FeatureSelectionWidget(QWidget):
    """
    Main widget for assigning prediction roles to features.
    Integrates threshold controls and dual-panel transfer: all features
    start as inputs (observable) on the left; features moved to the right
    are predicted as outputs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_models()

    def _init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QLabel("Feature Selection")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)

        # Threshold control widget
        self.threshold_control = ThresholdControlWidget()
        self.threshold_control.thresholdChanged.connect(self._onThresholdChanged)
        main_layout.addWidget(self.threshold_control)

        # Main content with splitters
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Left panel - Input features (observable)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_title = QLabel("Input Features")
        left_title.setToolTip(
            "Observable features used to condition the prediction. "
            "All features are inputs initially."
        )
        left_title.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(left_title)

        self.input_table = QTableView()
        self.input_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.input_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.input_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_layout.addWidget(self.input_table)

        # Transfer button panel
        self.transfer_panel = TransferButtonPanel()
        self.transfer_panel.transferRight.connect(self._transferFeaturesToOutput)
        self.transfer_panel.transferLeft.connect(self._transferFeaturesToInput)

        # Right panel - Output features (to predict)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_title = QLabel("Features to Predict")
        right_title.setToolTip(
            "Features predicted from the input features when clicking Predict."
        )
        right_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(right_title)

        self.output_table = QTableView()
        self.output_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.output_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.output_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.output_table)

        # Add panels and transfer buttons to content layout
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(self.transfer_panel, 0)
        content_layout.addWidget(right_panel, 1)

        main_layout.addWidget(content_widget, 1)

    def _init_models(self):
        """Initialize the data models"""
        # Single source of truth shared by both panel views; exclusivity
        # between the panels holds by construction.
        self._table_model = FeatureSelectionTableModel()

        self.input_model = InputFeaturesProxyModel()
        self.input_model.setSourceModel(self._table_model)

        self.output_model = OutputFeaturesProxyModel()
        self.output_model.setSourceModel(self._table_model)

        # Set models to table views
        self.input_table.setModel(self.input_model)
        self.output_table.setModel(self.output_model)

        # Configure table views
        for table in [self.input_table, self.output_table]:
            table.horizontalHeader().setStretchLastSection(True)
            table.verticalHeader().setVisible(False)
            table.setSortingEnabled(False)

    def setSourceModel(self, source_model: CorrelationSQLProxyModel):
        """Extract feature metrics from the correlation model"""
        self._table_model.setMetrics(
            feature_metrics_from_correlation_model(source_model)
        )

    def _onThresholdChanged(self, threshold_type: str, threshold_value: float):
        """Handle threshold changes from the control widget"""
        self._table_model.setCriterionThreshold(threshold_type, threshold_value)

    def _mapViewSelectionToSource(self, table: QTableView, proxy_model) -> list[int]:
        """Map the selected rows of a panel view to source model rows"""
        return sorted(
            {
                proxy_model.mapToSource(index).row()
                for index in table.selectionModel().selectedRows()
            },
            reverse=True,
        )

    def _transferFeaturesToOutput(self):
        """Move the selected input features to the prediction targets"""
        source_rows = self._mapViewSelectionToSource(self.input_table, self.input_model)
        self.input_table.selectionModel().clearSelection()
        self._table_model.setOutput(source_rows, True)

    def _transferFeaturesToInput(self):
        """Move the selected prediction targets back to the inputs"""
        source_rows = self._mapViewSelectionToSource(
            self.output_table, self.output_model
        )
        self.output_table.selectionModel().clearSelection()
        self._table_model.setOutput(source_rows, False)

    def getInputFeatures(self) -> list[str]:
        """Get the names of the input (observable) features"""
        return self._table_model.inputNames()

    def getOutputFeatures(self) -> list[str]:
        """Get the names of the features marked for prediction"""
        return self._table_model.outputNames()

    def hasVisibleInputFeatures(self) -> bool:
        """Check the left panel: any input feature passes the threshold"""
        return self.input_model.rowCount() > 0
