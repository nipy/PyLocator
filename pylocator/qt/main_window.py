
from __future__ import annotations

from typing import List

"""Main Qt window for the PyLocator application."""

from collections import OrderedDict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QGridLayout,
    QCheckBox,
    QLabel,
    QMainWindow,
    QSlider,
    QTextEdit,
    QToolBar,
    QWidget,
    QPushButton,
    QColorDialog,
)

from ..nifti_loader import NiftiVolume
from .models import Marker
import logging
logging.basicConfig(level=logging.WARNING)
from .views import SliceView, VolumeView


from .widgets.gamma_slider import GammaSlider

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
        self._create_isosurface_controls()
        self._create_marker_list_panel()
        self._create_view_menu()
        # Arrange default dock layout: controls on top, info below
        self._reset_dock_layout()
        # Wire iso-surface stats once
        try:
            self._volume_view.iso_stats_changed.connect(self._on_iso_stats_changed)
        except Exception:
            logging.exception("Failed to connect iso_stats_changed signal")
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
        self._dock_markers = dock

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
        self._dock_info = dock

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
        self._dock_slice = dock

    def _create_volume_controls(self) -> None:
        widget = QWidget(self)
        layout = QFormLayout(widget)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Show/Hide volume
        vol_toggle = QCheckBox("Show Volume", widget)
        vol_toggle.setObjectName("showVolumeCheck")
        vol_toggle.setChecked(True)
        vol_toggle.toggled.connect(lambda v: self._volume_view.set_volume_enabled(v))
        layout.addRow(vol_toggle)

        opacity_label = QLabel("Opacity", widget)
        self._vol_opacity = GammaSlider(widget, gamma=2.0, initial=0.8)
        # Preserve legacy objectName on inner slider for tests/tools
        self._vol_opacity.slider.setObjectName("volumeOpacitySlider")
        self._vol_opacity.valueChanged.connect(self._volume_view.set_opacity_factor)
        layout.addRow(opacity_label, self._vol_opacity)

        # Apply initial opacity to view via control emit
        self._vol_opacity.setValue(0.8)

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
        self._dock_volume = dock

    def _create_isosurface_controls(self) -> None:
        widget = QWidget(self)
        layout = QFormLayout(widget)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Enable toggle
        self._iso_enable = QCheckBox("Enable IsoSurface", widget)
        self._iso_enable.setObjectName("isoEnableCheck")
        self._iso_enable.setChecked(False)
        self._iso_enable.toggled.connect(lambda v: self._volume_view.set_isosurface_enabled(v))
        layout.addRow(self._iso_enable)


        # Isovalue slider (mapped 0..1000 -> value_range)
        self._iso_value_slider = QSlider(Qt.Horizontal, widget)
        self._iso_value_slider.setObjectName("isoValueSlider")
        self._iso_value_slider.setMinimum(0)
        self._iso_value_slider.setMaximum(1000)
        self._iso_value_slider.setEnabled(False)

        self._iso_value_label = QLabel("—", widget)
        self._iso_value_label.setObjectName("isoValueLabel")

        def on_iso_value_changed(pos: int) -> None:
            if not self._current_volume:
                return
            vmin, vmax = self._current_volume.value_range
            t = max(0.0, min(1.0, pos / 1000.0))
            value = vmin + t * (vmax - vmin)
            self._volume_view.set_isosurface_value(value)
            self._iso_value_label.setText(f"{value:.3g}")
            # update stats as in-progress
            if hasattr(self, "_iso_tri_label"):
                self._iso_tri_label.setText("…")
            if hasattr(self, "_iso_time_label"):
                self._iso_time_label.setText("…")

        self._iso_value_slider.valueChanged.connect(on_iso_value_changed)
        layout.addRow(QLabel("Isovalue", widget), self._iso_value_slider)
        layout.addRow(QLabel("Value", widget), self._iso_value_label)

        # Opacity control using non-linear slider
        # Use gamma < 1 for coarser response in the low range
        self._iso_opacity_control = GammaSlider(widget, gamma=0.7, initial=0.6)
        self._iso_opacity_control.setEnabled(False)
        self._iso_opacity_control.slider.setObjectName("isoOpacitySlider")
        self._iso_opacity_control.valueChanged.connect(self._volume_view.set_isosurface_opacity)
        layout.addRow(QLabel("Opacity", widget), self._iso_opacity_control)

        # Color picker button
        self._iso_color_btn = QPushButton("Color…", widget)
        self._iso_color_btn.setObjectName("isoColorButton")
        def on_pick_color() -> None:
            col = QColorDialog.getColor(parent=self)
            if col.isValid():
                self._volume_view.set_isosurface_color(col.redF(), col.greenF(), col.blueF())
        self._iso_color_btn.clicked.connect(on_pick_color)
        layout.addRow(self._iso_color_btn)

        # Stats
        self._iso_tri_label = QLabel("—", widget)
        self._iso_tri_label.setObjectName("isoTrianglesLabel")
        layout.addRow(QLabel("Triangles", widget), self._iso_tri_label)

        self._iso_time_label = QLabel("—", widget)
        self._iso_time_label.setObjectName("isoTimeLabel")
        layout.addRow(QLabel("Time (ms)", widget), self._iso_time_label)

        dock = QDockWidget("IsoSurface", self)
        dock.setObjectName("isoSurfaceDock")
        dock.setWidget(widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(False)
        self._dock_iso = dock

    # ------------------------------------------------------------------
    # View menu and dock layout
    # ------------------------------------------------------------------
    def _create_view_menu(self) -> None:
        view_menu = self.menuBar().addMenu("&View")

        def add_toggle(title: str, dock: QDockWidget):
            act = view_menu.addAction(title)
            act.setCheckable(True)
            act.setChecked(dock.isVisible())
            act.toggled.connect(dock.setVisible)
            try:
                dock.visibilityChanged.connect(act.setChecked)
            except Exception:
                pass
            return act

        # Controls first
        add_toggle("Slice controls", self._dock_slice)
        add_toggle("Volume controls", self._dock_volume)
        add_toggle("IsoSurface", self._dock_iso)
        add_toggle("Markers", self._dock_markers)
        view_menu.addSeparator()
        # Info panels
        add_toggle("Volume information", self._dock_info)
        view_menu.addSeparator()

        reset_action = view_menu.addAction("Reset Layout")
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self._reset_dock_layout)

    def _reset_dock_layout(self) -> None:
        # Ensure docks are visible and stacked: controls first (top), then info below
        docks = [
            getattr(self, name, None)
            for name in ("_dock_slice", "_dock_volume", "_dock_iso", "_dock_markers", "_dock_info")
        ]
        docks = [d for d in docks if d is not None]
        if not docks:
            return
        for d in docks:
            try:
                d.setFloating(False)
                d.setVisible(True)
            except Exception:
                pass
        # Re-add and split to enforce order
        anchor = docks[0]
        try:
            self.addDockWidget(Qt.RightDockWidgetArea, anchor)
        except Exception:
            pass
        prev = anchor
        for d in docks[1:]:
            try:
                self.splitDockWidget(prev, d, Qt.Vertical)
            except Exception:
                pass
            prev = d

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def display_volume(self, volume: NiftiVolume) -> None:
        """Render *volume* inside the VTK viewports."""

        self._current_volume = volume
        self._volume_view.set_volume(volume)
        # Apply current show/hide state (default: on)
        try:
            show = True
            # If the checkbox exists, use its value
            chk = self.findChild(QCheckBox, "showVolumeCheck")
            if chk is not None:
                show = chk.isChecked()
            self._volume_view.set_volume_enabled(show)
        except Exception:
            logging.exception("Failed to apply volume visibility state on load")

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


        # Init IsoSurface controls based on volume range
        vmin, vmax = volume.value_range
        # Set slider to mid by default
        mid = int(round(0.5 * 1000))
        self._iso_value_slider.blockSignals(True)
        self._iso_value_slider.setEnabled(True)
        self._iso_value_slider.setValue(mid)
        self._iso_value_slider.blockSignals(False)
        # Apply value to view and label
        iso_val = vmin + 0.5 * (vmax - vmin)
        self._volume_view.set_isosurface_value(iso_val)
        self._iso_value_label.setText(f"{iso_val:.3g}")
        self._iso_opacity_control.setEnabled(True)
        self._iso_enable.setEnabled(True)

    def _on_iso_stats_changed(self, triangles: int, ms: float) -> None:
        try:
            self._iso_tri_label.setText(str(triangles))
            self._iso_time_label.setText(f"{ms:.1f}")
        except Exception:
            logging.exception("Failed updating iso-surface stats labels")
        # Optional: brief status update without referencing volume
        try:
            self.statusBar().showMessage(f"IsoSurface: {triangles} tris, {ms:.1f} ms")
        except Exception:
            logging.exception("Failed to update status bar message for iso-surface stats")

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
