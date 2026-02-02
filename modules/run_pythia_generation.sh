#!/bin/bash

####################################################
### Script run to generate Pythia8 event
### generation via CERN HTCondor 

echo "Starting Pythia8 event generation script..."

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

echo "Setting up voms proxy for xrootd access..."
# voms proxy setup
# NOTE change path also in the setup.sh script when necessary
export X509_USER_PROXY=$1
# export X509_USER_PROXY=/afs/cern.ch/user/m/mamerl/private/x509up
voms-proxy-info -all
voms-proxy-info -all -file ${X509_USER_PROXY}

echo "Current working directory: $(pwd)"
echo "ls -altr"
ls -altr

# make the Pythia executable
make

# run the Pythia event generation
echo "Running Pythia to generate events..."
./pythia_generate $2 output_events.hepmc output_events_xsec.txt
echo "Pythia run completed."

echo "Running Delphes to simulate detector response..."

# use LCG_106 DelphesHepMC2 with ATLAS card
DELPHES_CARD="/cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/share/Delphes/cards/delphes_card_ATLAS.tcl"
DELPHES_OUT="$3"

DelphesHepMC2 "${DELPHES_CARD}" "${DELPHES_OUT}" output_events.hepmc

echo "Delphes run completed. Output: ${DELPHES_OUT}"

echo "ls -altr"
ls -altr

# copy the output file to EOS
echo "Copying output file to EOS..."
xrdcp ${DELPHES_OUT} root://eosuser.cern.ch/$4
echo "Output file copied to EOS."
