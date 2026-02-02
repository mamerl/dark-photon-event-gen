#############################################
### Setup script for MadGraph5_aMC@NLO
### using CVMFS LCG environment
###

MG_VERSION=3_6_7
MG_URL=https://launchpad.net/mg5amcnlo/3.0/3.6.x/+download/MG5_aMC_v3.6.7.tar.gz

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

# variables for directory paths
SCRIPT_DIR=$(pwd)
WORKDIR=./run

# install MadGraph via the install script
# if it does not exist yet
if [[ ! -d ${WORKDIR}/MG5_aMC_v${MG_VERSION} ]]; then
  echo "MadGraph5_aMC@NLO v${MG_VERSION} not found. Installing now..."
  MG_VERSION_DOT=${MG_VERSION//_/.}
  ./install.sh -v ${MG_VERSION_DOT} -u ${MG_URL}
fi

# setup some path variables
cd ${WORKDIR}/MG5_aMC_v${MG_VERSION}
# setup needed for Pythia8
export PYTHIA8DATA=$(pwd)/HEPTools/pythia8/share/Pythia8/xmldoc/
# setup needed for Delphes
export LD_LIBRARY_PATH=$(pwd)/Delphes:${LD_LIBRARY_PATH}
export ROOT_INCLUDE_PATH=$(pwd)/Delphes:${ROOT_INCLUDE_PATH}
cd ${SCRIPT_DIR}

# copy necessary files to the MG5 working directory
# create tarball name/path
TARBALL="MG5_aMC_v${MG_VERSION}_with_dependencies.tar.gz"
TARBALL_PATH="./run/${TARBALL}"

# warn if it exists
if [[ -f "${TARBALL_PATH}" ]]; then
  echo "WARNING: ${TARBALL_PATH} already exists and will be deleted."
  read -p "Delete and replace? [y/N] " ans
  case "${ans}" in
    [yY]|[yY][eE][sS]) rm -f "${TARBALL_PATH}" || { echo "Failed to remove existing tarball"; return 1; } ;;
    *) echo "Aborting: existing tarball preserved."; return 1 ;;
  esac
fi

# create tarball of WORKDIR contents in the current directory
echo "Creating ${TARBALL} from ${WORKDIR}..."
mkdir ${WORKDIR}/artefacts
cd ${WORKDIR}
tar -czvf ./artefacts/${TARBALL} MG5_aMC_v${MG_VERSION} || { echo "Failed to create tarball"; return 1; }
mv ./artefacts/${TARBALL} ${TARBALL}
rm -rf ./artefacts
echo "Created ${TARBALL_PATH}"
cd ..
