import os
import sys

import numpy as np
import pandas as pd
from button_page import ButtonWindow
from input_output import IOWindow
from jointgrid import jointgridWindow
from link_table import LinkTabWindow
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from bn_modeller.bayesian_nets.utils import check_non_select_table, find_zero_columns


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = "Bayes model"
        self.left = 0
        self.top = 0
        self.width = 1500
        self.height = 1000
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()

    def closeEvent(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()


class MyTableWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.pathIOFile = "data/io_table.csv"
        self.pathLinkFile = "data/link_table.xlsx"
        self.pathInputFile = "data/data_2.csv"

        self.input_feature = None
        self.output_feature = None
        self.lenCheck = len(pd.read_csv(self.pathInputFile, index_col=0).columns)
        self.stateIO = self.initStateIO()
        self.stateLink = self.initStateLinkTable()
        self.linkTable = None
        self.stateJointplot = None

        self.setWindowTitle("Bayes inference")

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)

        # Initialize Widgets for tabs
        self.ioTab = IOWindow(
            self, input_df=self.getInitialDataframe(), state=self.getStateIO()
        )
        self.update()

        self.linkTab = LinkTabWindow(
            self, input_df=self.getDataFrame(), state=self.stateLink
        )

        self.buttonTab = ButtonWindow(self, pd.DataFrame(), pd.DataFrame(), 1)
        self.buttonTab.acycle_button.clicked.connect(self.updateLinkTableFromAcyclic)

        self.jointgridTab = jointgridWindow(
            self,
            data=self.getInitialDataframe(),
            predicted_data=self.buttonTab.getPrediction(),
        )

        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.ioTab, "Input-Output")
        self.tabs.addTab(self.linkTab, "Links")
        self.tabs.addTab(self.buttonTab, "Calculation")
        self.tabs.addTab(self.jointgridTab, "Plot")
        self.tabs.currentChanged.connect(self.on_click)  # changed!
        self.ioTab.block_signal.connect(self.blockButtonTab)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    @Slot()
    def on_click(self):
        """
        action between tabs
        """
        index = self.tabs.currentIndex()
        if index == 0:
            # print("Switched to Tab 1")
            return 1

        elif index == 1:
            self.blockButtonTab()

        elif index == 2:

            self.linkTab.save_clicked()
            self.updateStateLink()
            self.updateLinkTable()

            # проверить выделены ли хоть какие-то связи

            if check_non_select_table(self.linkTable):
                self.buttonTab.acycle_button.setEnabled(False)
                self.buttonTab.rankCorrButton.setEnabled(False)
                self.buttonTab.calcInferenceButton.setEnabled(False)
            else:
                self.buttonTab.acycle_button.setEnabled(True)
            self.tmp()

        elif index == 3:
            self.jointgridTab.removeTableWidget()
            self.jointgridTab.updateData(self.buttonTab.getPrediction())

    @Slot()
    def blockButtonTab(self):
        self.ioTab.save_clicked()
        self.ioTab.saveState()
        self.update()
        self.updateStateIO()

        if self.stateIO is None:
            self.tabs.setTabEnabled(2, False)
        else:
            # the value of each tick is 2
            # in order for the calculations tab to be opened, you need to click at least 2 "in" and 1 "out" checkboxes
            if (
                sum([i[0].value for i in self.stateIO]) >= 4
                and sum([i[1].value for i in self.stateIO]) >= 2
            ):
                self.tabs.setTabEnabled(2, True)
            else:
                self.tabs.setTabEnabled(2, False)

    @Slot()
    def update(self):
        self.updateFeaturesList(
            self.ioTab.getInputFeature(), self.ioTab.getOutputFeature()
        )

    def getInitialDataframe(self):
        data_input = pd.read_csv(self.pathInputFile, index_col=0)
        # add_quotes = lambda x: f'"{x}"'
        # data_input.columns = list(map(add_quotes, data_input.columns))
        data_input = data_input.replace("[^0-9]+", np.nan, regex=True)
        data_input = data_input.astype(float)
        nan_columns = find_zero_columns(data_input)
        data_input = data_input.drop(nan_columns, axis=1)
        # if not self.input_feature is None:
        #     data_input = data_input.loc[:, self.input_feature + self.output_feature]
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

    def updateLinkTableFromAcyclic(self):
        if self.buttonTab.updLinkTable is not None:
            self.linkTable = self.buttonTab.getNewLinkTab()
        self.stateLink = self.linkTable.values
        self.linkTab.removeTableWidget()
        self.linkTab.updateInput(self.getDataFrame(), self.getStateLink())

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
        if set(self.linkTab.getColumnNames()) != set(
            self.input_feature + self.output_feature
        ):
            self.linkTab.removeTableWidget()
            self.linkTab.updateInput(self.getDataFrame(), self.getStateLink())
        self.saveStateIO()

    def saveStateIO(self):
        df = pd.DataFrame(
            columns=["input", "output"],
            index=["Select ALL"] + list(self.getInitialDataframe().columns),
            data=self.stateIO,
        )
        df.to_csv(self.pathIOFile)

    def initStateIO(self):
        if os.path.exists(self.pathIOFile):
            df = pd.read_csv(self.pathIOFile, index_col=0)
            if self.lenCheck != len(df.index):
                return None
            return df.values
        else:
            return None

    def initStateLinkTable(self):
        if os.path.exists(self.pathLinkFile):
            df = pd.read_excel(self.pathLinkFile, index_col=0)
            # print(self.stateIO.)
            # # df.insert(loc=0, column='Select All', value=[0]*len(df))
            # if self.lenCheck != len(df.columns):
            #     return None
            return df.values
        else:
            return None

    def updateStateLink(self):
        self.stateLink = self.linkTab.state

    def tmp(self):
        self.buttonTab.updateDataFrame(self.getDataFrame())
        self.buttonTab.updateLinkTable(self.getLinkTable())
        self.buttonTab.updateLenInputFeature(len(self.input_feature))
        self.buttonTab.updateMatrix()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
