#!/bin/bash

####################################################
### Script run to generate MadGraph5_aMC@NLO event
### samples via CERN HTCondor for cross-section calculation only
### this is an abridged version of generate.sh

echo "Starting MadGraph5_aMC@NLO cross-section calculator script..."

MG_VERSION=3_6_7

# Check if we have access to cvfms 
# use the ATLAS setup to get an LCG release and xrootd
if [[ -r /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase ]] ; then
    echo "Setting up ATLAS environment..."
    export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
    source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh -3
    lsetup "views LCG_106 x86_64-el9-gcc13-opt"
    lsetup xrootd
else
  echo "ERROR: cvmfs not accessible. You need to run on lxplus"
  exit 1
fi

echo "Current working directory: $(pwd)"
# perform an xrootd copy of the tarball from EOS
# NOTE you should change this path to wherever you have tarball stored
TARBALL_PATH=/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/run/MG5_aMC_v${MG_VERSION}_with_dependencies.tar.gz
echo "Copying MadGraph tarball from ${TARBALL_PATH}..."
xrdcp root://eosuser.cern.ch/${TARBALL_PATH} .

# unpack MG5 and MadDM dependencies tarball
echo "Unpacking MadGraph tarball..."
tar -xzf MG5_aMC_v${MG_VERSION}_with_dependencies.tar.gz
ls -altr
echo ""

# setup some path variables
# setup needed for Pythia8
export PYTHIA8DATA=$(pwd)/MG5_aMC_v${MG_VERSION}/HEPTools/pythia8/share/Pythia8/xmldoc/
# setup needed for Delphes
export LD_LIBRARY_PATH=$(pwd)/MG5_aMC_v${MG_VERSION}/Delphes:${LD_LIBRARY_PATH}
export ROOT_INCLUDE_PATH=$(pwd)/MG5_aMC_v${MG_VERSION}/Delphes:${ROOT_INCLUDE_PATH}

# run the event generation
echo "Running MadGraph to generate events..." 
# need to provide a command line argument corresponding to 
# the MG5 instruction card to be run
./MG5_aMC_v${MG_VERSION}/bin/mg5_aMC $2
echo "MadGraph run completed."

echo "ls -altr of working directory after event generation:"
ls -altr
echo "ls -altr of MadGraph output directory after event generation:"
ls -altr generated_events
