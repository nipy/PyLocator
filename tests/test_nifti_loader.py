from __future__ import annotations

import nibabel as nib
import numpy as np
import pytest

from pylocator.nifti_loader import NiftiLoadError, load_nifti_volume


def test_load_nifti_volume(tmp_path):
    data = np.arange(27, dtype=np.float32).reshape((3, 3, 3))
    affine = np.diag([2.0, 2.0, 2.0, 1.0]).astype(np.float32)
    img = nib.Nifti1Image(data, affine)
    path = tmp_path / "volume.nii.gz"
    nib.save(img, path)

    volume = load_nifti_volume(str(path))

    assert volume.shape == (3, 3, 3)
    assert volume.voxel_size == pytest.approx((2.0, 2.0, 2.0))
    assert volume.value_range == pytest.approx((0.0, float(data.max())))
    assert volume.image_data.GetDimensions() == (3, 3, 3)


def test_missing_file(tmp_path):
    missing = tmp_path / "missing.nii.gz"
    with pytest.raises(NiftiLoadError):
        load_nifti_volume(str(missing))


def test_rejects_non_3d(tmp_path):
    data = np.zeros((3, 3, 3, 2), dtype=np.float32)
    affine = np.eye(4, dtype=np.float32)
    img = nib.Nifti1Image(data, affine)
    path = tmp_path / "4d.nii.gz"
    nib.save(img, path)

    with pytest.raises(NiftiLoadError):
        load_nifti_volume(str(path))
