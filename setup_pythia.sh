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