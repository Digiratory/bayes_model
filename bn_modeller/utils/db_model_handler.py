import pandas as pd
import numpy as np

from PySide6.QtCore import Qt, QSortFilterProxyModel, QObject, QModelIndex, QPersistentModelIndex
from PySide6.QtSql import QSqlTableModel, QSqlIndex

from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel


class SampleFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._sampleId = None

    def enableFilter(self, sampleId):
        self._sampleId = sampleId
        self.invalidateFilter()

    def disableFilter(self):
        self._sampleId = None
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex):
        index = self.sourceModel().index(source_row,
                                         self.sourceModel().record().indexOf(SampleSqlTableModel.column_sample_id),
                                         source_parent)
        if self._sampleId is not None:
            data = self.sourceModel().data(index)
            return data == self._sampleId

        return super().filterAcceptsRow(source_row, source_parent)


def add_values_from_csv(csv_file_path: str,
                        featureSqlTableModel: FeatureSqlTableModel,
                        sampleSqlTableModel: SampleSqlTableModel):

    data_pd = pd.read_csv(csv_file_path, index_col=0)
    data_pd.index = data_pd.index.astype(int)

    feature_proxy = QSortFilterProxyModel()
    feature_proxy.setSourceModel(featureSqlTableModel)
    feature_proxy.setFilterKeyColumn(
        featureSqlTableModel.fieldIndex(featureSqlTableModel.column_name))

    new_features = []
    for col_candidate in data_pd.columns:
        feature_proxy.setFilterFixedString(col_candidate)        
        if feature_proxy.rowCount() == 0:
            new_features.append(col_candidate)

    for new_feature in new_features:
        rowRecord = featureSqlTableModel.record()
        rowRecord.remove(rowRecord.indexOf(FeatureSqlTableModel.column_id))
        rowRecord.setValue(FeatureSqlTableModel.column_name, new_feature)
        rowRecord.setValue(FeatureSqlTableModel.column_is_active, 1)
        rowRecord.setValue(FeatureSqlTableModel.column_description, "")
        featureSqlTableModel.insertRecord(-1, rowRecord)
    featureSqlTableModel.submitAll()

    

    # sample_proxy = SampleFilterProxyModel()
    # sample_proxy.setSourceModel(sampleSqlTableModel)
    # new_samples = []
    # for sample_candidate in data_pd.index:
    #     sample_proxy.enableFilter(sample_candidate)
    #     if sample_proxy.rowCount() == 0:
    #         new_samples.append(sample_candidate)
    # Logic with searching dublication is extremelly slow, ignore DB update as a temporal solution.
    # TODO: reimplement with raw sql query.
    if sampleSqlTableModel.rowCount() > 0:
        return

    # for new_sample in new_samples:
        # row_pd = data_pd.loc[new_sample]
    for index, row_pd in data_pd.iterrows():        
        for col in data_pd.columns:
            if not np.isnan(row_pd[col]):
                rowRecord = sampleSqlTableModel.record()
                rowRecord.remove(rowRecord.indexOf(
                    SampleSqlTableModel.column_id))

                feature_proxy.setFilterFixedString(col)

                rowRecord.setValue(SampleSqlTableModel.column_feature_id,
                                   feature_proxy.index(0, featureSqlTableModel.fieldIndex(
                                       FeatureSqlTableModel.column_id)).data()
                                   )
                rowRecord.setValue(
                    SampleSqlTableModel.column_sample_id, int(index))
                rowRecord.setValue(
                    SampleSqlTableModel.column_value, float(row_pd[col]))
                sampleSqlTableModel.insertRecord(-1, rowRecord)
    sampleSqlTableModel.submitAll()
    # for index, row in data_pd.iterrows():
