from PySide6.QtWidgets import QWidget, QStackedWidget
from PySide6.QtCore import Qt, Signal, Slot

from bn_modeller.windows.base_window import BaseWindow


class MainWindow(BaseWindow):
    go_back = Signal()

    def __init__(self, parent: QWidget | None = None, flags=Qt.WindowType()):
        
        super().__init__("", parent, flags)
        
        self._main_widget: QStackedWidget

        self._title = self.tr("Bayesian Network Modeller")

        self._init_ui()

        self._views_history: list[QWidget] = []

    def _init_ui(self):
        self._main_widget = QStackedWidget()
        self.set_central_title(self._title)

        self.setCentralWidget(self._main_widget)

    def _save_to_history(self, previousWidget: QWidget):
        self._viewsHistory.append(previousWidget)

    def _set_current_widget(self, newCurrentWidget: QWidget):
        self._save_to_history(self._main_widget.currentWidget())
        self._main_widget.setCurrentWidget(newCurrentWidget)

    @Slot()
    def go_back_clicked(self):
        if len(self._views_history) > 0:
            previousWidget: QWidget = self._views_history.pop()
            self._main_widget.setCurrentWidget(previousWidget)
            self.setCentralTitle('', '')
            self.go_back.emit()

    @Slot()
    def home_clicked(self):
        self._views_history.clear()
        self._main_widget.setCurrentWidget(self._homepageWidget)
        self.setCentralTitle('', '')
        self.go_back.emit()