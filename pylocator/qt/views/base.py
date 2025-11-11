"""Base helpers for VTK-backed Qt views."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkRenderer


class _BaseVTKView(QObject):
    """Common helpers for views backed by QVTKRenderWindowInteractor."""

    marker_added = Signal(int, int, int)  # x, y, z in voxel coordinates

    def __init__(self, parent: QWidget | None = None, *, interactor_style: type | None = None) -> None:
        super().__init__(parent)
        self.frame = QFrame(parent)
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setLineWidth(2)
        self.frame.setStyleSheet("border: 2px solid #888;")
        self.frame.setFocusPolicy(Qt.StrongFocus)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.widget = QVTKRenderWindowInteractor(self.frame)
        self.widget.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.widget)
        self.frame.setLayout(layout)
        self.renderer = vtkRenderer()
        render_window = self.widget.GetRenderWindow()
        render_window.AddRenderer(self.renderer)
        self._interactor = render_window.GetInteractor()
        self._interactor.Initialize()
        if interactor_style is not None:
            self._interactor.SetInteractorStyle(interactor_style())

        self._setup_marker_events()
        self.set_active_frame(False)

    def _setup_marker_events(self):
        self._last_mouse_voxel = None
        try:
            self.widget.installEventFilter(self)
        except Exception:
            pass
        try:
            self.frame.installEventFilter(self)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if obj is not self.widget:
            return False
        if event.type() == event.Type.MouseMove:
            pos = event.position() if hasattr(event, 'position') else event.pos()
            self._last_mouse_voxel = self._map_screen_to_voxel(pos.x(), pos.y())
        elif event.type() == event.Type.MouseButtonPress:
            try:
                self.widget.setFocus(Qt.MouseFocusReason)
                self.set_active_frame(True)
            except Exception:
                pass
        elif event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_I and self._last_mouse_voxel:
                x, y, z = self._last_mouse_voxel
                self.marker_added.emit(x, y, z)
                return True
        elif event.type() == event.Type.FocusIn:
            self.set_active_frame(True)
        elif event.type() == event.Type.FocusOut:
            self.set_active_frame(False)
        return False

    def _map_screen_to_voxel(self, x, y):
        return None

    def set_active_frame(self, active: bool):
        if active:
            self.frame.setStyleSheet("border: 2.5px solid #0078d7;")
        else:
            self.frame.setStyleSheet("border: 2px solid #888;")

    def render(self) -> None:
        self.widget.GetRenderWindow().Render()


__all__ = ["_BaseVTKView"]

