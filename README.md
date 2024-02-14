# rebin

Script to rebin stacks of jp2 images. This is designed to minimise memory usage, and scale across multiple processes.

## Installing
To get this working on any operating system, it's recommended to [install miniconda](https://docs.anaconda.com/free/miniconda/miniconda-install/), and then use the `conda-env.yml` environment file in this repository to [create a new conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file).
This will ensure that all the dependencies for running the rebin script (including `openjpeg`) are installed and available.

## Usage

Download `rebin.py`.
Example run: 
```bash
python rebin.py --bin-factor=2 --cratio=10 --num-workers=8 --directory path/to/jp2/directory --output-directory path/to/output/directory 
```

```
Usage: rebin.py [OPTIONS]

Options:
  --bin-factor INTEGER     Number of pixels in each bin.
  --cratio INTEGER         Compression ratio to use to save jp2 images.
  --num_workers INTEGER    Number of workers used to process in parallel.
  --directory TEXT         Directory with jp2 images.
  --output_directory TEXT  Directory to output images to.
  --fname_prefix TEXT      String to add the beginning of all output jp2
                           files.
  --help                   Show this message and exit.
```
