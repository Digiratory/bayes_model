import pandas as pd
from PyQt5 import QtCore, QtWidgets


def read_data(path='data/tmp.csv'):
    data_input = pd.read_csv(path, index_col=0)
    return data_input


class IOWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, input_df=None, state=None):
        super(IOWindow, self).__init__(parent)
        self.input_table = input_df
        col_name = self.input_table.columns

        self.df_input_output = pd.DataFrame(columns=['input', 'output'], index=col_name)
        col_name = col_name.insert(0, 'Select ALL')

        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 2)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tableWidget)

        self.tableWidget.setHorizontalHeaderLabels(['input', 'output'])
        self.tableWidget.setVerticalHeaderLabels(col_name)
        self.state = state if state else self.initState()
        for i in range(self.tableWidget.rowCount()):
            for j in range(2):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                # item.setCheckState(QtCore.Qt.Unchecked)
                item.setCheckState(self.state[i][j])
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.cellChanged.connect(self.select_all_clicked_by_columns)
        self.tableWidget.cellChanged.connect(self.turnOffClicked)

    def select_all_clicked_by_columns(self, row, column):
        if row != 0:
            return 0
        state = self.tableWidget.item(0, column).checkState()
        # state = self.tableWidget.state()
        for i in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(i, column)
            item.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

    # def turnOffClicked(self, row, column):
    #     # all_columns = list(range(self.tableWidget.rowCount()))
    #     # all_columns.remove(column)
    #
    #     state = self.tableWidget.item(row, column).checkState()
    #     for i in range(self.tableWidget.columnCount()):
    #         item = self.tableWidget.item(row, i)
    #         if state == QtCore.Qt.Checked:
    #             item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
    #         else:
    #             item.setFlags(item.flags() & ~QtCore.Qt.ItemIsUserCheckable)

    def turnOffClicked(self, row, column):
        state = self.tableWidget.item(row, column).checkState()

        all_columns = list(range(self.tableWidget.columnCount()))
        all_columns.remove(column)

        for i in all_columns:
            item = self.tableWidget.item(row, i)
            if state == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)
                # item.setCheckState(QtCore.Qt.Checked)
            # else:
                # item.setCheckState(QtCore.Qt.Unchecked)
                # item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)

    @QtCore.pyqtSlot()
    def save_clicked(self):
        items = []
        for i in range(1, self.tableWidget.rowCount()):
            it = []
            for j in range(0, self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                it.append(item.checkState())
            items.append(it)

        self.df_input_output.loc[:, :] = items

    def getDataframe(self):
        # Use this method to retrieve the dataframe
        return self.df_input_output

    def setDataframe(self, df):
        self.input_table = df

    def getInputFeature(self):
        return list(self.df_input_output[self.df_input_output['input'] > 0].index)

    def getOutputFeature(self):
        return list(self.df_input_output[self.df_input_output['output'] > 0].index)

    def saveState(self):
        self.state = []
        for i in range(self.tableWidget.rowCount()):
            it = []
            for j in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                it.append(item.checkState())
            self.state.append(it)

    def initState(self):
        return [[QtCore.Qt.Unchecked] * 2] * self.tableWidget.rowCount()

    def getState(self):
        return self.state


