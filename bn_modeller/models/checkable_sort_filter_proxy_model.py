from PySide6.QtCore import (
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)


class CheckableSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.booleanSet: dict[int, bool] = {}

    def mapFromSource(self, sourceIndex: QModelIndex | QPersistentModelIndex):
        if sourceIndex.isValid():
            return self.createIndex(sourceIndex.row(), sourceIndex.column())
        else:
            return super().mapFromSource(sourceIndex)

    def mapToSource(self, proxyIndex: QModelIndex | QPersistentModelIndex):
        if proxyIndex.isValid():
            return self.createIndex(proxyIndex.row(), proxyIndex.column())
        else:
            return super().mapToSource(proxyIndex)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() == -1:
            return None

        if role == Qt.ItemDataRole.CheckStateRole:
            return (
                Qt.CheckState.Checked
                if self.booleanSet.get(index.row(), False)
                else Qt.CheckState.Unchecked
            )
        elif role == Qt.ItemDataRole.DisplayRole:
            i = self.mapToSource(index)
            r = super().data(self.mapToSource(index), role)
            return r
        else:
            super().data(self.mapToSource(index), role)
        return super().data(index, role)

    def setData(
        self, index: QModelIndex, value, role: int = Qt.ItemDataRole.DisplayRole
    ):
        if role == Qt.ItemDataRole.CheckStateRole:
            self.booleanSet[index.row()] = bool(value)
            self.dataChanged.emit(index, index, [role])
            return True
        else:
            return super().setData(self.mapToSource(index), value, role)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled

        return (
            Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | super().flags(self.mapToSource(index)) & ~Qt.ItemFlag.ItemIsEditable
        )

    def setSourceModel(self, sourceModel):
        self.booleanSet = {i: False for i in range(sourceModel.rowCount())}
        return super().setSourceModel(sourceModel)
