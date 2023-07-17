import pandas as pd 
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5 import QtCore, QtWidgets, QtGui
from utils import get_index_outliers



class JointGridWidget(FigureCanvas):

    def __init__(self, parent=None, dpi=100, initial_message=None):
        fig,ax = plt.subplots()
        #fig = Figure(figsize=(5, 5), dpi=dpi, tight_layout=True)
        #self.fig = plt.figure()
        #self.axes = plt.Axes()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        #FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        #self.updateGeometry()
        palette = self.palette()
        self.setContentsMargins(0,0,0,0)
        #fig.set_facecolor(palette.Background().color().getRgbF()[0:3])
        self.axes = ax


    def make_plot(self, data,x_name,z_name, outcome):
        sns.set_style("darkgrid")
        plt.sca(self.axes)
        plt.clf()
        pg=sns.lmplot(x_name, outcome, data, hue=z_name)
        #ax = plt.gca()
        #ax.legend(numpoints=1, fancybox=True, fontsize="small", )
        #self.axes.get_legend().draggable(True, update="loc")
        fig = pg.fig
        fig.set_canvas(self)
        self.figure = fig
        fig = self.figure
        palette = self.palette()
        #fig.set_facecolor(palette.Background().color().getRgbF()[0:3])

        plt.show()
        self.draw()
        self.resize_event()
        self.draw()

class jointgridWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, data=None,):
        super(jointgridWindow, self).__init__(parent)

        self.data = data
        col_name = self.data.columns
        self.df_select = pd.DataFrame(columns=['select'], index=col_name)
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 1)
        self.build_button = QtWidgets.QPushButton("Построить")

        #self.canvas = FigureCanvas(self.g.fig)
        #self.g = self.fig.add_subplot(111)

        plot_layout = QtWidgets.QVBoxLayout()
        #plot_layout.addWidget(self.canvas)

        select_layout = QtWidgets.QVBoxLayout(self)
        select_layout.addWidget(self.tableWidget)
        select_layout.addWidget(self.build_button)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(plot_layout)
        main_layout.addLayout(select_layout)

        self.selected_items = []
        self.selected_items_names = []
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

        self.show()

    def turnOffClicked(self, row, column):
        item = self.tableWidget.item(row, column)
        item_name = self.tableWidget.verticalHeaderItem(row).text()
        if item.checkState() == QtCore.Qt.Checked:
            self.selected_items.append(item)
            self.selected_items_names.append(item_name)
            if len(self.selected_items) > self.num_of_selected_items:
                for item_ in self.selected_items[:-self.num_of_selected_items]:
                    self.selected_items.pop(0)
                    self.selected_items_names.pop(0)
                    item_.setCheckState(QtCore.Qt.Unchecked)
        elif item.checkState() == QtCore.Qt.Unchecked and item in self.selected_items:
            delete_index=self.selected_items.index(item)
            self.selected_items.pop(delete_index)
            self.selected_items_names.pop(delete_index)


    def on_pushButton_clicked(self):
        if len(self.selected_items) == self.num_of_selected_items:
            df = self.data
            df = df.replace('[^0-9]+', np.nan, regex=True)
            df = df.astype(float)
            column_name1 = self.selected_items_names[0]
            column_name2 = self.selected_items_names[1]
            df_without_nan = df.dropna(subset=[column_name1, column_name2])
            outliers_index = get_index_outliers(df_without_nan[[column_name1, column_name2]])

            df_outliers = df_without_nan.loc[outliers_index]
            df_without_outliers = df_without_nan.drop(outliers_index)

            r, _ = stats.pearsonr(df_without_nan[column_name1], df_without_nan[column_name2])
            r_w, _ = stats.pearsonr(df_without_outliers[column_name1], df_without_outliers[column_name2])
            x, y = df_without_outliers[column_name1], df_without_outliers[column_name2]
            x_outlier, y_outlier = df_outliers[column_name1], df_outliers[column_name2]

            g = sns.JointGrid()
            g.fig.set_size_inches((8, 8))
            sns.scatterplot(x=x, y=y, s=100, linewidth=1.5, ax=g.ax_joint, color='b')
            sns.scatterplot(x=x_outlier, y=y_outlier, s=100, linewidth=1.5, ax=g.ax_joint, color='r')

            sns.regplot(x=df_without_nan[column_name1], y=df_without_nan[column_name2],
                        ax=g.ax_joint, color='r', scatter=False, line_kws={'linewidth': 1})
            sns.regplot(x=x, y=y, ax=g.ax_joint, color='black', scatter=False)
            g.ax_marg_x.set_xlim(0)
            sns.kdeplot(y=y, linewidth=2, ax=g.ax_marg_y)
            sns.kdeplot(x=x, linewidth=2, ax=g.ax_marg_x)
            g.ax_joint.annotate(f'$R = {r:.3f}$ - все точки',
                                xy=(0.1, 0.9), xycoords='axes fraction',
                                ha='left', va='center',
                                color='red',
                                bbox={'boxstyle': 'round', 'fc': 'powderblue', 'ec': 'navy'})

            g.ax_joint.annotate(f'$R = {r_w:.3f}$ - после удаления выбросов',
                                xy=(0.1, 0.95), xycoords='axes fraction',
                                ha='left', va='center',
                                bbox={'boxstyle': 'round', 'fc': 'powderblue', 'ec': 'navy'})
            plt.show()

