"""Main Qt window for the PyLocator application."""

from __future__ import annotations

from collections import OrderedDict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QGridLayout,
    QLabel,
    QMainWindow,
    QSlider,
    QTextEdit,
    QToolBar,
    QWidget,
)

from ..nifti_loader import NiftiVolume
from .views import SliceView, VolumeView


class MainWindow(QMainWindow):
    """Top-level PyLocator window."""

    request_open_file = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PyLocator")
        self.resize(1400, 900)

        self._current_volume: NiftiVolume | None = None

        self._create_actions()
        self._create_toolbar()
        self._create_views()
        self._create_info_dock()
        self._create_slice_controls()
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    # Qt UI helpers
    # ------------------------------------------------------------------
    def _create_actions(self) -> None:
        self.open_action = QAction("&Open…", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self.request_open_file)

        self.close_action = QAction("E&xit", self)
        self.close_action.setShortcut(QKeySequence.Quit)
        self.close_action.triggered.connect(self.close)

    def _create_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_action)

        toolbar = QToolBar("File", self)
        toolbar.setObjectName("fileToolbar")
        toolbar.addAction(self.open_action)
        self.addToolBar(toolbar)

    def _create_views(self) -> None:
        container = QWidget(self)
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._slice_views: OrderedDict[str, SliceView] = OrderedDict()
        for column, orientation in enumerate(("axial", "coronal")):
            view = SliceView(orientation, container)
            self._slice_views[orientation] = view
            layout.addWidget(view.widget, 0, column)

        sagittal_view = SliceView("sagittal", container)
        self._slice_views["sagittal"] = sagittal_view
        layout.addWidget(sagittal_view.widget, 1, 0)

        self._volume_view = VolumeView(container)
        layout.addWidget(self._volume_view.widget, 1, 1)

        container.setLayout(layout)
        self.setCentralWidget(container)

    def _create_info_dock(self) -> None:
        self._info_panel = QTextEdit(self)
        self._info_panel.setObjectName("infoPanel")
        self._info_panel.setReadOnly(True)

        dock = QDockWidget("Volume information", self)
        dock.setObjectName("volumeInfoDock")
        dock.setWidget(self._info_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _create_slice_controls(self) -> None:
        widget = QWidget(self)
        layout = QFormLayout(widget)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self._slice_sliders: dict[str, QSlider] = {}
        for orientation in self._slice_views:
            label = QLabel(orientation.capitalize(), widget)
            slider = QSlider(Qt.Horizontal, widget)
            slider.setObjectName(f"sliceSlider_{orientation}")
            slider.setMinimum(0)
            slider.setMaximum(0)
            slider.setEnabled(False)
            slider.valueChanged.connect(
                lambda value, orient=orientation: self._slice_views[orient].set_slice(value)
            )
            self._slice_sliders[orientation] = slider
            layout.addRow(label, slider)

        dock = QDockWidget("Slice controls", self)
        dock.setObjectName("sliceControlsDock")
        dock.setWidget(widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(False)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def display_volume(self, volume: NiftiVolume) -> None:
        """Render *volume* inside the VTK viewports."""

        self._current_volume = volume
        self._volume_view.set_volume(volume)

        for orientation, view in self._slice_views.items():
            geometry = view.set_volume(volume)
            slider = self._slice_sliders[orientation]
            slider.blockSignals(True)
            slider.setEnabled(True)
            slider.setMinimum(geometry.minimum)
            slider.setMaximum(geometry.maximum)
            slider.setValue(geometry.current)
            slider.blockSignals(False)

        self._update_info_panel(volume)
        self.statusBar().showMessage(f"Loaded {volume.path.name}")

    # ------------------------------------------------------------------
    # Info panel helpers
    # ------------------------------------------------------------------
    def _update_info_panel(self, volume: NiftiVolume) -> None:
        location = volume.path
        shape = " × ".join(str(v) for v in volume.shape)
        vox = ", ".join(f"{v:.3g}" for v in volume.voxel_size)
        vmin, vmax = volume.value_range

        info = (
            f"Path: {location}\n"
            f"Dimensions: {shape}\n"
            f"Voxel size: {vox} mm\n"
            f"Value range: {vmin:.3g} – {vmax:.3g}"
        )
        self._info_panel.setPlainText(info)


__all__ = ["MainWindow"]
