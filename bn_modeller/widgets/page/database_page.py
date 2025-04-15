from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

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

        # Left side widget with feature selector view
        leftSideWidget = QWidget()
        leftSideWidgetLayout = QVBoxLayout(leftSideWidget)

        self.featureSelectorView = SelectableListView()
        leftSideWidgetLayout.addWidget(self.featureSelectorView)

        featureSelectorExplanationLabel = QLabel(
            self.tr(
                "Here you can select features to evaluate and visualize correlations between them in the pairplot view."
            )
        )
        featureSelectorExplanationLabel.setWordWrap(True)
        leftSideWidgetLayout.addWidget(featureSelectorExplanationLabel)

        self.addWidget(leftSideWidget)

        # Right side widget with pairplot view

        rightSideWidget = QWidget()
        rightSideWidgetLayout = QVBoxLayout(rightSideWidget)

        self.pairPlorView = PairplotView()
        rightSideWidgetLayout.addWidget(self.pairPlorView)

        pairplotExplanationLabel = QLabel(
            self.tr(
                "Here you can see a pairplot of selected features. This allows you to visualize correlations between selected features. The number in the top of each subplot represents the Spearman correlation coefficient between the two features."
            )
        )
        pairplotExplanationLabel.setWordWrap(True)
        rightSideWidgetLayout.addWidget(pairplotExplanationLabel)

        self.addWidget(rightSideWidget)

        # self.databaseView = AllSamplesView()
        # self.addWidget(self.databaseView)

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

        # self.databaseView.setModel(self.visualisationProxyModel)
        self.pairPlorView.setModel(
            self.visualisationProxyModel,
            self._featureSqlTableModel.fieldIndex(FeatureSqlTableModel.column_name),
            self._sampleSqlTableModel.fieldIndex(SampleSqlTableModel.column_sample_id),
            self._sampleSqlTableModel.fieldIndex(SampleSqlTableModel.column_feature_id),
            self._sampleSqlTableModel.fieldIndex(SampleSqlTableModel.column_value),
        )
