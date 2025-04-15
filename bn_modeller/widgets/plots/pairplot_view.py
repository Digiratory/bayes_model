import matplotlib
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget
from scipy import stats

from bn_modeller.models import RelationalSortFilterProxyModel
from bn_modeller.models.checkable_sort_filter_proxy_model import (
    CheckableSortFilterProxyModel,
)

matplotlib.use("Qt5Agg")


class PairplotMplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=12, height=12, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.axes = None

    def update_plot(self, data_pd):
        if len(data_pd) == 0:
            return

        labels = data_pd.columns
        num_vars = len(labels)

        self.fig.clear()

        # Create new subplots
        if num_vars == 1:
            self.axes = self.fig.add_subplot(111)
        else:
            self.axes = self.fig.subplots(num_vars, num_vars)

        for i in range(num_vars):
            for j in range(num_vars):
                if num_vars == 1:
                    ax = self.axes
                else:
                    ax = self.axes[i, j]

                if i == j:
                    ax.hist(data_pd.iloc[:, i])
                    if j == 0:
                        ax.set_ylabel(labels[i])
                    if i == num_vars - 1:
                        ax.set_xlabel(labels[j])
                else:
                    ax.scatter(data_pd.iloc[:, j], data_pd.iloc[:, i], alpha=0.6)
                    ax.set_xlabel("" if i != num_vars - 1 else labels[j])
                    ax.set_ylabel("" if j != 0 else labels[i])

                    # Add correlation
                    df1, df2 = data_pd.iloc[:, i], data_pd.iloc[:, j]
                    # df1_cleaned, df2_cleaned = df1.align(df2, join='inner')
                    df1_cleaned, df2_cleaned = df1.dropna(), df2.dropna()

                    # Убираем те строки, в которых один из столбцов имеет NaN
                    df1_cleaned, df2_cleaned = df1_cleaned.align(
                        df2_cleaned, join="inner"
                    )

                    corr = stats.spearmanr(df1_cleaned, df2_cleaned).statistic
                    ax.annotate(
                        f"{corr:.2f}",
                        xy=(0.5, 0.9),
                        xycoords="axes fraction",
                        ha="center",
                        fontsize=10,
                        color="red",
                    )

        self.fig.tight_layout(pad=3.0)
        self.fig.subplots_adjust(hspace=0.3, wspace=0.3)
        self.draw()


class PairplotView(QFrame):
    def __init__(self, parent: QWidget = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._model: RelationalSortFilterProxyModel = None
        self.init_ui()

    def init_ui(self):
        self.mainLayout = QVBoxLayout()
        self.mplCanvas = PairplotMplCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.mplCanvas, self)
        self.mainLayout.addWidget(self.toolbar)
        self.mainLayout.addWidget(self.mplCanvas)
        self.setLayout(self.mainLayout)

    def setModel(
        self,
        model: RelationalSortFilterProxyModel,
        hue_names_col: int,
        sample_id_col: int,
        hue_id_col: int,
        value_col: int,
    ):
        if self._model is not None:
            self._model.filterInvalidated.disconnect(self.updateVisualization)
        self._model = model
        self._model.filterInvalidated.connect(self.updateVisualization)

        self._value_col = value_col
        self._sample_id_col = sample_id_col
        self._hue_id_col = hue_id_col
        self._hue_names_col = hue_names_col

    @Slot()
    def updateVisualization(self):
        filterModel = self._model.filterModel()
        filter_labels = {
            filterModel.data(
                filterModel.index(rowIdx, self._model.filterValueColumn())
            ): filterModel.data(filterModel.index(rowIdx, self._hue_names_col))
            for rowIdx in range(filterModel.rowCount())
        }

        data_dict = {"sample": [], "value": [], "label": []}
        for rowIdx in range(self._model.rowCount()):
            data_dict["sample"].append(
                self._model.data(self._model.index(rowIdx, self._sample_id_col))
            )
            data_dict["label"].append(
                filter_labels[
                    self._model.data(self._model.index(rowIdx, self._hue_id_col))
                ]
            )
            data_dict["value"].append(
                self._model.data(self._model.index(rowIdx, self._value_col))
            )

        data_pd = pd.DataFrame.from_dict(data_dict).pivot(
            index="sample", columns="label", values="value"
        )

        if len(data_pd) == 0:
            return

        filtered_order = [
            col for col in filter_labels.values() if col in data_pd.columns
        ]
        data_pd = data_pd[filtered_order]

        self.mplCanvas.update_plot(data_pd)
