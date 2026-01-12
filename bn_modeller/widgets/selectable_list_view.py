from PySide6.QtCore import QAbstractItemModel, Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QListView, QMenu, QWidget

from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.widgets.all_samples_view import AllSamplesView


class SelectableListView(QListView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.setSelectionRectVisible(True)
        self.initContextMenu()

    def initContextMenu(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self.menu = QMenu(self)

        selectBySelection = QAction(self.tr("Select"), self)
        selectBySelection.triggered.connect(self.setCheckStateBySelection)
        self.menu.addAction(selectBySelection)

        unselectBySelection = QAction(self.tr("Unselect"), self)
        unselectBySelection.triggered.connect(self.removeCheckStateBySelection)
        self.menu.addAction(unselectBySelection)

        self.menu.addSeparator()

        selectAllAction = QAction(self.tr("Select All"), self)
        selectAllAction.triggered.connect(self.setCheckStateAll)
        self.menu.addAction(selectAllAction)

        unselectAllAction = QAction(self.tr("Unselect All"), self)
        unselectAllAction.triggered.connect(self.removeCheckStateAll)
        self.menu.addAction(unselectAllAction)

    @Slot()
    def showContextMenu(self, pos):
        self.menu.popup(self.mapToGlobal(pos))

    @Slot()
    def setCheckStateBySelection(self):
        source = self.sender()
        self._setCheckStateForSelectionBySender(source, True)

    @Slot()
    def removeCheckStateBySelection(self):
        source = self.sender()
        self._setCheckStateForSelectionBySender(source, False)

    @Slot()
    def setCheckStateAll(self):
        source = self.sender()
        self._setAllCheckStateBySender(source, True)

    @Slot()
    def removeCheckStateAll(self):
        source = self.sender()
        self._setAllCheckStateBySender(source, False)

    def _setAllCheckStateBySender(self, source, checkState: bool):
        if isinstance(source, QAction):
            for r in range(self.model().rowCount()):
                self.model().setData(
                    self.model().index(r, 0),
                    checkState,
                    role=Qt.ItemDataRole.CheckStateRole,
                )

    def _setCheckStateForSelectionBySender(self, source, checkState: bool):
        if isinstance(source, QAction):
            for index in self.selectedIndexes():
                self.model().setData(
                    index,
                    checkState,
                    role=Qt.ItemDataRole.CheckStateRole,
                )
