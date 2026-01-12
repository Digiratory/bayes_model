import os
import shutil

import numpy as np
from PySide6.QtCore import QObject, QSettings, QStandardPaths, Qt, QUrl, Slot
from PySide6.QtGui import QDesktopServices, QDoubleValidator
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
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
        layout.addRow(
            QLabel(
                (
                    f"The program supports only numeric values for measurements, but found '{value}'.\n"
                    + f"Please enter a numeric value instead of '{value}'.\n"
                    + f"The value '{value}' will be replaced by NaN if you do not provide a valid number.\n"
                    + "All values in the dataset will be replaced by NaN or new value."
                )
            )
        )
        layout.addRow(QLabel(f"New Value instead of '{value}':"), line_edit)
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


class DataSourceTemplatePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Datasource Template"))
        self.path_edit: FilePathWidget
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        explanation_label = QLabel(
            self.tr(
                "Please select a datasource template file. \n"
                "If you already have a datasource file with compatible format, you can skip this step.\n\n"
                "We provide two templates: \n"
                "1. A template for a CSV/Excel file with samples in rows.\n"
                "2. A template for a CSV/Excel file with samples in columns.\n\n"
                "Please select the appropriate template for your data."
            )
        )

        # Layout with buttons for selecting and saving the template file.
        hbox = QHBoxLayout()

        get_template_rows_button = QPushButton(
            self.tr("Get Template with samples in Rows")
        )
        get_template_rows_button.clicked.connect(self.on_get_template_rows_clicked)
        hbox.addWidget(get_template_rows_button)

        get_template_cols_button = QPushButton(
            self.tr("Get Template with samples in Columns")
        )
        get_template_cols_button.clicked.connect(self.on_get_template_cols_clicked)
        hbox.addWidget(get_template_cols_button)

        main_layout.addWidget(explanation_label)
        main_layout.addLayout(hbox)

        self.setLayout(main_layout)

    @Slot()
    def on_get_template_rows_clicked(self):
        # Code to handle the button click event
        fileName = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Template"),
            None,
            "Comma-separated values File (*.csv);;Excel Workbook (*.xlsx)",
        )
        if len(fileName[0]) > 0:
            if fileName[0].endswith(".csv"):
                shutil.copyfile(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "resources",
                        "templates",
                        "datasource_rows.csv",
                    ),
                    fileName[0],
                )
            elif fileName[0].endswith(".xlsx"):
                shutil.copyfile(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "resources",
                        "templates",
                        "datasource_rows.xlsx",
                    ),
                    fileName[0],
                )
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(fileName[0])))

    @Slot()
    def on_get_template_cols_clicked(self):
        fileName = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Template"),
            None,
            "Comma-separated values File (*.csv);;Excel Workbook (*.xlsx)",
        )
        if len(fileName[0]) > 0:
            if fileName[0].endswith(".csv"):
                shutil.copyfile(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "resources",
                        "templates",
                        "datasource_cols.csv",
                    ),
                    fileName[0],
                )
            elif fileName[0].endswith(".xlsx"):
                shutil.copyfile(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "resources",
                        "templates",
                        "datasource_cols.xlsx",
                    ),
                    fileName[0],
                )
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(fileName[0])))


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
        vbox = QVBoxLayout()

        # Add a label to explain the format options
        orientation_expl_label = QLabel(
            self.tr(
                "Select how samples are organized in your file. If samples are in rows, each row represents a sample. If samples are in columns, each column represents a sample."
            )
        )
        orientation_expl_label.setWordWrap(True)
        orientation_expl_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        vbox.addWidget(orientation_expl_label)

        self.radioSampleInRow = QRadioButton(self.tr("Samples in rows"))
        self.radioSampleInRow.setChecked(True)
        self.radioSampleInColumn = QRadioButton(self.tr("Samples in columns"))

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

        # Add a label to explain the purpose of the skip rows and columns fields
        skip_expl_label = QLabel(
            self.tr(
                "If you are using a custom format, you can specify the number of rows and columns to skip to make the dataset compatible with the program."
            )
        )
        skip_expl_label.setWordWrap(True)
        vbox.addWidget(skip_expl_label)

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
    def __init__(self, pre_done_handler=None, parent=None):
        super().__init__(parent)
        # self.setWindowTitle(self.tr("Open project"))
        self._pre_done_handler = pre_done_handler

        self.source_page = ProjectLocationPage()
        self.sourcePageId = self.addPage(self.source_page)

        self.datasourceTemplatePage = DataSourceTemplatePage()
        self.datasourceTemplatePageId = self.addPage(self.datasourceTemplatePage)

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
                return self.datasourceTemplatePageId
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
        self.loadModelsFromDb()

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

    def loadModelsFromDb(self):
        self.featureSqlTableModel = FeatureSqlTableModel(db=self._db)
        self.sampleSqlTableModel = SampleSqlTableModel(db=self._db)

    def connectDb(self):
        self._db = None
        ProjectLoadWizard.closeDb()
        self._db = ProjectLoadWizard.openDb(self.source_page.path_edit.file_path)

    def done(self, result):
        if self._pre_done_handler is not None:
            self._pre_done_handler(self, result)
        if result:
            if self.source_page.radioOpen.isChecked():
                self.connectDb()
                self.loadModelsFromDb()
            else:
                if os.path.exists(self.source_page.path_edit.file_path):
                    # TODO: ask user to delete the file
                    os.remove(self.source_page.path_edit.file_path)
                self.connectDb()
                self.createDb()

        return super().done(result)

    @staticmethod
    def closeDb():
        for conn_name in QSqlDatabase.connectionNames():
            db = QSqlDatabase.database(conn_name)
            db.commit()
            db.close()
            QSqlDatabase.removeDatabase(conn_name)

    @staticmethod
    def openDb(path: str) -> QSqlDatabase:
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName(path)
        db.open()
        return db
