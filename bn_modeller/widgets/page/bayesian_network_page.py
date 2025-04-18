from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QWidget,
)

from bn_modeller.models import (
    CorrelationSQLProxyModel,
    FilterPairTableSQLProxyModel,
    PairTableSQLProxyModel,
)
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
        self.featureSelectorView.setStatusTip(
            self.tr("Select features for the Bayesian Network.")
        )
        self.dependencyTabWidget.addWidget(self.featureSelectorView)
        self.dependencyTabWidget.setStretchFactor(0, 1)

        # Dependency Table
        depTableWidget = QWidget()
        depTableLayout = QGridLayout()

        self._depTable = DependencySetupTableView()
        depTableLayout.addWidget(self._depTable, 1, 1)

        independentLabel = QVertivalLabel("Independent")
        depTableLayout.addWidget(independentLabel, 1, 0, Qt.AlignmentFlag.AlignCenter)

        dependentLabel = QLabel("Dependent")
        depTableLayout.addWidget(dependentLabel, 0, 1, Qt.AlignmentFlag.AlignCenter)

        explanationLabel = QLabel(
            self.tr(
                "Here you can setup expert-defined dependencies between features, choosen in the left side of the window.\n"
                "In the table you can see Spearman correlation coefficients between features as well as partial correlation coefficients.\n"
                "The background color of the table cells indicates the strength of the correlation.\n\n"
                "To visualize the Bayesian Network, open the 'Visualization' tab.\n\n"
                "Please note, that these dependencies are not learned from the data. "
                "They are defined by experts and used to guide the learning process.\n\n"
                "Hint: You can select entire rows or columns by clicking using right mouse button on the row or column header."
            )
        )
        depTableLayout.addWidget(
            explanationLabel, 2, 0, 1, 2, Qt.AlignmentFlag.AlignLeft
        )

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

        filterPairTableSQLProxyModel: FilterPairTableSQLProxyModel = (
            FilterPairTableSQLProxyModel()
        )
        filterPairTableSQLProxyModel.setSourceModel(pairTableSQLProxyModel)
        filterPairTableSQLProxyModel.setFilterModel(
            self._featureCheckableSortFilterProxyModel,
            pairTableSQLProxyModel.getFeatureSqlTableModel().fieldIndex(
                FeatureSqlTableModel.column_id
            ),
        )

        self._correlationModel = CorrelationSQLProxyModel(filterPairTableSQLProxyModel)
        self._correlationModel.partialCorrGeneralError.connect(
            self.onPartialCorrError, type=Qt.ConnectionType.QueuedConnection
        )

        self._depTable.setModel(self._correlationModel)

        self.visualizationTabWidget.setModels(self._correlationModel)

    @Slot()
    def onPartialCorrError(self):
        res = QMessageBox.critical(
            self,
            self.tr("Partial Correlation Error"),
            self.tr(
                "An error occurred while calculating the partial correlation. \n\n"
                "Highly likely, it is caused by a missing value in the data set.\n"
                "To resolve this issue, you can try to disable features with all NAN values in the correlation matrix or select additional features that might help fill in the gaps."
            ),
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
        )
