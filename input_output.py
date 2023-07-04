import pandas as pd
from PyQt5 import QtCore, QtWidgets


def read_data(path='data/tmp.csv'):
    data_input = pd.read_csv(path, index_col=0)
    return data_input


class IOWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, input_df=None):
        super(IOWindow, self).__init__(parent)
        # mainwindow.setWindowIcon(QtGui.QIcon('PhotoIcon.png'))
        self.ToolsBTN = QtWidgets.QPushButton('Далее', self)
        # self.ToolsBTN.move(50, 350)

        self.input_table = input_df

        col_name = self.input_table.columns

        self.df_input_output = pd.DataFrame(columns=['input', 'output'], index=col_name)
        col_name = col_name.insert(0, 'Select ALL')

        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 2)
        self.save_button = QtWidgets.QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_clicked)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tableWidget)
        lay.addWidget(self.save_button)
        lay.addWidget(self.ToolsBTN)

        self.tableWidget.setHorizontalHeaderLabels(['input', 'output'])
        self.tableWidget.setVerticalHeaderLabels(col_name)

        for i in range(self.tableWidget.rowCount()):
            for j in range(2):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.cellChanged.connect(self.select_all_clicked_by_columns)

    def select_all_clicked_by_columns(self, row, column):
        if row != 0:
            return 0
        state = self.tableWidget.item(0, column).checkState()
        # state = self.tableWidget.state()
        print(state)
        for i in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(i, column)
            item.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

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