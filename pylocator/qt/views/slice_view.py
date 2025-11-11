"""Orthogonal 2-D slice view into the volume."""
from __future__ import annotations

import math
import logging
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkRenderingCore import (
    vtkImageProperty,
    vtkImageSlice,
    vtkImageSliceMapper,
    vtkActor,
    vtkPolyDataMapper,
    vtkPropPicker,
)

from ...nifti_loader import NiftiVolume
from ..models import Marker
from .base import _BaseVTKView


@dataclass(slots=True)
class SliceGeometry:
    orientation: str
    minimum: int
    maximum: int
    current: int


class SliceView(_BaseVTKView):
    def focusInEvent(self, event):
        self.set_active_frame(True)
        self.frame.setFocus(Qt.OtherFocusReason)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.set_active_frame(False)
        super().focusOutEvent(event)

    def mousePressEvent(self, event):
        self.frame.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)

    def set_markers(self, markers):
        try:
            self._last_markers = list(markers)
        except Exception:
            logging.exception("SliceView.set_markers: failed to copy markers; resetting cache")
            self._last_markers = []
        for actor in getattr(self, '_marker_actors', []):
            self.renderer.RemoveActor(actor)
        self._marker_actors = []
        if self._volume is None or self._geometry is None:
            self.render()
            return
        from vtkmodules.vtkFiltersSources import vtkRegularPolygonSource
        orientation = self.orientation
        slice_idx = int(self._geometry.current)
        spacing = self._volume.voxel_size
        cam = self.renderer.GetActiveCamera()
        height_world = 2.0 * cam.GetParallelScale()
        base_radius = max(min(spacing) * 2.5, 0.02 * height_world)
        try:
            base_radius *= float(self._marker_size_factor)
        except Exception:
            logging.exception("SliceView.set_markers: invalid _marker_size_factor; using base radius")
        for marker in markers:
            mx, my, mz = [m * s for m, s in zip((marker.x, marker.y, marker.z), spacing)]
            if orientation == 'axial':
                plane_pos = slice_idx * spacing[2]
                d = abs(plane_pos - mz)
                normal = (0, 0, 1)
                center = (mx, my, plane_pos)
            elif orientation == 'coronal':
                plane_pos = slice_idx * spacing[1]
                d = abs(plane_pos - my)
                normal = (0, 1, 0)
                center = (mx, plane_pos, mz)
            else:
                plane_pos = slice_idx * spacing[0]
                d = abs(plane_pos - mx)
                normal = (1, 0, 0)
                center = (plane_pos, my, mz)
            if d > base_radius:
                continue
            ring_radius = max(min(spacing) * 1.0, math.sqrt(max(base_radius * base_radius - d * d, 0.0)))
            cam = self.renderer.GetActiveCamera()
            cx, cy, cz = cam.GetPosition()
            vx, vy, vz = center
            dirx, diry, dirz = cx - vx, cy - vy, cz - vz
            norm = math.sqrt(dirx * dirx + diry * diry + dirz * dirz)
            if norm > 1e-9:
                eps = 0.1 * min(spacing)
                center = (vx + eps * dirx / norm, vy + eps * diry / norm, vz + eps * dirz / norm)
            ring = vtkRegularPolygonSource()
            ring.SetCenter(*center)
            ring.SetNormal(*normal)
            ring.SetRadius(ring_radius)
            ring.SetNumberOfSides(32)
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(ring.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(1, 0, 0)
            lw = 2
            if hasattr(self, "_ring_thickness"):
                try:
                    lw = max(1, int(round(2 * float(self._ring_thickness))))
                except Exception:
                    logging.exception("SliceView.set_markers: invalid _ring_thickness; using default")
                    lw = 2
            actor.GetProperty().SetLineWidth(lw)
            actor.GetProperty().SetOpacity(1.0)
            actor.GetProperty().SetRepresentationToWireframe()
            self.renderer.AddActor(actor)
            self._marker_actors.append(actor)
        self.render()

    def set_marker_size_factor(self, factor: float) -> None:
        self._marker_size_factor = max(0.1, min(5.0, float(factor)))
        self.set_markers(getattr(self, "_last_markers", []))

    def set_ring_thickness(self, factor: float) -> None:
        self._ring_thickness = max(0.25, min(5.0, float(factor)))
        self.set_markers(getattr(self, "_last_markers", []))

    def __init__(self, orientation: str, parent: QWidget | None = None) -> None:
        super().__init__(parent, interactor_style=vtkInteractorStyleImage)
        self.orientation = orientation
        self._volume: NiftiVolume | None = None
        self._mapper = vtkImageSliceMapper()
        self._actor = vtkImageSlice()
        self._actor.SetMapper(self._mapper)
        self.renderer.AddViewProp(self._actor)
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        self.renderer.SetBackground(0.0, 0.0, 0.0)
        self._geometry: SliceGeometry | None = None
        self._marker_size_factor: float = 1.0
        self._ring_thickness: float = 1.0
        self._last_markers: list[Marker] = []
        self._picker = vtkPropPicker()
        self._picker.PickFromListOn()
        self._picker.AddPickList(self._actor)

        self._setup_marker_events()
        self.widget.setFocusPolicy(Qt.StrongFocus)
        self.set_active_frame(False)

        if self.orientation == "axial":
            self._mapper.SetOrientationToZ()
            cam = self.renderer.GetActiveCamera()
            cam.SetViewUp(0.0, 1.0, 0.0)
            cam.SetPosition(0.0, 0.0, 1.0)
        elif self.orientation == "coronal":
            self._mapper.SetOrientationToY()
            cam = self.renderer.GetActiveCamera()
            cam.SetViewUp(0.0, 0.0, 1.0)
            cam.SetPosition(0.0, -1.0, 0.0)
        elif self.orientation == "sagittal":
            self._mapper.SetOrientationToX()
            cam = self.renderer.GetActiveCamera()
            cam.SetViewUp(0.0, 0.0, 1.0)
            cam.SetPosition(1.0, 0.0, 0.0)
        else:
            raise ValueError(f"Unsupported orientation: {self.orientation}")

    def _map_screen_to_voxel(self, x, y):
        if self._volume is None or self._geometry is None:
            return None
        try:
            dpr = float(self.widget.devicePixelRatioF())
        except Exception:
            logging.exception("SliceView._map_screen_to_voxel: devicePixelRatioF() failed; defaulting to 1.0")
            dpr = 1.0
        h = self.widget.height()
        display_x = x * dpr
        display_y = (h - y) * dpr
        success = self._picker.Pick(display_x, display_y, 0, self.renderer)
        if not success:
            return None
        if self._picker.GetViewProp() is not self._actor:
            return None
        wx, wy, wz = self._picker.GetPickPosition()
        sx, sy, sz = self._volume.voxel_size
        if self.orientation == "axial":
            vx = int(round(wx / sx))
            vy = int(round(wy / sy))
            vz = int(self._geometry.current)
        elif self.orientation == "coronal":
            vx = int(round(wx / sx))
            vy = int(self._geometry.current)
            vz = int(round(wz / sz))
        else:
            vx = int(self._geometry.current)
            vy = int(round(wy / sy))
            vz = int(round(wz / sz))
        shape = self._volume.shape
        vx = max(0, min(vx, shape[0] - 1))
        vy = max(0, min(vy, shape[1] - 1))
        vz = max(0, min(vz, shape[2] - 1))
        return (vx, vy, vz)

    @property
    def geometry(self) -> SliceGeometry | None:
        return self._geometry

    def set_volume(self, volume: NiftiVolume) -> SliceGeometry:
        self._volume = volume
        image = volume.image_data
        self._mapper.SetInputData(image)
        extent = image.GetExtent()
        if self.orientation == "axial":
            minimum, maximum = extent[4], extent[5]
        elif self.orientation == "coronal":
            minimum, maximum = extent[2], extent[3]
        else:
            minimum, maximum = extent[0], extent[1]
        current = (minimum + maximum) // 2
        geometry = SliceGeometry(self.orientation, minimum, maximum, current)
        self._geometry = geometry
        self._mapper.SetSliceNumber(current)

        prop: vtkImageProperty = self._actor.GetProperty()
        min_val, max_val = volume.value_range
        if max_val - min_val < 1e-5:
            max_val = min_val + 1.0
        prop.SetColorLevel((max_val + min_val) / 2.0)
        prop.SetColorWindow(max_val - min_val)
        prop.SetInterpolationTypeToLinear()

        self.renderer.ResetCamera()
        self.render()
        return geometry

    def set_slice(self, index: int) -> None:
        if self._volume is None:
            return
        if self._geometry is None:
            raise RuntimeError("Slice geometry is not initialised")
        clamped = max(self._geometry.minimum, min(self._geometry.maximum, index))
        self._mapper.SetSliceNumber(clamped)
        self._geometry = SliceGeometry(
            self._geometry.orientation, self._geometry.minimum, self._geometry.maximum, clamped
        )
        self.render()


__all__ = ["SliceView", "SliceGeometry"]
