"""3-D volume rendering view with iso-surface overlay."""
from __future__ import annotations

import math
import logging

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkVolume,
    vtkVolumeProperty,
    vtkActor,
    vtkPolyDataMapper,
    vtkCellPicker,
)
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkFiltersCore import vtkFlyingEdges3D, vtkPolyDataNormals
try:  # optional fallback
    from vtkmodules.vtkFiltersCore import vtkMarchingCubes
except Exception:  # pragma: no cover
    vtkMarchingCubes = None

try:
    from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
except ImportError:  # pragma: no cover
    from vtkmodules.vtkRenderingVolume import vtkSmartVolumeMapper

from ...nifti_loader import NiftiVolume
from ..models import Marker
from .base import _BaseVTKView


class VolumeView(_BaseVTKView):
    """3-D volume rendering viewport."""

    iso_stats_changed = Signal(int, float)  # triangles, elapsed_ms

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, interactor_style=vtkInteractorStyleTrackballCamera)
        self.renderer.SetBackground(0.1, 0.1, 0.1)
        self._volume: NiftiVolume | None = None
        self._marker_actors = []
        self._opacity_factor: float = 1.0
        self._marker_size_factor: float = 1.0
        self._value_range: tuple[float, float] | None = None
        self._volume_property: vtkVolumeProperty | None = None
        self._opacity_tf: vtkPiecewiseFunction | None = None
        self._volume_actor: vtkVolume | None = None
        self._volume_enabled: bool = True
        self._last_markers: list[Marker] = []
        # Iso-surface state
        self._iso_enabled: bool = False
        self._iso_value: float | None = None
        self._iso_color: tuple[float, float, float] = (0.2, 0.8, 0.8)
        self._iso_opacity: float = 0.6
        self._iso_actor: vtkActor | None = None
        self._iso_picker = vtkCellPicker()
        try:
            self._iso_picker.PickFromListOn()
        except Exception:
            logging.exception("VolumeView: failed to enable PickFromList for iso picker")

    def set_markers(self, markers):
        try:
            self._last_markers = list(markers)
        except Exception:
            logging.exception("VolumeView.set_markers: failed to copy markers; resetting cache")
            self._last_markers = []
        for actor in getattr(self, '_marker_actors', []):
            self.renderer.RemoveActor(actor)
        self._marker_actors = []
        if self._volume is None:
            self.render()
            return
        sx, sy, sz = self._volume.voxel_size
        nx, ny, nz = self._volume.shape
        diag = math.sqrt((nx * sx) ** 2 + (ny * sy) ** 2 + (nz * sz) ** 2)
        sphere_radius = max(min(sx, sy, sz) * 2.5, 0.01 * diag) * float(self._marker_size_factor)
        from vtkmodules.vtkFiltersSources import vtkSphereSource
        for marker in markers:
            spacing = self._volume.voxel_size
            x, y, z = [m * s for m, s in zip((marker.x, marker.y, marker.z), spacing)]
            sphere = vtkSphereSource()
            sphere.SetCenter(x, y, z)
            sphere.SetRadius(sphere_radius)
            sphere.SetThetaResolution(16)
            sphere.SetPhiResolution(16)
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(1, 0, 0)
            actor.GetProperty().SetOpacity(0.7)
            self.renderer.AddActor(actor)
            self._marker_actors.append(actor)
        try:
            self.renderer.ResetCameraClippingRange()
        except Exception:
            logging.exception("VolumeView: ResetCameraClippingRange failed after marker update")
        self.render()

    def _map_screen_to_voxel(self, x, y):
        if self._volume is None or not self._iso_enabled or self._iso_actor is None:
            return None
        try:
            try:
                dpr = float(self.widget.devicePixelRatioF())
            except Exception:
                logging.exception("VolumeView._map_screen_to_voxel: devicePixelRatioF failed; using 1.0")
                dpr = 1.0
            h = self.widget.height()
            display_x = x * dpr
            display_y = (h - y) * dpr
            try:
                self._iso_picker.InitializePickList()
                self._iso_picker.AddPickList(self._iso_actor)
            except Exception:
                pass
            success = self._iso_picker.Pick(display_x, display_y, 0, self.renderer)
            if not success:
                return None
            if self._iso_picker.GetActor() is not self._iso_actor:
                return None
            wx, wy, wz = self._iso_picker.GetPickPosition()
            sx, sy, sz = self._volume.voxel_size
            nx, ny, nz = self._volume.shape
            vx = int(round(wx / sx))
            vy = int(round(wy / sy))
            vz = int(round(wz / sz))
            vx = max(0, min(nx - 1, vx))
            vy = max(0, min(ny - 1, vy))
            vz = max(0, min(nz - 1, vz))
            return (vx, vy, vz)
        except Exception:
            logging.exception("VolumeView iso pick failed")
            return None

    def set_volume(self, volume: NiftiVolume) -> None:
        self.renderer.RemoveAllViewProps()
        self._volume = volume
        self._value_range = volume.value_range

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
        opacity_tf.AddPoint(max_val, self._opacity_factor)

        properties = vtkVolumeProperty()
        properties.SetColor(color_tf)
        properties.SetScalarOpacity(opacity_tf)
        properties.SetInterpolationTypeToLinear()

        actor = vtkVolume()
        actor.SetMapper(mapper)
        actor.SetProperty(properties)

        self._volume_property = properties
        self._opacity_tf = opacity_tf
        self._volume_actor = actor

        self.renderer.AddVolume(actor)
        try:
            actor.SetVisibility(1 if self._volume_enabled else 0)
        except Exception:
            pass
        self.renderer.ResetCamera()
        try:
            vmin, vmax = volume.value_range
            self._iso_value = float(vmin + 0.5 * (vmax - vmin))
        except Exception:
            logging.exception("VolumeView.set_volume: failed to compute default iso value")
            self._iso_value = None
        self._update_isosurface()
        self.render()

    def set_marker_size_factor(self, factor: float) -> None:
        self._marker_size_factor = max(0.1, min(5.0, float(factor)))
        self.set_markers(self._last_markers)

    def set_opacity_factor(self, factor: float) -> None:
        self._opacity_factor = max(0.0, min(1.0, float(factor)))
        if self._opacity_tf is None or self._value_range is None:
            return
        min_val, max_val = self._value_range
        self._opacity_tf.RemoveAllPoints()
        self._opacity_tf.AddPoint(min_val, 0.0)
        self._opacity_tf.AddPoint(max_val, self._opacity_factor)
        self.render()

    def set_volume_enabled(self, enabled: bool) -> None:
        self._volume_enabled = bool(enabled)
        if self._volume_actor is not None:
            try:
                self._volume_actor.SetVisibility(1 if self._volume_enabled else 0)
            except Exception:
                logging.exception("VolumeView.set_volume_enabled: failed to set visibility")
            self.render()

    # Iso-surface controls
    def set_isosurface_enabled(self, enabled: bool) -> None:
        self._iso_enabled = bool(enabled)
        self._update_isosurface()

    def set_isosurface_value(self, value: float) -> None:
        try:
            self._iso_value = float(value)
        except Exception:
            logging.exception("VolumeView.set_isosurface_value: invalid value")
            return
        self._update_isosurface()

    def set_isosurface_opacity(self, opacity: float) -> None:
        self._iso_opacity = max(0.0, min(1.0, float(opacity)))
        if self._iso_actor is not None:
            try:
                self._iso_actor.GetProperty().SetOpacity(self._iso_opacity)
            except Exception:
                logging.exception("VolumeView.set_isosurface_opacity: failed to set opacity")
            self.render()

    def set_isosurface_color(self, r: float, g: float, b: float) -> None:
        self._iso_color = (max(0.0, min(1.0, float(r))),
                           max(0.0, min(1.0, float(g))),
                           max(0.0, min(1.0, float(b))))
        if self._iso_actor is not None:
            try:
                self._iso_actor.GetProperty().SetColor(*self._iso_color)
            except Exception:
                logging.exception("VolumeView.set_isosurface_color: failed to set color")
            self.render()

    def _update_isosurface(self) -> None:
        if not self._iso_enabled or self._volume is None or self._iso_value is None:
            if self._iso_actor is not None:
                try:
                    self.renderer.RemoveActor(self._iso_actor)
                except Exception:
                    logging.exception("VolumeView: failed to remove iso-surface actor")
                self._iso_actor = None
            self.render()
            return
        try:
            import time
            t0 = time.perf_counter()
            image = self._volume.image_data
            try:
                contour = vtkFlyingEdges3D()
                contour.SetInputData(image)
                contour.SetValue(0, float(self._iso_value))
                contour.ComputeNormalsOff()
            except Exception:
                logging.exception("FlyingEdges failed; falling back to MarchingCubes")
                if vtkMarchingCubes is None:
                    return
                contour = vtkMarchingCubes()
                contour.SetInputData(image)
                contour.SetValue(0, float(self._iso_value))
                contour.ComputeNormalsOff()
            normals = vtkPolyDataNormals()
            normals.SetInputConnection(contour.GetOutputPort())
            normals.SetFeatureAngle(60.0)
            normals.SplittingOff()
            normals.ConsistencyOn()
            normals.Update()
            poly = normals.GetOutput()
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(poly)
            try:
                mapper.ScalarVisibilityOff()
            except Exception:
                logging.exception("VolumeView: failed to disable scalar visibility on iso mapper")
            actor = self._iso_actor or vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*self._iso_color)
            actor.GetProperty().SetOpacity(self._iso_opacity)
            if self._iso_actor is None:
                self.renderer.AddActor(actor)
                self._iso_actor = actor
            try:
                self._iso_picker.InitializePickList()
                self._iso_picker.AddPickList(self._iso_actor)
            except Exception:
                logging.exception("VolumeView: failed to update iso picker pick list")
            try:
                self.renderer.ResetCameraClippingRange()
            except Exception:
                logging.exception("VolumeView: ResetCameraClippingRange failed after iso update")
            try:
                tris = int(poly.GetNumberOfPolys()) if hasattr(poly, 'GetNumberOfPolys') else 0
                ms = (time.perf_counter() - t0) * 1000.0
                self.iso_stats_changed.emit(tris, ms)
            except Exception:
                logging.exception("VolumeView: failed to emit iso-stats")
        finally:
            self.render()


__all__ = ["VolumeView"]
