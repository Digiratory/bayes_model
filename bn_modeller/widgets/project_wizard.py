import os

from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QRadioButton,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QLabel,
    QMessageBox,
    QApplication,
    QDialog, QGroupBox
)
from PySide6.QtCore import QRegularExpression, Signal, Slot, QPoint, Qt, QSettings, QStandardPaths
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QPen,
    QMouseEvent,
    QRegularExpressionValidator,
    QColor,
    QImage,
)
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from bn_modeller.widgets.file_path_widget import FilePathWidget
from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.utils.db_model_handler import add_values_from_csv


class ProjectLocationPage(QWizardPage):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Select Data Source"))

        self.path_edit: FilePathWidget
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        # createOrOpenRadioGroup
        groupBox = QGroupBox(self.tr("Create or Open"))

        self.radioOpen = QRadioButton(self.tr("Open existing"))
        self.radioOpen.setChecked(True)
        self.radioOpen.toggled.connect(self.changeFileMode)
        self.radioNew = QRadioButton(self.tr("Create New"))
        self.radioNew.toggled.connect(self.changeFileMode)

        vbox = QVBoxLayout()
        vbox.addWidget(self.radioOpen)
        vbox.addWidget(self.radioNew)
        # vbox.addStretch(1)
        groupBox.setLayout(vbox)

        main_layout.addWidget(groupBox)
        # File path row

        self.path_edit = FilePathWidget(
            self.tr("Select file"),
            self.tr("BNM Project File (*.sqlite)"),
            QSettings().value("projectLoadWizard/lastProjectLocationDir",
                              QStandardPaths.standardLocations(QStandardPaths.StandardLocation.DocumentsLocation)[0]),
            mode=FilePathWidget.FilePathMode.OpenFileName)
        self.registerField("ProjectLocationPage/projectLocation*",
                           self.path_edit.path_edit)
        self.path_edit.file_path_changed.connect(self.saveLastFilePath)
        main_layout.addWidget(self.path_edit)

        self.setLayout(main_layout)

    def initializePage(self):
        res = super().initializePage()
        self.path_edit.file_path = QSettings().value(
            "projectLoadWizard/lastProjectLocation", "")
        return res

    @Slot(bool)
    def changeFileMode(self, checked: bool):
        if checked:
            source = self.sender()
            if source == self.radioNew:
                self.path_edit.setMode(
                    FilePathWidget.FilePathMode.SaveFileName)
                self.setFinalPage(False)
            elif source == self.radioOpen:
                self.path_edit.setMode(
                    FilePathWidget.FilePathMode.OpenFileName)
                self.setFinalPage(True)

    @Slot(str)
    def saveLastFilePath(self, newFilePath: str):
        QSettings().setValue("projectLoadWizard/lastProjectLocationDir",
                             os.path.dirname(newFilePath))
        QSettings().setValue("projectLoadWizard/lastProjectLocation", newFilePath)


class DataImportPage(QWizardPage):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Import data"))
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        self.path_edit = FilePathWidget(
            self.tr("Select source file"),
            self.tr("Comma-separated values File (*.csv)"),
            QSettings().value("DataImportPage/lastSourceLocationDir",
                              QStandardPaths.standardLocations(QStandardPaths.StandardLocation.DocumentsLocation)[0]),
            mode=FilePathWidget.FilePathMode.OpenFileName)
        self.path_edit.file_path_changed.connect(self.saveLastFilePath)
        main_layout.addWidget(self.path_edit)
        self.registerField("DataImportPage/csvPath*", self.path_edit.path_edit)

        self.setLayout(main_layout)

    @Slot(str)
    def saveLastFilePath(self, newFilePath: str):
        QSettings().setValue("DataImportPage/lastSourceLocationDir",
                             os.path.dirname(newFilePath))

class ProjectLoadWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setWindowTitle(self.tr("Open project"))

        self.source_page = ProjectLocationPage()
        self.sourcePageId = self.addPage(self.source_page)

        self.importDataPage = DataImportPage()
        self.importDataPageId = self.addPage(self.importDataPage)

        self.button(QWizard.FinishButton).clicked.connect(self.close)

    def get_title(self):
        return self.tr("Open project")

    def get_project_path(self) -> str:
        return self.source_page.path_edit.file_path

    def nextId(self):
        if self.currentPage() == self.source_page:
            if self.source_page.radioOpen.isChecked():
                return -1
            else:
                return self.importDataPageId
        return super().nextId()

    def createDb(self):
        query = QSqlQuery()
        query.exec("PRAGMA page_size = 4096;")
        query.exec("PRAGMA cache_size = 16384;")
        query.exec("PRAGMA temp_store = MEMORY;")
        query.exec("PRAGMA journal_mode = PERSIST;")
        query.exec("PRAGMA locking_mode = EXCLUSIVE;")
        # WARNING: IT IS NOT SAFE. It can cause a DB damage in case of a bad termination.
        query.exec("PRAGMA synchronous = OFF;")
        self.openDb()
        
        add_values_from_csv(self.field("DataImportPage/csvPath"), self.featureSqlTableModel, self.sampleSqlTableModel)

    def openDb(self):
        self.featureSqlTableModel = FeatureSqlTableModel(db=self._db)
        self.sampleSqlTableModel = SampleSqlTableModel(db=self._db)

    def done(self, result):
        self._db = QSqlDatabase.addDatabase("QSQLITE")
        self._db.setDatabaseName(self.source_page.path_edit.file_path)
        self._db.open()
        if self.source_page.radioOpen.isChecked():
            self.openDb()
        else:
            self.createDb()

        return super().done(result)
