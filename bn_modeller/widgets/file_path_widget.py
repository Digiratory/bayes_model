import enum

from PySide6.QtCore import Property, QPoint, QRegularExpression, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QStyle,
    QWidget,
)


class FilePathWidget(QWidget):
    file_path_changed = Signal(str)

    class FilePathMode(enum.IntEnum):
        SaveFileName = (0,)
        OpenFileName = 1

    def __init__(
        self,
        caption: str,
        fileSelectionFilter: str,
        defaultDir: str = None,
        mode: FilePathMode = FilePathMode.SaveFileName,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._caption: str = caption
        self._defaultDir: str = defaultDir
        self._fileSelectionFilter: str = fileSelectionFilter
        self._dialogFcn = (
            QFileDialog.getSaveFileName
            if mode == FilePathWidget.FilePathMode.SaveFileName
            else QFileDialog.getOpenFileName
        )
        self._init_ui()

    def setMode(self, mode: FilePathMode):
        self._dialogFcn = (
            QFileDialog.getSaveFileName
            if mode == FilePathWidget.FilePathMode.SaveFileName
            else QFileDialog.getOpenFileName
        )

    def _init_ui(self):
        self.root_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(self.tr("Select file path"))
        self.dialog_button = QPushButton(
            icon=self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
        )
        self.dialog_button.clicked.connect(self.selectFile)

        self.root_layout.addWidget(self.path_edit)
        self.root_layout.addWidget(self.dialog_button)
        self.setLayout(self.root_layout)

    @Slot()
    def selectFile(self):
        fileName = self._dialogFcn(
            self, self._caption, self._defaultDir, self._fileSelectionFilter
        )
        if len(fileName[0]) > 0:
            self.file_path = fileName[0]

    def set_file_path(self, file_path: str):
        self.path_edit.setText(file_path)
        self.file_path_changed.emit(file_path)

    def get_file_path(self) -> str:
        return self.path_edit.text()

    file_path = Property(
        str,
        fget=get_file_path,
        fset=set_file_path,
        notify=file_path_changed,
        doc="Current selected path",
    )
