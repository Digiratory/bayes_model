from PyQt5.QtWidgets import QMainWindow, QApplication, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget
import sys
from input_output import IOWindow
from jointgrid import jointgridWindow
from link_table import LinkTabWindow
import pandas as pd
from button_page import ButtonWindow
from utils import find_zero_columns
import numpy as np


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Bayes model'
        self.left = 0
        self.top = 0
        self.width = 1500
        self.height = 1000
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()


class MyTableWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        self.input_feature = None
        self.output_feature = None
        self.stateIO = None
        self.stateLink = None
        self.linkTable = None
        self.stateJointplot = None

        self.setWindowTitle("Bayes inference")

        # Initialize tab screen
        self.tabs = QTabWidget()

        self.ioTab = IOWindow(self,
                              input_df=self.getInitialDataframe(),
                              state=self.getStateIO())

        self.linkTab = LinkTabWindow(self, input_df=pd.DataFrame({"1": [0, 0], "2": [0, 0]}))

        self.buttonTab = ButtonWindow(self, pd.DataFrame(), pd.DataFrame(), 1)

        self.jointgridTab = jointgridWindow(self,
                              input_df=self.getInitialDataframe())

        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.ioTab, "Вход-выход")
        self.tabs.addTab(self.linkTab, "Связи")
        self.tabs.addTab(self.buttonTab, "Расчеты")
        self.tabs.addTab(self.jointgridTab, "График двух переменных")
        self.tabs.currentChanged.connect(self.on_click)  # changed!

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    @pyqtSlot()
    def on_click(self):
        index = self.tabs.currentIndex()
        if index == 0:
            # print("Switched to Tab 1")
            return 1
            # Perform actions specific to Tab 1

        elif index == 1:
            self.ioTab.save_clicked()
            self.ioTab.saveState()
            self.update()
            self.updateStateIO()
            # Perform actions specific to Tab 2

        elif index == 2:
            self.linkTab.save_clicked()
            self.updateStateLink()
            self.updateLinkTable()
            self.tmp()

        elif index == 3:
            pass

    def update(self):
        self.updateFeaturesList(self.ioTab.getInputFeature(), self.ioTab.getOutputFeature())

    def getInitialDataframe(self, path='data/tmp2.csv'):
        data_input = pd.read_csv(path, index_col=0)
        data_input = data_input.replace('[^0-9]+', np.nan, regex=True)
        data_input = data_input.astype(float)
        nan_columns = find_zero_columns(data_input)
        data_input = data_input.drop(nan_columns, axis=1)
        return data_input

    def updateFeaturesList(self, input_features, output_features):
        self.input_feature = input_features
        self.output_feature = output_features

    def getDataFrame(self):
        df = self.getInitialDataframe()
        df = df.loc[:, self.input_feature + self.output_feature]
        return df

    def updateLinkTable(self):
        self.linkTable = self.linkTab.getDataFrame()

    def getLinkTable(self):
        return self.linkTable

    def getStateIO(self):
        return self.stateIO
    
    def getStateJointplot(self):
        return self.stateJointplot

    def getStateLink(self):
        return self.stateLink

    def updateStateIO(self):
        self.stateIO = self.ioTab.getState()
        if set(self.linkTab.getColumnNames()) != set(self.input_feature + self.output_feature):
            self.linkTab.removeTableWidget()
            self.linkTab.updateInput(self.getDataFrame(), self.getStateLink())

    def updateStateLink(self):
        self.stateLink = self.linkTab.state

    def tmp(self):
        self.buttonTab.updateDataFrame(self.getDataFrame())
        self.buttonTab.updateLinkTable(self.getLinkTable())
        self.buttonTab.updateLenInputFeature(len(self.input_feature))
        self.buttonTab.updateMatrix()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
