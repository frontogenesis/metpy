# Setup Metpy Environment

## Instructions

1. Install Miniconda: https://docs.conda.io/en/latest/miniconda.html
2. If you haven't already done so, add conda-forge by typing `conda config --add channels conda-forge`.
3. In the command prompt, type `conda env create`. This will install all packages from the environment.yml file.
4. After packages are installed, type `conda activate metpy`.
5. Type `jupyter lab` or `jupyter notebook` to fire up a python notebook to run the scripts.

### For Windows users
I've noticed an environment variable needs to be setup so that pygrib (which includes eccodes) will work with any scripts requiring
either (or both) of those modules. Add this directory to your environment variable

ECCODES_DEFINITION_PATH  C:\Users\[name_of_your_computer]\miniconda3\envs\metpy\Library\share\eccodes\definitions