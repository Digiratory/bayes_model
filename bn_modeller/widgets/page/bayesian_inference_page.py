from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from bn_modeller.models import CorrelationSQLProxyModel
from bn_modeller.widgets.feature_selection_widget import FeatureSelectionWidget


class BayesianInferencePageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QVBoxLayout(self)

        # Create feature selection widget
        self.feature_selection_widget = FeatureSelectionWidget()
        self.mainLayout.addWidget(self.feature_selection_widget)

        # Finalization
        self.setLayout(self.mainLayout)

    def setModels(self, correlation_model: CorrelationSQLProxyModel):
        """Set the correlation model for feature selection"""
        self.feature_selection_widget.setSourceModel(correlation_model)

    def getSelectedFeatures(self) -> list[str]:
        """Get the list of selected features"""
        return self.feature_selection_widget.getSelectedFeatures()

    def getAvailableFeatures(self) -> list[str]:
        """Get the list of available features"""
        return self.feature_selection_widget.getAvailableFeatures()
