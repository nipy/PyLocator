from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QGridLayout, QSlider, QLabel


class GammaSlider(QWidget):
    valueChanged = Signal(float)

    def __init__(self, parent=None, *, gamma: float = 2.0, initial: float | None = None):
        super().__init__(parent)
        self._gamma = float(gamma)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self._label = QLabel("", self)
        layout.addWidget(self.slider, 0, 0)
        layout.addWidget(self._label, 0, 1)

        def on_changed(pos: int) -> None:
            t = max(0.0, min(1.0, pos / 100.0))
            v = t ** self._gamma
            self._label.setText(f"{v*100:.1f}%")
            self.valueChanged.emit(v)

        self.slider.valueChanged.connect(on_changed)
        if initial is not None:
            self.setValue(initial)

    def setValue(self, value: float) -> None:
        v = max(0.0, min(1.0, float(value)))
        # Map value in [0,1] to slider position using inverse gamma
        pos = int(round((v ** (1.0 / self._gamma)) * 100.0)) if self._gamma != 0 else int(round(v * 100.0))
        old = self.slider.blockSignals(True)
        try:
            self.slider.setValue(pos)
        finally:
            self.slider.blockSignals(old)
        # Manually update label and emit
        self._label.setText(f"{v*100:.1f}%")
        self.valueChanged.emit(v)

    def value(self) -> float:
        t = max(0.0, min(1.0, self.slider.value() / 100.0))
        return t ** self._gamma if self._gamma != 0 else t

__all__ = ["GammaSlider"]

