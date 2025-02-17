from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QTabWidget,
    QWidget,
)

from bn_modeller.models import FilterPairTableSQLProxyModel, PairTableSQLProxyModel
from bn_modeller.models.feature_sqltable_model import (
    FeatureSqlTableModel,
    PersistanceCheckableFeatureListProxyModel,
)
from bn_modeller.widgets import DependencySetupTableView, SelectableListView
from bn_modeller.widgets.bn_visualization_view import BayesianNetView
from bn_modeller.widgets.vertical_label import QVertivalLabel


class BayesianNetworkPageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QHBoxLayout(self)

        self.tabWidget = QTabWidget()

        # Dependency tab

        # Feature selection
        self.dependencyTabWidget = QSplitter()
        self.featureSelectorView = SelectableListView()
        self.dependencyTabWidget.addWidget(self.featureSelectorView)
        self.dependencyTabWidget.setStretchFactor(0, 1)

        # Dependency Table
        depTableWidget = QWidget()
        depTableLayout = QGridLayout()

        self._depTable = DependencySetupTableView()
        depTableLayout.addWidget(self._depTable, 1, 1)

        dependentLabel = QVertivalLabel("Independent")
        depTableLayout.addWidget(dependentLabel, 1, 0, Qt.AlignmentFlag.AlignCenter)

        dependentLabel = QLabel("Dependent")
        depTableLayout.addWidget(dependentLabel, 0, 1, Qt.AlignmentFlag.AlignCenter)

        depTableWidget.setLayout(depTableLayout)
        self.dependencyTabWidget.addWidget(depTableWidget)
        self.dependencyTabWidget.setStretchFactor(1, 2)

        self.tabWidget.addTab(self.dependencyTabWidget, self.tr("Dependency"))

        # Visualization Tab
        self.visualizationTabWidget = BayesianNetView()

        self.tabWidget.addTab(self.visualizationTabWidget, self.tr("Visulization"))

        # Finalization
        self.mainLayout.addWidget(self.tabWidget)
        self.setLayout(self.mainLayout)

    def setModels(self, pairTableSQLProxyModel: PairTableSQLProxyModel):
        # TODO: т.к. при реализации обсчета байесовских сетей нужно использовать
        # self._pairTableSQLProxyModel, вероятно, её нужно будет вытащить наружу
        # или сделать рассчеты дочерним объектом этой страницы

        self._featureCheckableSortFilterProxyModel = (
            PersistanceCheckableFeatureListProxyModel()
        )
        self._featureCheckableSortFilterProxyModel.setSourceModel(
            pairTableSQLProxyModel.getFeatureSqlTableModel()
        )

        self.featureSelectorView.setModel(self._featureCheckableSortFilterProxyModel)
        self.featureSelectorView.setModelColumn(
            pairTableSQLProxyModel.getFeatureSqlTableModel().fieldIndex(
                pairTableSQLProxyModel.getFeatureSqlTableModel().column_name
            )
        )

        self._pairTableSQLProxyModel = FilterPairTableSQLProxyModel()
        self._pairTableSQLProxyModel.setSourceModel(pairTableSQLProxyModel)
        self._pairTableSQLProxyModel.setFilterModel(
            self._featureCheckableSortFilterProxyModel,
            pairTableSQLProxyModel.getFeatureSqlTableModel().fieldIndex(
                FeatureSqlTableModel.column_id
            ),
        )
        self._depTable.setModel(self._pairTableSQLProxyModel)

        self.visualizationTabWidget.setModels(self._pairTableSQLProxyModel)
