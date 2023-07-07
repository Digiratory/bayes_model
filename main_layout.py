from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QBoxLayout
from PyQt5.QtCore import Qt
import sys
from PyQt5 import QtWidgets
from input_output import IOWindow
from link_table import LinkTabWindow
import pandas as pd
from button_page import ButtonWindow
from utils import find_zero_columns


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)
        # self.setGeometry(50, 50, 400, 450)
        # self.setFixedSize(400, 450)
        # self.startUIToolTab()
        self.resize(2000, 1000)
        self.input_feature = None
        self.output_feature = None
        self.stateIO = None
        self.linkTable = None

        self.setWindowTitle("Bayes inference")

        widget_layout = QBoxLayout(QBoxLayout.RightToLeft)

        # общая панель справа
        self.BWindow = ButtonWindow(self, pd.DataFrame(), pd.DataFrame(), 1)
        # self.BWindow.corr_button.clicked.connect(self.update)
        widget_layout.addWidget(self.BWindow)

        # self.resize(2000, 1000)
        self.stk_w = QStackedWidget(self)

        self.Window = IOWindow(self,
                               input_df=self.getInitialDataframe(),
                               state=self.getStateIO())
        self.Window.save_button.clicked.connect(self.update)
        self.Window.ToolsBTN.clicked.connect(self.updateStateIO)
        # self.Window.ToolsBTN.clicked.connect(self.startUIToolTab)

        self.stk_w.addWidget(self.Window)

        self.ToolTab = LinkTabWindow(self, input_df=pd.DataFrame({"1": [0, 0], "2": [0, 0]}))
        self.ToolTab.BackBTN.clicked.connect(self.startUIWindow)
        self.ToolTab.save_button.clicked.connect(self.updateLinkTable)
        self.ToolTab.save_button.clicked.connect(self.tmp)
        self.stk_w.addWidget(self.ToolTab)

        widget_layout.addWidget(self.stk_w)
        self.setLayout(widget_layout)

        # self.ToolTab.save_button.clicked.connect(self.BWindow.updateLenInputFeature(self.input_feature))
        # self.ToolTab.save_button.clicked.connect(self.BWindow.updateDataFrame(self.getDataFrame()))
        # self.ToolTab.save_button.clicked.connect(self.BWindow.updateLinkTable(self.getLinkTable()))


    def startUIWindow(self):
        self.stk_w.setCurrentWidget(self.Window)
        self.ToolTab.removeTableWidget()

    # def startUIToolTab(self):
    #     self.ToolTab = LinkTabWindow(self, self.getDataFrame())
    #     self.resize(2000, 1000)
    #     self.setWindowTitle("Связи")
    #     self.setCentralWidget(self.ToolTab)
    #     self.ToolTab.CPSBTN.clicked.connect(self.startUIWindow)
    #     self.ToolTab.NextBTN.clicked.connect(self.startButtonWindow)
    #     # self.ToolTab.CPSBTN.clicked.connect(self.startUIWindow)
    #     self.show()
    #
    # def startButtonWindow(self):
    #     self.updateLinkTable()
    #     self.BWindow = ButtonWindow(self, self.getDataFrame(),
    #                                 self.getLinkTable(),
    #                                 len(self.input_feature))
    #     self.setWindowTitle("Кнопки")
    #     self.setCentralWidget(self.BWindow)
    #     self.BWindow.PreviousBTN.clicked.connect(self.startUIToolTab)
    #     # self.BWindow.ToolsBTN.clicked.connect(self.startUIToolTab)
    #     self.show()

    def update(self):
        self.updateFeaturesList(self.Window.getInputFeature(), self.Window.getOutputFeature())

    def getInitialDataframe(self, path='data/tmp2.csv'):
        data_input = pd.read_csv(path, index_col=0)
        nan_columns = find_zero_columns(data_input)
        data_input = data_input.drop(nan_columns, axis=1)
        return data_input

    def updateFeaturesList(self, input_features, output_features):
        self.input_feature = input_features
        self.output_feature = output_features
        # print(self.input_feature)
        # print(self.output_feature)

    def getDataFrame(self):
        df = self.getInitialDataframe()
        df = df.loc[:, self.input_feature + self.output_feature]
        return df

    def updateLinkTable(self):
        self.linkTable = self.ToolTab.getDataFrame()

    def getLinkTable(self):
        return self.linkTable

    def getStateIO(self):
        return self.stateIO

    def updateStateIO(self):
        self.stateIO = self.Window.getState()

        self.ToolTab.updateInput(self.getDataFrame())
        # self.stk_w.setCurrentIndex(1)
        self.ToolTab.update()
        self.stk_w.setCurrentWidget(self.ToolTab)

    def tmp(self):
        self.BWindow.updateDataFrame(self.getDataFrame())
        self.BWindow.updateLinkTable(self.getLinkTable())
        self.BWindow.updateLenInputFeature(len(self.input_feature))
        self.BWindow.update()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
