from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel, QWidget


class QVertivalLabel(QLabel):
    def __init__(
        self,
        text: str,
        parent: QWidget | None = None,
        f: Qt.WindowType = Qt.WindowType(),
    ):
        super().__init__(text, parent, f)
        # self.setSizePolicy(QSizePolicy.Policy.Minimum,
        #                    QSizePolicy.Policy.Expanding)

    def paintEvent(self, arg__1):
        painter = QPainter(self)
        painter.translate(0, self.sizeHint().height())
        painter.rotate(270)
        painter.drawText(
            QRect(QPoint(0, 0), super().sizeHint()),
            Qt.AlignmentFlag.AlignCenter,
            self.text(),
        )

    def minimumSizeHint(self):
        s = super().minimumSizeHint()
        return QSize(s.height(), s.width())

    def sizeHint(self):
        s = super().sizeHint()
        return QSize(s.height(), s.width())
