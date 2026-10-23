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
    AvailableFeaturesProxyModel,
    FeatureSelectionTableModel,
    SelectedFeaturesProxyModel,
    feature_metrics_from_correlation_model,
)
from bn_modeller.widgets.threshold_control_widget import ThresholdControlWidget
from bn_modeller.widgets.transfer_button_panel import TransferButtonPanel


class FeatureSelectionWidget(QWidget):
    """
    Main widget for feature selection interface.
    Integrates threshold controls, dual-panel feature transfer, and filtering functionality.
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

        # Left panel - Available features
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_title = QLabel("Available Features")
        left_title.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(left_title)

        self.available_table = QTableView()
        self.available_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.available_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.available_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_layout.addWidget(self.available_table)

        # Transfer button panel
        self.transfer_panel = TransferButtonPanel()
        self.transfer_panel.transferRight.connect(self._transferFeaturesRight)
        self.transfer_panel.transferLeft.connect(self._transferFeaturesLeft)

        # Right panel - Selected features
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_title = QLabel("Selected Features")
        right_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(right_title)

        self.selected_table = QTableView()
        self.selected_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.selected_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.selected_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.selected_table)

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

        self.available_model = AvailableFeaturesProxyModel()
        self.available_model.setSourceModel(self._table_model)

        self.selected_model = SelectedFeaturesProxyModel()
        self.selected_model.setSourceModel(self._table_model)

        # Set models to table views
        self.available_table.setModel(self.available_model)
        self.selected_table.setModel(self.selected_model)

        # Configure table views
        for table in [self.available_table, self.selected_table]:
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

    def _mapSelectedRowsToSource(self, table: QTableView, proxy_model) -> list[int]:
        """Map the selected rows of a panel view to source model rows"""
        return sorted(
            {
                proxy_model.mapToSource(index).row()
                for index in table.selectionModel().selectedRows()
            },
            reverse=True,
        )

    def _transferFeaturesRight(self):
        """Transfer selected features from available to selected"""
        source_rows = self._mapSelectedRowsToSource(
            self.available_table, self.available_model
        )
        self.available_table.selectionModel().clearSelection()
        self._table_model.setSelected(source_rows, True)

    def _transferFeaturesLeft(self):
        """Transfer selected features from selected to available"""
        source_rows = self._mapSelectedRowsToSource(
            self.selected_table, self.selected_model
        )
        self.selected_table.selectionModel().clearSelection()
        self._table_model.setSelected(source_rows, False)

    def getSelectedFeatures(self) -> list[str]:
        """Get the names of the selected features"""
        return self._table_model.selectedNames()

    def getAvailableFeatures(self) -> list[str]:
        """Get the names of the available (not selected) features"""
        return self._table_model.availableNames()

    def hasAvailableFeatures(self) -> bool:
        """Check the left panel: any not-selected feature passes the threshold"""
        return self.available_model.rowCount() > 0
