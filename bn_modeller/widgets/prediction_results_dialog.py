import pandas as pd
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class PredictionResultsDialog(QDialog):
    """Dialog showing per-sample predictions next to the observed values."""

    def __init__(self, results: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Prediction Results"))
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setColumnCount(len(results.columns))
        table.setRowCount(len(results))
        table.setHorizontalHeaderLabels([str(column) for column in results.columns])
        for row in range(len(results)):
            for column_index, column in enumerate(results.columns):
                table.setItem(
                    row,
                    column_index,
                    QTableWidgetItem(self._format(results.iloc[row][column])),
                )
        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(self.close)
        layout.addWidget(buttons)

    @staticmethod
    def _format(value) -> str:
        if pd.isna(value):
            return ""
        return f"{value:.6g}"
