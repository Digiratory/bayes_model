from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow

import pandas as pd


def read_data(path='data/tmp.csv'):
    data_input = pd.read_csv(path, index_col=0)
    return data_input


class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        col_name = read_data().columns
        self.result_df = pd.DataFrame(columns=col_name, index=col_name)
        col_name = col_name.insert(0, 'Select ALL')
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), len(col_name))
        self.save_button = QtWidgets.QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_clicked)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tableWidget)
        lay.addWidget(self.save_button)

        self.tableWidget.setHorizontalHeaderLabels(col_name)
        self.tableWidget.setVerticalHeaderLabels(col_name)

        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget.setItem(i, j, item)

        # self.tableWidget.cellChanged.connect(self.select_all_clicked)

        self.tableWidget.cellChanged.connect(self.select_all_clicked_by_columns)
        self.tableWidget.cellChanged.connect(self.select_all_clicked_by_rows)

    def select_all_clicked_by_columns(self, row, column):
        if row != 0:
            return 0
        state = self.tableWidget.item(0, column).checkState()
        # state = self.tableWidget.state()
        print(state)
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

    @QtCore.pyqtSlot()
    def save_clicked(self):
        items = []
        for i in range(1, self.tableWidget.rowCount()):
            it = []
            for j in range(1, self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                it.append(item.checkState())
            items.append(it)

        self.result_df.loc[:, :] = items
        self.result_df.to_excel('data/link_table.xls')


class RealMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(RealMainWindow, self).__init__(parent)
        self.setWindowTitle("QTableView Example")
        self.resize(2000, 1000)

        w = Widget()
        self.setCentralWidget(w)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = RealMainWindow()
    win.show()
    sys.exit(app.exec_())