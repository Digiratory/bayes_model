from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from bn_modeller.models import CorrelationSQLProxyModel
from bn_modeller.widgets.feature_selection_widget import FeatureSelectionWidget


class BayesianInferencePageWidget(QWidget):
    predictRequested = Signal()

    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QVBoxLayout(self)

        # Create feature selection widget
        self.feature_selection_widget = FeatureSelectionWidget()
        self.mainLayout.addWidget(self.feature_selection_widget, 1)

        # Predict action
        self.predictButton = QPushButton(self.tr("Predict"))
        self.predictButton.clicked.connect(self.predictRequested.emit)
        self.mainLayout.addWidget(self.predictButton)

        # Finalization
        self.setLayout(self.mainLayout)

    def setModels(self, correlation_model: CorrelationSQLProxyModel):
        """Set the correlation model for feature selection"""
        self.feature_selection_widget.setSourceModel(correlation_model)

    def getInputFeatures(self) -> list[str]:
        """Get the list of input (observable) features"""
        return self.feature_selection_widget.getInputFeatures()

    def getOutputFeatures(self) -> list[str]:
        """Get the list of features marked for prediction"""
        return self.feature_selection_widget.getOutputFeatures()

    def hasVisibleInputFeatures(self) -> bool:
        """Check the input panel: any input feature passes the threshold"""
        return self.feature_selection_widget.hasVisibleInputFeatures()
