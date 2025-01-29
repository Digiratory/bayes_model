from PySide6.QtCore import QObject, Qt, Property, Signal, QSize, QRect
from PySide6.QtWidgets import QTableView, QHeaderView, QStyle, QStyleOptionHeader
from PySide6.QtGui import QPainter, QFont, QFontMetrics


class RotatableHeaderView(QHeaderView):
    """Draft for Rotated header. It does not work.
    """
    rotate_angle_changed = Signal()

    def __init__(self, orientation: Qt.Orientation, parent: QObject = None):
        super().__init__(orientation, parent)
        self._font = QFont("helvetica", 15)
        self._metrics: QFontMetrics = QFontMetrics(self._font)
        self._descent = self._metrics.descent()
        self._margin = 10

        self._rotateAngle = 0

    def set_rotate_angle(self, angle: int):
        self._rotateAngle = angle

    def get_rotate_angle(self):
        return self._rotateAngle

    def paintSection(self, painter: QPainter, rect: QRect, index: int):
        if not rect.isValid():
            return
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)

        state = QStyle.StateFlag.State_None
        if (self.isEnabled()):
            state |= QStyle.StateFlag.State_Enabled
        if (self.window().isActiveWindow()):
            state |= QStyle.StateFlag.State_Active
        if (self.isSortIndicatorShown() and self.sortIndicatorSection() == index):
            opt.sortIndicator = QStyleOptionHeader.SortIndicator.SortDown if self.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder else  QStyleOptionHeader.SortIndicator.SortUp

        # setup the style options structure
        opt.rect = rect
        opt.section = index
        opt.state |= state

        opt.iconAlignment = Qt.AlignmentFlag.AlignVCenter
        opt.text = self.model().headerData(index, self.orientation(), Qt.ItemDataRole.DisplayRole)

        #@// the section position
        visual = self.visualIndex(index)
        if self.count() == 1:
            opt.position = QStyleOptionHeader.SectionPosition.OnlyOneSection
        elif visual == 0:
            opt.position = QStyleOptionHeader.SectionPosition.Beginning
        elif visual == self.count() - 1:
            opt.position = QStyleOptionHeader.SectionPosition.End
        else:
            opt.position = QStyleOptionHeader.SectionPosition.Middle

        #// the selected position

        #// draw the section
        
        #//store the header text
        headerText = opt.text
        #//reset the header text to no text
        opt.text = ""
        #//draw the control (unrotated!)
        self.style().drawControl(QStyle.ControlElement.CE_Header, opt, painter, self)

        painter.save()
        painter.translate(rect.x(), rect.y())
        painter.rotate(self.rotateAngle);# // or 270
        painter.drawText(0, 0, headerText)
        painter.restore()

        # return super().paintSection(painter, rect, index)

    def sizeHint(self):
        return QSize(0, self._get_text_width() + 2 * self._margin)

    def _get_text_width(self):
        try:
            return max([self._metrics.horizontalAdvance(self._get_data(i))
                        for i in range(0, self.model().columnCount())])
        except:
            return 0

    # def _get_data(self, index):
    #     return self.model().headerData(index, self.orientation())

    rotateAngle = Property(str, fget=get_rotate_angle, fset=set_rotate_angle, notify=rotate_angle_changed,
                           doc="Current rotation angle")


class DependencySetupTableView(QTableView):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        # horizontalHeaderView = RotatableHeaderView(Qt.Orientation.Horizontal)
        # horizontalHeaderView.rotateAngle = 90
        # self.setHorizontalHeader(horizontalHeaderView)
