from PySide6.QtWidgets import QWidget, QTableView, QHBoxLayout
from PySide6.QtCore import QAbstractItemModel, Qt, Signal, Slot

from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel, PersistanceCheckableFeatureListProxyModel
from bn_modeller.models import CheckableSortFilterProxyModel, RelationalSortFilterProxyModel,FilterPairTableSQLProxyModel

from bn_modeller.models import PairTableSQLProxyModel
from bn_modeller.widgets import DependencySetupTableView, SelectableListView


class DependencySetupPageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QHBoxLayout(self)

        self.featureSelectorView = SelectableListView()
        self.mainLayout.addWidget(self.featureSelectorView, 1)

        self._depTable = DependencySetupTableView()
        self.mainLayout.addWidget(self._depTable, 2)

        self.setLayout(self.mainLayout)

    def setModels(self, pairTableSQLProxyModel: PairTableSQLProxyModel):
        # TODO: т.к. при реализации обсчета байесовских сетей нужно использовать 
        # self._pairTableSQLProxyModel, вероятно, её нужно будет вытащить наружу 
        # или сделать рассчеты дочерним объектом этой страницы
        
        self._featureCheckableSortFilterProxyModel = PersistanceCheckableFeatureListProxyModel()
        self._featureCheckableSortFilterProxyModel.setSourceModel(
            pairTableSQLProxyModel.getFeatureSqlTableModel())

        self.featureSelectorView.setModel(
            self._featureCheckableSortFilterProxyModel)
        self.featureSelectorView.setModelColumn(
            pairTableSQLProxyModel.getFeatureSqlTableModel().fieldIndex(
                pairTableSQLProxyModel.getFeatureSqlTableModel().column_name))

        self._pairTableSQLProxyModel = FilterPairTableSQLProxyModel()
        self._pairTableSQLProxyModel.setSourceModel(pairTableSQLProxyModel)
        self._pairTableSQLProxyModel.setFilterModel(
            self._featureCheckableSortFilterProxyModel, 
            pairTableSQLProxyModel.getFeatureSqlTableModel().fieldIndex(FeatureSqlTableModel.column_id))
        self._depTable.setModel(self._pairTableSQLProxyModel)
