from pathlib import Path

import glymur
import numpy as np
import pytest

from rebin import rebin


@pytest.fixture
def input_jp2_folder(tmp_path: Path) -> Path:
    """
    Populate a (temporary) directory with some .jp2 files.
    """
    jp2_path = tmp_path / "input_jp2s"
    jp2_path.mkdir()
    fname = f"img0.jp2"
    jp2 = glymur.Jp2k(str(jp2_path / fname), numres=1)
    jp2[:] = np.array([[0, 1], [2, 5]]).astype(np.uint16)

    return jp2_path


def test_rebin(input_jp2_folder: Path) -> None:
    output_dir = rebin(input_jp2_folder, bin_factor=2)
    assert output_dir.exists()
    jp2_files = list(output_dir.glob("*.jp2"))
    assert len(jp2_files) == 1
    jp2 = glymur.Jp2k(str(jp2_files[0]))
    np.testing.assert_equal(jp2[:], np.array([[2]], dtype=np.uint16))
