import networkx as nx
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QWidget

from bn_modeller.bayesian_nets.graph_preparation import GraphPreparation
from bn_modeller.models import (FilterPairTableSQLProxyModel,
                                PairTableSQLProxyModel)
from bn_modeller.utils.model_adapters import tablemodel_to_dataframe


class BayesianNetCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=12, height=12, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.bn_ax = self.fig.add_subplot(1, 1, 1)

    def update_plot(self, graph):
        self.bn_ax.clear()
        # self.bn_ax = self.fig.add_subplot(1, 1, 1)

        elarge = [(u, v)
                  for (u, v, d) in graph.edges(data=True) if d["weight"] > 0.5]
        esmall = [(u, v)
                  for (u, v, d) in graph.edges(data=True) if d["weight"] <= 0.5]

        pos = nx.drawing.nx_agraph.graphviz_layout(graph, prog='dot')

        # nodes
        nx.draw_networkx_nodes(graph, pos, node_size=15, ax=self.bn_ax)

        # edges
        nx.draw_networkx_edges(graph, pos, edgelist=elarge,
                               width=1, alpha=0.4, ax=self.bn_ax)
        nx.draw_networkx_edges(
            graph, pos, edgelist=esmall, width=1, alpha=0.4, edge_color="b", style="dashed", ax=self.bn_ax
        )

        # node labels
        nx.draw_networkx_labels(
            graph, pos, font_size=12, font_family="sans-serif", verticalalignment='bottom', ax=self.bn_ax)

        # edge weight labels
        edge_labels = nx.get_edge_attributes(graph, "weight")
        nx.draw_networkx_edge_labels(
            graph, pos, edge_labels, font_size=12, ax=self.bn_ax)
        self.draw()


class BayesianNetView(QWidget):
    file_path_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.depModel: FilterPairTableSQLProxyModel = None
        self.thresholdValue = 0.5  # TODO: make it a property
        self._init_ui()

    def _init_ui(self):
        self.root_layout = QHBoxLayout()

        self.bn_canvas = BayesianNetCanvas()
        self.root_layout.addWidget(self.bn_canvas)

        self.setLayout(self.root_layout)

    def setModels(self, depModel: FilterPairTableSQLProxyModel):
        self.depModel = depModel
        self.depModel.filterInvalidated.connect(self.drawBN)
        self.depModel.dataChanged.connect(self.drawBN)

        self.drawBN()

    @Slot()
    def drawBN(self):
        if self.depModel is None:
            return
        print("BayesianNetView.drawBN")
        corr_matrix = tablemodel_to_dataframe(
            self.depModel, role=PairTableSQLProxyModel.PearsonCorrRole)
        linkTable = tablemodel_to_dataframe(
            self.depModel, role=Qt.ItemDataRole.CheckStateRole)
        graph = GraphPreparation(
            corr_matrix, linkTable, self.thresholdValue)

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
