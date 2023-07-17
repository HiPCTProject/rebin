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
    "array_in, bin_factor, expected_arrays",
    [
        (np.array([[[0, 1], [2, 5]]]), 2, [np.array([[2]])]),
        # downscale_local_mean pads with zeros, so the edge here is calculated
        # as (10 + 12 + 0 + 0) / 4 = 5
        (np.array([[[0, 1], [2, 5], [10, 12]]]), 2, [np.array([[2], [5]])]),
        # A test that writes two jp2 files
        (
            np.ones(shape=(10, 10, 10)),
            5,
            [np.ones(shape=(2, 2)), np.ones(shape=(2, 2))],
        ),
    ],
)
def test_rebin(
    tmp_path: Path,
    array_in: np.ndarray,
    bin_factor: int,
    expected_arrays: list[np.ndarray],
) -> None:
    jp2_path = tmp_path / "input_jp2s"
    jp2_path.mkdir()
    populate_jp2_files(array_in, jp2_path)

    output_dir = rebin(jp2_path, bin_factor=bin_factor)
    assert output_dir.exists()
    jp2_files = sorted(output_dir.glob("*.jp2"))
    assert len(jp2_files) == len(expected_arrays)

    for jp2_file, arr in zip(jp2_files, expected_arrays, strict=True):
        jp2 = glymur.Jp2k(str(jp2_file))
        np.testing.assert_equal(jp2[:], arr.astype(np.uint16))


@pytest.mark.parametrize(
    "array_in, bin_factor, err_msg",
    [
        (np.array([[[0, 1], [2, 5]]]), 1, "bin_factor must be > 1"),
        (np.array([[[0, 1], [2, 5]]]), 1.5, "bin_factor must be an integer"),
    ],
)
def test_rebin_errors(
    tmp_path: Path,
    array_in: np.ndarray,
    bin_factor: int,
    err_msg: str,
) -> None:
    """
    Test for rebinning errors.
    """
    jp2_path = tmp_path / "input_jp2s"
    jp2_path.mkdir()
    populate_jp2_files(array_in, jp2_path)

    with pytest.raises(Exception, match=err_msg):
        rebin(jp2_path, bin_factor=bin_factor)
