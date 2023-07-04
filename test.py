import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from input_output import IOWindow
from link_table import LinkTabWindow
import pandas as pd


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # self.setGeometry(50, 50, 400, 450)
        # self.setFixedSize(400, 450)
        # self.startUIToolTab()
        self.startUIWindow()
        self.resize(2000, 1000)
        self.input_feature = None
        self.output_feature = None

    def startUIToolTab(self):
        self.ToolTab = LinkTabWindow(self, self.getDataFrame())
        self.setWindowTitle("Связи")
        self.setCentralWidget(self.ToolTab)
        self.ToolTab.CPSBTN.clicked.connect(self.startUIWindow)
        self.show()

    def startUIWindow(self):
        self.Window = IOWindow(self, self.getInitialDataframe())
        self.setWindowTitle("Вход-выход")
        self.setCentralWidget(self.Window)
        self.Window.save_button.clicked.connect(self.update)
        self.Window.ToolsBTN.clicked.connect(self.startUIToolTab)

        self.show()
    def update(self):
        self.updateFeaturesList(self.Window.getInputFeature(), self.Window.getOutputFeature())

    def getInitialDataframe(self, path='data/tmp.csv'):
        data_input = pd.read_csv(path, index_col=0)
        return data_input

    def updateDataframe(self, new_df):
        # This method can be called from IOWindow to update the dataframe in MainWindow
        print("Updated dataframe:", new_df)

    def updateFeaturesList(self, input_features, output_features):
        self.input_feature = input_features
        self.output_feature = output_features
        print(self.input_feature)
        print(self.output_feature)
    def getDataFrame(self):
        df = self.getInitialDataframe()
        print(df)
        print(self.input_feature, self.output_feature)
        df = df.loc[:, self.input_feature + self.output_feature]
        print(df)
        return df


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
