"""Styling layer for the pair-correlation table.

``PairTableStyledProxyModel`` wraps a :class:`PairTableSQLProxyModel` and
paints the ``BackgroundRole`` of each cell with a matplotlib colormap driven
by the Pearson correlation stored on the source model (see
``depTable/colormap`` in :class:`~bn_modeller.utils.settings_service.SettingsService`).
Keeping this layer separate lets the data model stay reusable without
matplotlib or the settings service.
"""

import matplotlib as mpl
import pandas as pd
from PySide6.QtCore import (
    QByteArray,
    QIdentityProxyModel,
    QObject,
    Qt,
    Slot,
)
from PySide6.QtGui import QBrush, QColor

from bn_modeller.models.dependency_sqltable_model import PairTableSQLProxyModel
from bn_modeller.utils.settings_service import SettingsService


class PairTableStyledProxyModel(QIdentityProxyModel):
    colormapSettingKey = "depTable/colormap"
    defaultColormapName = "coolwarm"

    def __init__(self, sourceModel: PairTableSQLProxyModel, parent: QObject = None):
        super().__init__(parent)
        self.setSourceModel(sourceModel)
        self._settings = SettingsService.instance()
        self._correlationColormap = self._resolveColormap(
            self._settings.get_value(self.colormapSettingKey, value_type=str)
        )
        self._settings.settingChanged.connect(self._onSettingChanged)

    def _resolveColormap(self, name):
        """Resolve a colormap name, falling back to the default when invalid.

        Args:
            name (str): Matplotlib colormap name from user-editable settings.

        Returns:
            matplotlib.colors.Colormap: Resolved colormap object.
        """
        try:
            return mpl.colormaps[name]
        except (KeyError, TypeError, ValueError):
            return mpl.colormaps[self.defaultColormapName]

    @Slot(str, object)
    def _onSettingChanged(self, key: str, value):
        """Refresh the correlation colormap when its setting changes.

        Args:
            key (str): Changed settings key.
            value (Any): New stored value for the key.
        """
        if key != self.colormapSettingKey:
            return
        self._correlationColormap = self._resolveColormap(value)
        row_count = self.rowCount()
        column_count = self.columnCount()
        if row_count > 0 and column_count > 0:
            self.dataChanged.emit(
                self.index(0, 0), self.index(row_count - 1, column_count - 1)
            )

    def getFeatureSqlTableModel(self):
        return self.sourceModel().getFeatureSqlTableModel()

    def getSamplesDataFrame(self) -> pd.DataFrame:
        return self.sourceModel().getSamplesDataFrame()

    def data(self, item, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.BackgroundRole:
            if item.column() == item.row():
                return None
            pearsonCorr = self.sourceModel().data(
                item, role=PairTableSQLProxyModel.PearsonCorrRole
            )
            # colormap works with range [0,1], but correlation can be [-1,1]
            color = self._correlationColormap((pearsonCorr + 1) / 2, bytes=True)
            return QBrush(QColor(color[0], color[1], color[2], color[3]))
        return super().data(item, role)

    def roleNames(self) -> dict[int, QByteArray]:
        d = super().roleNames()
        d[Qt.ItemDataRole.BackgroundRole] = "background".encode()
        return d
