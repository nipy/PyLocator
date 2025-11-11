"""Reusable VTK-backed view widgets for the Qt UI."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtCore import QObject
from PySide6.QtGui import QKeyEvent
from .main_window import Marker

from dataclasses import dataclass

from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout
import math
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkInteractionStyle import (
    vtkInteractorStyleImage,
    vtkInteractorStyleTrackballCamera,
)
from vtkmodules.vtkFiltersSources import vtkSphereSource
        
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkImageProperty,
    vtkImageSlice,
    vtkImageSliceMapper,
    vtkRenderer,
    vtkVolume,
    vtkVolumeProperty,
    vtkActor, 
    vtkPolyDataMapper,
    vtkPropPicker,
)

try:
    from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
except ImportError:  # pragma: no cover
    from vtkmodules.vtkRenderingVolume import vtkSmartVolumeMapper

from ..nifti_loader import NiftiVolume


@dataclass(slots=True)
class SliceGeometry:
    """Metadata describing how a slice view maps to the volume indices."""

    orientation: str
    minimum: int
    maximum: int
    current: int


class _BaseVTKView(QObject):
    """Common helpers for views backed by :class:`QVTKRenderWindowInteractor`."""

    marker_added = Signal(int, int, int)  # x, y, z in voxel coordinates

    def __init__(self, parent: QWidget | None = None, *, interactor_style: type | None = None) -> None:
        super().__init__(parent)
        self.frame = QFrame(parent)
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setLineWidth(2)
        # Set a default border (gray, always visible)
        self.frame.setStyleSheet("border: 2px solid #888;")
        # Ensure the frame can accept focus
        self.frame.setFocusPolicy(Qt.StrongFocus)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.widget = QVTKRenderWindowInteractor(self.frame)
        self.widget.setFocusPolicy(Qt.StrongFocus)
        # Do not call Initialize here; let Qt handle it when shown
        layout.addWidget(self.widget)
        self.frame.setLayout(layout)
        self.renderer = vtkRenderer()
        render_window = self.widget.GetRenderWindow()
        render_window.AddRenderer(self.renderer)
        self._interactor = render_window.GetInteractor()
        self._interactor.Initialize()
        if interactor_style is not None:
            self._interactor.SetInteractorStyle(interactor_style())
        # Do not call self.widget.Start(); Qt's event loop is sufficient.
        # Do not call self.widget.Start(); Qt's event loop is sufficient.

    def _setup_marker_events(self):
        # Track last hovered voxel (for adding markers with keyboard)
        self._last_mouse_voxel = None
        # Listen for focus/mouse/key events on both the VTK widget and frame
        try:
            self.widget.installEventFilter(self)
        except Exception:
            pass
        try:
            self.frame.installEventFilter(self)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        # Only handle events for our widget
        if obj is not self.widget:
            return False
        # Mouse move: update last hovered voxel
        if event.type() == event.Type.MouseMove:
            pos = event.position() if hasattr(event, 'position') else event.pos()
            self._last_mouse_voxel = self._map_screen_to_voxel(pos.x(), pos.y())
        # Mouse press: ensure focus is set to the VTK widget for key handling
        elif event.type() == event.Type.MouseButtonPress:
            try:
                self.widget.setFocus(Qt.MouseFocusReason)
                self.set_active_frame(True)
            except Exception:
                pass
        # Key press: add marker if 'i' is pressed
        elif event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_I and self._last_mouse_voxel:
                x, y, z = self._last_mouse_voxel
                self.marker_added.emit(x, y, z)
                return True
        # Focus changes: update frame highlight
        elif event.type() == event.Type.FocusIn:
            self.set_active_frame(True)
        elif event.type() == event.Type.FocusOut:
            self.set_active_frame(False)
        return False

    def _map_screen_to_voxel(self, x, y):
        # Placeholder: map screen coordinates to voxel coordinates
        # This needs to be implemented for each view type
        return None

    def set_active_frame(self, active: bool):
        if active:
            # Use a highly visible blue border for focus
            self.frame.setStyleSheet("border: 2.5px solid #0078d7;")
        else:
            # Use a neutral gray border when not focused
            self.frame.setStyleSheet("border: 2px solid #888;")

    def render(self) -> None:
        """Trigger a redraw of the underlying VTK window."""

        self.widget.GetRenderWindow().Render()


class VolumeView(_BaseVTKView):
    """3-D volume rendering viewport."""

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
        self._last_markers: list[Marker] = []
        # Enable event filtering to keep focus highlight in sync
        self._setup_marker_events()
        self.set_active_frame(False)
        # Use the main renderer for both volume and marker spheres

    def set_markers(self, markers):
        # Cache last markers for UI-driven re-rendering
        try:
            self._last_markers = list(markers)
        except Exception:
            self._last_markers = []
        # Remove previous marker actors
        for actor in getattr(self, '_marker_actors', []):
            self.renderer.RemoveActor(actor)
        self._marker_actors = []
        if self._volume is None:
            self.render()
            return
        # Choose a robust world-space sphere radius relative to volume size
        sx, sy, sz = self._volume.voxel_size
        nx, ny, nz = self._volume.shape
        diag = math.sqrt((nx * sx) ** 2 + (ny * sy) ** 2 + (nz * sz) ** 2)
        sphere_radius = max(min(sx, sy, sz) * 2.5, 0.01 * diag) * float(self._marker_size_factor)
        for marker in markers:
            # Convert voxel to world coordinates
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
        # Ensure clipping planes include markers
        try:
            self.renderer.ResetCameraClippingRange()
        except Exception:
            pass
        self.render()

    def _map_screen_to_voxel(self, x, y):
        # Map widget display coords to a 3D ray in world space and
        # intersect with the volume's AABB, then convert to voxel coords.
        if self._volume is None:
            return None
        try:
            rw = self.widget.GetRenderWindow()
            if rw is None:
                return None
            ren = self.renderer
            # Convert Qt coords (origin top-left) to VTK display (origin bottom-left)
            h = max(1, int(self.widget.height()))
            dx = float(x)
            dy = float(h - 1 - int(y))

            # Near and far world points
            ren.SetDisplayPoint(dx, dy, 0.0)
            ren.DisplayToWorld()
            p0 = ren.GetWorldPoint()
            if abs(p0[3]) < 1e-9:
                return None
            p0 = (p0[0] / p0[3], p0[1] / p0[3], p0[2] / p0[3])

            ren.SetDisplayPoint(dx, dy, 1.0)
            ren.DisplayToWorld()
            p1 = ren.GetWorldPoint()
            if abs(p1[3]) < 1e-9:
                return None
            p1 = (p1[0] / p1[3], p1[1] / p1[3], p1[2] / p1[3])

            # Ray direction
            dirx, diry, dirz = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            # Segment param t in [0,1] goes from near (p0) to far (p1)
            # Intersect against volume bounds
            bounds = self._volume.image_data.GetBounds()  # (xmin,xmax, ymin,ymax, zmin,zmax)
            xmin, xmax, ymin, ymax, zmin, zmax = bounds
            tmin, tmax = 0.0, 1.0
            eps = 1e-12
            for coord, d, bmin, bmax in (
                (p0[0], dirx, xmin, xmax),
                (p0[1], diry, ymin, ymax),
                (p0[2], dirz, zmin, zmax),
            ):
                if abs(d) < eps:
                    if coord < bmin or coord > bmax:
                        return None
                    # Parallel axis within slab; continue
                    continue
                invd = 1.0 / d
                t0 = (bmin - coord) * invd
                t1 = (bmax - coord) * invd
                if t0 > t1:
                    t0, t1 = t1, t0
                if t0 > tmin:
                    tmin = t0
                if t1 < tmax:
                    tmax = t1
                if tmin > tmax:
                    return None

            # Hit entry point
            thit = tmin
            hx = p0[0] + thit * dirx
            hy = p0[1] + thit * diry
            hz = p0[2] + thit * dirz

            # Convert world position to voxel indices
            sx, sy, sz = self._volume.voxel_size
            nx, ny, nz = self._volume.shape
            vx = int(round(hx / sx))
            vy = int(round(hy / sy))
            vz = int(round(hz / sz))
            # Clamp to valid range
            vx = max(0, min(nx - 1, vx))
            vy = max(0, min(ny - 1, vy))
            vz = max(0, min(nz - 1, vz))
            return (vx, vy, vz)
        except Exception:
            return None

    def set_volume(self, volume: NiftiVolume) -> None:
        """Render *volume* using VTK's smart volume mapper."""

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
        self.renderer.ResetCamera()
        self.render()

    def set_marker_size_factor(self, factor: float) -> None:
        """Set a global size multiplier for 3D marker spheres."""
        self._marker_size_factor = max(0.1, min(5.0, float(factor)))
        self.set_markers(self._last_markers)

    def set_opacity_factor(self, factor: float) -> None:
        """Adjust overall volume opacity [0..1] while preserving transfer shape."""

        self._opacity_factor = max(0.0, min(1.0, float(factor)))
        if self._opacity_tf is None or self._value_range is None:
            return
        min_val, max_val = self._value_range
        self._opacity_tf.RemoveAllPoints()
        self._opacity_tf.AddPoint(min_val, 0.0)
        self._opacity_tf.AddPoint(max_val, self._opacity_factor)
        self.render()


class SliceView(_BaseVTKView):
    def focusInEvent(self, event):
        # Forward focus to frame and update border
        self.set_active_frame(True)
        self.frame.setFocus(Qt.OtherFocusReason)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.set_active_frame(False)
        super().focusOutEvent(event)

    def mousePressEvent(self, event):
        # Ensure clicking the widget gives it focus (and thus updates border)
        self.frame.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)
    def set_markers(self, markers):
        # Cache markers for UI-driven re-rendering
        try:
            self._last_markers = list(markers)
        except Exception:
            self._last_markers = []
        # Remove previous marker actors
        for actor in getattr(self, '_marker_actors', []):
            self.renderer.RemoveActor(actor)
        self._marker_actors = []
        if self._volume is None or self._geometry is None:
            self.render()
            return
        from vtkmodules.vtkFiltersSources import vtkRegularPolygonSource
        from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
        orientation = self.orientation
        slice_idx = int(self._geometry.current)
        spacing = self._volume.voxel_size
        # Determine a robust world-space marker radius that adapts to zoom
        cam = self.renderer.GetActiveCamera()
        height_world = 2.0 * cam.GetParallelScale()  # visible height in world units
        base_radius = max(min(spacing) * 2.5, 0.02 * height_world)
        # Apply global marker size factor if present
        try:
            base_radius *= float(self._marker_size_factor)
        except Exception:
            pass
        for marker in markers:
            # World center of the stored marker
            mx, my, mz = [m * s for m, s in zip((marker.x, marker.y, marker.z), spacing)]
            # Distance from current plane to marker center and ring radius from sphere-plane intersection
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
            else:  # sagittal
                plane_pos = slice_idx * spacing[0]
                d = abs(plane_pos - mx)
                normal = (1, 0, 0)
                center = (plane_pos, my, mz)
            if d > base_radius:
                continue
            ring_radius = max(min(spacing) * 1.0, math.sqrt(max(base_radius * base_radius - d * d, 0.0)))
            # Slightly offset the ring towards the camera to avoid z-fighting
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
                    lw = 2
            actor.GetProperty().SetLineWidth(lw)
            actor.GetProperty().SetOpacity(1.0)
            actor.GetProperty().SetRepresentationToWireframe()
            self.renderer.AddActor(actor)
            self._marker_actors.append(actor)
        self.render()

    def set_marker_size_factor(self, factor: float) -> None:
        """Set a global size multiplier for 2D ring radius (projection of sphere)."""
        self._marker_size_factor = max(0.1, min(5.0, float(factor)))
        self.set_markers(getattr(self, "_last_markers", []))

    def set_ring_thickness(self, factor: float) -> None:
        """Set a line width multiplier for the 2D ring overlays."""
        self._ring_thickness = max(0.25, min(5.0, float(factor)))
        self.set_markers(getattr(self, "_last_markers", []))
    """Orthogonal 2-D slice view into the volume."""

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
        # Picker to convert display coordinates to world on the slice actor
        self._picker = vtkPropPicker()
        self._picker.PickFromListOn()
        self._picker.AddPickList(self._actor)

        self._setup_marker_events()
        self.widget.setFocusPolicy(Qt.StrongFocus)
        self.set_active_frame(False)

        # Configure mapper orientation and camera based on the view
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
        else:  # pragma: no cover - guarded by callers
            raise ValueError(f"Unsupported orientation: {self.orientation}")

    def _map_screen_to_voxel(self, x, y):
        # Use VTK picking to map display coords -> world -> voxel indices
        if self._volume is None or self._geometry is None:
            return None
        # Account for device pixel ratio on HiDPI displays
        try:
            dpr = float(self.widget.devicePixelRatioF())
        except Exception:
            dpr = 1.0
        # Flip y because Qt origin is top-left while VTK uses bottom-left
        h = self.widget.height()
        display_x = x * dpr
        display_y = (h - y) * dpr
        # Perform a constrained pick on the slice actor
        success = self._picker.Pick(display_x, display_y, 0, self.renderer)
        if not success:
            return None
        # Ensure we picked our slice actor (vtkImageSlice is a ViewProp, not an Actor)
        if self._picker.GetViewProp() is not self._actor:
            return None
        wx, wy, wz = self._picker.GetPickPosition()
        sx, sy, sz = self._volume.voxel_size
        shape = self._volume.shape
        if self.orientation == "axial":
            vx = int(round(wx / sx))
            vy = int(round(wy / sy))
            vz = int(self._geometry.current)
        elif self.orientation == "coronal":
            vx = int(round(wx / sx))
            vy = int(self._geometry.current)
            vz = int(round(wz / sz))
        else:  # sagittal
            vx = int(self._geometry.current)
            vy = int(round(wy / sy))
            vz = int(round(wz / sz))
        # Clamp to valid index range
        vx = max(0, min(vx, shape[0] - 1))
        vy = max(0, min(vy, shape[1] - 1))
        vz = max(0, min(vz, shape[2] - 1))
        return (vx, vy, vz)

        # (Removed misplaced orientation config; handled in __init__)

    @property
    def geometry(self) -> SliceGeometry | None:
        """Return the current slice geometry metadata."""

        return self._geometry

    def set_volume(self, volume: NiftiVolume) -> SliceGeometry:
        """Bind *volume* to the slice view and return slice metadata."""

        self._volume = volume
        image = volume.image_data
        self._mapper.SetInputData(image)

        extent = image.GetExtent()
        if self.orientation == "axial":
            minimum, maximum = extent[4], extent[5]
        elif self.orientation == "coronal":
            minimum, maximum = extent[2], extent[3]
        else:  # sagittal
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
        """Update the displayed slice to *index*."""

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


__all__ = ["SliceView", "SliceGeometry", "VolumeView"]
