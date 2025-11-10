
from __future__ import annotations

from dataclasses import dataclass
from typing import List
@dataclass
class Marker:
    x: int
    y: int
    z: int

"""Main Qt window for the PyLocator application."""

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
    # Marker management
    markers: List[Marker] = []
    """Top-level PyLocator window."""

    request_open_file = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PyLocator")
        self.resize(1400, 900)

        self._current_volume: NiftiVolume | None = None

        # Marker list
        self.markers: List[Marker] = []

        self._create_actions()
        self._create_toolbar()
        self._create_views()
        self._create_info_dock()
        self._create_slice_controls()
        self._create_volume_controls()
        self._create_marker_list_panel()
        self.statusBar().showMessage("Ready")

    def _create_marker_list_panel(self) -> None:
        from PySide6.QtWidgets import QListWidget, QDockWidget

        self._marker_list_widget = QListWidget(self)
        self._marker_list_widget.setObjectName("markerListWidget")

        dock = QDockWidget("Markers", self)
        dock.setObjectName("markerListDock")
        dock.setWidget(self._marker_list_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(False)

    def add_marker(self, x: int, y: int, z: int) -> None:
        marker = Marker(x, y, z)
        self.markers.append(marker)
        self._update_marker_list()
        # Update marker visualization in all views
        for view in self._slice_views.values():
            view.set_markers(self.markers)
        self._volume_view.set_markers(self.markers)

    def _update_marker_list(self) -> None:
        self._marker_list_widget.clear()
        for idx, marker in enumerate(self.markers, 1):
            self._marker_list_widget.addItem(f"#{idx}: ({marker.x}, {marker.y}, {marker.z})")

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

        #toolbar = QToolBar("File", self)
        #toolbar.setObjectName("fileToolbar")
        #toolbar.addAction(self.open_action)
        #self.addToolBar(toolbar)

    def _create_views(self) -> None:
        container = QWidget(self)
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._slice_views: OrderedDict[str, SliceView] = OrderedDict()
        for column, orientation in enumerate(("axial", "coronal")):
            view = SliceView(orientation, container)
            view.marker_added.connect(self.add_marker)
            self._slice_views[orientation] = view
            layout.addWidget(view.frame, 0, column)

        sagittal_view = SliceView("sagittal", container)
        sagittal_view.marker_added.connect(self.add_marker)
        self._slice_views["sagittal"] = sagittal_view
        layout.addWidget(sagittal_view.frame, 1, 0)

        self._volume_view = VolumeView(container)
        self._volume_view.marker_added.connect(self.add_marker)
        layout.addWidget(self._volume_view.frame, 1, 1)

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
            def on_slice_changed(value, orient=orientation):
                view = self._slice_views[orient]
                view.set_slice(value)
                # Reapply markers to update per-slice overlays
                view.set_markers(self.markers)

            slider.valueChanged.connect(on_slice_changed)
            self._slice_sliders[orientation] = slider
            layout.addRow(label, slider)

        dock = QDockWidget("Slice controls", self)
        dock.setObjectName("sliceControlsDock")
        dock.setWidget(widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(False)

    def _create_volume_controls(self) -> None:
        widget = QWidget(self)
        layout = QFormLayout(widget)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        opacity_label = QLabel("Opacity", widget)
        opacity_slider = QSlider(Qt.Horizontal, widget)
        opacity_slider.setObjectName("volumeOpacitySlider")
        opacity_slider.setMinimum(0)
        opacity_slider.setMaximum(100)
        opacity_slider.setValue(80)

        def on_opacity_changed(value: int) -> None:
            factor = value / 100.0
            self._volume_view.set_opacity_factor(factor)

        opacity_slider.valueChanged.connect(on_opacity_changed)
        layout.addRow(opacity_label, opacity_slider)

        # Apply initial value
        self._volume_view.set_opacity_factor(opacity_slider.value() / 100.0)

        # Marker size (affects 3D spheres and ring radii)
        size_label = QLabel("Marker size", widget)
        size_slider = QSlider(Qt.Horizontal, widget)
        size_slider.setObjectName("markerSizeSlider")
        size_slider.setMinimum(50)
        size_slider.setMaximum(200)
        size_slider.setValue(100)

        def on_size_changed(value: int) -> None:
            factor = value / 100.0
            self._volume_view.set_marker_size_factor(factor)
            for view in self._slice_views.values():
                view.set_marker_size_factor(factor)

        size_slider.valueChanged.connect(on_size_changed)
        layout.addRow(size_label, size_slider)

        # Ring thickness (2D overlay line width)
        thick_label = QLabel("Ring thickness", widget)
        thick_slider = QSlider(Qt.Horizontal, widget)
        thick_slider.setObjectName("ringThicknessSlider")
        thick_slider.setMinimum(1)
        thick_slider.setMaximum(10)
        thick_slider.setValue(3)

        def on_thickness_changed(value: int) -> None:
            factor = value / 2.0  # map 1..10 to 0.5..5.0
            for view in self._slice_views.values():
                view.set_ring_thickness(factor)

        thick_slider.valueChanged.connect(on_thickness_changed)
        layout.addRow(thick_label, thick_slider)

        # Apply initial values
        on_size_changed(size_slider.value())
        on_thickness_changed(thick_slider.value())

        dock = QDockWidget("Volume controls", self)
        dock.setObjectName("volumeControlsDock")
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

        # Ensure current markers are drawn on the new volume
        for view in self._slice_views.values():
            view.set_markers(self.markers)
        self._volume_view.set_markers(self.markers)

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
