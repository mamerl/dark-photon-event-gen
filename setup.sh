#############################################
### Setup script for MadGraph5_aMC@NLO
### using CVMFS LCG environment
###


MG_VERSION=2_9_24
MG_URL=https://launchpad.net/mg5amcnlo/lts/2.9.x/+download/MG5_aMC_v2.9.24.tar.gz

# Check if we have access to cvfms 
if [[ -r /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase ]] ; then
  source /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh
else
  echo "ERROR: cvmfs not accessible. You need to run on lxplus"
  return 1
fi

# first make sure module level imports work by adding the top-level
# git repo directory to PYTHONPATH
TOP_DIR=$(cd .. && pwd)
export PYTHONPATH=${TOP_DIR}:$PYTHONPATH

# variables for directory paths
SCRIPT_DIR=$(pwd)
WORKDIR=../../StandaloneMG5

# install MadGraph via the install script
# if it does not exist yet
if [[ ! -d ${WORKDIR}/MG5_aMC_v${MG_VERSION} ]]; then
  echo "MadGraph5_aMC@NLO v${MG_VERSION} not found. Installing now..."
  MG_VERSION_DOT=${MG_VERSION//_/.}
  ./install.sh -v ${MG_VERSION_DOT} -u ${MG_URL}
fi

# copy necessary files to the MG5 working directory
# create tarball name/path
TARBALL="MG5_aMC_v${MG_VERSION}_with_dependencies.tar.gz"
TARBALL_PATH="${SCRIPT_DIR}/${TARBALL}"

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
tar -czvf ${TARBALL_PATH} -C ${WORKDIR} . || { echo "Failed to create tarball"; return 1; }
echo "Created ${TARBALL_PATH}"
