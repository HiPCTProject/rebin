"""
Script to re-bin stacks of 2D images.

Currently only works for jp2 images.

Design
------
This script is implemented using dask to:
1. Lazily load jp2 slices a handful at a time,
   instead of reading them all into memory at once.
2. Distribute calculating the mean across several processes.

Each 'slab' of thickness `bin_factor` is passed to `rebin_and_save_slab`.
Once that slab of images has been binned and saved, the slices are
automatically unloaded from memory, preventing memory overloads.
"""


import logging
from pathlib import Path
import math
import os

import dask.array as da
import glymur
import numpy as np
from dask import delayed
from dask.diagnostics import ProgressBar
from skimage.transform import downscale_local_mean

logging.basicConfig(level=logging.INFO)

# Make sure numpy or glymur doesn't try to use more than one thread
glymur.set_option("lib.num_threads", 1)
for var in [
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "BLIS_NUM_THREADS",
]:
    os.environ[var] = "1"


def save_jp2(
    arr: np.ndarray, file_path: Path, dtype: np.uint8 | np.uint16, *, cratios: list[int]
) -> None:
    """
    Save an array to a jp2 file.

    Parameters
    ----------
    arr :
        Data array.
    file_path :
        File to save to.
    dtype :
        Data type to cast to, must be uint8 or uint16 (8-bit or 16-bit).
    cratios :
        Compression ratios.
    """
    jp2 = glymur.Jp2k(str(file_path), cratios=[10])
    jp2[:] = np.asarray(arr).astype(dtype)


def rebin_slab(arr: np.ndarray, factor: int) -> np.ndarray:
    """
    Rebin a 3D slab.
    """
    # Mean over z-axis
    arr = np.mean(arr, axis=2)
    # Mean over x/y axes
    arr = downscale_local_mean(arr, (factor, factor))
    return arr


@delayed  # type: ignore[misc]
def rebin_and_save_slab(
    arr: np.ndarray,
    factor: int,
    file_path: Path,
    dtype: np.uint8 | np.uint16,
) -> None:
    # Read array into memory
    arr = np.asarray(arr)
    arr = rebin_slab(arr, factor)
    save_jp2(arr, file_path, dtype, cratios=[10])


def rebin(directory: Path, *, bin_factor: int) -> Path:
    """
    Rebin a series of jp2 images.

    Assumes that all the input jp2 images have their filenames
    sorted in alpha-numeric order,
    e.g., slice_000.jp2, slice_001.jp2, slice_002.jp2...

    Parameters
    ----------
    directory :
        Path to directory with jp2 images.
    bin_factor : int
        Number of pixels in each bin.
    """
    if bin_factor <= 1:
        raise ValueError("bin_factor must be > 1")
    if int(bin_factor) != bin_factor:
        raise ValueError("bin_factor must be an integer")

    im_list = sorted(directory.glob("*.jp2"))
    n_ims = len(im_list)
    logging.info(f"Found {n_ims} jp2 files")

    output_dir = directory.parent / f"{directory.name}_bin{bin_factor}"
    output_dir.mkdir(exist_ok=True)

    # A list of jp2k objects, does *not* read any data into memory.
    j2ks = [glymur.Jp2k(f) for f in im_list]
    slice_shape = j2ks[0].shape
    dtype_in = j2ks[0].dtype

    logging.info(f"Input shape is {(slice_shape, n_ims)}")
    output_shape = (
        math.ceil(slice_shape[0] / bin_factor),
        math.ceil(slice_shape[1] / bin_factor),
        math.ceil(n_ims / bin_factor),
    )
    logging.info(f"Output shape is {output_shape}")

    # Create a dask array for full input volume, does *not* read any data into memory.
    volume = da.stack([da.from_array(j2k, chunks=slice_shape) for j2k in j2ks], axis=-1)

    delayed_slab_saves = []
    # Loop through z-slices of output image, and set up delayded calls to
    # rebin_and_save_slab
    logging.info("Setting up computation...")
    for z in range(output_shape[2]):
        slab = volume[:, :, z * bin_factor : (z + 1) * bin_factor]
        fname = rebin_and_save_slab(
            slab, bin_factor, output_dir / f"{str(z).zfill(6)}.jp2", dtype_in
        )
        delayed_slab_saves.append(fname)

    logging.info("Running computation!")
    with ProgressBar():
        delayed(delayed_slab_saves).compute()
    return output_dir


if __name__ == "__main__":
    output_dir = rebin(Path("/Users/dstansby/data/kidney2"), 5)
    logging.info(f"Done, rebinned files in {output_dir}")
