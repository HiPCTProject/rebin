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
import math
import os
from pathlib import Path
from typing import List, Union

import click
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

JP2K_PARAMS = {"irreversible": True}


def save_jp2(
    arr: np.ndarray,
    file_path: Path,
    dtype: Union[np.uint8, np.uint16],
    *,
    cratios: List[int],
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
    jp2 = glymur.Jp2k(str(file_path), cratios=cratios, numres=1, **JP2K_PARAMS)
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
    dtype: Union[np.uint8, np.uint16],
    *,
    cratios: List[int],
) -> None:
    # Read array into memory
    arr = np.asarray(arr)
    arr = rebin_slab(arr, factor)
    save_jp2(arr, file_path, dtype, cratios=cratios)


def rebin(
    directory: Path,
    *,
    bin_factor: int,
    cratio: int,
    num_workers: int = 4,
    output_directory: Path = None,
    fname_prefix: str = "",
) -> Path:
    """
    Rebin a series of jp2 images.

    Assumes that all the input jp2 images have their filenames
    sorted in alpha-numeric order,
    e.g., slice_000.jp2, slice_001.jp2, slice_002.jp2...

    :param directory: Path to directory with jp2 images.
    :param bin_factor: Number of pixels in each bin.
    :param cratio: Compression ratio to use to save jp2 images.
    :param num_workers: Number of workers used to process in parallel.
    :param output_directory: Directory to output images to.
    :param fname_prefix: String to add the beginning of all output jp2 files.
    """
    if bin_factor <= 1:
        raise ValueError("bin_factor must be > 1")
    if int(bin_factor) != bin_factor:
        raise ValueError("bin_factor must be an integer")

    im_list = sorted(directory.glob("*.jp2"))
    n_ims = len(im_list)
    logging.info(f"Found {n_ims} jp2 files")

    if output_directory is None:
        output_directory = directory.parent / f"{directory.name}_bin{bin_factor}"
    output_directory.mkdir(exist_ok=True)

    # A list of jp2k objects, does *not* read any data into memory.
    logging.info("Constructing Jp2k objects...")
    j2ks = [glymur.Jp2k(f) for f in im_list]
    slice_shape = j2ks[0].shape
    dtype_in = j2ks[0].dtype

    logging.info(f"Data type is {dtype_in}")
    logging.info(f"Compression ratios is {cratio}")
    logging.info(f"Input shape is {(*slice_shape, n_ims)}")
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
            slab,
            bin_factor,
            output_directory / f"{fname_prefix}{str(z).zfill(6)}.jp2",
            dtype_in,
            cratios=[cratio],
        )
        delayed_slab_saves.append(fname)

    logging.info("Running computation!")
    with ProgressBar(dt=1):
        delayed(delayed_slab_saves).compute(num_workers=num_workers)
    return output_directory


@click.command()
@click.option("--bin-factor", help="Number of pixels in each bin.", type=int)
@click.option("--cratio", help="Compression ratio to use to save jp2 images.", type=int)
@click.option(
    "--num-workers",
    help="Number of workers used to process in parallel.",
    type=int,
)
@click.option("--directory", help="Directory with jp2 images.")
@click.option("--output-directory", help="Directory to output images to.")
@click.option(
    "--fname-prefix",
    help="String to add the beginning of all output jp2 files.",
    default="",
)
def rebin_cmd(
    *,
    directory: Path,
    bin_factor: int,
    cratio: int,
    num_workers: int,
    output_directory: Path,
    fname_prefix: str,
):
    return rebin(
        Path(directory),
        bin_factor=bin_factor,
        cratio=cratio,
        num_workers=num_workers,
        output_directory=Path(output_directory),
        fname_prefix=fname_prefix,
    )


if __name__ == "__main__":
    rebin_cmd()
