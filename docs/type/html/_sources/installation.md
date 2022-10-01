Installation
===============

## Installing packages

`spyglass` can be installed via `pip`:

```bash
pip install spyglass-neuro
```

Some of the pipeline requires installation of additional packages. For example, the spike sorting pipeline relies on `spikeinterface`. We recommend installing it direclty from the GitHub repo:

```bash
pip install git+https://github.com/SpikeInterface/spikeinterface.git
```

You may also need to install individual sorting algorithms. For example, Loren Frank's lab at UCSF typically uses `mountainsort4`:

```bash
pip install mountainsort4
```

The LFP pipeline uses `ghostipy`:

```bash
pip install ghostipy
```

WARNING: If you are on an M1 Mac, you need to install `pyfftw` via `conda` BEFORE installing `ghostipy`:

```bash
conda install -c conda-forge pyfftw
```

### Setting up database access

1. To use `spyglass`, you need to have access to a MySQL database. If your lab already administers a database, connect to it by setting `datajoint` configurations. If you want to run your own database, consult instructions in [datajoint tutorial](https://tutorials.datajoint.org/setting-up/get-database.html) and/or [our tutorial notebook](./notebooks/docker_mysql_tutorial.ipynb).

   > If you're a member of the Frank lab, ask Loren or Eric.

2. Add the following environment variables (e.g. in `~/.bashrc`). The following are specific to Frank lab so you may want to change `SPYGLASS_BASE_DIR`.

   ```bash
   export SPYGLASS_BASE_DIR="/stelmo/nwb"
   export SPYGLASS_RECORDING_DIR="$SPYGLASS_BASE_DIR/recording"
   export SPYGLASS_SORTING_DIR="$SPYGLASS_BASE_DIR/sorting"
   export SPYGLASS_WAVEFORMS_DIR="$SPYGLASS_BASE_DIR/waveforms"
   export SPYGLASS_TEMP_DIR="$SPYGLASS_BASE_DIR/tmp/spyglass"
   export DJ_SUPPORT_FILEPATH_MANAGEMENT="TRUE"
   ```

   Note that a local `SPYGLASS_TEMP_DIR` (e.g. one on your machine) will speed up spike sorting, but make sure it has enough free space (ideally at least 500GB)

3. Set up [`kachery-cloud`](https://github.com/flatironinstitute/kachery-cloud) (if you are in Frank lab, skip this step). Once you have initialized a `kachery-cloud` directory, add the following environment variables (again, shown for Frank lab).

   ```bash
   export KACHERY_CLOUD_DIR="$SPYGLASS_BASE_DIR/.kachery-cloud"
   export KACHERY_TEMP_DIR="$SPYGLASS_BASE_DIR/tmp"
   ```

4. Configure DataJoint. To connect to the Datajoint database, we have to specify information about it such as the hostname and the port. You should also change your password from the temporary one you were given. Go to the config directory, and run [`dj_config.py`](https://github.com/LorenFrankLab/spyglass/blob/master/config/dj_config.py) in the terminal with your username:

    ```bash
    cd config # change to the config directory
    python dj_config.py <username> # run the configuration script
    ```

Finally, open up a python console (e.g. run `ipython` from terminal) and import `spyglass` to check that the installation has worked.
