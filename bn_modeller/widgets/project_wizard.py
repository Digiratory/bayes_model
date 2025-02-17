import os

import numpy as np
from PySide6.QtCore import QObject, QSettings, QStandardPaths, Slot
from PySide6.QtGui import QDoubleValidator
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.models.sample_sqltable_model import SampleSqlTableModel
from bn_modeller.utils.db_model_handler import add_values_from_csv
from bn_modeller.widgets.file_path_widget import FilePathWidget
from bn_modeller.widgets.separator_widget import QSeparator


class TableValueFixer(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.cache = {}

    def askUserForNewValue(self, value: str) -> float:
        dialog = QDialog(parent=self.parent())
        dialog.setWindowTitle("Unexpected value")
        layout = QFormLayout()
        line_edit = QLineEdit()
        line_edit.setValidator(QDoubleValidator())  # only allow float inputs
        layout.addRow(QLabel(f"Enter a value instead of: {value}"))
        layout.addRow(QLabel("New Value:"), line_edit)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        if dialog.exec() == QDialog.Accepted:
            new_value = line_edit.text()
            try:
                return float(new_value)
            except ValueError:
                print("Invalid input. Replacing with NaN.")
                return np.nan
        else:
            return np.nan

    def fixValue(self, value: str) -> float:
        if value not in self.cache:
            self.cache[value] = self.askUserForNewValue(value)
        return self.cache[value]


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
            QSettings().value(
                "projectLoadWizard/lastProjectLocationDir",
                QStandardPaths.standardLocations(
                    QStandardPaths.StandardLocation.DocumentsLocation
                )[0],
            ),
            mode=FilePathWidget.FilePathMode.OpenFileName,
        )
        self.registerField(
            "ProjectLocationPage/projectLocation*", self.path_edit.path_edit
        )
        self.path_edit.file_path_changed.connect(self.saveLastFilePath)
        main_layout.addWidget(self.path_edit)

        self.setLayout(main_layout)

    def initializePage(self):
        res = super().initializePage()
        self.path_edit.file_path = QSettings().value(
            "projectLoadWizard/lastProjectLocation", ""
        )
        return res

    @Slot(bool)
    def changeFileMode(self, checked: bool):
        if checked:
            source = self.sender()
            if source == self.radioNew:
                self.path_edit.setMode(FilePathWidget.FilePathMode.SaveFileName)
                self.setFinalPage(False)
            elif source == self.radioOpen:
                self.path_edit.setMode(FilePathWidget.FilePathMode.OpenFileName)
                self.setFinalPage(True)

    @Slot(str)
    def saveLastFilePath(self, newFilePath: str):
        QSettings().setValue(
            "projectLoadWizard/lastProjectLocationDir", os.path.dirname(newFilePath)
        )
        QSettings().setValue("projectLoadWizard/lastProjectLocation", newFilePath)


class DataImportPage(QWizardPage):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Import data"))
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        # File path row
        self.path_edit = FilePathWidget(
            self.tr("Select source file"),
            self.tr(
                "Comma-separated values File (*.csv);;Excel Workbook (*.xlsx *.xls)"
            ),
            QSettings().value(
                "DataImportPage/lastSourceLocationDir",
                QStandardPaths.standardLocations(
                    QStandardPaths.StandardLocation.DocumentsLocation
                )[0],
            ),
            mode=FilePathWidget.FilePathMode.OpenFileName,
        )
        self.path_edit.file_path_changed.connect(self.saveLastFilePath)
        main_layout.addWidget(self.path_edit)
        self.registerField("DataImportPage/csvPath*", self.path_edit.path_edit)

        self.setLayout(main_layout)

        # File settings group box
        groupBox = QGroupBox(self.tr("Source file format"))

        self.radioSampleInRow = QRadioButton(self.tr("Samples in rows"))
        self.radioSampleInRow.setChecked(True)
        self.radioSampleInColumn = QRadioButton(self.tr("Samples in columns"))
        vbox = QVBoxLayout()
        vbox.addWidget(self.radioSampleInRow)
        vbox.addWidget(self.radioSampleInColumn)
        vbox.addWidget(QSeparator())

        # Add a new HBoxLayout with two spinboxes and labels for each one
        hbox = QHBoxLayout()
        self.skip_rows_spinbox = QSpinBox()
        self.skip_rows_spinbox.setRange(0, 100)  # Set the range to 100
        hbox.addWidget(QLabel(self.tr("Skip rows: ")))
        hbox.addWidget(self.skip_rows_spinbox)

        self.skip_cols_spinbox = QSpinBox()
        self.skip_cols_spinbox.setRange(0, 100)  # Set the range to 100
        hbox.addWidget(QLabel(self.tr("Skip columns: ")))
        hbox.addWidget(self.skip_cols_spinbox)
        vbox.addLayout(hbox)

        groupBox.setLayout(vbox)
        self.registerField("DataImportPage/isSampleInRows", self.radioSampleInRow)
        self.registerField("DataImportPage/skipRows", self.skip_rows_spinbox)
        self.registerField("DataImportPage/skipColumns", self.skip_cols_spinbox)
        main_layout.addWidget(groupBox)

    @Slot(str)
    def saveLastFilePath(self, newFilePath: str):
        QSettings().setValue(
            "DataImportPage/lastSourceLocationDir", os.path.dirname(newFilePath)
        )


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

        try:
            valueFixer = TableValueFixer(self)
            add_values_from_csv(
                self.field("DataImportPage/csvPath"),
                not self.field("DataImportPage/isSampleInRows"),
                self.featureSqlTableModel,
                self.sampleSqlTableModel,
                skip_rows=self.field("DataImportPage/skipRows"),
                skip_cols=self.field("DataImportPage/skipColumns"),
                value_fixer_callback=valueFixer.fixValue,
            )
        except Exception as e:
            # TODO: handle the exception, ask the user to retry or quit
            print(e)

    def openDb(self):
        self.featureSqlTableModel = FeatureSqlTableModel(db=self._db)
        self.sampleSqlTableModel = SampleSqlTableModel(db=self._db)

    def connectDb(self):
        self._db = QSqlDatabase.addDatabase("QSQLITE")
        self._db.setDatabaseName(self.source_page.path_edit.file_path)
        self._db.open()

    def done(self, result):

        if self.source_page.radioOpen.isChecked():
            self.connectDb()
            self.openDb()
        else:
            if os.path.exists(self.source_page.path_edit.file_path):
                # TODO: ask user to delete the file
                os.remove(self.source_page.path_edit.file_path)
            self.connectDb()
            self.createDb()

        return super().done(result)
