"""Main Qt window for the PyLocator application."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QTextEdit,
    QToolBar,
)
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkRenderer,
    vtkVolume,
    vtkVolumeProperty,
)
try:
    from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
except ImportError:  # pragma: no cover - fallback for alternative VTK builds
    from vtkmodules.vtkRenderingVolume import vtkSmartVolumeMapper

# VTK requires the OpenGL and interaction backends to be imported explicitly.
import vtkmodules.vtkInteractionStyle  # noqa: F401  pylint: disable=unused-import
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401  pylint: disable=unused-import

from ..nifti_loader import NiftiVolume


class MainWindow(QMainWindow):
    """Top-level PyLocator window."""

    request_open_file = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PyLocator")
        self.resize(1200, 800)

        self._current_volume: NiftiVolume | None = None

        self._create_actions()
        self._create_toolbar()
        self._create_vtk_view()
        self._create_info_dock()
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

    def _create_vtk_view(self) -> None:
        self._vtk_widget = QVTKRenderWindowInteractor(self)
        self.setCentralWidget(self._vtk_widget)
        self._vtk_widget.Initialize()

        render_window = self._vtk_widget.GetRenderWindow()
        self._renderer = vtkRenderer()
        render_window.AddRenderer(self._renderer)
        self._interactor = render_window.GetInteractor()
        self._interactor.Initialize()

    def _create_info_dock(self) -> None:
        self._info_panel = QTextEdit(self)
        self._info_panel.setObjectName("infoPanel")
        self._info_panel.setReadOnly(True)

        dock = QDockWidget("Volume information", self)
        dock.setObjectName("volumeInfoDock")
        dock.setWidget(self._info_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def display_volume(self, volume: NiftiVolume) -> None:
        """Render *volume* inside the VTK viewport."""

        self._current_volume = volume
        self._renderer.RemoveAllViewProps()

        mapper = vtkSmartVolumeMapper()
        mapper.SetInputData(volume.image_data)

        min_val, max_val = volume.value_range
        if max_val - min_val < 1e-5:
            max_val = min_val + 1.0

        color_tf = vtkColorTransferFunction()
        color_tf.AddRGBPoint(min_val, 0.0, 0.0, 0.0)
        color_tf.AddRGBPoint(max_val, 1.0, 1.0, 1.0)

        opacity_tf = vtkPiecewiseFunction()
        opacity_tf.AddPoint(min_val, 0.0)
        opacity_tf.AddPoint(max_val, 1.0)

        properties = vtkVolumeProperty()
        properties.SetColor(color_tf)
        properties.SetScalarOpacity(opacity_tf)
        properties.SetInterpolationTypeToLinear()

        actor = vtkVolume()
        actor.SetMapper(mapper)
        actor.SetProperty(properties)

        self._renderer.AddVolume(actor)
        self._renderer.ResetCamera()
        self._vtk_widget.GetRenderWindow().Render()

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
