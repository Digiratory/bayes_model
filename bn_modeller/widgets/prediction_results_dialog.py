from textwrap import wrap

import numpy as np
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from bn_modeller.bayesian_nets.utils import get_outliers_cooks

PREDICTED_PREFIX = "Predicted "
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _csvSafeHeader(name) -> str:
    """Neutralize spreadsheet formula injection in exported CSV headers."""
    text = str(name)
    if text.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + text
    return text


class PredictionScatterCanvas(FigureCanvasQTAgg):
    """Predicted-vs-observed scatter for one target feature.

    Ported from the legacy PlotInferenceResult: Cook's distance outliers
    are highlighted in red and a linear fit with the R coefficients is
    shown for the remaining points.
    """

    def __init__(self, parent=None, width=6.4, height=4.8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)

    def update_plot(self, df: pd.DataFrame, name: str):
        """Draw the scatter for a df with 'pred' and 'true' columns."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.grid()

        df = df.dropna()
        if df.empty:
            ax.text(
                0.5,
                0.5,
                self.tr("Not enough data for the plot"),
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            self.draw()
            return

        outliers = list(get_outliers_cooks(df))
        df_no_outliers = df[~df.index.isin(outliers)]

        xseq = np.linspace(df["pred"].min() - 5, df["pred"].max() + 5, num=100)
        ax.scatter(df_no_outliers["pred"], df_no_outliers["true"])
        if len(df_no_outliers) > 1:
            b, a = np.polyfit(df_no_outliers["pred"], df_no_outliers["true"], deg=1)
            ax.plot(xseq, a + b * xseq, lw=1)

        corr = df["true"].corr(df["pred"])
        corr_no_outliers = df_no_outliers["true"].corr(df_no_outliers["pred"])

        if len(outliers):
            outlier_points = df.loc[outliers]
            ax.scatter(outlier_points["pred"], outlier_points["true"], color="r")

        wrapped_name = "\n".join(wrap(name, 30))
        ax.set_xlabel(f"{self.tr('Predicted')}, {wrapped_name}")
        ax.set_ylabel(f"{self.tr('Observed')}, {wrapped_name}")
        ax.set_title(rf"$R$ {round(corr, 3)}$\rightarrow${round(corr_no_outliers, 3)}")
        self.fig.tight_layout()
        self.draw()


class PredictionResultsDialog(QDialog):
    """Dialog showing per-sample predictions, per-target plots and CSV export."""

    def __init__(self, results: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._results = results
        self.setWindowTitle(self.tr("Prediction Results"))
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._buildTableTab(), self.tr("Table"))
        for column in results.columns:
            columnName = str(column)
            if not columnName.startswith(PREDICTED_PREFIX):
                continue
            target = columnName[len(PREDICTED_PREFIX) :]
            if target not in results.columns:
                continue
            self._tabs.addTab(
                self._buildPlotTab(results[column], results[target]), target
            )
        layout.addWidget(self._tabs, 1)

        buttonsLayout = QHBoxLayout()
        saveCsvButton = QPushButton(self.tr("Save CSV..."))
        saveCsvButton.clicked.connect(self._onSaveCsv)
        buttonsLayout.addWidget(saveCsvButton)
        buttonsLayout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(self.close)
        buttonsLayout.addWidget(buttons)
        layout.addLayout(buttonsLayout)

    def _buildTableTab(self) -> QWidget:
        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setColumnCount(len(self._results.columns))
        table.setRowCount(len(self._results))
        table.setHorizontalHeaderLabels(
            [str(column) for column in self._results.columns]
        )
        values = self._results.to_numpy(dtype=object)
        for row in range(values.shape[0]):
            for column_index in range(values.shape[1]):
                table.setItem(
                    row,
                    column_index,
                    QTableWidgetItem(self._format(values[row, column_index])),
                )
        return table

    def _buildPlotTab(self, predicted: pd.Series, observed: pd.Series) -> QWidget:
        widget = QWidget()
        plotLayout = QVBoxLayout(widget)
        plotLayout.setContentsMargins(0, 0, 0, 0)

        canvas = PredictionScatterCanvas()
        toolbar = NavigationToolbar2QT(canvas, widget)
        plotLayout.addWidget(toolbar)
        plotLayout.addWidget(canvas)

        canvas.update_plot(
            pd.DataFrame({"pred": predicted, "true": observed}),
            str(predicted.name)[len(PREDICTED_PREFIX) :],
        )
        return widget

    def _onSaveCsv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Prediction Results"),
            "result.csv",
            self.tr("CSV files (*.csv)"),
        )
        if not path:
            return
        try:
            export = self._results.copy()
            export.columns = [_csvSafeHeader(column) for column in export.columns]
            export.to_csv(path)
        except OSError as e:
            QMessageBox.critical(
                self,
                self.tr("Save Error"),
                self.tr("Failed to save the file: {}").format(e),
            )

    @staticmethod
    def _format(value) -> str:
        if pd.isna(value):
            return ""
        return f"{value:.6g}"
