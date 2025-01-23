from bn_modeller.models.checkable_sort_filter_proxy_model import CheckableSortFilterProxyModel
from bn_modeller.models import RelationalSortFilterProxyModel

from PySide6.QtCore import Qt, QObject, QModelIndex, QPersistentModelIndex, Signal, Slot, QAbstractItemModel
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout


from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import numpy as np
matplotlib.use('Qt5Agg')

class PairplotMplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class PairplotView(QFrame):
    def __init__(self, parent: QWidget = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._model: RelationalSortFilterProxyModel = None
        self.mplCanvas = None
        self.init_ui()

    def init_ui(self):
        self.mainLayout = QVBoxLayout()

        # self.mplCanvas = PairplotMplCanvas(self)

        self.setLayout(self.mainLayout)

    def setModel(self, model: RelationalSortFilterProxyModel, hue_names_col: int, sample_id_col: int, hue_id_col: int, value_col: int):
        if self._model is not None:
            # TODO: replace with builtin Qt Signal
            self._model.filterInvalidated.disconnect(self.updateVisualization)
        self._model = model
        self._model.filterInvalidated.connect(self.updateVisualization)
        
        self._value_col = value_col
        self._sample_id_col = sample_id_col
        self._hue_id_col = hue_id_col
        self._hue_names_col = hue_names_col


    # @Slot("QList<QPersistentModelIndex>", QAbstractItemModel.LayoutChangeHint)
    # def updateVisualization(self, parents: list[QPersistentModelIndex] = [],
    #                         hint: QAbstractItemModel.LayoutChangeHint = QAbstractItemModel.LayoutChangeHint.NoLayoutChangeHint):

    # @Slot(QModelIndex, QModelIndex, "QList<int>")
    # def updateVisualization(self, topLeft: QModelIndex = None, bottomRight: QModelIndex = None, roles: list[int] = None):

    @Slot()
    def updateVisualization(self):
        filterModel = self._model.filterModel()
        filter_labels = {}
        for rowIdx in range(filterModel.rowCount()):
            k = filterModel.data(
                filterModel.index(rowIdx, self._model.filterValueColumn()))
            v = filterModel.data(filterModel.index(
                rowIdx, self._hue_names_col))
            filter_labels[k] = v

        data_dict = {"sample": [],
                     "value": [],
                     "label": []}
        for rowIdx in range(self._model.rowCount()):
            data_dict["sample"].append(self._model.data(
                self._model.index(rowIdx, self._sample_id_col)))
            data_dict["label"].append(filter_labels[self._model.data(
                self._model.index(rowIdx, self._hue_id_col))])
            data_dict["value"].append(self._model.data(
                self._model.index(rowIdx, self._value_col)))
        data_pd = pd.DataFrame.from_dict(data_dict)
        data_pd = data_pd.pivot(
            index="sample", columns="label", values="value")

        if len(data_pd) == 0:
            return

        # Создаем графики
        labels = data_pd.columns
        num_vars = len(labels)
        fig, axes = plt.subplots(num_vars, num_vars, figsize=(12, 12))

        # Проверяем, является ли axes двумерным массивом или одиночным объектом
        for i in range(num_vars):
            for j in range(num_vars):
                ax = axes[i, j] if isinstance(axes, np.ndarray) else axes

                if i == j:
                    ax.hist(data_pd.iloc[:, i], bins=20, color='lightgray')
                    # ax.set_title(labels[i])
                else:
                    ax.scatter(data_pd.iloc[:, j], data_pd.iloc[:, i], alpha=0.6)
                    ax.set_xlabel(labels[j])
                    ax.set_ylabel(labels[i])

                    # Добавление корреляции
                    df1 = data_pd.iloc[:, i]
                    df2 = data_pd.iloc[:, j]

                    df1_cleaned, df2_cleaned = df1.dropna(), df2.dropna()

                    # Убираем те строки, в которых один из столбцов имеет NaN
                    df1_cleaned, df2_cleaned = df1_cleaned.align(df2_cleaned, join='inner')

                    corr = np.corrcoef(df1_cleaned, df2_cleaned)[0, 1]
                    ax.annotate(f'Corr: {corr:.2f}', xy=(0.5, 0.9), xycoords='axes fraction', ha='center', fontsize=10,
                                color='red')

        plt.tight_layout(pad=3.0)
        fig.subplots_adjust(hspace=0.3, wspace=0.3)

        newMplCanvas = FigureCanvasQTAgg(fig)

        # Добавляем панель инструментов
        toolbar = NavigationToolbar2QT(newMplCanvas, self)

        if hasattr(self, 'toolbar'):
            self.mainLayout.replaceWidget(self.toolbar, toolbar)
        else:
            self.toolbar = toolbar
            self.mainLayout.addWidget(self.toolbar)

        if self.mplCanvas is not None:
            self.mainLayout.replaceWidget(self.mplCanvas, newMplCanvas)
            del self.mplCanvas
        self.mplCanvas = newMplCanvas
        self.mainLayout.addWidget(self.mplCanvas)




