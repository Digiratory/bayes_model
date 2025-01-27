from typing import Any
from PySide6.QtSql import QSqlRelationalTableModel, QSqlDatabase, QSqlQuery
from PySide6.QtCore import Qt, QObject, QModelIndex, QPersistentModelIndex, QByteArray, QAbstractTableModel, QSortFilterProxyModel, Signal, Slot

from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.feature_sqltable_model import PersistanceCheckableFeatureListProxyModel


class DependencyManyToManySqlTableModel(QSqlRelationalTableModel):
    table_name = "feature_dependency"
    column_source_feature_id = "source_feature_id"
    column_target_feature_id = "target_feature_id"

    def __init__(self, parent: QObject = None, db: QSqlDatabase = None):
        super().__init__(parent, db)

        query = QSqlQuery(f"CREATE TABLE IF NOT EXISTS {DependencyManyToManySqlTableModel.table_name} (\
                          {DependencyManyToManySqlTableModel.column_source_feature_id} INTEGER NOT NULL, \
                          {DependencyManyToManySqlTableModel.column_target_feature_id} INTEGER NOT NULL, \
                          PRIMARY KEY ({DependencyManyToManySqlTableModel.column_source_feature_id}, {DependencyManyToManySqlTableModel.column_target_feature_id}), \
                          FOREIGN KEY({DependencyManyToManySqlTableModel.column_source_feature_id}) REFERENCES {FeatureSqlTableModel.table_name}({FeatureSqlTableModel.column_id})\
                          FOREIGN KEY({DependencyManyToManySqlTableModel.column_target_feature_id}) REFERENCES {FeatureSqlTableModel.table_name}({FeatureSqlTableModel.column_id})\
                          );\
                          ")

        if not query.exec():
            raise RuntimeError(f"Unable to connect to DB: {query.lastError()}")
        self.setTable(DependencyManyToManySqlTableModel.table_name)


class PairTableSQLProxyModel(QAbstractTableModel):
    pairs_table_name = DependencyManyToManySqlTableModel.table_name

    index_tbl_cls = FeatureSqlTableModel
    index_table_name = index_tbl_cls.table_name

    column_source_feature_id = DependencyManyToManySqlTableModel.column_source_feature_id
    column_target_feature_id = DependencyManyToManySqlTableModel.column_target_feature_id

    def __init__(self, featureSqlTableModel: FeatureSqlTableModel, parent: QObject = None, db: QSqlDatabase = None):
        super().__init__(parent)
        self._db = db
        self._featureSqlTableModel = featureSqlTableModel

    def getFeatureSqlTableModel(self):
        return self._featureSqlTableModel

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return self._getFeaturesCount()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self._getFeaturesCount()

    def data(self, item: QModelIndex,  role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return
        elif role == Qt.ItemDataRole.CheckStateRole:
            return Qt.CheckState.Checked if self._getConnectionState(item) else Qt.CheckState.Unchecked
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return
        elif role == Qt.ItemDataRole.CheckStateRole:
            if bool(value):
                self._setConnection(index)
            else:
                self._removeConnection(index)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return self._getFeatureName(section)
        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled

        return (Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                & ~Qt.ItemFlag.ItemIsEditable)

    # def roleNames(self) -> dict[int, QByteArray]:
    #     pass

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        pass

    def canFetchMore(self, parent: QModelIndex = QModelIndex()) -> bool:
        return False

    def fetchMore(self, parent: QModelIndex = QModelIndex()) -> None:
        return

    def insertColumns(self, column: int, count: int,  parent: QModelIndex = QModelIndex()) -> bool:
        raise NotImplementedError("insertColumns is not supported")

    def removeColumns(self, column: int, count: int,  parent: QModelIndex = QModelIndex()) -> bool:
        raise NotImplementedError("removeColumns is not supported")

    def _getConnectionState(self,  index: QModelIndex):
        source_id, target_id = self._indexToId(index)
        query = QSqlQuery(
            f"SELECT COUNT(*) FROM {self.pairs_table_name} WHERE {self.column_source_feature_id} = {source_id} AND {self.column_target_feature_id} = {target_id};", self._db)
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}")
        query.next()
        return bool(query.value(0))

    def _setConnection(self,  index: QModelIndex):
        source_id, target_id = self._indexToId(index)
        query = QSqlQuery(
            f"INSERT INTO {self.pairs_table_name}({self.column_source_feature_id}, {self.column_target_feature_id}) VALUES ({source_id}, {target_id}) ON CONFLICT DO NOTHING;", self._db)
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}")

    def _removeConnection(self,  index: QModelIndex):
        source_id, target_id = self._indexToId(index)
        query = QSqlQuery(
            f"DELETE FROM {self.pairs_table_name} WHERE {self.column_source_feature_id} = {source_id} AND {self.column_target_feature_id} = {target_id};", self._db)
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}")

    def _indexToId(self, index: QModelIndex):
        source_id = self._featureSqlTableModel.data(
            self._featureSqlTableModel.index(index.row(),
                                             self._featureSqlTableModel.fieldIndex(
                                                 self._featureSqlTableModel.column_id)
                                             ))
        target_id = self._featureSqlTableModel.data(
            self._featureSqlTableModel.index(index.column(),
                                             self._featureSqlTableModel.fieldIndex(
                                                 self._featureSqlTableModel.column_id)
                                             ))
        return (source_id, target_id)

    def _getFeaturesCount(self):
        query = QSqlQuery(
            f"SELECT COUNT(*) FROM {self.index_table_name};", self._db)
        if not query.exec():
            raise RuntimeError(
                f"Unable to retrieve row count from DB: {query.lastError()}")
        query.next()
        return query.value(0)

    def _getFeatureName(self, feature_index: int):
        v = self._featureSqlTableModel.data(
            self._featureSqlTableModel.index(feature_index,
                                             self._featureSqlTableModel.fieldIndex(
                                                 self._featureSqlTableModel.column_name)
                                             ))
        return v


class FilterPairTableSQLProxyModel(QSortFilterProxyModel):
    filterInvalidated = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.booleanSet: dict[int, bool] = {}
        self._filterModel: PersistanceCheckableFeatureListProxyModel = None

    def filterModel(self) -> PersistanceCheckableFeatureListProxyModel:
        return self._filterModel

    def setFilterModel(self,
                       filterModel: PersistanceCheckableFeatureListProxyModel,
                       filterValueColumn: int):
        if self._filterModel is not None:
            self._filterModel.dataChanged.disconnect(self.invalidateCache)
        self._filterModel = filterModel
        self._filterValueColumn = filterValueColumn
        self._filterModel.dataChanged.connect(self.invalidateCache)
        self.invalidateCache()

    def filterAcceptsRow(self,
                         source_row: int,
                         source_parent: QModelIndex | QPersistentModelIndex):
        index = self._filterModel.index(source_row, self.filterKeyColumn(), source_parent)
        return self._filter_cache.get(index.data(), False)

    def filterAcceptsColumn(self,
                            source_column: int,
                            source_parent: QModelIndex | QPersistentModelIndex):
        index = self._filterModel.index(source_column, self.filterKeyColumn(), source_parent)
        return self._filter_cache.get(index.data(), False)

    @Slot(QModelIndex, QModelIndex, "QList<int>")
    def invalidateCache(self, topLeft: QModelIndex = None, bottomRight: QModelIndex = None, roles: list[int] = None):
        self._filter_cache = {}
        for rowIdx in range(self._filterModel.rowCount()):
            k = self._filterModel.data(
                self._filterModel.index(rowIdx, self._filterValueColumn))
            v = self._filterModel.data(self._filterModel.index(
                rowIdx, self._filterValueColumn), role=Qt.ItemDataRole.CheckStateRole)
            self._filter_cache[k] = (v == Qt.CheckState.Checked)
        self.invalidateFilter()
        self.filterInvalidated.emit()
