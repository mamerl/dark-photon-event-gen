

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

# first make sure module level imports work by adding this directory to 
# the PYTHONPATH
export PYTHONPATH=$(pwd):$PYTHONPATH

# create a new voms proxy for xrootd access in HTCondor
# NOTE change the output path to your private x509up file path on AFS
# make sure this gets propagated to condor_submission.txt via the
# Proxy_path variable

# NOTE change the experiment name if not ATLAS
# change AFS path accordingly if the proxy should
# be stored somewhere else
export EXPERIMENT=atlas
export AFS_PATH=/afs/cern.ch/user/${USER:0:1}/${USER}

echo "Creating new voms proxy for xrootd access..."
voms-proxy-init -voms ${EXPERIMENT} -valid 191:0 -out ${AFS_PATH}/private/x509up || { echo "Failed to create voms proxy"; return 1; }