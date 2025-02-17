import pandas as pd
import scipy.stats as stats
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6 import QtCore, QtWidgets

from bn_modeller.bayesian_nets.utils import get_index_outliers, get_outliers_cooks


class JointPlot(QtWidgets.QMainWindow):

    def __init__(
        self,
        parent=None,
        x=None,
        y=None,
        x_outlier=None,
        y_outlier=None,
        df_without_nan=None,
        column_name1=None,
        column_name2=None,
        r=None,
        r_w=None,
    ):
        super(JointPlot, self).__init__(parent)

        # self.setWindowTitle('Матрица')

        self.main_widget = QtWidgets.QWidget(self)

        self.resize(600, 600)

        self.fig = Figure()

        self.fig = self.initFigure(
            x,
            y,
            x_outlier,
            y_outlier,
            df_without_nan,
            column_name1,
            column_name2,
            r,
            r_w,
        )

        self.canvas = FigureCanvas(self.fig)

        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.updateGeometry()
        # self.label = QtWidgets.QLabel("A plot:")
        toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtWidgets.QGridLayout(self.main_widget)
        self.layout.addWidget(toolbar)
        # self.layout.addWidget(self.label)
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self.main_widget)
        self.show()
        self.fig.tight_layout()

    def initFigure(
        self,
        x,
        y,
        x_outlier,
        y_outlier,
        df_without_nan,
        column_name1,
        column_name2,
        r,
        r_w,
    ):

        g = sns.JointGrid()
        # g.fig.set_size_inches((8, 8))
        g.ax_marg_x.set_xlim(left=min(x) - 1, right=max(x) + 1)

        sns.scatterplot(
            x=x, y=y, s=50, linewidth=0, ax=g.ax_joint, color="tab:blue", alpha=0.7
        )
        sns.scatterplot(
            x=x_outlier,
            y=y_outlier,
            s=50,
            linewidth=0,
            ax=g.ax_joint,
            color="tab:red",
            alpha=0.7,
        )

        sns.regplot(
            x=df_without_nan[column_name1],
            y=df_without_nan[column_name2],
            ax=g.ax_joint,
            color="r",
            scatter=False,
            line_kws={"linewidth": 1},
        )
        sns.regplot(x=x, y=y, ax=g.ax_joint, color="black", scatter=False)

        sns.kdeplot(y=y, linewidth=2, ax=g.ax_marg_y)
        sns.kdeplot(x=x, linewidth=2, ax=g.ax_marg_x)
        g.ax_joint.annotate(
            f"$R = {r:.3f}$ - все точки",
            xy=(0.1, 0.9),
            xycoords="axes fraction",
            ha="left",
            va="center",
            color="tab:red",
        )

        g.ax_joint.annotate(
            f"$R = {r_w:.3f}$ - без выбросов",
            xy=(0.1, 0.85),
            xycoords="axes fraction",
            ha="left",
            va="center",
            color="tab:blue",
        )
        return g.fig


class jointgridWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, data=None, predicted_data=pd.DataFrame()):
        super(jointgridWindow, self).__init__(parent)

        self.error_dialog = QtWidgets.QErrorMessage()

        self.df = data.join(predicted_data)
        col_name = self.df.columns

        self.df_select = pd.DataFrame(columns=["select"], index=col_name)
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 1)
        self.build_button = QtWidgets.QPushButton("Plot")

        # self.canvas = FigureCanvas(self.g.fig)
        # self.g = self.fig.add_subplot(111)

        plot_layout = QtWidgets.QVBoxLayout()
        # plot_layout.addWidget(self.canvas)

        self.select_layout = QtWidgets.QVBoxLayout(self)
        self.select_layout.addWidget(self.tableWidget)
        # self.select_layout.addWidget(self.build_button)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(plot_layout)
        main_layout.addLayout(self.select_layout)

        self.selected_items = []
        self.selected_items_names = []
        self.num_of_selected_items = 2

        self.tableWidget.setHorizontalHeaderLabels(["select"])
        self.tableWidget.setVerticalHeaderLabels(col_name)
        for i in range(self.tableWidget.rowCount()):
            for j in range(2):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                # item.setCheckState(self.state[i][j])
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.cellChanged.connect(self.turnOffClicked)
        self.build_button.clicked.connect(self.on_pushButton_clicked)
        #
        # self.show()
        self.dialogs = list()

    def turnOffClicked(self, row, column):
        item = self.tableWidget.item(row, column)
        item_name = self.tableWidget.verticalHeaderItem(row).text()
        if item.checkState() == QtCore.Qt.Checked:
            self.selected_items.append(item)
            self.selected_items_names.append(item_name)
            if len(self.selected_items) > self.num_of_selected_items:
                for item_ in self.selected_items[: -self.num_of_selected_items]:
                    self.selected_items.pop(0)
                    self.selected_items_names.pop(0)
                    item_.setCheckState(QtCore.Qt.Unchecked)
        elif item.checkState() == QtCore.Qt.Unchecked and item in self.selected_items:
            delete_index = self.selected_items.index(item)
            self.selected_items.pop(delete_index)
            self.selected_items_names.pop(delete_index)

    def updateData(self, df_predicted):

        if not set(df_predicted.columns).intersection(set(self.df.columns)):
            self.df = self.df.join(df_predicted)

        col_name = self.df.columns

        self.df_select = pd.DataFrame(columns=["select"], index=col_name)
        self.tableWidget = QtWidgets.QTableWidget(len(col_name), 1)
        # self.build_button = QtWidgets.QPushButton("Построить")
        #
        # plot_layout = QtWidgets.QVBoxLayout()
        # # plot_layout.addWidget(self.canvas)
        #
        # select_layout = QtWidgets.QVBoxLayout(self)
        self.select_layout.addWidget(self.tableWidget)
        self.select_layout.addWidget(self.build_button)
        #
        # main_layout = QtWidgets.QHBoxLayout()
        # main_layout.addLayout(plot_layout)
        # main_layout.addLayout(select_layout)
        #
        # self.selected_items = []
        # self.selected_items_names = []
        # self.num_of_selected_items = 2

        self.tableWidget.setHorizontalHeaderLabels(["select"])
        self.tableWidget.setVerticalHeaderLabels(col_name)
        for i in range(self.tableWidget.rowCount()):
            for j in range(2):
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                # item.setCheckState(self.state[i][j])
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.cellChanged.connect(self.turnOffClicked)
        # self.build_button.clicked.connect(self.on_pushButton_clicked)

        # self.show()

    def removeTableWidget(self):
        self.tableWidget.deleteLater()

    def on_pushButton_clicked(self):

        if len(self.selected_items) == self.num_of_selected_items:
            column_name1 = self.selected_items_names[0]
            column_name2 = self.selected_items_names[1]
            df_without_nan = self.df.dropna(subset=[column_name1, column_name2])

            if len(df_without_nan) < 2:
                self.error_dialog.showMessage("Not enough intersecting data")
                return 1

            # нахождение выбросов
            # outliers_index = get_index_outliers(df_without_nan[[column_name1, column_name2]])
            outliers_index = get_outliers_cooks(
                df_without_nan[[column_name1, column_name2]]
            )

            # датафрейм выбросов и без выбросов
            df_outliers = df_without_nan.loc[list(outliers_index)]
            df_without_outliers = df_without_nan.drop(outliers_index)

            # корреляция полного датафрейма и без выбросов
            r, _ = stats.pearsonr(
                df_without_nan[column_name1], df_without_nan[column_name2]
            )
            r_w, _ = stats.pearsonr(
                df_without_outliers[column_name1], df_without_outliers[column_name2]
            )

            # точки где нет выбросов, точки с выбросами
            x, y = df_without_outliers[column_name1], df_without_outliers[column_name2]
            x_outlier, y_outlier = df_outliers[column_name1], df_outliers[column_name2]

            dialog = JointPlot(
                self,
                x=x,
                y=y,
                x_outlier=x_outlier,
                y_outlier=y_outlier,
                df_without_nan=df_without_nan,
                column_name1=column_name1,
                column_name2=column_name2,
                r=r,
                r_w=r_w,
            )
            self.dialogs.append(dialog)
            dialog.show()
