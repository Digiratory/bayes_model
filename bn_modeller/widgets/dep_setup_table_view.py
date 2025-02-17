from PySide6.QtCore import (
    Property,
    QModelIndex,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QHeaderView, QMenu, QStyle, QStyleOptionHeader, QTableView


class RotatableHeaderView(QHeaderView):
    """Draft for Rotated header. It does not work."""

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
        if self.isEnabled():
            state |= QStyle.StateFlag.State_Enabled
        if self.window().isActiveWindow():
            state |= QStyle.StateFlag.State_Active
        if self.isSortIndicatorShown() and self.sortIndicatorSection() == index:
            opt.sortIndicator = (
                QStyleOptionHeader.SortIndicator.SortDown
                if self.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
                else QStyleOptionHeader.SortIndicator.SortUp
            )

        # setup the style options structure
        opt.rect = rect
        opt.section = index
        opt.state |= state

        opt.iconAlignment = Qt.AlignmentFlag.AlignVCenter
        opt.text = self.model().headerData(
            index, self.orientation(), Qt.ItemDataRole.DisplayRole
        )

        # @// the section position
        visual = self.visualIndex(index)
        if self.count() == 1:
            opt.position = QStyleOptionHeader.SectionPosition.OnlyOneSection
        elif visual == 0:
            opt.position = QStyleOptionHeader.SectionPosition.Beginning
        elif visual == self.count() - 1:
            opt.position = QStyleOptionHeader.SectionPosition.End
        else:
            opt.position = QStyleOptionHeader.SectionPosition.Middle

        # // the selected position

        # // draw the section

        # //store the header text
        headerText = opt.text
        # //reset the header text to no text
        opt.text = ""
        # //draw the control (unrotated!)
        self.style().drawControl(QStyle.ControlElement.CE_Header, opt, painter, self)

        painter.save()
        painter.translate(rect.x(), rect.y())
        painter.rotate(self.rotateAngle)  # // or 270
        painter.drawText(0, 0, headerText)
        painter.restore()

        # return super().paintSection(painter, rect, index)

    def sizeHint(self):
        return QSize(0, self._get_text_width() + 2 * self._margin)

    def _get_text_width(self):
        try:
            return max(
                [
                    self._metrics.horizontalAdvance(self._get_data(i))
                    for i in range(0, self.model().columnCount())
                ]
            )
        except:
            return 0

    # def _get_data(self, index):
    #     return self.model().headerData(index, self.orientation())

    rotateAngle = Property(
        str,
        fget=get_rotate_angle,
        fset=set_rotate_angle,
        notify=rotate_angle_changed,
        doc="Current rotation angle",
    )


class DependencySetupTableView(QTableView):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        # horizontalHeaderView = RotatableHeaderView(Qt.Orientation.Horizontal)
        # horizontalHeaderView.rotateAngle = 90
        # self.setHorizontalHeader(horizontalHeaderView)
        self.initContextMenu()

    def initContextMenu(self):

        self.horizontalHeader().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.horizontalHeader().customContextMenuRequested.connect(
            self.showHorizontalHeaderContextMenu
        )
        self.verticalHeader().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.verticalHeader().customContextMenuRequested.connect(
            self.showVerticalHeaderContextMenu
        )

        self.headerMenu: QMenu = QMenu(self)
        selectAllAction = QAction(self.tr("Select All"), self)
        selectAllAction.triggered.connect(self.setCheckStateAll)
        self.headerMenu.addAction(selectAllAction)

        unselectAllAction = QAction(self.tr("Unselect All"), self)
        unselectAllAction.triggered.connect(self.removeCheckStateAll)
        self.headerMenu.addAction(unselectAllAction)

        swapSelectionAction = QAction(self.tr("Swap selection"), self)
        swapSelectionAction.triggered.connect(self.invertCheckStateAll)
        self.headerMenu.addAction(swapSelectionAction)

    @Slot(QPoint)
    def showHorizontalHeaderContextMenu(self, pos: QPoint):
        index: QModelIndex = self.indexAt(pos)
        self.headerMenu.popup(self.horizontalHeader().viewport().mapToGlobal(pos))

    @Slot(QPoint)
    def showVerticalHeaderContextMenu(self, pos: QPoint):
        index: QModelIndex = self.indexAt(pos)
        self.headerMenu.popup(self.verticalHeader().viewport().mapToGlobal(pos))

    @Slot()
    def setCheckStateAll(self):
        source = self.sender()
        self._setCheckStateBySender(source, True)

    @Slot()
    def removeCheckStateAll(self):
        source = self.sender()
        self._setCheckStateBySender(source, False)

    @Slot()
    def invertCheckStateAll(self):
        source = self.sender()
        if isinstance(source, QAction):
            if (
                self.horizontalHeader()
                .geometry()
                .contains(self.mapFromGlobal(self.headerMenu.pos()))
            ):
                index: QModelIndex = self.indexAt(
                    self.horizontalHeader().mapFromGlobal(self.headerMenu.pos())
                )
                print(index)
                for r in range(self.model().rowCount()):
                    i = index.siblingAtRow(r)
                    old_value = (
                        i.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
                    )
                    self.model().setData(
                        i, not old_value, role=Qt.ItemDataRole.CheckStateRole
                    )
            elif (
                self.verticalHeader()
                .geometry()
                .contains(self.mapFromGlobal(self.headerMenu.pos()))
            ):
                index: QModelIndex = self.indexAt(
                    self.verticalHeader().mapFromGlobal(self.headerMenu.pos())
                )
                for c in range(self.model().columnCount()):
                    i = index.siblingAtColumn(c)
                    old_value = (
                        i.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
                    )
                    self.model().setData(
                        i, not old_value, role=Qt.ItemDataRole.CheckStateRole
                    )

    def _setCheckStateBySender(self, source, checkState: bool):
        if isinstance(source, QAction):
            if (
                self.horizontalHeader()
                .geometry()
                .contains(self.mapFromGlobal(self.headerMenu.pos()))
            ):
                index: QModelIndex = self.indexAt(
                    self.horizontalHeader().mapFromGlobal(self.headerMenu.pos())
                )
                for r in range(self.model().rowCount()):
                    self.model().setData(
                        index.siblingAtRow(r),
                        checkState,
                        role=Qt.ItemDataRole.CheckStateRole,
                    )
            elif (
                self.verticalHeader()
                .geometry()
                .contains(self.mapFromGlobal(self.headerMenu.pos()))
            ):
                index: QModelIndex = self.indexAt(
                    self.verticalHeader().mapFromGlobal(self.headerMenu.pos())
                )
                for c in range(self.model().columnCount()):
                    self.model().setData(
                        index.siblingAtColumn(c),
                        checkState,
                        role=Qt.ItemDataRole.CheckStateRole,
                    )
