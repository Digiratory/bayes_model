from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import pingouin as pg
import numpy as np


# class CorrMatrix(QtWidgets.QMainWindow):
#     def __init__(self, parent=None, input_df=None):
#         super(CorrMatrix, self).__init__(parent)
#         self.input_df = input_df
#         self.corr = self.input_df.corr(method='spearman').round(1)
#
#         self.main_widget = QtWidgets.QWidget(self)
#         self.resize(2000, 1000)
#
#         self.fig = self.seabornplot()
#         self.canvas = FigureCanvas(self.fig)
#
#         self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
#                       QtWidgets.QSizePolicy.Expanding)
#         self.canvas.updateGeometry()
#         self.label = QtWidgets.QLabel("A plot:")
#         toolbar = NavigationToolbar(self.canvas, self)
#
#         self.layout = QtWidgets.QGridLayout(self.main_widget)
#         self.layout.addWidget(toolbar)
#         self.layout.addWidget(self.label)
#         self.layout.addWidget(self.canvas)
#
#         self.setCentralWidget(self.main_widget)
#         self.show()


class CorrMatrix(QtWidgets.QMainWindow):
    def __init__(self, parent=None, input_df=None):
        super(CorrMatrix, self).__init__(parent)
        self.input_df = input_df
        self.corr = self.input_df.corr(method='spearman').round(1)

        self.main_widget = QtWidgets.QWidget(self)
        self.resize(2000, 1000)

        self.fig = self.seabornplot()
        self.canvas = FigureCanvas(self.fig)

        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                      QtWidgets.QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.label = QtWidgets.QLabel("A plot:")
        toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtWidgets.QGridLayout(self.main_widget)
        self.layout.addWidget(toolbar)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self.main_widget)
        self.show()


class PartCorrMatrix(QtWidgets.QMainWindow):
    def __init__(self, parent=None, input_df=None):
        super(PartCorrMatrix, self).__init__(parent)
        self.input_df = input_df
        print(self.input_df.info())
        self.corr = self.find_part_cor(self.input_df)
        self.corr = self.corr.astype('float')
        print(self.corr)

        self.main_widget = QtWidgets.QWidget(self)
        self.resize(2000, 1000)

        self.fig = self.seabornplot()
        self.canvas = FigureCanvas(self.fig)

        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.label = QtWidgets.QLabel("A plot:")
        toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtWidgets.QGridLayout(self.main_widget)
        self.layout.addWidget(toolbar)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self.main_widget)
        self.show()

    def seabornplot(self):
        fig, ax = plt.subplots(figsize=(30, 30))
        im = sns.heatmap(self.corr,
                         xticklabels=self.corr.columns.values,
                         yticklabels=self.corr.columns.values,
                         annot=True,
                         ax=ax, annot_kws={"size": 8})
        plt.yticks(rotation=0, fontsize=8)
        plt.xticks(rotation=90, fontsize=8)
        plt.savefig("output_full.svg")
        return fig

    def find_part_cor(self, df):
        columns_all = df.columns
        P = pd.DataFrame(columns=df.columns, index=df.columns)
        for column_name1 in df.columns:
            for column_name2 in df.columns:
                #         print(column_name1, column_name2)
                if column_name1 == column_name2:
                    P.loc[column_name1, column_name2] = 1
                elif len(pd.crosstab(df[column_name1], df[column_name2]).values) < 4:
                    P.loc[column_name1, column_name2] = np.nan
                else:
                    columns_select = columns_all.drop(column_name1)
                    columns_select = columns_select.drop(column_name2)

                    try:
                        result = pg.partial_corr(data=df, x=column_name1,
                                                 y=column_name2, covar=list(columns_select), method='spearman')
                        P.loc[column_name1, column_name2] = result['r'].values[0]
                    except:
                        result = np.nan
        return P


class ButtonWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, input_df=None):
        super(ButtonWindow, self).__init__(parent)
        self.PreviousBTN = QtWidgets.QPushButton('Назад', self)
        self.corr_button = QtWidgets.QPushButton('Матрица корреляций Спирмена', self)
        self.corr_button.clicked.connect(self.on_pushButton_clicked)

        self.part_corr_button = QtWidgets.QPushButton('Матрица частных корреляций Спирмена', self)
        self.part_corr_button.clicked.connect(self.on_part_corr_button_clicked)

        # self.part_corr_button = QtWidgets.QPushButton('Найти ациклический граф', self)
        # self.part_corr_button.clicked.connect(self.on_part_corr_button_clicked)

        self.input_df = input_df

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.corr_button)
        lay.addWidget(self.part_corr_button)
        lay.addWidget(self.PreviousBTN)
        self.dialogs = list()

    @QtCore.pyqtSlot()
    def corr_clicked(self):
        self.input_df
        return 0

    @QtCore.pyqtSlot()
    def on_pushButton_clicked(self):
        dialog = CorrMatrix(self, self.input_df)
        self.dialogs.append(dialog)
        dialog.show()

    @QtCore.pyqtSlot()
    def on_part_corr_button_clicked(self):
        dialog = PartCorrMatrix(self, self.input_df)
        self.dialogs.append(dialog)
        dialog.show()

    @QtCore.pyqtSlot()
    def on_graph_button_clicked(self):
        dialog = PartCorrMatrix(self, self.input_df)
        self.dialogs.append(dialog)
        dialog.show()