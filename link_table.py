from PyQt5 import QtCore, QtWidgets
import pandas as pd


class LinkTabWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, input_df=None):
        """
        Для матрицы связей
        :param parent:
        :param input_df:
        """
        super(LinkTabWindow, self).__init__(parent)
        self.CPSBTN = QtWidgets.QPushButton("Назад", self)
        self.CPSBTN.move(100, 350)

        self.NextBTN = QtWidgets.QPushButton("Вперед", self)
        self.NextBTN.move(100, 350)

        self.input_df = input_df
        col_name = input_df.columns
        self.result_df = pd.DataFrame(columns=col_name, index=col_name)

        col_name = col_name.insert(0, 'Select ALL')
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), len(col_name))
        self.save_button = QtWidgets.QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_clicked)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tableWidget)
        lay.addWidget(self.save_button)
        lay.addWidget(self.CPSBTN)
        lay.addWidget(self.NextBTN)

        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_widget.setLayout(buttons_layout)
        buttons_layout.addWidget(self.CPSBTN)
        buttons_layout.addWidget(self.NextBTN)
        lay.addWidget(buttons_widget)

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
        self.result_df = self.result_df.replace({2: 1})
        self.result_df.to_excel('data/link_table.xls')

    def getDataFrame(self) -> pd.DataFrame:
        return self.result_df

