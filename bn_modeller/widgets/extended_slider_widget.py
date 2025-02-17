from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QSlider, QWidget


class ExtendedSliderWidget(QWidget):
    valueChanged = Signal(float)

    def __init__(self, text="", parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self.initUI()
        self.initSignals()
        self._ignore_change_signal = False
        self._is_integer = False
        self.tickNumber = 100

    def initUI(self):
        self._root_layout = QHBoxLayout()

        self.caption = QLabel(self._text)

        self.slider = QSlider()
        self.slider.setRange(0, 1000)
        self.slider.setOrientation(Qt.Horizontal)

        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setRange(0.0, 100.0)
        self.value_spinbox.setSingleStep(0.1)

        self._root_layout.addWidget(self.caption)
        self._root_layout.addWidget(self.slider)
        self._root_layout.addWidget(self.value_spinbox)

        self.setLayout(self._root_layout)

    def value(self):
        return self.value_spinbox.value()

    def setSingleStep(self, step_size: float):
        self.value_spinbox.setSingleStep(step_size)

    def set_integer(self, is_integer: bool):
        self._is_integer = is_integer
        if is_integer:
            self.value_spinbox.setDecimals(0)
        else:
            self.value_spinbox.setDecimals(2)

    def setRange(self, mininum: float, maximum: float):
        self.slider.setRange(
            int(mininum * self.tickNumber), int(maximum * self.tickNumber)
        )
        self.value_spinbox.setRange(mininum, maximum)

    def setValue(self, new_value: float):
        self._ignore_change_signal = True
        self.value_spinbox.setValue(new_value)
        self._ignore_change_signal = True
        self.slider.setValue(int(new_value * self.tickNumber))

    def setTrackMovements(self, trackMovements):
        self._trackMovements = trackMovements

    def initSignals(self):
        self.slider.sliderMoved.connect(self.slider_change_value_handler)
        self.slider.sliderReleased.connect(self.slider_released)
        self.value_spinbox.valueChanged.connect(self.text_change_value_handler)

    def slider_released(self):
        value = self.slider.value()
        self.slider_change_value_handler(value)
        self.valueChanged.emit(value)

    def slider_change_value_handler(self, new_value: float):
        if self._ignore_change_signal:
            self._ignore_change_signal = False
            return
        new_value = new_value / float(self.tickNumber)
        if self._is_integer:
            new_value = int(new_value)
        self._ignore_change_signal = True
        self.value_spinbox.setValue(new_value)
        if self._trackMovements:
            self.valueChanged.emit(new_value)

    def text_change_value_handler(self, new_value: float):
        if self._is_integer:
            new_value = int(new_value)
        if self._ignore_change_signal:
            self._ignore_change_signal = False
            return
        self._ignore_change_signal = True
        self.slider.setValue(int(new_value))
        self.valueChanged.emit(new_value)
