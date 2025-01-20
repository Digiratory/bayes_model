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
    QDialog,
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


class DataSourcePage(QWizardPage):
    def __init__(self, stream_ip: str = None, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Select Data Source"))

        self.path_edit: FilePathWidget
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        self.path_edit = FilePathWidget()
        self.path_edit.file_path = QSettings().value("projectLoadWizard/dataSourceDir",
                                                     QStandardPaths.standardLocations(QStandardPaths.StandardLocation.DocumentsLocation)[0])
        main_layout.addWidget(self.path_edit)

        self.setLayout(main_layout)


class ProjectLoadWizard(QWizard):
    def __init__(self, parent=None, stream_ip: str = None):
        super().__init__(parent)
        self.setWindowTitle("Calibration Tool")
        self.fixed_size = (720, 480)

        self.source_page = DataSourcePage(stream_ip)
        self.source_page.setTitle("Data source")

        # for page in [self.source_page, self.checkerboard_page, self.scalefactor_page]:
        #     page.setFixedSize(*self.fixed_size)

        self.addPage(self.source_page)

        self.button(QWizard.FinishButton).clicked.connect(self.close)

    def get_title(self):
        return self.tr("Open project")

    def get_project_path(self) -> str:
        return self.source_page.path_edit.file_path
