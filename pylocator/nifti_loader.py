"""Utilities for reading NIfTI volumes and converting them to VTK data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
from vtkmodules.util import numpy_support
from vtkmodules.vtkCommonDataModel import vtkImageData


class NiftiLoadError(RuntimeError):
    """Raised when a NIfTI volume cannot be loaded."""


@dataclass(slots=True)
class NiftiVolume:
    """A loaded NIfTI volume ready for rendering."""

    image_data: vtkImageData
    path: Path
    shape: tuple[int, int, int]
    voxel_size: tuple[float, float, float]
    value_range: tuple[float, float]


def _to_vtk_image(array: np.ndarray, voxel_size: tuple[float, float, float]) -> vtkImageData:
    image = vtkImageData()
    dims = tuple(int(v) for v in array.shape)
    image.SetDimensions(*dims)
    image.SetSpacing(*voxel_size)
    image.SetOrigin(0.0, 0.0, 0.0)

    flat = numpy_support.numpy_to_vtk(
        num_array=np.ravel(array, order="F"),
        deep=True,
        array_type=numpy_support.get_vtk_array_type(array.dtype),
    )
    image.GetPointData().SetScalars(flat)
    return image


def load_nifti_volume(filename: str) -> NiftiVolume:
    """Load *filename* into memory and return a :class:`NiftiVolume`."""

    path = Path(filename)
    if not path.exists():
        raise NiftiLoadError(f"NIfTI file does not exist: {path}")

    try:
        nifti = nib.load(path)
    except (OSError, nib.spatialimages.ImageDataError) as exc:
        raise NiftiLoadError(f"Failed to open {path}: {exc}") from exc

    data = nifti.get_fdata(dtype=np.float32)
    if data.ndim != 3:
        raise NiftiLoadError(
            f"PyLocator currently supports 3-D volumes only, got shape {data.shape!r}"
        )

    voxel_size = tuple(float(z) for z in nifti.header.get_zooms()[:3])
    vtk_image = _to_vtk_image(data, voxel_size)
    value_range = float(np.min(data)), float(np.max(data))

    return NiftiVolume(
        image_data=vtk_image,
        path=path.resolve(),
        shape=tuple(int(v) for v in data.shape),
        voxel_size=voxel_size,
        value_range=value_range,
    )


__all__ = ["NiftiLoadError", "NiftiVolume", "load_nifti_volume"]
