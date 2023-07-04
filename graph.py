from PyQt5 import QtGui, QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar


tips = sns.load_dataset("tips")


def seabornplot():
    # g = sns.FacetGrid(tips, col="sex", hue="time", palette="Set1",
    #                             hue_order=["Dinner", "Lunch"])
    # g.map(plt.scatter, "total_bill", "tip", edgecolor="w")
    global tips
    tips = tips.replace({'Female': 1, 'Male': 0})
    tips = tips.replace({'Yes': 1, 'No': 0})
    # print(tips)
    t = tips[['total_bill', 'tip']].corr()
    print(t)

    fig, ax = plt.subplots()
    im = sns.heatmap(t, ax=ax)

    # fig, ax = plt.subplots()
    # im, cbar = heatmap(data, row_labels=xlabs, col_labels=ylabs,
    #                    ax=ax, cmap="YlGn", cbarlabel="Label")
    return fig


class MainWindow(QtWidgets.QMainWindow):
    send_fig = QtCore.pyqtSignal(str)

    def __init__(self):
        super(MainWindow, self).__init__()

        self.main_widget = QtWidgets.QWidget(self)

        self.fig = seabornplot()
        self.canvas = FigureCanvas(self.fig)

        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                      QtWidgets.QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.button = QtWidgets.QPushButton("Button")
        self.label = QtWidgets.QLabel("A plot:")

        toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtWidgets.QGridLayout(self.main_widget)
        self.layout.addWidget(toolbar)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self.main_widget)
        self.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec_())