#!/bin/bash

##################################################
### Script run to generate DMsimp_s_spin1
### samples via CERN HTCondor

echo "Starting DMsimp_s_spin1 event generation script..."

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

echo "Setting up voms proxy for xrootd access..."
# voms proxy setup
# NOTE change path also in the setup.sh script when necessary
export X509_USER_PROXY=$1
# export X509_USER_PROXY=/afs/cern.ch/user/m/mamerl/private/x509up
voms-proxy-info -all
voms-proxy-info -all -file ${X509_USER_PROXY}

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

ls -altr
ls -altr output_dmsimp

EOS_OUTPUT_PATH=$3
OUTPUT_FILE_PATTERN="$4"

ROOT_DIR="output_dmsimp/Events/run_01"
ls -altr $ROOT_DIR
if [[ -d "$ROOT_DIR" ]]; then
  count=0
  for f in $(find "$ROOT_DIR" -maxdepth 1 -type f -name '*.root'); do
    ((count++))
    out_name="${out_pattern/\*/$count}"   # replace first '*' with count
    echo "Copying $f to EOS as $out_name"
    xrdcp "$f" "root://eosuser.cern.ch/${EOS_OUT_DIR}/${out_name}"
  done
else
  echo "Directory $ROOT_DIR not found"
fi
