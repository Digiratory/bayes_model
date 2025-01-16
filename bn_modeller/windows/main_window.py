from PySide6.QtWidgets import QWidget, QStackedWidget, QApplication
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from bn_modeller.windows.base_window import BaseWindow
from bn_modeller.widgets.project_wizard import ProjectLoadWizard

class MainWindow(BaseWindow):
    go_back = Signal()

    def __init__(self, parent: QWidget | None = None, flags=Qt.WindowType()):
        
        super().__init__("", parent, flags)
        
        self._main_widget: QStackedWidget

        self._title = self.tr("Bayesian Network Modeller")

        self._init_ui()

        self._views_history: list[QWidget] = []
        self._project_path = None

        QGuiApplication.instance().applicationStateChanged.connect(self.application_state_changed)

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

    @Slot(Qt.ApplicationState)
    def application_state_changed(self, state: Qt.ApplicationState):
        if self._project_path is None:
            wizard = ProjectLoadWizard()
            wizard_ret = wizard.exec()
            if wizard_ret != 1:
                self.close_app()            
            self._project_path = wizard.get_project_path()
