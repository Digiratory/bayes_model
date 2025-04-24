import itertools as it

import networkx as nx
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from bn_modeller.bayesian_nets.graph_preparation import GraphPreparation
from bn_modeller.models import CorrelationSQLProxyModel, PairTableSQLProxyModel
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
        # connectionstyle = [f"arc3,rad={r}" for r in it.accumulate([0.15] * 4)]
        connectionstyle = f"angle3,angleA=0, angleB=90"
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=elarge,
            width=1,
            alpha=0.4,
            ax=self.bn_ax,
            connectionstyle=connectionstyle,
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
            connectionstyle=connectionstyle,
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
            graph,
            pos,
            edge_labels,
            font_size=12,
            connectionstyle=connectionstyle,
            ax=self.bn_ax,
        )
        self.fig.tight_layout(pad=3.0)
        self.draw()


class BayesianNetView(QSplitter):
    file_path_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.depModel: CorrelationSQLProxyModel = None
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
        settingsWidget = QWidget()
        settingsLayout = QHBoxLayout()

        # Checkbox for filtering by p-value
        self.filterByPValueCheckBox = QCheckBox(self.tr("Filter by P-Value"))
        self.filterByPValueCheckBox.stateChanged.connect(self.drawBN)
        settingsLayout.addWidget(self.filterByPValueCheckBox)

        # Dropdown for selecting BN Correlation Type

        self.correlationTypeComboBox = QComboBox()
        self.correlationTypeComboBox.addItems(
            ["Pearson", "Spearman", "Partial Correlation"]
        )
        self.correlationTypeComboBox.currentIndexChanged.connect(self.drawBN)
        self.correlationTypeComboBox.setCurrentIndex(1)
        self.correlationTypeComboBoxMapping = [
            PairTableSQLProxyModel.PearsonCorrRole,
            PairTableSQLProxyModel.SpearmanCorrRole,
            CorrelationSQLProxyModel.PartialCorrRole,
        ]
        self.pvalueTypeComboBoxMapping = [
            PairTableSQLProxyModel.PearsonPValueRole,
            PairTableSQLProxyModel.SpearmanPValueRole,
            CorrelationSQLProxyModel.PartialPValueRole,
        ]
        settingsLayout.addWidget(self.correlationTypeComboBox)

        # Slider Widget for adjusting BN Visualization Threshold
        self.threadSliderWidget = ExtendedSliderWidget()
        self.threadSliderWidget.setRange(0, 1)
        self.threadSliderWidget.setValue(0.3)
        self.threadSliderWidget.setTrackMovements(False)
        self.threadSliderWidget.valueChanged.connect(self.drawBN)
        settingsLayout.addWidget(self.threadSliderWidget)

        settingsWidget.setLayout(settingsLayout)
        self.addWidget(settingsWidget)

        # Explanation Widgets
        self.explanationWidget = QLabel(
            self.tr(
                "Here you can work with a visualization of the Bayesian Network.\n"
                "Using the dropdown above you can select the type of correlation to be used for drawing the Bayesian Network. "
                "Also you can adjust the threshold for edge visibility using the slider above and see how it affects the network.\n"
                "The buttons in the toolbar allow you to interact with the plot, including zooming and saving the plot in numerous formats."
            )
        )
        self.addWidget(self.explanationWidget)

    def setModels(self, depModel: CorrelationSQLProxyModel):
        self.depModel = depModel
        # self.depModel.filterInvalidated.connect(self.drawBN)
        self.depModel.dataChanged.connect(self.drawBN)

        self.drawBN()

    @Slot()
    def drawBN(self):
        if self.depModel is None or not self.isVisible():
            return
        print("BayesianNetView.drawBN")

        corr_matrix = tablemodel_to_dataframe(
            self.depModel,
            role=self.correlationTypeComboBoxMapping[
                self.correlationTypeComboBox.currentIndex()
            ],
        )
        pvalue_matrix = None

        if self.filterByPValueCheckBox.isChecked():
            pvalue_matrix = tablemodel_to_dataframe(
                self.depModel,
                role=self.pvalueTypeComboBoxMapping[
                    self.correlationTypeComboBox.currentIndex()
                ],
            )

        linkTable = tablemodel_to_dataframe(
            self.depModel, role=Qt.ItemDataRole.CheckStateRole
        )
        graph = GraphPreparation(
            corr_matrix,
            linkTable,
            self.threadSliderWidget.value(),
            pvalue_matrix=pvalue_matrix,
            pvalue_threshold=0.05,
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
