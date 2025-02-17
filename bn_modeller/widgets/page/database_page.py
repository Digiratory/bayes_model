from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget

from bn_modeller.models import (
    CheckableSortFilterProxyModel,
    RelationalSortFilterProxyModel,
)
from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.widgets.all_samples_view import AllSamplesView
from bn_modeller.widgets.plots import PairplotView
from bn_modeller.widgets.selectable_list_view import SelectableListView


class DatabasePageWidget(QSplitter):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._init_ui()

    def _init_ui(self):
        self.setOrientation(Qt.Orientation.Horizontal)

        self.featureSelectorView = SelectableListView()
        self.addWidget(self.featureSelectorView)

        self.databaseView = AllSamplesView()
        self.addWidget(self.databaseView)

        self.pairPlorView = PairplotView()
        self.addWidget(self.pairPlorView)

    def setModels(
        self,
        featureSqlTableModel: FeatureSqlTableModel,
        sampleSqlTableModel: SampleSqlTableModel,
    ):
        self._sampleSqlTableModel = sampleSqlTableModel
        self._featureSqlTableModel = featureSqlTableModel

        self._featureCheckableSortFilterProxyModel = CheckableSortFilterProxyModel()
        self._featureCheckableSortFilterProxyModel.setSourceModel(
            self._featureSqlTableModel
        )
        self.featureSelectorView.setModel(self._featureCheckableSortFilterProxyModel)
        self.featureSelectorView.setModelColumn(
            featureSqlTableModel.fieldIndex(featureSqlTableModel.column_name)
        )

        self.visualisationProxyModel = RelationalSortFilterProxyModel()
        self.visualisationProxyModel.setSourceModel(self._sampleSqlTableModel)
        self.visualisationProxyModel.setFilterModel(
            self._featureCheckableSortFilterProxyModel,
            self._featureSqlTableModel.fieldIndex(FeatureSqlTableModel.column_id),
        )
        self.visualisationProxyModel.setFilterKeyColumn(
            self._sampleSqlTableModel.fieldIndex(SampleSqlTableModel.column_feature_id)
        )

        self.databaseView.setModel(self.visualisationProxyModel)
        self.pairPlorView.setModel(
            self.visualisationProxyModel,
            self._featureSqlTableModel.fieldIndex(FeatureSqlTableModel.column_name),
            self._sampleSqlTableModel.fieldIndex(SampleSqlTableModel.column_sample_id),
            self._sampleSqlTableModel.fieldIndex(SampleSqlTableModel.column_feature_id),
            self._sampleSqlTableModel.fieldIndex(SampleSqlTableModel.column_value),
        )
