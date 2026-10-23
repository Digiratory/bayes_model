from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class TransferButtonPanel(QWidget):
    """
    Widget with transfer buttons for moving features between panels.
    Provides ">" and "<" buttons for transferring selected features.
    """

    transferRight = Signal()  # Move selected features from left to right
    transferLeft = Signal()  # Move selected features from right to left

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Transfer right button (left to right)
        self.transfer_right_button = QPushButton(">")
        self.transfer_right_button.setFixedSize(40, 40)
        self.transfer_right_button.clicked.connect(self.transferRight.emit)

        # Transfer left button (right to left)
        self.transfer_left_button = QPushButton("<")
        self.transfer_left_button.setFixedSize(40, 40)
        self.transfer_left_button.clicked.connect(self.transferLeft.emit)

        # Add buttons to layout
        layout.addStretch()
        layout.addWidget(self.transfer_right_button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.transfer_left_button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        # Set fixed width for the panel
        self.setFixedWidth(60)
