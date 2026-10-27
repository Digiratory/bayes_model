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
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from bn_modeller.bayesian_nets.prediction_results import PREDICTED_PREFIX
from bn_modeller.bayesian_nets.utils import get_outliers_cooks

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
    are highlighted in red and a linear fit is shown for the remaining
    points. The R coefficients are returned to the caller for display.
    """

    def __init__(self, parent=None, width=6.4, height=4.8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)

    def update_plot(self, df: pd.DataFrame, name: str) -> tuple[float, float] | None:
        """Draw the scatter for a df with 'pred' and 'true' columns.

        Returns:
            tuple[float, float] | None: Pearson R between the predicted and
            observed values, and R without the Cook's-distance outliers;
            None when there is not enough data.
        """
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
            return None

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
        self.fig.tight_layout()
        self.draw()
        return corr, corr_no_outliers


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

        correlations = canvas.update_plot(
            pd.DataFrame({"pred": predicted, "true": observed}),
            str(predicted.name)[len(PREDICTED_PREFIX) :],
        )
        caption = QLabel(self._formatCorrelationCaption(correlations))
        caption.setWordWrap(True)
        plotLayout.addWidget(caption)
        return widget

    def _formatCorrelationCaption(
        self, correlations: tuple[float, float] | None
    ) -> str:
        """Caption under the scatter explaining the R coefficients."""
        explanation = self.tr(
            "Pearson correlation between the predicted and observed values; "
            "the second value excludes outliers detected by Cook's distance."
        )
        if correlations is None:
            return f"<b>{self.tr('R: not enough data')}</b> — {explanation}"
        values = [
            "n/a" if np.isnan(value) else f"{value:.3f}" for value in correlations
        ]
        return f"<b>{self.tr('R:')} {values[0]} &rarr; {values[1]}</b> — {explanation}"

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
            # The sample ids are a real column; the positional index is not
            # part of the result table.
            export.to_csv(path, index=False)
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
