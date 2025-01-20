from PySide6.QtWidgets import QWidget, QTableView, QVBoxLayout
from PySide6.QtCore import QAbstractItemModel, Qt, Signal, Slot

from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.widgets.all_samples_view import AllSamplesView


class DatabasePageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QVBoxLayout(self)

        self.databaseView = AllSamplesView()
        self.mainLayout.addWidget(self.databaseView)

        self.setLayout(self.mainLayout)

    def setModels(self, sampleSqlTableModel: SampleSqlTableModel):
        self._sampleSqlTableModel = sampleSqlTableModel

        self.databaseView.setModel(self._sampleSqlTableModel)
