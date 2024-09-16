# rebin

Script to rebin stacks of jp2 images. This is designed to minimise memory usage, and scale across multiple processes.

> :warning: The JPEG2000 compression parameters are tailored to HiP-CT images, so may not be appropriate for other datasets.

## Installing
To get this working on any operating system, it's recommended to [install miniconda](https://docs.anaconda.com/free/miniconda/miniconda-install/).
Once you have a terminal (or "Anaconda prompt" on Windows) open after installation, these steps will set you up to run the rebinning:

1. Change to a directory where you want to download this code.
2. `git clone https://github.com/HiPCTProject/rebin`
3. `cd rebin`
4. `conda env create --name rebin`
5. `conda activate rebin`
6. `conda install uv`
7. `uv sync`

Now you should be able to run the rebinning code using the example below.

## Usage

Download `rebin.py`.
Example run:
```bash
python rebin.py --bin-factor=2 --cratio=10 --num-workers=8 --directory path/to/jp2/directory --output-directory path/to/output/directory
```

```bash
python rebin.py --help
Usage: rebin.py [OPTIONS]

Options:
  --bin-factor INTEGER     Number of pixels in each bin.
  --cratio INTEGER         Compression ratio to use to save jp2 images.
  --num-workers INTEGER    Number of workers used to process in parallel.
  --directory TEXT         Directory with jp2 images.
  --output-directory TEXT  Directory to output images to.
  --fname-prefix TEXT      String to add the beginning of all output jp2
                           files.
  --help                   Show this message and exit.
```
