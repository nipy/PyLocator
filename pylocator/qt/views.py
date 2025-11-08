"""Reusable VTK-backed view widgets for the Qt UI."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkImageProperty,
    vtkImageSlice,
    vtkImageSliceMapper,
    vtkRenderer,
    vtkVolume,
    vtkVolumeProperty,
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


class _BaseVTKView:
    """Common helpers for views backed by :class:`QVTKRenderWindowInteractor`."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self.widget = QVTKRenderWindowInteractor(parent)
        self.widget.Initialize()
        self.renderer = vtkRenderer()
        render_window = self.widget.GetRenderWindow()
        render_window.AddRenderer(self.renderer)
        self._interactor = render_window.GetInteractor()
        self._interactor.Initialize()

    def render(self) -> None:
        """Trigger a redraw of the underlying VTK window."""

        self.widget.GetRenderWindow().Render()


class VolumeView(_BaseVTKView):
    """3-D volume rendering viewport."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.renderer.SetBackground(0.1, 0.1, 0.1)

    def set_volume(self, volume: NiftiVolume) -> None:
        """Render *volume* using VTK's smart volume mapper."""

        self.renderer.RemoveAllViewProps()

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

        self.renderer.AddVolume(actor)
        self.renderer.ResetCamera()
        self.render()


class SliceView(_BaseVTKView):
    """Orthogonal 2-D slice view into the volume."""

    def __init__(self, orientation: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.orientation = orientation
        self._volume: NiftiVolume | None = None
        self._mapper = vtkImageSliceMapper()
        self._actor = vtkImageSlice()
        self._actor.SetMapper(self._mapper)
        self.renderer.AddViewProp(self._actor)
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        self.renderer.SetBackground(0.0, 0.0, 0.0)
        self._geometry: SliceGeometry | None = None

        if orientation == "axial":
            self._mapper.SetOrientationToZ()
            self.renderer.GetActiveCamera().SetViewUp(0.0, 1.0, 0.0)
            self.renderer.GetActiveCamera().SetPosition(0.0, 0.0, 1.0)
        elif orientation == "coronal":
            self._mapper.SetOrientationToY()
            self.renderer.GetActiveCamera().SetViewUp(0.0, 0.0, 1.0)
            self.renderer.GetActiveCamera().SetPosition(0.0, -1.0, 0.0)
        elif orientation == "sagittal":
            self._mapper.SetOrientationToX()
            self.renderer.GetActiveCamera().SetViewUp(0.0, 0.0, 1.0)
            self.renderer.GetActiveCamera().SetPosition(1.0, 0.0, 0.0)
        else:  # pragma: no cover - guarded by callers
            raise ValueError(f"Unsupported orientation: {orientation}")

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
