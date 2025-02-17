from PySide6.QtCore import (
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
    Slot,
)

from bn_modeller.models.checkable_sort_filter_proxy_model import (
    CheckableSortFilterProxyModel,
)


class RelationalSortFilterProxyModel(QSortFilterProxyModel):
    filterInvalidated = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._filterModel: CheckableSortFilterProxyModel = None
        self._filterValueColumn: int = None
        self._filter_cache: dict

    def filterModel(self) -> CheckableSortFilterProxyModel:
        return self._filterModel

    def filterValueColumn(self) -> int:
        return self._filterValueColumn

    def setFilterModel(
        self, filterModel: CheckableSortFilterProxyModel, filterValueColumn: int
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
        index = self.sourceModel().index(
            source_row, self.filterKeyColumn(), source_parent
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
