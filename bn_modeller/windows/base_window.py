import os

from PySide6.QtCore import QCoreApplication, Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QStyle, QToolBar, QWidget


class BaseWindow(QMainWindow):
    def __init__(
        self, title: str, parent: QWidget | None = None, flags=Qt.WindowType()
    ) -> None:
        super(BaseWindow, self).__init__(parent, flags)
        self.caption = title
        # self.setup_toolbar()
        my_icon = QIcon()
        my_icon.addFile(
            os.path.join(os.path.dirname(__file__), "..", "resources\\icon.ico")
        )
        self.setWindowIcon(my_icon)
        self.set_central_title(title)
        self.statusBar().showMessage("Ready")

    def set_central_title(self, title):
        self.setWindowTitle(title)

    # def setup_toolbar(self):
    #     self._toolbar = QToolBar(self.tr('Main ToolBar'))

    #     back_action = QAction(self.style().standardIcon(
    #         QStyle.StandardPixmap.SP_ArrowBack), '&Back', self)
    #     back_action.setStatusTip(self.tr('Go Back'))
    #     back_action.triggered.connect(self.go_back_clicked)

    #     self.addToolBar(self._toolbar)
    #     self._toolbar.addAction(back_action)

    def getMainToolBar(self) -> QToolBar:
        return self._toolbar

    @Slot()
    def go_back_clicked(self):
        raise NotImplementedError()

    @Slot()
    def home_clicked(self):
        raise NotImplementedError()

    @Slot()
    def exit_clicked(self):
        return

    @Slot()
    def close_app(self):
        QCoreApplication.instance().quit()
