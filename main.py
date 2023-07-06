import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from input_output import IOWindow
from link_table import LinkTabWindow
import pandas as pd
from button_page import ButtonWindow
from utils import find_zero_columns


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # self.setGeometry(50, 50, 400, 450)
        # self.setFixedSize(400, 450)
        # self.startUIToolTab()
        self.input_feature = None
        self.output_feature = None
        self.stateIO = None
        self.linkTable = None

        self.startUIWindow()
        # self.resize(2000, 1000)

    def startUIWindow(self):
        self.Window = IOWindow(self,
                               input_df=self.getInitialDataframe(),
                               state=self.getStateIO())

        # self.setGeometry(50, 50, 400, 450)
        self.resize(600, 1000)
        self.setWindowTitle("Вход-выход")
        self.setCentralWidget(self.Window)
        self.Window.save_button.clicked.connect(self.update)
        self.Window.ToolsBTN.clicked.connect(self.updateStateIO)
        self.Window.ToolsBTN.clicked.connect(self.startUIToolTab)

        self.show()

    def startUIToolTab(self):
        self.ToolTab = LinkTabWindow(self, self.getDataFrame())
        self.resize(2000, 1000)
        self.setWindowTitle("Связи")
        self.setCentralWidget(self.ToolTab)
        self.ToolTab.CPSBTN.clicked.connect(self.startUIWindow)
        self.ToolTab.NextBTN.clicked.connect(self.startButtonWindow)
        # self.ToolTab.CPSBTN.clicked.connect(self.startUIWindow)
        self.show()

    def startButtonWindow(self):
        self.updateLinkTable()
        self.BWindow = ButtonWindow(self, self.getDataFrame(),
                                    self.getLinkTable(),
                                    len(self.input_feature))
        self.setWindowTitle("Кнопки")
        self.setCentralWidget(self.BWindow)
        self.BWindow.PreviousBTN.clicked.connect(self.startUIToolTab)
        # self.BWindow.ToolsBTN.clicked.connect(self.startUIToolTab)
        self.show()

    def update(self):
        self.updateFeaturesList(self.Window.getInputFeature(), self.Window.getOutputFeature())

    def getInitialDataframe(self, path='data/tmp.csv'):
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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
