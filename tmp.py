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
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), len(col_name))
        self.book_button = QtWidgets.QPushButton("Book")
        self.book_button.clicked.connect(self.book_clicked)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tableWidget)
        lay.addWidget(self.book_button)

        self.tableWidget.setHorizontalHeaderLabels(col_name)
        self.tableWidget.setVerticalHeaderLabels(col_name)
        b = 0
        for i in range(0, self.tableWidget.rowCount()):
            for j in range(0, self.tableWidget.columnCount()):
                if b==0:

                    b = 1
                    break
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                # item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget.setItem(i, j, item)

        self.header_checkbox = QtWidgets.QCheckBox()
        self.tableWidget.setCellWidget(0, 0, self.header_checkbox)
        self.header_checkbox.stateChanged.connect(self.select_all_changed)

        # if self.tableWidget.item(0, 0).checkState():
        #     self.tableWidget.item(0, 1).setCheckState(1)

    def select_all_changed(self, state):
        for i in range(self.tableWidget.rowCount()):
            item = self.tableWidget.cellWidget(i, 0)
            if item is not None:
                item.setChecked(state == QtCore.Qt.Checked)

    @QtCore.pyqtSlot()
    def book_clicked(self):
        items = []
        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                if item.checkState() == QtCore.Qt.Checked:
                    items.append(item)

        for it in items:
            r = it.row()
            c = it.column()
            v, h = self.tableWidget.horizontalHeaderItem(c).text(), self.tableWidget.verticalHeaderItem(r).text()
            print(h, v)


class RealMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QTableView Example")
        self.resize(415, 200)

        w = Widget()
        w.show()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = Widget()
    w.resize(2000, 1000)
    w.show()
    # win = RealMainWindow()

    sys.exit(app.exec_())