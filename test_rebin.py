from pathlib import Path

import glymur
import numpy as np
import pytest

from rebin import rebin


def populate_jp2_files(data: np.ndarray, path: Path) -> None:
    """
    Populate a directory or jp2 files from array data.
    """
    assert data.ndim == 3
    for i, arr in enumerate(data):
        f_path = path / f"img{str(i).zfill(4)}.jp2"
        jp2 = glymur.Jp2k(str(f_path), numres=1)
        jp2[:] = arr.astype(np.uint16)


@pytest.mark.parametrize(
    "array_in, expected_arrays", [(np.array([[[0, 1], [2, 5]]]), [np.array([[2]])])]
)
def test_rebin(
    tmp_path: Path, array_in: np.ndarray, expected_arrays: list[np.ndarray]
) -> None:
    jp2_path = tmp_path / "input_jp2s"
    jp2_path.mkdir()
    populate_jp2_files(array_in, jp2_path)

    output_dir = rebin(jp2_path, bin_factor=2)
    assert output_dir.exists()
    jp2_files = sorted(output_dir.glob("*.jp2"))
    assert len(jp2_files) == len(expected_arrays)

    for jp2_file, arr in zip(jp2_files, expected_arrays, strict=True):
        jp2 = glymur.Jp2k(str(jp2_file))
        np.testing.assert_equal(jp2[:], arr.astype(np.uint16))
