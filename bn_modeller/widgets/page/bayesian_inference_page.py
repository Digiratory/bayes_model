from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class BayesianInferencePageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):

        self.mainLayout = QVBoxLayout(self)

        # Top Layout with tables

        topLayout = QHBoxLayout()
        self.tableSource = QTableView()
        self.tableTarget = QTableView()

        topLayout.addWidget(self.tableSource)
        topLayout.addWidget(self.tableTarget)

        # Finalization
        self.setLayout(self.mainLayout)
