from typing import Any

import matplotlib as mpl
import numpy as np
import pandas as pd
import pingouin as pg
from PySide6.QtCore import (
    QAbstractTableModel,
    QByteArray,
    QIdentityProxyModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSettings,
    QSortFilterProxyModel,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlRelationalTableModel
from scipy import stats

from bn_modeller.models.feature_sqltable_model import (
    FeatureSqlTableModel,
    PersistanceCheckableFeatureListProxyModel,
)
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.utils.model_adapters import tablemodel_to_dataframe


class DependencyManyToManySqlTableModel(QSqlRelationalTableModel):
    table_name = "feature_dependency"
    column_source_feature_id = "source_feature_id"
    column_target_feature_id = "target_feature_id"

    def __init__(self, parent: QObject = None, db: QSqlDatabase = None):
        super().__init__(parent, db)

        query = QSqlQuery(
            f"CREATE TABLE IF NOT EXISTS {DependencyManyToManySqlTableModel.table_name} (\
                          {DependencyManyToManySqlTableModel.column_source_feature_id} INTEGER NOT NULL, \
                          {DependencyManyToManySqlTableModel.column_target_feature_id} INTEGER NOT NULL, \
                          PRIMARY KEY ({DependencyManyToManySqlTableModel.column_source_feature_id}, {DependencyManyToManySqlTableModel.column_target_feature_id}), \
                          FOREIGN KEY({DependencyManyToManySqlTableModel.column_source_feature_id}) REFERENCES {FeatureSqlTableModel.table_name}({FeatureSqlTableModel.column_id})\
                          FOREIGN KEY({DependencyManyToManySqlTableModel.column_target_feature_id}) REFERENCES {FeatureSqlTableModel.table_name}({FeatureSqlTableModel.column_id})\
                          );\
                          "
        )

        if not query.exec():
            raise RuntimeError(f"Unable to connect to DB: {query.lastError()}")
        self.setTable(DependencyManyToManySqlTableModel.table_name)


class PairTableSQLProxyModel(QAbstractTableModel):
    pairs_table_name = DependencyManyToManySqlTableModel.table_name
    samples_table_name = SampleSqlTableModel.table_name

    index_tbl_cls = FeatureSqlTableModel
    index_table_name = index_tbl_cls.table_name

    column_source_feature_id = (
        DependencyManyToManySqlTableModel.column_source_feature_id
    )
    column_target_feature_id = (
        DependencyManyToManySqlTableModel.column_target_feature_id
    )

    ValuePairsRole = Qt.ItemDataRole.UserRole + 1
    PearsonCorrRole = Qt.ItemDataRole.UserRole + 2
    SpearmanCorrRole = Qt.ItemDataRole.UserRole + 3
    PearsonPValueRole = Qt.ItemDataRole.UserRole + 4
    SpearmanPValueRole = Qt.ItemDataRole.UserRole + 5

    def __init__(
        self,
        featureSqlTableModel: FeatureSqlTableModel,
        parent: QObject = None,
        db: QSqlDatabase = None,
    ):
        super().__init__(parent)
        self._db = db
        self._featureSqlTableModel = featureSqlTableModel

        self._cacheValuePairsRole = {}

        self._cachePearsonCorrRole = {}
        self._cachePearsonPValueRole = {}

        self._cacheSpearmanCorrRole = {}
        self._cacheSpearmanPValueRole = {}

        self._settings = QSettings()
        self._correlationColormap = mpl.colormaps[
            self._settings.value("depTable/colormap", "coolwarm")
        ]

    def getFeatureSqlTableModel(self):
        return self._featureSqlTableModel

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return self._getFeaturesCount()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self._getFeaturesCount()

    def data(self, item: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.CheckStateRole:
            return (
                Qt.CheckState.Checked
                if self._getConnectionState(item)
                else Qt.CheckState.Unchecked
            )
        elif role == self.ValuePairsRole:
            firstFeatureId, secondFeatureId = self._indexToId(index=item)
            if (firstFeatureId, secondFeatureId) not in self._cacheValuePairsRole:
                self._cacheValuePairsRole[(firstFeatureId, secondFeatureId)] = (
                    self._getFeaturePairSamples(firstFeatureId, secondFeatureId)
                )
            return self._cacheValuePairsRole[(firstFeatureId, secondFeatureId)]
        elif role == self.PearsonCorrRole:
            firstFeatureId, secondFeatureId = self._indexToId(index=item)
            if (firstFeatureId, secondFeatureId) not in self._cachePearsonCorrRole:
                values_np = self.data(item=item, role=self.ValuePairsRole)
                nas = np.logical_or(np.isnan(values_np[0]), np.isnan(values_np[1]))
                try:
                    pearsonCorr = stats.pearsonr(values_np[0, ~nas], values_np[1, ~nas])
                    self._cachePearsonCorrRole[(firstFeatureId, secondFeatureId)] = (
                        pearsonCorr.correlation
                    )
                    self._cachePearsonPValueRole[(firstFeatureId, secondFeatureId)] = (
                        pearsonCorr.pvalue
                    )
                except ValueError:
                    self._cachePearsonCorrRole[(firstFeatureId, secondFeatureId)] = (
                        np.nan
                    )
            return self._cachePearsonCorrRole[(firstFeatureId, secondFeatureId)]
        elif role == self.PearsonPValueRole:
            firstFeatureId, secondFeatureId = self._indexToId(index=item)
            if (firstFeatureId, secondFeatureId) not in self._cachePearsonPValueRole:
                self.data(item=item, role=self.PearsonCorrRole)
            return self._cachePearsonPValueRole[(firstFeatureId, secondFeatureId)]
        elif role == self.SpearmanCorrRole:
            firstFeatureId, secondFeatureId = self._indexToId(index=item)
            if (firstFeatureId, secondFeatureId) not in self._cacheSpearmanCorrRole:
                values_np = self.data(item=item, role=self.ValuePairsRole)
                nas = np.logical_or(np.isnan(values_np[0]), np.isnan(values_np[1]))
                spearmanrCorr = stats.spearmanr(values_np[0, ~nas], values_np[1, ~nas])
                self._cacheSpearmanCorrRole[(firstFeatureId, secondFeatureId)] = (
                    spearmanrCorr.statistic
                )
                self._cacheSpearmanPValueRole[(firstFeatureId, secondFeatureId)] = (
                    spearmanrCorr.pvalue
                )
            return self._cacheSpearmanCorrRole[(firstFeatureId, secondFeatureId)]
        elif role == self.SpearmanPValueRole:
            firstFeatureId, secondFeatureId = self._indexToId(index=item)
            if (firstFeatureId, secondFeatureId) not in self._cacheSpearmanPValueRole:
                self.data(item=item, role=self.SpearmanCorrRole)
            return self._cacheSpearmanPValueRole[(firstFeatureId, secondFeatureId)]
        elif role == Qt.ItemDataRole.BackgroundRole:
            if item.column() == item.row():
                return None
            pearsonCorr = self.data(item=item, role=self.PearsonCorrRole)
            # colormap works with range [0,1], but correlation can be [-1,1]
            color = self._correlationColormap((pearsonCorr + 1) / 2, bytes=True)
            return QBrush(QColor(color[0], color[1], color[2], color[3]))
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.DisplayRole
    ):
        if role == Qt.ItemDataRole.DisplayRole:
            return
        elif role == Qt.ItemDataRole.CheckStateRole:
            if bool(value):
                self._setConnection(index)
            else:
                self._removeConnection(index)
        self.dataChanged.emit(index, index, role)
        return True

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return self._getFeatureName(section)
        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled

        return (
            Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsEditable
        )

    def roleNames(self) -> dict[int, QByteArray]:
        d = {}
        d[Qt.ItemDataRole.DisplayRole] = "display".encode()
        d[Qt.ItemDataRole.CheckStateRole] = "CheckState".encode()
        d[Qt.ItemDataRole.BackgroundRole] = "background".encode()

        d[self.ValuePairsRole] = "Values".encode()
        d[self.PearsonCorrRole] = "PearsonCorr".encode()
        d[self.SpearmanCorrRole] = "SpearmanCorr".encode()
        d[self.PearsonPValueRole] = "PearsonPValue".encode()
        d[self.SpearmanPValueRole] = "SpearmanPValue".encode()
        return d

    def setHeaderData(
        self,
        section: int,
        orientation: Qt.Orientation,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        pass

    def canFetchMore(self, parent: QModelIndex = QModelIndex()) -> bool:
        return False

    def fetchMore(self, parent: QModelIndex = QModelIndex()) -> None:
        return

    def insertColumns(
        self, column: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        raise NotImplementedError("insertColumns is not supported")

    def removeColumns(
        self, column: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        raise NotImplementedError("removeColumns is not supported")

    def _getConnectionState(self, index: QModelIndex):
        source_id, target_id = self._indexToId(index)
        query = QSqlQuery(
            f"SELECT COUNT(*) FROM {self.pairs_table_name} WHERE {self.column_source_feature_id} = {source_id} AND {self.column_target_feature_id} = {target_id};",
            self._db,
        )
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}"
            )
        query.next()
        return bool(query.value(0))

    def _setConnection(self, index: QModelIndex):
        source_id, target_id = self._indexToId(index)
        query = QSqlQuery(
            f"INSERT INTO {self.pairs_table_name}({self.column_source_feature_id}, {self.column_target_feature_id}) VALUES ({source_id}, {target_id}) ON CONFLICT DO NOTHING;",
            self._db,
        )
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}"
            )

    def _removeConnection(self, index: QModelIndex):
        source_id, target_id = self._indexToId(index)
        query = QSqlQuery(
            f"DELETE FROM {self.pairs_table_name} WHERE {self.column_source_feature_id} = {source_id} AND {self.column_target_feature_id} = {target_id};",
            self._db,
        )
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}"
            )

    def _indexToId(self, index: QModelIndex) -> tuple[int, int]:
        source_id = self._featureSqlTableModel.data(
            self._featureSqlTableModel.index(
                index.row(),
                self._featureSqlTableModel.fieldIndex(
                    self._featureSqlTableModel.column_id
                ),
            )
        )
        target_id = self._featureSqlTableModel.data(
            self._featureSqlTableModel.index(
                index.column(),
                self._featureSqlTableModel.fieldIndex(
                    self._featureSqlTableModel.column_id
                ),
            )
        )
        return (source_id, target_id)

    def _getFeaturesCount(self):
        query = QSqlQuery(f"SELECT COUNT(*) FROM {self.index_table_name};", self._db)
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}"
            )
        query.next()
        return query.value(0)

    def _getFeatureName(self, feature_index: int):
        v = self._featureSqlTableModel.data(
            self._featureSqlTableModel.index(
                feature_index,
                self._featureSqlTableModel.fieldIndex(
                    self._featureSqlTableModel.column_name
                ),
            )
        )
        return v

    def _getFeatureSamples(self, featureId: int) -> np.ndarray:
        query = QSqlQuery(
            f"select\
            s.{SampleSqlTableModel.column_sample_id} sampleId,\
            max(case when s.{SampleSqlTableModel.column_feature_id}={featureId} then s.{SampleSqlTableModel.column_value} end) feature\
            from {SampleSqlTableModel.table_name} as s\
            join {FeatureSqlTableModel.table_name} as f \
            on f.{FeatureSqlTableModel.column_id}=s.{SampleSqlTableModel.column_feature_id}\
            group by sampleId\
            order by sampleId\
            ",
            self._db,
        )
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}"
            )
        featureFieldNo = query.record().indexOf("feature")
        values = []
        while query.next():
            # sampleTdValue: int = query.value(sampleTdValueFieldNo)
            featureValue = query.value(featureFieldNo)
            if isinstance(featureValue, str):
                featureValue = float(featureValue) if len(featureValue) > 0 else np.nan
            elif isinstance(featureValue, float):
                featureValue = float(featureValue)
            else:
                raise RuntimeError(
                    f"Unexpected type for firstFeatureFieldNo({featureFieldNo}): {type(featureValue)}"
                )
            values.append(featureValue)
        return np.array(values)

    def _getFeaturePairSamples(
        self, firstFeatureId: int, secondFeatureId: int
    ) -> np.ndarray:
        if firstFeatureId == secondFeatureId:
            return np.tile(self._getFeatureSamples(firstFeatureId), (2, 1))

        query = QSqlQuery(
            f"select\
            s.{SampleSqlTableModel.column_sample_id} sampleId,\
            max(case when s.{SampleSqlTableModel.column_feature_id}={firstFeatureId} then s.{SampleSqlTableModel.column_value} end) firstFeature,\
            max(case when s.{SampleSqlTableModel.column_feature_id}={secondFeatureId} then s.{SampleSqlTableModel.column_value} end) secondFeature\
            from {SampleSqlTableModel.table_name} as s\
            join {FeatureSqlTableModel.table_name} as f \
            on f.{FeatureSqlTableModel.column_id}=s.{SampleSqlTableModel.column_feature_id}\
            group by sampleId\
            order by sampleId\
            ",
            self._db,
        )
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}"
            )
        # sampleTdValueFieldNo = query.record().indexOf(
        #     {SampleSqlTableModel.column_sample_id})
        firstFeatureFieldNo = query.record().indexOf("firstFeature")
        secondFeatureFieldNo = query.record().indexOf("secondFeature")

        values = []
        while query.next():
            # sampleTdValue: int = query.value(sampleTdValueFieldNo)
            firstFeatureValue = query.value(firstFeatureFieldNo)
            if isinstance(firstFeatureValue, str):
                firstFeatureValue = (
                    float(firstFeatureValue) if len(firstFeatureValue) > 0 else np.nan
                )
            elif isinstance(firstFeatureValue, float):
                firstFeatureValue = float(firstFeatureValue)
            else:
                raise RuntimeError(
                    f"Unexpected type for firstFeatureFieldNo({firstFeatureFieldNo}): {type(firstFeatureValue)}"
                )

            secondFeatureValue = query.value(secondFeatureFieldNo)
            if isinstance(secondFeatureValue, str):
                secondFeatureValue = (
                    float(secondFeatureValue) if len(secondFeatureValue) > 0 else np.nan
                )
            elif isinstance(secondFeatureValue, float):
                secondFeatureValue = float(secondFeatureValue)
            else:
                raise RuntimeError(
                    f"Unexpected type for secondFeatureFieldNo({secondFeatureFieldNo}): {type(secondFeatureValue)}"
                )
            values.append([firstFeatureValue, secondFeatureValue])
        return np.array(values).T


class FilterPairTableSQLProxyModel(QSortFilterProxyModel):
    filterInvalidated = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.booleanSet: dict[int, bool] = {}
        self._filterModel: PersistanceCheckableFeatureListProxyModel = None

    def filterModel(self) -> PersistanceCheckableFeatureListProxyModel:
        return self._filterModel

    def setFilterModel(
        self,
        filterModel: PersistanceCheckableFeatureListProxyModel,
        filterValueColumn: int,
    ):
        if self._filterModel is not None:
            self._filterModel.dataChanged.disconnect(self.invalidateCache)
        self._filterModel = filterModel
        self._filterValueColumn = filterValueColumn
        self._filterModel.dataChanged.connect(self.invalidateCache)
        self.invalidateCache()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ):
        index = self._filterModel.index(
            source_row, self.filterKeyColumn(), source_parent
        )
        return self._filter_cache.get(index.data(), False)

    def filterAcceptsColumn(
        self, source_column: int, source_parent: QModelIndex | QPersistentModelIndex
    ):
        index = self._filterModel.index(
            source_column, self.filterKeyColumn(), source_parent
        )
        return self._filter_cache.get(index.data(), False)

    @Slot(QModelIndex, QModelIndex, "QList<int>")
    def invalidateCache(
        self,
        topLeft: QModelIndex = None,
        bottomRight: QModelIndex = None,
        roles: list[int] = None,
    ):
        self._filter_cache = {}
        for rowIdx in range(self._filterModel.rowCount()):
            k = self._filterModel.data(
                self._filterModel.index(rowIdx, self._filterValueColumn)
            )
            v = self._filterModel.data(
                self._filterModel.index(rowIdx, self._filterValueColumn),
                role=Qt.ItemDataRole.CheckStateRole,
            )
            self._filter_cache[k] = v == Qt.CheckState.Checked
        self.invalidateFilter()
        self.filterInvalidated.emit()


class CorrelationSQLProxyModel(QIdentityProxyModel):
    partialCorrGeneralError = Signal()
    PartialCorrRole = Qt.ItemDataRole.UserRole + 10
    PartialPValueRole = Qt.ItemDataRole.UserRole + 11

    def __init__(
        self, sourceModel: FilterPairTableSQLProxyModel, parent: QObject = None
    ):
        super().__init__(parent)
        self._partial_corr_matrix = None
        self._partial_corr_pvalue_matrix = None
        self.sourceModelChanged.connect(self._sourceModelChangedHandler)
        self.setSourceModel(sourceModel)

    def data(self, item: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            spearmanCorr = self.data(
                item=item, role=PairTableSQLProxyModel.SpearmanCorrRole
            )
            partialCorr = self.data(item=item, role=self.PartialCorrRole)
            return f"{spearmanCorr:.2F} / {partialCorr:.2F}"
        elif role == self.PartialCorrRole:
            return self._partialPartialCorrelationMatrix()[item.row(), item.column()]
        elif role == self.PartialPValueRole:
            return self._partialPartialCorrelationPvalueMatrix()[
                item.row(), item.column()
            ]
        else:
            return super().data(item, role)

    @Slot()
    def _sourceModelChangedHandler(self):
        # self.sourceModel().dataChanged.connect(self._invalidatePartialCorrelationMatrix)
        self.sourceModel().filterInvalidated.connect(
            self._invalidatePartialCorrelationMatrix
        )

    def _invalidatePartialCorrelationMatrix(self):
        """Invalidate the cached partial correlation matrix."""
        self._partial_corr_matrix = None
        self._partial_corr_pvalue_matrix = None

    def _partialPartialCorrelationMatrix(self) -> np.ndarray:
        """Returns the cached partial correlation matrix. If it is not cached, it will be evaluated and cached.

        Returns:
            np.ndarray: Partial correlation matrix
        """
        if self._partial_corr_matrix is None:
            self._partial_corr_matrix, self._partial_corr_pvalue_matrix = (
                self._evaluatePartialCorrelationMatrix()
            )
        return self._partial_corr_matrix

    def _partialPartialCorrelationPvalueMatrix(self) -> np.ndarray:
        if self._partial_corr_pvalue_matrix is None:
            self._partial_corr_matrix, self._partial_corr_pvalue_matrix = (
                self._evaluatePartialCorrelationMatrix()
            )
        return self._partial_corr_pvalue_matrix

    def _evaluatePartialCorrelationMatrix(self) -> tuple[np.ndarray, np.ndarray]:
        """Evaluate the partial correlation matrix.

        Returns:
            np.ndarray: Partial correlation matrix.
        """
        featuresCount = self.columnCount()
        if featuresCount <= 1:
            return np.array([[]])

        data_pd = pd.DataFrame(
            columns=[
                self.headerData(c, Qt.Orientation.Horizontal)
                for c in range(featuresCount)
            ]
        )

        d = {}
        for r in range(featuresCount):
            data_np = self.data(
                self.index(r, r), role=PairTableSQLProxyModel.ValuePairsRole
            )
            d[r] = data_np[0]
        df = pd.DataFrame(d)

        pcorrMatrix = np.eye(featuresCount, dtype=float)
        pvalMatrix = np.eye(featuresCount, dtype=float)

        hasNan = False
        for i in range(featuresCount):
            for j in range(i + 1, featuresCount):
                covar_features = list(range(featuresCount))
                covar_features.remove(i)
                covar_features.remove(j)
                try:
                    pcorr_df = df.partial_corr(x=i, y=j, covar=covar_features)
                    pcorrMatrix[i, j] = pcorrMatrix[j, i] = pcorr_df["r"].iloc[0]
                    pvalMatrix[i, j] = pvalMatrix[j, i] = pcorr_df["p-val"].iloc[0]
                except AssertionError:
                    pcorrMatrix[i, j] = pcorrMatrix[j, i] = np.nan
                    pvalMatrix[i, j] = pvalMatrix[j, i] = np.nan
                    hasNan = True

        if hasNan and np.isnan(pvalMatrix).sum() == (featuresCount**2 - featuresCount):
            try:
                self.partialCorrGeneralError.emit()
                pcorrMatrix = df.pcorr().to_numpy()
                pvalMatrix = np.full((featuresCount, featuresCount), np.nan)
            except np.linalg.LinAlgError as e:
                # self.partialCorrGeneralError.emit()
                pcorrMatrix = np.full((featuresCount, featuresCount), np.nan)
                pvalMatrix = np.full((featuresCount, featuresCount), np.nan)
        return pcorrMatrix, pvalMatrix
