from PySide6.QtCore import (
    QIdentityProxyModel,
    QModelIndex,
    QObject,
    QSortFilterProxyModel,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtSql import (
    QSqlDatabase,
    QSqlQuery,
    QSqlRelation,
    QSqlRelationalTableModel,
)


class FeatureSqlTableModel(QSqlRelationalTableModel):
    table_name = "feature"
    column_id = "id"
    column_name = "name"
    column_description = "description"
    column_is_active = "is_active"

    def __init__(self, parent: QObject = None, db: QSqlDatabase = None):
        super().__init__(parent, db)

        query = QSqlQuery(
            f"CREATE TABLE IF NOT EXISTS {FeatureSqlTableModel.table_name} (\
                          {FeatureSqlTableModel.column_id} INTEGER PRIMARY KEY AUTOINCREMENT, \
                          {FeatureSqlTableModel.column_name} TEXT, \
                          {FeatureSqlTableModel.column_description} TEXT, \
                          {FeatureSqlTableModel.column_is_active} INTEGER\
                          );\
                          "
        )

        if not query.exec():
            raise RuntimeError(f"Unable to connect to DB: {query.lastError()}")
        self.setTable(FeatureSqlTableModel.table_name)

    def setData(
        self, index: QModelIndex, value, role: int = Qt.ItemDataRole.DisplayRole
    ):
        if not index.isValid():
            return False
        if index.column() == self.fieldIndex(self.column_is_active):
            if self._setIsActiveSql(index, bool(value)):
                self.submitAll()
                self.select()
                self.dataChanged.emit(index, index, [role])
                return True
            else:
                return False
        else:
            return super().setData(index, value, role)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        if index.column() == self.fieldIndex(self.column_is_active):
            return (
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsEditable
            )
        else:
            return super().flags(index)

    def _setIsActiveSql(self, index: QModelIndex, value: bool):
        query = QSqlQuery()
        query.prepare(
            f"UPDATE {self.table_name} SET {self.column_is_active} = ? where {self.column_id} = ?"
        )
        query.addBindValue(value)
        query.addBindValue(
            index.siblingAtColumn(self.fieldIndex(self.column_id)).data()
        )
        return query.exec()


class PersistanceCheckableFeatureListProxyModel(QIdentityProxyModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def setSourceModel(self, sourceModel: FeatureSqlTableModel):
        return super().setSourceModel(sourceModel)

    def sourceModel(self) -> FeatureSqlTableModel:
        return super().sourceModel()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        sourceIndex: QModelIndex = self.mapToSource(index)
        if role == Qt.ItemDataRole.CheckStateRole:
            is_checked = sourceIndex.siblingAtColumn(
                self.sourceModel().fieldIndex(self.sourceModel().column_is_active)
            ).data()
            return Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked
        return super().data(index, role)

    def setData(
        self, index: QModelIndex, value, role: int = Qt.ItemDataRole.DisplayRole
    ):
        sourceIndex: QModelIndex = self.mapToSource(index)
        if role == Qt.ItemDataRole.CheckStateRole:
            flagIndex = sourceIndex.siblingAtColumn(
                self.sourceModel().fieldIndex(self.sourceModel().column_is_active)
            )
            if super().setData(flagIndex, bool(value)):
                self.dataChanged.emit(index, index, [role])
                return True
            else:
                return False
        else:
            return super().setData(sourceIndex, value, role)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return (
            Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | super().flags(self.mapToSource(index)) & ~Qt.ItemFlag.ItemIsEditable
        )
