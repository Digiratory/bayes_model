from PySide6.QtCore import QAbstractItemModel, Qt, Signal, Slot
from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QListView, QWidget

from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.widgets.all_samples_view import AllSamplesView


class SelectableListView(QListView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.setSelectionRectVisible(True)
