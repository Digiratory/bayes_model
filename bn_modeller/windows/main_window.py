import os
import shutil

from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMenuBar,
    QStackedWidget,
    QStyle,
    QTabWidget,
    QWidget,
)

from bn_modeller.dialogs import AboutDialog
from bn_modeller.models import DependencyManyToManySqlTableModel, PairTableSQLProxyModel
from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.widgets.page.bayesian_network_page import BayesianNetworkPageWidget
from bn_modeller.widgets.page.database_page import DatabasePageWidget
from bn_modeller.widgets.project_wizard import ProjectLoadWizard
from bn_modeller.windows.base_window import BaseWindow


class MainWindow(BaseWindow):
    go_back = Signal()

    def __init__(self, parent: QWidget | None = None, flags=Qt.WindowType()):

        super().__init__("", parent, flags)

        self._main_widget: QTabWidget

        self._title = self.tr("Bayesian Network Modeller")

        self._init_ui()

        self._views_history: list[QWidget] = []
        self._project_path = None
        self._db: QSqlDatabase = None

        self.featureSqlTableModel: FeatureSqlTableModel = None
        self.sampleSqlTableModel: SampleSqlTableModel = None
        self._dependPairModel: PairTableSQLProxyModel = None
        self._dependencyManyToManySqlTableModel: DependencyManyToManySqlTableModel = (
            None
        )

        self.projectWizardOpened: ProjectLoadWizard = False

        QGuiApplication.instance().applicationStateChanged.connect(
            self.application_state_changed
        )

    def _remove_models(self):
        if self._dependencyManyToManySqlTableModel is not None:
            self._dependencyManyToManySqlTableModel.clear()
        self._dependencyManyToManySqlTableModel = None

        self._dependPairModel = None

        if self.featureSqlTableModel is not None:
            self.featureSqlTableModel.clear()
        self.featureSqlTableModel = None

        if self.sampleSqlTableModel is not None:
            self.sampleSqlTableModel.clear()
        self.sampleSqlTableModel = None

    def _init_db(self):
        self.project_path_widget.setText(self._project_path)

        self.featureSqlTableModel = FeatureSqlTableModel(db=self._db)
        self.sampleSqlTableModel = SampleSqlTableModel(db=self._db)
        self._initCacheDbInMemory()

        self._dependencyManyToManySqlTableModel = DependencyManyToManySqlTableModel(
            db=self._db
        )
        self._dependPairModel = PairTableSQLProxyModel(
            self.featureSqlTableModel, db=self._db
        )

        self.databasePageWidget.setModels(
            featureSqlTableModel=self.featureSqlTableModel,
            sampleSqlTableModel=self.sampleSqlTableModel,
        )

        self.dependencySetupPageWidget.setModels(
            pairTableSQLProxyModel=self._dependPairModel
        )

    def _init_ui(self):
        self._main_widget = QTabWidget()
        self.set_central_title(self._title)

        self.databasePageWidget = DatabasePageWidget()
        self._main_widget.addTab(
            self.databasePageWidget, self.tr("Evaluation of variables correlations")
        )

        self.dependencySetupPageWidget = BayesianNetworkPageWidget()
        self._main_widget.addTab(
            self.dependencySetupPageWidget, self.tr("Bayesian Networks")
        )

        self.setCentralWidget(self._main_widget)

        # add_data_action = QAction(self.style().standardIcon(
        #     QStyle.StandardPixmap.SP_FileDialogContentsView), '&AddData', self)
        # add_data_action.setStatusTip(self.tr('Add Data'))
        # add_data_action.triggered.connect(self.add_data_clicked)
        # self.getMainToolBar().addAction(add_data_action)

        # Create a menu bar
        self._menu_bar = QMenuBar()
        self.setMenuBar(self._menu_bar)

        # Create the "File" menu
        self._file_menu = self._menu_bar.addMenu(self.tr("File"))
        # Create an action for the "Open" item in the "File" menu
        open_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            "&Open",
            self,
        )
        open_action.setStatusTip(self.tr("Open a project"))
        open_action.triggered.connect(self.open_file_clicked)
        self._file_menu.addAction(open_action)

        # Create an action for the "Save as..." item in the "File" menu
        save_as_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            self.tr("&Save As..."),
            self,
        )
        save_as_action.setStatusTip(self.tr("Save project as a new file"))
        save_as_action.triggered.connect(self.save_file_clicked)
        self._file_menu.addAction(save_as_action)

        # Create an action for the "Exit" item in the "File" menu
        self._file_menu.addSeparator()
        exit_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton),
            "&Exit",
            self,
        )
        exit_action.setStatusTip(self.tr("Exit application"))
        exit_action.triggered.connect(self.close_app)
        self._file_menu.addAction(exit_action)

        # Create the "Help" menu
        self._help_menu = self._menu_bar.addMenu(self.tr("Help"))

        # Create an action for the "Report Bug" item in the "Help" menu
        report_bug_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion),
            "&Report Bug",
            self,
        )
        report_bug_action.setStatusTip(self.tr("Report a bug"))
        report_bug_action.triggered.connect(self.report_bug)
        self._help_menu.addAction(report_bug_action)

        # Create an action for the "About" item in the "Help" menu
        self._help_menu.addSeparator()
        about_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation),
            "&About",
            self,
        )
        about_action.setStatusTip(self.tr("Show About Dialog"))
        about_action.triggered.connect(self.show_about_dialog)

        # Add the action to the "Help" menu
        self._help_menu.addAction(about_action)

        # Add widget to status bar with a current path to project
        self.project_path_widget = QLabel()
        self.statusBar().addPermanentWidget(self.project_path_widget)

    @Slot()
    def report_bug(self):
        QDesktopServices.openUrl(
            QUrl(
                "https://github.com/Digiratory/bayes_model/issues/new?template=bug_report.md"
            )
        )

    @Slot()
    def open_file_clicked(self):
        self._open_project()

    @Slot()
    def save_file_clicked(self):
        print("'Save as...' clicked")
        fileName = QFileDialog.getSaveFileName(
            self,
            self.tr("Save project as..."),
            os.path.dirname(self._project_path),
            self.tr("BNM Project File (*.sqlite)"),
        )
        if fileName[0]:
            print(fileName)
            ProjectLoadWizard.closeDb()
            shutil.copyfile(
                self._project_path,
                fileName[0],
            )
            self._project_path = fileName[0]
            self._db = ProjectLoadWizard.openDb(fileName[0])
            self._init_db()

    def show_about_dialog(self):
        dialog = AboutDialog()
        dialog.exec()

    def _save_to_history(self, previousWidget: QWidget):
        self._viewsHistory.append(previousWidget)

    def _set_current_widget(self, newCurrentWidget: QWidget):
        self._save_to_history(self._main_widget.currentWidget())
        self._main_widget.setCurrentWidget(newCurrentWidget)

    def _initCacheDbInMemory(self):
        self.featureSqlTableModel.select()
        while self.featureSqlTableModel.canFetchMore():
            self.featureSqlTableModel.fetchMore()
        self.sampleSqlTableModel.select()
        while self.sampleSqlTableModel.canFetchMore():
            self.sampleSqlTableModel.fetchMore()

    def projectLoadWizardFinalozationInterceptor(
        self, wizard: ProjectLoadWizard, result
    ):
        """Pre-Finalize callback of the project load wizard and clean up any resources.

        Args:
            wizard (ProjectLoadWizard): The project load wizard instance.
            result (bool): The result of the wizard.
        """
        if result and self._db is not None:
            self._remove_models()
            self._db = None

    def _open_project(self) -> bool:
        self.projectWizardOpened = True
        projectWizard = ProjectLoadWizard(
            pre_done_handler=self.projectLoadWizardFinalozationInterceptor
        )
        wizard_ret = projectWizard.exec()
        if wizard_ret != 1:
            return False
        self._project_path = projectWizard.get_project_path()
        self._db = projectWizard._db
        self._init_db()
        return True

    @Slot()
    def go_back_clicked(self):
        if len(self._views_history) > 0:
            previousWidget: QWidget = self._views_history.pop()
            self._main_widget.setCurrentWidget(previousWidget)
            self.setCentralTitle("", "")
            self.go_back.emit()

    @Slot()
    def home_clicked(self):
        self._views_history.clear()
        self._main_widget.setCurrentWidget(self._homepageWidget)
        self.setCentralTitle("", "")
        self.go_back.emit()

    @Slot(Qt.ApplicationState)
    def application_state_changed(self, state: Qt.ApplicationState):
        if self._project_path is None and not self.projectWizardOpened:
            if not self._open_project():
                self.close_app()
