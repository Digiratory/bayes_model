import numpy as np
import pandas as pd
from PySide6 import QtCore, QtWidgets


class LinkTabWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, input_df=None, state=None):
        """
        Для матрицы связей
        :param parent:
        :param input_df:
        """
        super(LinkTabWindow, self).__init__(parent)

        self.widget_page = QtWidgets.QWidget()
        self.input_df = input_df
        self.columnNames = list(input_df.columns)
        self.result_df = pd.DataFrame(columns=self.columnNames, index=self.columnNames)

        self.columnNames.insert(0, "Select ALL")
        self.tableWidget = QtWidgets.QTableWidget(
            len(self.columnNames), len(self.columnNames)
        )

        self.state = (
            self.updateState(state)
            if state is not None and (len(state) + 1 == len(self.columnNames))
            else self.initState()
        )
        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                # item.setCheckState(QtCore.Qt.Unchecked)
                item.setCheckState(self.state[i][j])
                self.tableWidget.setItem(i, j, item)

        self.lay = QtWidgets.QVBoxLayout(self)

    def select_all_clicked_by_columns(self, row, column):
        if row != 0:
            return 0
        state = self.tableWidget.item(0, column).checkState()
        for i in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(i, column)
            item.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

    def select_all_clicked_by_rows(self, row, column):
        if column != 0:
            return 0
        state = self.tableWidget.item(row, 0).checkState()
        for i in range(self.tableWidget.columnCount()):
            item = self.tableWidget.item(row, i)
            item.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

    @QtCore.Slot()
    def save_clicked(self):
        items = []
        for i in range(1, self.tableWidget.rowCount()):
            it = []
            for j in range(1, self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                it.append(item.checkState())
            items.append(it)

        self.result_df.loc[:, :] = items
        self.result_df = self.result_df.replace({2: 1})
        if len(self.result_df) > 1:
            self.result_df.to_excel("data/link_table.xlsx", engine="openpyxl")

    def getDataFrame(self) -> pd.DataFrame:
        return self.result_df

    def updateInput(self, input_df, state=None):
        self.input_df = input_df

        self.columnNames = input_df.columns
        self.result_df = pd.DataFrame(columns=self.columnNames, index=self.columnNames)

        self.columnNames = self.columnNames.insert(0, "Select ALL")
        self.tableWidget = QtWidgets.QTableWidget(
            len(self.columnNames), len(self.columnNames)
        )

        self.tableWidget.setHorizontalHeaderLabels(self.columnNames)
        self.tableWidget.setVerticalHeaderLabels(self.columnNames)
        if state is not None:
            if (type(state[0][0]) == np.int64) & (
                len(state) + 1 == self.tableWidget.rowCount()
            ):
                self.state = self.updateState(state)
            else:
                self.state = self.initState()
        else:
            self.state = self.initState()

        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                # item.setCheckState(QtCore.Qt.Unchecked)
                item.setCheckState(self.state[i][j])
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.cellChanged.connect(self.select_all_clicked_by_columns)
        self.tableWidget.cellChanged.connect(self.select_all_clicked_by_rows)

        self.lay.addWidget(self.tableWidget)

    def removeTableWidget(self):
        self.tableWidget.deleteLater()

    def initState(self):
        return [
            [QtCore.Qt.Unchecked] * self.tableWidget.columnCount()
        ] * self.tableWidget.rowCount()

    def updateState(self, input_vector):
        new_vector = [
            [QtCore.Qt.Unchecked] * self.tableWidget.columnCount()
            for _ in range(self.tableWidget.rowCount())
        ]

        for i in range(0, len(input_vector)):
            for j in range(0, len(input_vector[0])):
                new_vector[i + 1][j + 1] = (
                    QtCore.Qt.Checked if input_vector[i][j] > 0 else QtCore.Qt.Unchecked
                )
        return new_vector

    def getColumnNames(self):
        return self.columnNames[1:]

    def saveState(self):
        self.state = []
        for i in range(self.tableWidget.rowCount()):
            it = []
            for j in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                it.append(item.checkState())
            self.state.append(it)
