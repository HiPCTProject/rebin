import logging
from pathlib import Path
import math

import dask.array as da
import glymur
import numpy as np
from dask import delayed

logging.basicConfig(level=logging.INFO)


glymur.set_option("lib.num_threads", 1)


def save_jp2(arr: np.ndarray, file_path: Path, dtype: np.uint8 | np.uint16) -> Path:
    """
    Save an array to a jp2 file.
    """
    logging.info(f"Saving to {file_path}")
    jp2 = glymur.Jp2k(str(file_path), cratios=[10])
    jp2[:] = np.asarray(arr).astype(dtype)
    return file_path


def rebin_slab(arr: np.ndarray, shape_2d: tuple[int, int]):
    """
    Rebin a 3D slab.
    """
    # Mean over z-axis
    arr = np.mean(arr, axis=2)
    # Mean over x/y axes
    shape = (
        shape_2d[0],
        arr.shape[0] // shape_2d[0],
        shape_2d[1],
        arr.shape[1] // shape_2d[1],
    )
    arr = arr.reshape(shape).mean(axis=-1).mean(axis=1).astype(arr.dtype)
    return arr


@delayed
def rebin_and_save_slab(
    arr: np.ndarray,
    shape_2d: tuple[int, int],
    file_path: Path,
    dtype: np.uint8 | np.uint16,
) -> Path:
    logging.info(f"Rebinning for {file_path}")
    arr = rebin_slab(arr, shape_2d)
    return save_jp2(arr, file_path, dtype)


def rebin(directory: Path, bin_factor: int) -> Path:
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

    output_shape = (
        math.ceil(slice_shape[0] / bin_factor),
        math.ceil(slice_shape[1] / bin_factor),
        math.ceil(n_ims / bin_factor),
    )
    logging.info(f"Output shape is {output_shape}")

    # Create a dask array for full input volume, still does *not* read any data into memory.
    volume = da.stack([da.from_array(j2k, chunks=slice_shape) for j2k in j2ks], axis=-1)
    logging.info(f"{volume.shape=}")

    jp2_fnames_delayed = []
    # Loop through z-slices of output image
    for z in range(output_shape[2]):
        slab = volume[:, :, z * bin_factor : (z + 1) * bin_factor]
        fname = rebin_and_save_slab(
            slab, output_shape[:2], output_dir / f"{str(z).zfill(6)}.jp2", dtype_in
        )
        jp2_fnames_delayed.append(fname)

    # Run computation!
    delayed(jp2_fnames_delayed).compute()
    return output_dir


if __name__ == "__main__":
    output_dir = rebin(Path("/Users/dstansby/data/kidney2"), 2)
    logging.info(f"Done, rebinned files in {output_dir}")
