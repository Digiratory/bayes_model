import os

from PySide6.QtWidgets import QWidget, QStackedWidget, QStyle, QTabWidget
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication, QAction
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from bn_modeller.windows.base_window import BaseWindow
from bn_modeller.widgets.project_wizard import ProjectLoadWizard
from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel

from bn_modeller.widgets.page.database_page import DatabasePageWidget
from bn_modeller.utils.db_model_handler import add_values_from_csv


class MainWindow(BaseWindow):
    go_back = Signal()

    def __init__(self, parent: QWidget | None = None, flags=Qt.WindowType()):

        super().__init__("", parent, flags)

        self._main_widget: QStackedWidget

        self._title = self.tr("Bayesian Network Modeller")

        self._init_ui()

        self._views_history: list[QWidget] = []
        self._project_path = None
        self._db: QSqlDatabase = None

        self.featureSqlTableModel: FeatureSqlTableModel = None
        self.sampleSqlTableModel: SampleSqlTableModel = None

        QGuiApplication.instance().applicationStateChanged.connect(
            self.application_state_changed)

    def _init_db(self):
        self._db = QSqlDatabase.addDatabase("QSQLITE")
        self._db.setDatabaseName(os.path.join(
            self._project_path, "project_database.sqlite"))
        self._db.open()
        query = QSqlQuery()
        query.exec("PRAGMA page_size = 4096;")
        query.exec("PRAGMA cache_size = 16384;")
        query.exec("PRAGMA temp_store = MEMORY;")
        query.exec("PRAGMA journal_mode = PERSIST;")
        query.exec("PRAGMA locking_mode = EXCLUSIVE;")
        query.exec("PRAGMA synchronous = OFF;") # WARNING: IT IS NOT SAFE. It can cause a DB damage in case of a bad termination. 
        
        self.featureSqlTableModel = FeatureSqlTableModel(db=self._db)
        self.sampleSqlTableModel = SampleSqlTableModel(db=self._db)
        self._initCacheDbInMemory()

        self.databasePageWidget.setModels(
            featureSqlTableModel=self.featureSqlTableModel,
            sampleSqlTableModel=self.sampleSqlTableModel)

    def _init_ui(self):
        self._main_widget = QTabWidget()
        self.set_central_title(self._title)

        self.databasePageWidget = DatabasePageWidget()
        self._main_widget.addTab(self.databasePageWidget, "Database")

        self.setCentralWidget(self._main_widget)

        add_data_action = QAction(self.style().standardIcon(
            QStyle.StandardPixmap.SP_FileDialogContentsView), '&AddData', self)
        add_data_action.setStatusTip(self.tr('Add Data'))
        add_data_action.triggered.connect(self.add_data_clicked)
        self.getMainToolBar().addAction(add_data_action)

    def _save_to_history(self, previousWidget: QWidget):
        self._viewsHistory.append(previousWidget)

    def _set_current_widget(self, newCurrentWidget: QWidget):
        self._save_to_history(self._main_widget.currentWidget())
        self._main_widget.setCurrentWidget(newCurrentWidget)

    def _initCacheDbInMemory(self):
        self.featureSqlTableModel.select()
        while (self.featureSqlTableModel.canFetchMore()):
            self.featureSqlTableModel.fetchMore()
        self.sampleSqlTableModel.select()
        while (self.sampleSqlTableModel.canFetchMore()):
            self.sampleSqlTableModel.fetchMore()

    @Slot()
    def add_data_clicked(self):
        add_values_from_csv(
            r"data\data_2.csv", self.featureSqlTableModel, self.sampleSqlTableModel)
        self._initCacheDbInMemory()

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
            self._init_db()
