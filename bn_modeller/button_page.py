import copy
from textwrap import wrap

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6 import QtCore, QtGui, QtWidgets

from bn_modeller.bayesian_nets import CorrMatrix, PartCorrMatrix
from bn_modeller.bayesian_nets.graph_preparation import GraphPreparation
from bn_modeller.bayesian_nets.pyBansheeCalculation import BansheeCalc
from bn_modeller.bayesian_nets.utils import get_outliers_cooks


def rescale_feature(input_vector, lower, upper):
    xmin, xmax = np.min(input_vector), np.max(
        input_vector
    )  # get max and min from input array

    input_vector = [(x - xmin) / (xmax - xmin) for x in input_vector]

    input_vector = [lower + (upper - lower) * x for x in input_vector]
    return input_vector


def test(y_pred, y_true):
    columns_list = y_true.columns
    result_list = {}
    for num, column_name in enumerate(columns_list):
        # k = y_true.iloc[:, num].dropna()
        # upper, lower = k.max(), k.min()
        df_result = pd.DataFrame(
            data={"pred": y_pred[:, num], "true": y_true.iloc[:, num]},
            index=y_true.index,
        )
        result_list[column_name] = df_result
    return result_list


def find_outliers(vector: pd.Series):
    outliers_index = vector.loc[
        (vector > vector.std() * 3 + vector.mean())
        | (vector < vector.mean() - vector.std() * 3)
    ].index
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

        # self.resize(2000, 1000)

        # layout_widget = QtWidgets.QWidget()
        # layoutVert = QtWidgets.QVBoxLayout()
        # self.setCentralWidget(layout_widget)
        #
        # # layout_widget = {}
        # # layoutVert = {}
        # m = len(data)
        # if m <= 4:
        #     layout_widget_H = QtWidgets.QWidget()
        #     layoutHor = QtWidgets.QHBoxLayout(layout_widget_H)
        #     for i in data:
        #         widgTmp = QtWidgets.QWidget()
        #         layoutUn = QtWidgets.QVBoxLayout(widgTmp)
        #         fig = self.initFigure(data[i], i)
        #         fig.tight_layout()
        #         canvas = FigureCanvas(fig)
        #         layoutUn.addWidget(NavigationToolbar(canvas, self))
        #         layoutUn.addWidget(canvas)
        #         layoutHor.addWidget(widgTmp)
        #
        #     layout_widget.setLayout(layoutHor)
        #     layoutVert.addWidget(layout_widget)
        # # else:
        # #     for i in range(m//4):
        # #         k_start = i * 4
        # #         for k in range(k_start, k_start+4):
        # #             if k > len(data):
        # #                 break
        # #             i = data.keys()[k]
        # #             layout_widget[i] = QtWidgets.QWidget()
        # #             layoutVert[i] = QtWidgets.QVBoxLayout(self._main)
        # #             layout_widget[i].setLayout(layoutVert[i])
        # #             fig = self.initFigure(data[i], i)
        # #             fig.tight_layout()
        # #             canvas = FigureCanvas(fig)
        # #
        # #             layoutVert[i].addWidget(NavigationToolbar(canvas, self))
        # #             layoutVert[i].addWidget(canvas)

    def initFigure(self, df, name):
        # plt.rcParams.update({'figure.autolayout': True})
        name = "\n".join(wrap(name, 30))
        fig = plt.figure(layout="tight")
        out = find_outliers(df["true"] - df["pred"])
        df_drop_out = df[~df.index.isin(out)]

        df_drop_out = df_drop_out.dropna()

        # sns.regplot(x=df_drop_out['true'], y=df_drop_out['pred'], color='tab:blue',
        #             scatter=False, line_kws={'linewidth': 1})

        xseq = np.linspace(df["true"].min() - 5, df["true"].max() + 5, num=100)
        plt.scatter(df_drop_out["true"], df_drop_out["pred"])
        if len(df_drop_out) > 1:
            b, a = np.polyfit(df_drop_out["true"], df_drop_out["pred"], deg=1)
            plt.plot(xseq, a + b * xseq, lw=1)

        # ci = 1.96 * np.std(a + b * xseq) / np.sqrt(len(xseq))
        # plt.fill_between(xseq, (a + b * xseq - ci), (a + b * xseq + ci), color='b', alpha=.1)

        r2 = df["true"].corr(df["pred"])
        r2_drop_out = df_drop_out["true"].corr(df_drop_out["pred"])

        if len(out):
            k = df.loc[out]
            # add linear regression
            plt.scatter(k["true"], k["pred"], color="r")

        plt.xlabel(f"Observed, {name}")
        plt.ylabel(f"Predicted, {name}")
        plt.grid()
        plt.title(rf"$R$ {round(r2, 3)}$\rightarrow${round(r2_drop_out, 3)}")
        return fig


class SubplotGraph(SubplotWindow):
    def initFigure(self, G, name):
        fig = plt.figure(figsize=(20, 20))
        elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] > 0.5]
        esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] <= 0.5]

        # pos = nx.spring_layout(G, seed=10, iterations=200)  # positions for all nodes - seed for reproducibility
        # pos = nx.fruchterman_reingold_layout(G)  # positions for all nodes - seed for reproducibility
        # pos = nx.circular_layout(G)
        # pos = nx.spectral_layout(G)
        # pos = nx.multipartite_layout(G)
        # pos = nx.planar_layout(G)
        # pos = nx.drawing.nx_agraph.graphviz_layout(G)
        pos = nx.drawing.nx_agraph.graphviz_layout(G, prog="dot")

        # nodes
        nx.draw_networkx_nodes(G, pos, node_size=5)

        # edges
        nx.draw_networkx_edges(G, pos, edgelist=elarge, width=1, alpha=0.4)
        nx.draw_networkx_edges(
            G, pos, edgelist=esmall, width=1, alpha=0.4, edge_color="b", style="dashed"
        )

        # node labels
        nx.draw_networkx_labels(
            G, pos, font_size=8, font_family="sans-serif", verticalalignment="bottom"
        )

        # edge weight labels
        edge_labels = nx.get_edge_attributes(G, "weight")
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig("imagenet_layout.eps")
        return fig


class PlotWindows(QtWidgets.QMainWindow):

    def __init__(self, parent=None, data=None, title="Matrix"):
        super(PlotWindows, self).__init__(parent)

        self.setWindowTitle(title)

        self.main_widget = QtWidgets.QWidget(self)
        self.resize(2000, 1000)

        self.data = data
        self.fig = Figure()

        self.initFigure()

        self.canvas = FigureCanvas(self.fig)

        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.updateGeometry()
        # self.label = QtWidgets.QLabel("A plot:")
        toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtWidgets.QGridLayout(self.main_widget)
        self.layout.addWidget(toolbar)
        # self.layout.addWidget(self.label)
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self.main_widget)
        self.show()
        self.fig.tight_layout()

    def initFigure(self):
        ax = self.fig.add_subplot(111)
        # discards the old graph
        ax.clear()

        column_name = ["\n".join(wrap(text, 30)) for text in self.data.columns.values]
        print(self.data)
        im = sns.heatmap(
            self.data,
            xticklabels=column_name,
            yticklabels=column_name,
            annot=True,
            ax=ax,
            annot_kws={"size": 8},
        )

        ax.set_xticklabels(column_name, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(column_name, rotation=0, ha="right", fontsize=8)


class PlotInferenceResult(QtWidgets.QMainWindow):
    def __init__(self, parent=None, data=None, name=None, title="Matrix"):
        super(PlotInferenceResult, self).__init__(parent)

        self.setWindowTitle(title)

        self.main_widget = QtWidgets.QWidget(self)
        self.resize(600, 400)

        self.data = data
        self.fig = Figure()

        self.initFigure(self.data, name)

        self.canvas = FigureCanvas(self.fig)

        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.updateGeometry()
        # self.label = QtWidgets.QLabel("A plot:")
        toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtWidgets.QGridLayout(self.main_widget)
        self.layout.addWidget(toolbar)
        # self.layout.addWidget(self.label)
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self.main_widget)
        self.show()
        self.fig.tight_layout()

    def initFigure(self, df, name):
        # plt.rcParams.update({'figure.autolayout': True})
        name = "\n".join(wrap(name, 30))
        ax = self.fig.add_subplot(111)
        ax.grid()
        # out = find_outliers(df['true']-df['pred'])

        out = get_outliers_cooks(df.dropna())

        df_drop_out = df[~df.index.isin(out)]

        df_drop_out = df_drop_out.dropna()

        # sns.regplot(x=df_drop_out['true'], y=df_drop_out['pred'], color='tab:blue',
        #             scatter=False, line_kws={'linewidth': 1})

        xseq = np.linspace(df["pred"].min() - 5, df["pred"].max() + 5, num=100)
        ax.scatter(df_drop_out["pred"], df_drop_out["true"])
        if len(df_drop_out) > 1:
            b, a = np.polyfit(df_drop_out["pred"], df_drop_out["true"], deg=1)
            ax.plot(xseq, a + b * xseq, lw=1)

        # ci = 1.96 * np.std(a + b * xseq) / np.sqrt(len(xseq))
        # plt.fill_between(xseq, (a + b * xseq - ci), (a + b * xseq + ci), color='b', alpha=.1)

        r2 = df["true"].corr(df["pred"])
        r2_drop_out = df_drop_out["true"].corr(df_drop_out["pred"])

        if len(out):
            k = df.loc[out]
            # add linear regression
            ax.scatter(k["pred"], k["true"], color="r")

        ax.set_xlabel(f"Predicted, {name}")
        ax.set_ylabel(f"Observed, {name}")

        ax.set_title(rf"$R$ {round(r2, 3)}$\rightarrow${round(r2_drop_out, 3)}")
        # return fig


class ButtonWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, input_df=None, linkTable=None, len_input=None):
        super(ButtonWindow, self).__init__(parent)
        self.input_df: pd.DataFrame = input_df
        self.setFixedSize(400, 500)
        self.move(0, 0)

        self.corr_button = QtWidgets.QPushButton("Full Spearman's Correlation", self)
        self.corr_button.clicked.connect(self.on_pushButton_clicked)

        self.part_corr_button = QtWidgets.QPushButton(
            "Partial Spearman's Correlation", self
        )
        self.part_corr_button.clicked.connect(self.on_part_corr_button_clicked)

        self.acycle_button = QtWidgets.QPushButton("Searching acyclic graph", self)
        self.acycle_button.clicked.connect(self.on_acycle_graph)

        self.rankCorrButton = QtWidgets.QPushButton(
            "Reconstruction of the correlation (Banshee)", self
        )
        self.rankCorrButton.clicked.connect(self.onRankCorrBanshee)
        self.rankCorrButton.setEnabled(False)

        self.calcInferenceButton = QtWidgets.QPushButton(
            "Calculating Bayesian model inference (Banshee)", self
        )
        self.calcInferenceButton.clicked.connect(self.onInferenceButton)
        self.calcInferenceButton.setEnabled(False)

        self.thresholdEdit = QtWidgets.QLineEdit(self, placeholderText="0.0")
        validator = QtGui.QDoubleValidator()  # Создание валидатора.
        validator.setRange(0.0, 1.0, 2)  # Установка диапазона значений.
        validator.setLocale(QtCore.QLocale("en_US"))
        # Установка валидатора для поля ввода
        self.thresholdEdit.setValidator(validator)
        self.thresholdEdit.textChanged[str].connect(self.onChanged)

        lay = QtWidgets.QGridLayout()
        lay.setSpacing(0)
        lay.setContentsMargins(0, -1, 0, -1)

        lay.addWidget(QtWidgets.QLabel("Threshold"), 1, 0)
        lay.addWidget(self.thresholdEdit, 1, 1)
        # lay.addWidget(self.formLayoutWidget)
        lay.addWidget(self.corr_button, 2, 0, 1, 2)
        lay.addWidget(self.part_corr_button, 3, 0, 1, 2)

        lay.addWidget(self.acycle_button, 4, 0, 1, 2)
        lay.addWidget(self.rankCorrButton, 5, 0, 1, 2)
        lay.addWidget(self.calcInferenceButton, 6, 0, 1, 2)
        self.setLayout(lay)

        self.dialogs = list()
        self.corr_matrix = CorrMatrix(self.input_df).getCorrMatrix()
        self.partCorrMatrix = PartCorrMatrix(self.input_df).getCorrMatrix()

        self.linkTable = linkTable
        self.len_input = len_input

        self.y_true = self.input_df.iloc[:, self.len_input :]

        # self.setGeometry(300, 300, 350, 300)

        self.thresholdValue = 0.0

        self.updLinkTable = None
        self.df_predicted = pd.DataFrame()
        self.error_dialog = QtWidgets.QErrorMessage()

    def onChanged(self, text):
        self.thresholdValue = float(text)

    @QtCore.Slot()
    def on_pushButton_clicked(self):
        dialog = PlotWindows(self, self.corr_matrix)
        self.dialogs.append(dialog)
        dialog.show()

    @QtCore.Slot()
    def on_part_corr_button_clicked(self):
        if len(self.partCorrMatrix.dropna()) < 1:
            self.error_dialog.showMessage("Error of the correlation matrix")
        else:
            dialog = PlotWindows(self, self.partCorrMatrix)
            self.dialogs.append(dialog)
            dialog.show()

    def on_acycle_graph(self):
        self.graph = GraphPreparation(
            self.corr_matrix, self.linkTable, self.thresholdValue
        )

        # удалить циклы в графе
        G_before = copy.deepcopy(self.graph.renaming())

        self.graph.drop_cycle()
        self.changeLinkTable()

        d = {"Before": G_before, "After": self.graph.renaming()}
        # import pickle
        # pickle.dump(self.graph, open('graph.txt', 'w'))
        # print(self.graph.G.nodes())

        nx.write_adjlist(self.graph.renaming(), "graph.txt")
        dialog = SubplotGraph(data=d)
        self.dialogs.append(dialog)
        dialog.show()
        self.rankCorrButton.setEnabled(True)

    def onRankCorrBanshee(self):
        self.banshee = BansheeCalc(
            self.graph.getNodeList(), self.graph.getEdgeList(), self.input_df
        )
        self.R = self.banshee.getRankCorr()
        if self.R is None:
            self.error_dialog.showMessage(
                "Error in the reconstruction of the correlation matrix"
            )
        else:
            self.banshee.saveGraph()

        column_name = self.input_df.columns
        dialog = PlotWindows(
            self, data=pd.DataFrame(self.R, columns=column_name, index=column_name)
        )
        self.dialogs.append(dialog)
        dialog.show()
        plt.tight_layout()
        self.calcInferenceButton.setEnabled(True)

    def onInferenceButton(self):
        y_predict = self.banshee.getInference(self.len_input)

        self.columnsForPredict = self.input_df.columns[self.len_input :]
        self.columnsFeatures = self.input_df.columns[: self.len_input]

        pred_column = ["Predicted " + i for i in self.columnsForPredict]
        self.df_predicted = pd.DataFrame(
            y_predict, index=self.input_df.index, columns=pred_column
        )
        df = self.input_df.join(self.df_predicted)

        df_tmp = df.copy(deep=True)
        df_tmp = df_tmp.dropna(subset=self.columnsFeatures)

        for col_name in self.columnsForPredict:
            lower, upper = self.input_df[col_name].min(), self.input_df[col_name].max()
            df_tmp.loc[:, "Predicted " + col_name] = rescale_feature(
                df_tmp.loc[:, "Predicted " + col_name], lower, upper
            )

        df = self.input_df.join(df_tmp[pred_column])
        self.df_predicted = df[pred_column]

        df.to_csv("data/result.csv")

        df = df.dropna(subset=self.columnsFeatures)

        # dictPredict = test(y_predict, self.y_true)
        dictPredict = test(df[pred_column].values, df[self.columnsForPredict])
        # dialog = SubplotWindow(data=dictPredict)
        for i in dictPredict:
            dialog = PlotInferenceResult(data=dictPredict[i], name=i)
            self.dialogs.append(dialog)
            dialog.show()
            plt.tight_layout()

    def updateDataFrame(self, input_df):
        self.input_df = input_df

    def updateLinkTable(self, linkTable):
        self.linkTable = linkTable
        self.updLinkTable = None

    def updateLenInputFeature(self, lenInput):
        self.len_input = lenInput

    def updateMatrix(self):
        self.corr_matrix = CorrMatrix(self.input_df).getCorrMatrix()
        # self.partCorrMatrix = PartCorrMatrix(self.input_df).getCorrMatrix()
        self.y_true = self.input_df.iloc[:, self.len_input :]

    def getThresholdVal(self):
        return self.thresholdValue

    def changeLinkTable(self):
        newLinkTab = pd.DataFrame(
            columns=self.input_df.columns, index=self.input_df.columns
        )

        for i in self.graph.renaming().edges(data=True):
            newLinkTab.loc[i[0], i[1]] = 1
        newLinkTab = newLinkTab.fillna(0)
        self.updLinkTable = newLinkTab

    def getNewLinkTab(self):
        return self.updLinkTable

    def getPrediction(self):
        return self.df_predicted
