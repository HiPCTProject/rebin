from pathlib import Path
from typing import List, Optional

import glymur
import numpy as np
import pytest

from rebin import rebin

CRATIO = 10


def get_nlevels(jp2: glymur.Jp2k) -> int:
    """
    Get number of layers in a jp2 file.
    """
    for line in jp2.__str__().split("\n"):
        line = line.strip()
        if line.startswith("Number of decomposition levels"):
            return int(line.split(":")[1])

    return 0

def populate_jp2_files(data: np.ndarray, path: Path) -> None:
    """
    Populate a directory or jp2 files from array data.
    """
    assert data.ndim == 3
    for i, arr in enumerate(data):
        f_path = path / f"img{str(i).zfill(4)}.jp2"
        jp2 = glymur.Jp2k(str(f_path), numres=1)
        jp2[:] = arr.astype(np.uint16)


@pytest.mark.parametrize("output_dir_in", [None, Path("output_dir")])
@pytest.mark.parametrize(
    "array_in, bin_factor, expected_arrays",
    [
        (np.array([[[0, 1], [2, 5]]]), 2, [np.array([[2]])]),
        (np.array([[[0, 1], [2, 5], [10, 12]]]), 2, [np.array([[2], [4]])]),
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
    expected_arrays: List[np.ndarray],
    output_dir_in: Optional[Path],
) -> None:
    jp2_path = tmp_path / "input_jp2s"
    jp2_path.mkdir()
    populate_jp2_files(array_in, jp2_path)

    if output_dir_in is not None:
        output_dir_in = tmp_path / output_dir_in

    output_dir_out = rebin(
        jp2_path,
        bin_factor=bin_factor,
        num_workers=2,
        output_directory=output_dir_in,
        fname_prefix="prefix_",
        cratio=CRATIO,
    )
    assert output_dir_out.exists()
    if output_dir_in is None:
        assert output_dir_out.name == f"input_jp2s_bin{bin_factor}"
    else:
        assert output_dir_out == output_dir_in

    jp2_files = sorted(output_dir_out.glob("prefix_*.jp2"))
    assert len(jp2_files) == len(expected_arrays)

    for jp2_file, arr in zip(jp2_files, expected_arrays):
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
        rebin(jp2_path, bin_factor=bin_factor, cratio=CRATIO)


def test_large_nlayers(tmp_path: Path):
    """
    Check number of layers for a large image.
    """
    input_dir = tmp_path / "input_jp2s"
    input_dir.mkdir()
    jp2 = glymur.Jp2k(input_dir / "test.jp2")
    jp2[:] = np.random.randint(low=0, high=2**16, size=(1000, 1000), dtype=np.uint16)

    output_dir = tmp_path / "output"
    output_dir = Path("/Users/dstansby/software/hipct/rebin/test-out")
    rebin(input_dir, bin_factor=2, cratio=CRATIO, output_directory=output_dir)

    for jp2_file in output_dir.glob("*.jp2"):
        assert get_nlevels(glymur.Jp2k(jp2_file)) == 8
