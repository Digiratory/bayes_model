from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QSortFilterProxyModel,
    Qt,
    Signal,
    Slot,
)


class BayesianInferenceModel(QAbstractItemModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: Qt.ItemDataRole = Qt.ItemDataRole,
    ):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return f"Column {section}"
            elif orientation == Qt.Vertical:
                return f"Row {section}"
        return super().headerData(section, orientation, role)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return 10
        return 5

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return None
        return 2

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.ItemDataRole):
        if not index.isValid():
            return None
        row = index.row()
        column = index.column()
        if role == Qt.DisplayRole:
            return f"Row {row}, Column {column}"
        return super().data(index, role)


class BayesianInferenceIOOnlyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
