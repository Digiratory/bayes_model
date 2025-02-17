from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QWidget


class QSeparator(QFrame):
    """A separator widget.
    A separator is a line  that are used to separate
    different parts of the user interface.

    Usage example:

    >>> separator = QSeparator()
    >>> layout.addWidget(separator)

    """

    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType()
    ):
        super().__init__(parent, f)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
