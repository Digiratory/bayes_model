import networkx as nx
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from bn_modeller.bayesian_nets.graph_preparation import GraphPreparation
from bn_modeller.models import FilterPairTableSQLProxyModel, PairTableSQLProxyModel
from bn_modeller.utils.model_adapters import tablemodel_to_dataframe
from bn_modeller.widgets.extended_slider_widget import ExtendedSliderWidget


class BayesianNetCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=12, height=12, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.bn_ax = self.fig.add_subplot(1, 1, 1)

    def update_plot(self, graph):
        self.bn_ax.clear()
        # self.bn_ax = self.fig.add_subplot(1, 1, 1)

        elarge = [(u, v) for (u, v, d) in graph.edges(data=True) if d["weight"] > 0.5]
        esmall = [(u, v) for (u, v, d) in graph.edges(data=True) if d["weight"] <= 0.5]

        pos = nx.drawing.nx_agraph.graphviz_layout(graph, prog="dot")

        # nodes
        nx.draw_networkx_nodes(graph, pos, node_size=15, ax=self.bn_ax)

        # edges
        nx.draw_networkx_edges(
            graph, pos, edgelist=elarge, width=1, alpha=0.4, ax=self.bn_ax
        )
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=esmall,
            width=1,
            alpha=0.4,
            edge_color="b",
            style="dashed",
            ax=self.bn_ax,
        )

        # node labels
        nx.draw_networkx_labels(
            graph,
            pos,
            font_size=12,
            font_family="sans-serif",
            verticalalignment="bottom",
            ax=self.bn_ax,
        )

        # edge weight labels
        edge_labels = nx.get_edge_attributes(graph, "weight")
        nx.draw_networkx_edge_labels(
            graph, pos, edge_labels, font_size=12, ax=self.bn_ax
        )
        self.fig.tight_layout(pad=3.0)
        self.draw()


class BayesianNetView(QSplitter):
    file_path_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.depModel: FilterPairTableSQLProxyModel = None
        self._init_ui()

    def _init_ui(self):
        self.setOrientation(Qt.Orientation.Vertical)
        # BN Plot
        bnPlotLayout = QVBoxLayout()

        self.bn_canvas = BayesianNetCanvas()
        self.toolbar = NavigationToolbar2QT(self.bn_canvas, self)
        bnPlotLayout.addWidget(self.toolbar)
        bnPlotLayout.addWidget(self.bn_canvas)
        bnPlotWidget = QWidget()
        bnPlotWidget.setLayout(bnPlotLayout)
        self.addWidget(bnPlotWidget)

        # BN Visualization Settings
        self.threadSliderWidget = ExtendedSliderWidget()
        self.threadSliderWidget.setRange(0, 1)
        self.threadSliderWidget.setValue(0.5)
        self.threadSliderWidget.setTrackMovements(False)
        self.threadSliderWidget.valueChanged.connect(self.drawBN)
        self.addWidget(self.threadSliderWidget)

    def setModels(self, depModel: FilterPairTableSQLProxyModel):
        self.depModel = depModel
        self.depModel.filterInvalidated.connect(self.drawBN)
        self.depModel.dataChanged.connect(self.drawBN)

        self.drawBN()

    @Slot()
    def drawBN(self):
        if self.depModel is None or not self.isVisible():
            return
        print("BayesianNetView.drawBN")
        corr_matrix = tablemodel_to_dataframe(
            self.depModel, role=PairTableSQLProxyModel.PearsonCorrRole
        )
        linkTable = tablemodel_to_dataframe(
            self.depModel, role=Qt.ItemDataRole.CheckStateRole
        )
        graph = GraphPreparation(
            corr_matrix, linkTable, self.threadSliderWidget.value()
        )

        graph.drop_cycle()
        # self.changeLinkTable()

        self.bn_canvas.update_plot(graph.renaming())
        # import pickle
        # pickle.dump(self.graph, open('graph.txt', 'w'))
        # print(self.graph.G.nodes())

        # nx.write_adjlist(self.graph.renaming(), 'graph.txt')

    def showEvent(self, event):
        v = super().showEvent(event)
        self.drawBN()
        return v
