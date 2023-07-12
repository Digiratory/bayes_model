import pandas as pd 
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import  QDialog


class jointgridWindow(QtWidgets.QWidget):
    def __init__(self, data=None, parent=None, input_df=None):
        super(jointgridWindow, self).__init__(parent)

        self.input_table = input_df
        self.data=data
        col_name = self.input_table.columns
        self.df_select = pd.DataFrame(columns=['select'], index=col_name)
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 1)
        self.build_button = QtWidgets.QPushButton("Построить")

        self.fig = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.fig)
        self.g = self.fig.add_subplot(111)


        plot_layout = QtWidgets.QVBoxLayout()
        plot_layout.addWidget(self.canvas)

        select_layout = QtWidgets.QVBoxLayout(self)
        select_layout.addWidget(self.tableWidget)
        select_layout.addWidget(self.build_button)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(plot_layout)
        main_layout.addLayout(select_layout)

        self.selected_items = []
        self.num_of_selected_items=2
        

        self.tableWidget.setHorizontalHeaderLabels(['select'])
        self.tableWidget.setVerticalHeaderLabels(col_name)
        for i in range(self.tableWidget.rowCount()):
            for j in range(2):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                #item.setCheckState(self.state[i][j])
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.cellChanged.connect(self.turnOffClicked)
        self.build_button.clicked.connect(self.on_pushButton_clicked)



    def turnOffClicked(self, row, column):
        item = self.tableWidget.item(row, column)
        if item.checkState() == QtCore.Qt.Checked:
            self.selected_items.append(item)
            if len(self.selected_items) > self.num_of_selected_items:
                for item_ in self.selected_items[:-self.num_of_selected_items]:
                    self.selected_items.pop(0)
                    item_.setCheckState(QtCore.Qt.Unchecked)
        elif item.checkState() == QtCore.Qt.Unchecked and item in self.selected_items:
            self.selected_items.pop(self.selected_items.index(item))


    def on_pushButton_clicked(self):
        #if len(self.selected_items)==self.num_of_selected_items:
        df = pd.read_csv('data/tmp2.csv')
        df = df.replace('[^0-9]+', np.nan, regex=True)
        df = df.astype(float)
        column_name1 = "PTA right 4000Hz AC"
        column_name2 = "PTA right 2000Hz AC"
        df_without_nan = df.dropna(subset=[column_name1, column_name2])
        r, _ = stats.pearsonr(df_without_nan[column_name1], df_without_nan[column_name2])
        x, y = df[column_name1], df[column_name2]
        self.g = sns.JointGrid()
        sns.scatterplot(x=x, y=y, s=100, linewidth=1.5, ax=self.g.ax_joint)
        sns.regplot(x=x, y=y, ax=self.g.ax_joint)
        self.g.ax_marg_x.set_xlim(0)
        sns.kdeplot(y=y, linewidth=2, ax=self.g.ax_marg_y)
        sns.kdeplot(x=x, linewidth=2, ax=self.g.ax_marg_x)
        self.g.ax_joint.annotate(f'$R = {r:.3f}$',
                            xy=(0.1, 0.9), xycoords='axes fraction',
                            ha='left', va='center',
                            bbox={'boxstyle': 'round', 'fc': 'powderblue', 'ec': 'navy'})

    def getDataframe(self):
        # Use this method to retrieve the dataframe
        return self.df_select
    
    