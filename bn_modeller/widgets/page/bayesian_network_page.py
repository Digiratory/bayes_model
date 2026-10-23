from PySide6.QtCore import QCoreApplication, QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QTabWidget,
    QWidget,
)

from bn_modeller.bayesian_nets.pyBansheeCalculation import BansheeCalc
from bn_modeller.models import (
    CorrelationSQLProxyModel,
    FilterPairTableSQLProxyModel,
    PairTableSQLProxyModel,
)
from bn_modeller.models.feature_sqltable_model import (
    FeatureSqlTableModel,
    PersistanceCheckableFeatureListProxyModel,
)
from bn_modeller.widgets import DependencySetupTableView, SelectableListView
from bn_modeller.widgets.bn_visualization_view import BayesianNetView
from bn_modeller.widgets.page.bayesian_inference_page import BayesianInferencePageWidget
from bn_modeller.widgets.prediction_results_dialog import (
    PREDICTED_PREFIX,
    PredictionResultsDialog,
)
from bn_modeller.widgets.vertical_label import QVertivalLabel


class _PredictionWorker(QObject):
    """Runs the CPU-bound Bayesian-network prediction off the GUI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        connectedFeatures,
        edgeList,
        samples,
        inputFeatures,
        targetFeatures,
        parent=None,
    ):
        super().__init__(parent)
        self._connectedFeatures = connectedFeatures
        self._edgeList = edgeList
        self._samples = samples
        self._inputFeatures = inputFeatures
        self._targetFeatures = targetFeatures

    @Slot()
    def run(self):
        try:
            banshee = BansheeCalc(
                list(range(len(self._connectedFeatures))),
                self._edgeList,
                self._samples,
            )
            if banshee.getRankCorr() is None:
                self.failed.emit(
                    self.tr(
                        "Failed to reconstruct the rank correlation matrix.\n\n"
                        "This is likely caused by missing values in the dataset."
                    )
                )
                return

            inputSamples = self._samples[self._inputFeatures]
            validMask = inputSamples.notna().all(axis=1).to_numpy()
            if not validMask.any():
                self.failed.emit(
                    self.tr(
                        "All samples contain missing values in the input features.\n\n"
                        "Predictions require samples with complete input values."
                    )
                )
                return

            predictions = banshee.getInference(
                self._inputFeatures, inputSamples.to_numpy()[validMask]
            )

            result = self._samples.loc[validMask, self._targetFeatures].reset_index(
                drop=True
            )
            for target in self._targetFeatures:
                result[PREDICTED_PREFIX + target] = predictions[target].to_numpy()
        except Exception as e:
            # py-banshee raises on invalid inputs (e.g. missing values in a
            # target feature); report it instead of failing silently in a slot.
            self.failed.emit(str(e))
            return
        self.finished.emit(result)


class BayesianNetworkPageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, f=Qt.WindowType()):
        super().__init__(parent, f)
        self._predictionThread = None
        QCoreApplication.instance().aboutToQuit.connect(self._stopPredictionThread)
        self._init_ui()

    def _init_ui(self):
        self.mainLayout = QHBoxLayout(self)

        self.tabWidget = QTabWidget()

        # Dependency tab

        ## Feature selection
        self.dependencyTabWidget = QSplitter()
        self.featureSelectorView = SelectableListView()
        self.featureSelectorView.setStatusTip(
            self.tr("Select features for the Bayesian Network.")
        )
        self.dependencyTabWidget.addWidget(self.featureSelectorView)
        self.dependencyTabWidget.setStretchFactor(0, 1)

        ## Dependency Table
        depTableWidget = QWidget()
        depTableLayout = QGridLayout()

        self._depTable = DependencySetupTableView()
        depTableLayout.addWidget(self._depTable, 1, 1)

        independentLabel = QVertivalLabel("Independent")
        depTableLayout.addWidget(independentLabel, 1, 0, Qt.AlignmentFlag.AlignCenter)

        dependentLabel = QLabel("Dependent")
        depTableLayout.addWidget(dependentLabel, 0, 1, Qt.AlignmentFlag.AlignCenter)

        explanationLabel = QLabel(
            self.tr(
                "Here you can setup expert-defined dependencies between features, choosen in the left side of the window.\n"
                "In the table you can see Spearman correlation coefficients between features as well as partial correlation coefficients.\n"
                "The background color of the table cells indicates the strength of the correlation.\n\n"
                "To visualize the Bayesian Network, open the 'Visualization' tab.\n\n"
                "Please note, that these dependencies are not learned from the data. "
                "They are defined by experts and used to guide the learning process.\n\n"
                "Hint: You can select entire rows or columns by clicking using right mouse button on the row or column header."
            )
        )
        depTableLayout.addWidget(
            explanationLabel, 2, 0, 1, 2, Qt.AlignmentFlag.AlignLeft
        )

        depTableWidget.setLayout(depTableLayout)
        self.dependencyTabWidget.addWidget(depTableWidget)
        self.dependencyTabWidget.setStretchFactor(1, 2)

        self.tabWidget.addTab(self.dependencyTabWidget, self.tr("Dependency"))

        # Visualization Tab
        self.visualizationTabWidget = BayesianNetView()

        self.tabWidget.addTab(self.visualizationTabWidget, self.tr("Visulization"))

        # Prediction Tab
        self.inferenceTabWidget = BayesianInferencePageWidget()
        self.inferenceTabWidget.predictRequested.connect(self.onPredict)
        self.tabWidget.addTab(self.inferenceTabWidget, self.tr("Prediction"))

        # Finalization
        self.mainLayout.addWidget(self.tabWidget)
        self.setLayout(self.mainLayout)

    def setModels(self, pairTableSQLProxyModel: PairTableSQLProxyModel):
        # TODO: т.к. при реализации обсчета байесовских сетей нужно использовать
        # self._pairTableSQLProxyModel, вероятно, её нужно будет вытащить наружу
        # или сделать рассчеты дочерним объектом этой страницы

        self._featureCheckableSortFilterProxyModel = (
            PersistanceCheckableFeatureListProxyModel()
        )
        self._featureCheckableSortFilterProxyModel.setSourceModel(
            pairTableSQLProxyModel.getFeatureSqlTableModel()
        )

        self.featureSelectorView.setModel(self._featureCheckableSortFilterProxyModel)
        self.featureSelectorView.setModelColumn(
            pairTableSQLProxyModel.getFeatureSqlTableModel().fieldIndex(
                pairTableSQLProxyModel.getFeatureSqlTableModel().column_name
            )
        )

        filterPairTableSQLProxyModel: FilterPairTableSQLProxyModel = (
            FilterPairTableSQLProxyModel()
        )
        filterPairTableSQLProxyModel.setSourceModel(pairTableSQLProxyModel)
        filterPairTableSQLProxyModel.setFilterModel(
            self._featureCheckableSortFilterProxyModel,
            pairTableSQLProxyModel.getFeatureSqlTableModel().fieldIndex(
                FeatureSqlTableModel.column_id
            ),
        )

        self._correlationModel = CorrelationSQLProxyModel(filterPairTableSQLProxyModel)
        self._correlationModel.partialCorrGeneralError.connect(
            self.onPartialCorrError, type=Qt.ConnectionType.QueuedConnection
        )

        self._depTable.setModel(self._correlationModel)

        self.visualizationTabWidget.setModels(self._correlationModel)

        # Set correlation model for prediction tab
        self.inferenceTabWidget.setModels(self._correlationModel)

    @Slot()
    def onPartialCorrError(self):
        res = QMessageBox.critical(
            self,
            self.tr("Partial Correlation Error"),
            self.tr(
                "An error occurred while calculating the partial correlation. \n\n"
                "Highly likely, it is caused by a missing value in the data set.\n"
                "To resolve this issue, you can try to disable features with all NAN values in the correlation matrix or select additional features that might help fill in the gaps."
            ),
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
        )

    def _showPredictionError(self, message: str):
        QMessageBox.critical(
            self,
            self.tr("Prediction Error"),
            message,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
        )

    @Slot()
    def onPredict(self):
        if self._predictionThread is not None:
            return

        # Build exactly the network the user sees in the Visualization tab.
        graph, corrMatrix = self.visualizationTabWidget.buildGraph()

        if len(graph.getEdgeList()) == 0:
            self._showPredictionError(
                self.tr(
                    "The Bayesian Network is empty: no links are defined in the "
                    "dependency table (or none survive the visualization threshold).\n\n"
                    "Please define dependencies in the 'Dependency' tab and check the "
                    "'Visualization' tab settings."
                )
            )
            return

        # Only features connected to the network take part in the Bayesian
        # network; graph node ids are positions within the filtered features.
        sortedNodes = sorted(graph.getNodeList())
        connectedFeatures = [corrMatrix.columns[node] for node in sortedNodes]
        nodeRemap = {node: new for new, node in enumerate(sortedNodes)}
        edgeList = [(nodeRemap[u], nodeRemap[v]) for u, v in graph.getEdgeList()]

        inputFeatures = self.inferenceTabWidget.getSelectedFeatures()
        targetFeatures = [
            feature for feature in connectedFeatures if feature not in inputFeatures
        ]

        if not inputFeatures and not self.inferenceTabWidget.hasAvailableFeatures():
            self._showPredictionError(
                self.tr(
                    "No features pass the current threshold.\n\n"
                    "Lower the threshold value or switch the criterion in the "
                    "'Prediction' tab."
                )
            )
            return
        if not inputFeatures:
            self._showPredictionError(
                self.tr(
                    "No input features are selected.\n\n"
                    "Transfer at least one feature to the 'Selected Features' panel."
                )
            )
            return
        unconnectedInputs = [
            feature for feature in inputFeatures if feature not in connectedFeatures
        ]
        if unconnectedInputs:
            self._showPredictionError(
                self.tr(
                    "The selected input features are not connected to the Bayesian "
                    "Network: {}.\n\nAdd dependencies for them in the 'Dependency' "
                    "tab or select other input features."
                ).format(", ".join(unconnectedInputs))
            )
            return
        if not targetFeatures:
            self._showPredictionError(
                self.tr(
                    "All features are selected as inputs.\n\n"
                    "Leave at least one feature in the 'Available Features' panel to "
                    "predict."
                )
            )
            return

        # Qt SQL objects have thread affinity: extract the samples on the GUI
        # thread and run only the CPU-bound inference in the worker.
        pairTableModel = self._correlationModel.sourceModel().sourceModel()
        samples = pairTableModel.getSamplesDataFrame()
        samples = samples[connectedFeatures]

        self._startPredictionWorker(
            connectedFeatures, edgeList, samples, inputFeatures, targetFeatures
        )

    def _stopPredictionThread(self):
        """Finish a running prediction before the widget tree is destroyed.

        The worker cannot be interrupted, so this blocks until the current
        inference completes; that is still safer than destroying a running
        QThread, which aborts the process.
        """
        if self._predictionThread is not None:
            self._predictionThread.quit()
            self._predictionThread.wait()

    def _startPredictionWorker(
        self,
        connectedFeatures,
        edgeList,
        samples,
        inputFeatures,
        targetFeatures,
    ):
        """Run the prediction in a worker thread with a busy progress dialog."""
        self._predictionProgress = QProgressDialog(
            self.tr("Computing predictions..."), None, 0, 0, self
        )
        self._predictionProgress.setWindowTitle(self.tr("Prediction"))
        self._predictionProgress.setWindowModality(Qt.WindowModality.WindowModal)
        self._predictionProgress.setMinimumDuration(0)
        self._predictionProgress.show()

        self._predictionThread = QThread(self)
        self._predictionWorker = _PredictionWorker(
            connectedFeatures, edgeList, samples, inputFeatures, targetFeatures
        )
        self._predictionWorker.moveToThread(self._predictionThread)

        self._predictionThread.started.connect(self._predictionWorker.run)
        self._predictionWorker.finished.connect(self._onPredictionFinished)
        self._predictionWorker.failed.connect(self._onPredictionFailed)
        self._predictionWorker.finished.connect(self._predictionThread.quit)
        self._predictionWorker.failed.connect(self._predictionThread.quit)
        self._predictionThread.finished.connect(self._onPredictionThreadFinished)
        self._predictionThread.finished.connect(self._predictionWorker.deleteLater)
        self._predictionThread.finished.connect(self._predictionThread.deleteLater)
        self._predictionThread.start()

    @Slot(object)
    def _onPredictionFinished(self, result):
        dialog = PredictionResultsDialog(result, self)
        dialog.exec()

    @Slot(str)
    def _onPredictionFailed(self, message):
        self._showPredictionError(self.tr("Prediction failed:\n{}").format(message))

    @Slot()
    def _onPredictionThreadFinished(self):
        self._predictionProgress.close()
        self._predictionProgress = None
        self._predictionWorker = None
        self._predictionThread = None
