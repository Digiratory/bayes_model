from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QStyle
from PySide6.QtCore import QRegularExpression, Signal, Slot, QPoint, Qt, Property


class FilePathWidget(QWidget):
    file_path_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.root_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(self.tr("Select file path"))
        self.dialog_button = QPushButton(icon=self.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogOpenButton))

        self.root_layout.addWidget(self.path_edit)
        self.root_layout.addWidget(self.dialog_button)
        self.setLayout(self.root_layout)

    def set_file_path(self, file_path):
        self.path_edit.setText(file_path)

    def get_file_path(self):
        return self.path_edit.text()

    file_path = Property(str, fget=get_file_path, fset=set_file_path, notify=file_path_changed,
                         doc="Current selected path")
