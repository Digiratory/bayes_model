from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout

import pandas as pd


def read_data(path='data/tmp.csv'):
    data_input = pd.read_csv(path, index_col=0)
    return data_input


class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        col_name = read_data().columns
        self.result_df = pd.DataFrame(columns=col_name, index=['input', 'output'])
        col_name = col_name.insert(0, 'Select ALL')
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 2)
        self.book_button = QtWidgets.QPushButton("Book")
        self.book_button.clicked.connect(self.book_clicked)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tableWidget)
        lay.addWidget(self.book_button)

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
    def book_clicked(self):
        items = []
        for i in range(1, self.tableWidget.rowCount()):
            it = []
            for j in range(1, self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                it.append(item.checkState())
            items.append(it)

        self.result_df.loc[:, :] = items
        self.result_df.to_excel('data/link_table.xls')


class PageWindow(QtWidgets.QMainWindow):
    gotoSignal = QtCore.pyqtSignal(str)

    def goto(self, name):
        self.gotoSignal.emit(name)


class MainWindow(PageWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MainWindow")
        self.resize(2000, 1000)

        # self.initUI()

        col_name = read_data().columns
        self.result_df = pd.DataFrame(columns=col_name, index=['input', 'output'])
        col_name = col_name.insert(0, 'Select ALL')
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 2)
        self.book_button = QtWidgets.QPushButton("Book")
        self.book_button.clicked.connect(self.book_clicked)

        self.searchButton = QtWidgets.QPushButton("ОК", self)
        self.searchButton.clicked.connect(
            self.make_handleButton("searchButton"))

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tableWidget)
        lay.addWidget(self.book_button)
        lay.addWidget(self.searchButton)

        self.tableWidget.setHorizontalHeaderLabels(['input', 'output'])
        self.tableWidget.setVerticalHeaderLabels(col_name)

        for i in range(self.tableWidget.rowCount()):
            for j in range(2):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.cellChanged.connect(self.select_all_clicked_by_columns)


    def make_handleButton(self, button):
        def handleButton():
            if button == "searchButton":
                self.goto("search")
        return handleButton


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
    def book_clicked(self):
        items = []
        for i in range(1, self.tableWidget.rowCount()):
            it = []
            for j in range(1, self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                it.append(item.checkState())
            items.append(it)

        self.result_df.loc[:, :] = items
        self.result_df.to_excel('data/link_table.xls')


class SearchWindow(PageWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Search for something")
        self.UiComponents()

    def goToMain(self):
        self.goto("main")

    def UiComponents(self):
        self.backButton = QtWidgets.QPushButton("BackButton", self)
        self.backButton.setGeometry(QtCore.QRect(5, 5, 100, 20))
        self.backButton.clicked.connect(self.goToMain)


class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.m_pages = {}

        self.register(MainWindow(), "main")
        self.register(SearchWindow(), "search")

        self.goto("main")

    def register(self, widget, name):
        self.m_pages[name] = widget
        self.stacked_widget.addWidget(widget)
        if isinstance(widget, PageWindow):
            widget.gotoSignal.connect(self.goto)

    @QtCore.pyqtSlot(str)
    def goto(self, name):
        if name in self.m_pages:
            widget = self.m_pages[name]
            self.stacked_widget.setCurrentWidget(widget)
            self.setWindowTitle(widget.windowTitle())


if __name__ == "__main__":


    app = QtWidgets.QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec_())