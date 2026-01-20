# Dark photon event generation

This repository handles event generation for dark photon models used for DMWG reinterpretations of Run 2 and Run 3 dijet resonance searches. The code is intended to be used with a batch system or interactive node connected to CVMFS. 

The repository structure is as follows:
```
analyses: this contains python modules storing the analysis code for different searches and can be extended to other dijet resonance searches in the future.

data: contains metadata and other related files configuring paths to generated samples.

HAHM_*: these are the UFO files defining the HAHM model that are imported into MadGraph.

modules: contains modules and scripts used to submit event generation and analyse event generation outputs.

run: contains the MadGraph installation and related files.
```

## Setup 

### Local and interactive setup
Several scripts are available to help with local setup and MadGraph installation. To setup the environment simply run `source setup.sh` and follow the script prompts. If MadGraph is not already installed inside the `run` directory, it will execute `install.sh` to install MadGraph and its dependencies (Delphes and Pythia8).

### Batch setup
Before submitting jobs to the batch system be sure to run `batch_setup.sh` to configure a VOMS proxy that can be used for xrootd file transfers allowing a tarball of the MadGraph installation to be sent to the batch system. The `EXPERIMENT` and `AFS_PATH` variables are user defined in this script and can be altered to change the VOMS proxy location. 

## Running event generation

## Analysing outputs from event generation

### Configuring analyses
Analyses are configured by defining a python module in the `analyses` directory.

### Defining metadata
To properly weight the generated MC events in histograms the Delphes event weights are used. The total event weight is calculated as:
```
mcEventWeight = (MG5 cross-section) * (Delphes Event.Weight) / (sum of Delphes Event.Weight for the sample).
```
The sum of weights and MG5 (MadGraph 5) cross-sections are metadata that needs to be extracted BEFORE attempting to analyse the generated events.

Obtain the MG5 cross-section from the MadGraph event generation output HTML files (normally available in `HTML/run_01/results.html` from the output directory for a single MC sample).

The sum of weights information can be extracted by running:
```
python modules/get_metadata.py --samples <sample ID for sample configured in data/samples.py>
```
which calculates and prints the sum of weights for each of the provided samples.

The cross-section and sum of weights should be added to a json file in the `data` directory with the format:
```
{
    "description": "< optional description field >",
    "< sample ID >": {
        "sumW": <sum of weights>,
        "xsec": <cross-section>
    }
}
```



