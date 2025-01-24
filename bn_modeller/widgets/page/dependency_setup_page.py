from PySide6.QtWidgets import QWidget, QTableView, QHBoxLayout
from PySide6.QtCore import QAbstractItemModel, Qt, Signal, Slot

from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models import CheckableSortFilterProxyModel, RelationalSortFilterProxyModel

from bn_modeller.models import PairTableSQLProxyModel
from bn_modeller.widgets import DependencySetupTableView

class DependencySetupPageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QHBoxLayout(self)
        
        self._depTable = DependencySetupTableView()
        self.mainLayout.addWidget(self._depTable)

        self.setLayout(self.mainLayout)

    def setModels(self, pairTableSQLProxyModel: PairTableSQLProxyModel):
        self._pairTableSQLProxyModel = pairTableSQLProxyModel
        self._depTable.setModel(self._pairTableSQLProxyModel)
