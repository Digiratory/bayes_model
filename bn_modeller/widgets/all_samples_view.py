from PySide6.QtWidgets import QWidget, QTableView
from PySide6.QtCore import QAbstractItemModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel

class AllSamplesView(QTableView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def setModel(self, model: SampleSqlTableModel):
        super().setModel(model)