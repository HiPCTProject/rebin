# rebin

Script to rebin stacks of jp2 images.

## Requirements
Requires Python 3.10+ and the following packages:
```
clize
dask
glymur
numpy
scikit-image
```

## Usage

Download `rebin.py`.
Example run: `python rebin.py path/to/jp2/directory --bin-factor=3 --num-workers=2`

```
Usage: rebin.py [OPTIONS] directory

Rebin a series of jp2 images.

Assumes that all the input jp2 images have their filenames sorted in alpha-numeric order, e.g., slice_000.jp2, slice_001.jp2, slice_002.jp2...

Arguments:
  directory                 Path to directory with jp2 images. (type: PATH)

Options:
  --output-directory=PATH
  --bin-factor=INT          Number of pixels in each bin.
  --num-workers=INT         Number of workers used to process in parallel. (default: 4)

Other actions:
  -h, --help                Show the help
```
