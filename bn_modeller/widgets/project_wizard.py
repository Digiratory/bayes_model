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

from bn_modeller.widgets.file_path_widget import FilePathWidget


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

        self._radioOpen = QRadioButton(self.tr("Open existing"))
        self._radioOpen.toggled.connect(self.changeFileMode)
        self._radioNew = QRadioButton(self.tr("Create New"))
        self._radioNew.toggled.connect(self.changeFileMode)
        self._radioOpen.setChecked(True)

        vbox = QVBoxLayout()
        vbox.addWidget(self._radioOpen)
        vbox.addWidget(self._radioNew)
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
        self.path_edit.file_path = QSettings().value(
            "projectLoadWizard/lastProjectLocation", "")
        self.path_edit.file_path_changed.connect(self.saveLastFilePath)
        main_layout.addWidget(self.path_edit)

        self.setLayout(main_layout)

    @Slot(bool)
    def changeFileMode(self, checked: bool):
        if checked:
            source = self.sender()
            if source == self._radioNew:
                self.path_edit.setMode(
                    FilePathWidget.FilePathMode.SaveFileName)
            elif source == self._radioOpen:
                self.path_edit.setMode(
                    FilePathWidget.FilePathMode.OpenFileName)

    @Slot(str)
    def saveLastFilePath(self, newFilePath: str):
        QSettings().setValue("projectLoadWizard/lastProjectLocationDir",
                             os.path.dirname(newFilePath))
        QSettings().setValue("projectLoadWizard/lastProjectLocation", newFilePath)
        pass


class ProjectLoadWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Open project"))
        # self.fixed_size = (720, 480)

        self.source_page = ProjectLocationPage()
        self.source_page.setTitle("Project Location")

        # for page in [self.source_page, self.checkerboard_page, self.scalefactor_page]:
        #     page.setFixedSize(*self.fixed_size)

        self.addPage(self.source_page)

        self.button(QWizard.FinishButton).clicked.connect(self.close)

    def get_title(self):
        return self.tr("Open project")

    def get_project_path(self) -> str:
        return self.source_page.path_edit.file_path
