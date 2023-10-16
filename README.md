# rebin

Script to rebin stacks of jp2 images. This is designed to minimise memory usage, and scale across multiple processes.

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
Example run: 
```bash
python rebin.py --bin-factor=2 --cratio=10 --num-workers=8 --output-directory path/to/output/directory  path/to/jp2/directory
```

```
Usage: rebin.py [OPTIONS] directory

Rebin a series of jp2 images.

Assumes that all the input jp2 images have their filenames sorted in alpha-numeric order, e.g., slice_000.jp2, slice_001.jp2, slice_002.jp2...

Arguments:
  directory                 Path to directory with jp2 images. (type: PATH)

Options:
  --bin-factor=INT          Number of pixels in each bin.
  --cratio=INT              Compression ratio to use to save jp2 images.
  --num-workers=INT         Number of workers used to process in parallel. (default: 4)
  --output-directory=PATH   Directory to output images to.
  --fname-prefix=STR        String to add the beginning of all output jp2 files. (default: )

Other actions:
  -h, --help                Show the help
```
