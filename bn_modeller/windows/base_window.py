from PySide6.QtCore import Qt, Signal, Slot, QCoreApplication
from PySide6.QtWidgets import QMainWindow, QWidget, QStyle, QToolBar
from PySide6.QtGui import QAction


class BaseWindow(QMainWindow):
    def __init__(self, title: str, parent: QWidget | None = None, flags=Qt.WindowType()) -> None:
        super(BaseWindow, self).__init__(parent, flags)
        self.caption = title
        self.setup_toolbar()
        self.set_central_title(title)

    def set_central_title(self, title):
        self.setWindowTitle(title)

    def setup_toolbar(self):
        toolbar = QToolBar(self.tr('Main ToolBar'))

        back_action = QAction(self.style().standardIcon(
            QStyle.StandardPixmap.SP_ArrowBack), '&Back', self)
        back_action.setStatusTip(self.tr('Go Back'))
        back_action.triggered.connect(self.go_back_clicked)

        self.addToolBar(toolbar)
        toolbar.addAction(back_action)

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
