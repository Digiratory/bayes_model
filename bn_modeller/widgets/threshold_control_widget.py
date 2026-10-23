from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QWidget,
)

_SLIDER_SCALE = 1000  # slider range 0..1000 maps to 0.0..1.0


class ThresholdControlWidget(QWidget):
    """
    Widget for controlling threshold type and value for feature filtering.
    Provides a dropdown for threshold type selection and a slider for value adjustment.
    """

    thresholdChanged = Signal(str, float)  # threshold_type, threshold_value

    _CRITERION_DEFAULTS = {"R": 0.0, "P": 0.0, "P_val": 0.05}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Threshold type dropdown
        self.threshold_type_combo = QComboBox()
        self.threshold_type_combo.addItems(list(self._CRITERION_DEFAULTS))
        self.threshold_type_combo.setCurrentIndex(0)  # Default to "R" (correlation)
        self.threshold_type_combo.currentTextChanged.connect(
            self._onThresholdTypeChanged
        )

        # Threshold value slider
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, _SLIDER_SCALE)
        self.threshold_slider.setValue(0)
        self.threshold_slider.valueChanged.connect(self._onSliderValueChanged)

        # Threshold value display
        self.threshold_display = QDoubleSpinBox()
        self.threshold_display.setRange(0.0, 1.0)
        self.threshold_display.setDecimals(3)
        self.threshold_display.setSingleStep(0.01)
        self.threshold_display.setValue(0.0)
        self.threshold_display.valueChanged.connect(self._onSpinBoxValueChanged)

        # Labels
        layout.addWidget(QLabel("Threshold Type:"))
        layout.addWidget(self.threshold_type_combo)
        layout.addWidget(QLabel("Value:"))
        layout.addWidget(self.threshold_slider)
        layout.addWidget(self.threshold_display)

        # Set stretch factors
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        layout.setStretch(2, 0)
        layout.setStretch(3, 2)
        layout.setStretch(4, 1)

    def _onThresholdTypeChanged(self, threshold_type: str):
        """Reset the value to the criterion default and notify"""
        default = self._CRITERION_DEFAULTS.get(threshold_type, 0.0)
        self._setValue(default)
        self.thresholdChanged.emit(threshold_type, default)

    def _onSliderValueChanged(self, value: int):
        """Handle slider value changes"""
        float_value = value / _SLIDER_SCALE
        self.threshold_display.blockSignals(True)
        self.threshold_display.setValue(float_value)
        self.threshold_display.blockSignals(False)

        self.thresholdChanged.emit(self.threshold_type_combo.currentText(), float_value)

    def _onSpinBoxValueChanged(self, value: float):
        """Handle spinbox value changes"""
        self.threshold_slider.blockSignals(True)
        self.threshold_slider.setValue(round(value * _SLIDER_SCALE))
        self.threshold_slider.blockSignals(False)

        self.thresholdChanged.emit(self.threshold_type_combo.currentText(), value)

    def _setValue(self, value: float):
        """Set both controls to the value without emitting thresholdChanged"""
        self.threshold_display.blockSignals(True)
        self.threshold_display.setValue(value)
        self.threshold_display.blockSignals(False)

        self.threshold_slider.blockSignals(True)
        self.threshold_slider.setValue(round(value * _SLIDER_SCALE))
        self.threshold_slider.blockSignals(False)

    def setThreshold(self, threshold_type: str, threshold_value: float):
        """Set threshold type and value programmatically and notify"""
        index = self.threshold_type_combo.findText(threshold_type)
        if index >= 0:
            self.threshold_type_combo.blockSignals(True)
            self.threshold_type_combo.setCurrentIndex(index)
            self.threshold_type_combo.blockSignals(False)

        self._setValue(threshold_value)
        self.thresholdChanged.emit(
            self.threshold_type_combo.currentText(), self.threshold_display.value()
        )

    def getThreshold(self) -> tuple[str, float]:
        """Get current threshold settings"""
        return self.threshold_type_combo.currentText(), self.threshold_display.value()
