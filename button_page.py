from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import pandas as pd
import pingouin as pg
import numpy as np
from graph_preparation import GraphPreparation
from pyBansheeCalculation import BansheeCalc
from textwrap import wrap
from sklearn.metrics import r2_score, mean_absolute_error
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import networkx as nx
import matplotlib.pyplot as plt
import copy


def test(y_pred, y_true):
    columns_list = y_true.columns
    result_list = {}
    for num, column_name in enumerate(columns_list):
        df_result = pd.DataFrame(data={'pred': y_pred[:, num], 'true': y_true.iloc[:, num]}, index=y_true.index)
        result_list[column_name] = df_result
    return result_list


def find_outliers(vector: pd.Series):
    outliers_index = vector.loc[(vector > vector.std()*3 + vector.mean()) |
                                (vector < vector.mean() - vector.std()*3)].index
    return list(outliers_index)


class SubplotWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None, data=None):
        super(SubplotWindow, self).__init__(parent)

        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QHBoxLayout(self._main)

        layout_widget = {}
        layoutVert = {}
        for i in data:
            layout_widget[i] = QtWidgets.QWidget()
            layoutVert[i] = QtWidgets.QVBoxLayout(self._main)
            layout_widget[i].setLayout(layoutVert[i])
            fig = self.initFigure(data[i], i)
            fig.tight_layout()
            canvas = FigureCanvas(fig)

            layoutVert[i].addWidget(NavigationToolbar(canvas, self))
            layoutVert[i].addWidget(canvas)

            layout.addWidget(layout_widget[i])

    def initFigure(self, df, name):
        plt.rcParams.update({'figure.autolayout': True})
        name = '\n'.join(wrap(name, 30))
        fig = plt.figure()
        out = find_outliers(df['true']-df['pred'])
        df_drop_out = df[~df.index.isin(out)]
        plt.scatter(df_drop_out['true'], df_drop_out['pred'])
        r2 = df['true'].corr(df['pred'])
        r2_drop_out = df_drop_out['true'].corr(df_drop_out['pred'])

        if len(out):
            k = df.loc[out]
            plt.scatter(k['true'], k['pred'], color='r')

        plt.xlabel(f'true, {name}')
        plt.ylabel(f'predict, {name}')
        plt.grid()
        plt.title(fr'$R^2$ {round(r2, 3)}->{round(r2_drop_out, 3)}')
        # plt.show()
        # plt.tight_layout()
        # print(df.corr()['true'][0])
        return fig


class SubplotGraph(SubplotWindow):
    def initFigure(self, G, name):
        fig = plt.figure()
        elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] > 0.5]
        esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] <= 0.5]

        pos = nx.spring_layout(G, seed=10, k=3)  # positions for all nodes - seed for reproducibility
        # pos = nx.circular_layout(G)

        # nodes
        nx.draw_networkx_nodes(G, pos, node_size=5)

        # edges
        nx.draw_networkx_edges(G, pos, edgelist=elarge, width=2, alpha=0.4)
        nx.draw_networkx_edges(
            G, pos, edgelist=esmall, width=2, alpha=0.4, edge_color="b", style="dashed"
        )

        # node labels
        nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif", verticalalignment='bottom')
        # edge weight labels
        edge_labels = nx.get_edge_attributes(G, "weight")
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        return fig


def preparing_df(df):
    df = df.replace('[^0-9]+', np.nan, regex=True)
    return df


class PlotWindows(QtWidgets.QMainWindow):

    def __init__(self, parent=None, data=None):
        super(PlotWindows, self).__init__(parent)

        self.setWindowTitle('Матрица')

        self.main_widget = QtWidgets.QWidget(self)
        self.resize(2000, 1000)

        self.data = data

        self.fig = self.initFigure()
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

    def initFigure(self):
        fig, ax = plt.subplots(figsize=(30, 30))
        column_name = ['\n'.join(wrap(text, 30)) for text in self.data.columns.values]
        im = sns.heatmap(self.data,
                         xticklabels=column_name,
                         yticklabels=column_name,
                         annot=True,
                         ax=ax, annot_kws={"size": 8})
        plt.yticks(rotation=0, fontsize=8, horizontalalignment='right')
        plt.xticks(rotation=30, fontsize=8, horizontalalignment='right')
        # fig.tight_layout()
        return fig


class CorrMatrix:
    def __init__(self, df):
        """
        Нахождение полной корреляции
        :param df:
        """
        self.df = df
        self.corr = self.df.corr(method='spearman')

    def getCorrMatrix(self, roundOrder=2):
        return self.corr.round(roundOrder)


class PartCorrMatrix:
    def __init__(self, df=None):
        """
        Нахождение частных корреляции
        :param parent:
        :param input_df:
        """
        self.df = df
        self.corr = self.find_part_cor()
        self.corr = self.corr.astype('float')

    def find_part_cor(self):
        columns_all = self.df.columns
        P = pd.DataFrame(columns=self.df.columns, index=self.df.columns)
        for column_name1 in self.df.columns:
            for column_name2 in self.df.columns:
                if column_name1 == column_name2:
                    P.loc[column_name1, column_name2] = 1
                elif len(pd.crosstab(self.df[column_name1], self.df[column_name2]).values) < 4:
                    P.loc[column_name1, column_name2] = np.nan
                else:
                    columns_select = columns_all.drop(column_name1)
                    columns_select = columns_select.drop(column_name2)

                    try:
                        result = pg.partial_corr(data=self.df, x=column_name1,
                                                 y=column_name2, covar=list(columns_select), method='spearman')
                        P.loc[column_name1, column_name2] = result['r'].values[0]
                    except:
                        result = np.nan
        return P

    def getCorrMatrix(self):
        return self.corr


class ButtonWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, input_df=None, linkTable=None, len_input=None):
        super(ButtonWindow, self).__init__(parent)

        self.input_df = input_df

        # self.PreviousBTN = QtWidgets.QPushButton('Назад', self)

        self.corr_button = QtWidgets.QPushButton('Матрица корреляций Спирмена', self)
        self.corr_button.clicked.connect(self.on_pushButton_clicked)

        self.part_corr_button = QtWidgets.QPushButton('Матрица частных корреляций Спирмена', self)
        self.part_corr_button.clicked.connect(self.on_part_corr_button_clicked)

        self.acycle_button = QtWidgets.QPushButton('Найти ациклический граф', self)
        self.acycle_button.clicked.connect(self.on_acycle_graph)

        self.rankCorrButton = QtWidgets.QPushButton('Матрица ранговых корреляция Banshee', self)
        self.rankCorrButton.clicked.connect(self.onRankCorrBanshee)

        self.calcInferenceButton = QtWidgets.QPushButton('Запуск инференса Banshee', self)
        self.calcInferenceButton.clicked.connect(self.onInferenceButton)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.corr_button)
        lay.addWidget(self.part_corr_button)
        lay.addWidget(self.acycle_button)
        lay.addWidget(self.rankCorrButton)
        lay.addWidget(self.calcInferenceButton)
        # lay.addWidget(self.PreviousBTN)

        self.dialogs = list()
        self.corr_matrix = CorrMatrix(self.input_df).getCorrMatrix()
        self.partCorrMatrix = PartCorrMatrix(self.input_df).getCorrMatrix()

        self.linkTable = linkTable
        self.len_input = len_input

        self.y_true = self.input_df.iloc[:, self.len_input:]

    @QtCore.pyqtSlot()
    def on_pushButton_clicked(self):
        dialog = PlotWindows(self, self.corr_matrix)
        self.dialogs.append(dialog)
        dialog.show()
        plt.tight_layout()

    @QtCore.pyqtSlot()
    def on_part_corr_button_clicked(self):
        dialog = PlotWindows(self, self.partCorrMatrix)
        self.dialogs.append(dialog)
        dialog.show()
        plt.tight_layout()

    def on_acycle_graph(self):
        self.graph = GraphPreparation(self.corr_matrix, self.linkTable)
        # удалить циклы в графе
        G_before = copy.deepcopy(self.graph.renaming())
        self.graph.drop_cycle()
        d = {'Before': G_before, 'After': self.graph.renaming()}
        dialog = SubplotGraph(data=d)
        self.dialogs.append(dialog)
        dialog.show()

    def onRankCorrBanshee(self):
        self.banshee = BansheeCalc(self.graph.getNodeList(), self.graph.getEdgeList(), self.input_df)
        self.R = self.banshee.getRankCorr()
        column_name = self.input_df.columns
        dialog = PlotWindows(self, data=pd.DataFrame(self.R, columns=column_name, index=column_name))
        self.dialogs.append(dialog)
        dialog.show()
        plt.tight_layout()

    def onInferenceButton(self):
        y_predict = self.banshee.getInference(self.len_input)
        dictPredict = test(y_predict, self.y_true)
        dialog = SubplotWindow(data=dictPredict)
        self.dialogs.append(dialog)
        dialog.show()
        plt.tight_layout()

    def updateDataFrame(self, input_df):
        self.input_df = input_df

    def updateLinkTable(self, linkTable):
        self.linkTable = linkTable

    def updateLenInputFeature(self, lenInput):
        self.len_input = lenInput

    def update(self):
        self.corr_matrix = CorrMatrix(self.input_df).getCorrMatrix()
        self.partCorrMatrix = PartCorrMatrix(self.input_df).getCorrMatrix()

        self.y_true = self.input_df.iloc[:, self.len_input:]






