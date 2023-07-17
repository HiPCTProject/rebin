import json
from pathlib import Path

import glymur
import numpy as np
import pytest

import rebin


@pytest.fixture
def input_jp2_folder(tmp_path: Path) -> Path:
    """
    Populate a (temporary) directory with some .jp2 files.
    """
    jp2_path = tmp_path / "50um_input_jp2_"
    jp2_path.mkdir()
    for i in range(256):
        fname = f"img{i}.jp2"
        jp2 = glymur.Jp2k(str(jp2_path / fname))
        jp2[:] = np.ones((512, 1024)).astype(np.uint16)

    return jp2_path


def test_rebin(input_jp2_folder: Path) -> None:
    rebin.rebin(input_jp2_folder, bin_factor=4)
