from PySide6.QtCore import QAbstractItemModel, Qt, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QTableView, QWidget

from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.widgets.all_samples_view import AllSamplesView


class RegrPlotPageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QHBoxLayout(self)
