##### Installation script for MadDM environment #####

# Parse -v command line argument for verbosity (store string)
MG_VERSION=""
URL=""
while getopts "v:u:" opt; do
    case $opt in
        v)
            MG_VERSION="$OPTARG"
            ;;
        u)
            URL="$OPTARG"
            ;;
        *)
            echo "Usage: $0 -v <MG version (e.g., 2.9.24)> -u <MG download URL>"
            return 0
            ;;
    esac
done

echo "MadGraph version set to: $MG_VERSION"
echo "MadGraph download URL set to: $URL"

MG_VERSION_SCORE=${MG_VERSION//./_}

# store the script directory
SCRIPT_DIR=$(pwd)

# go to standalone working directory
WORKDIR=../../StandaloneMadDM
mkdir -p $WORKDIR
cd $WORKDIR
echo "Entered directory $(pwd)"
ABS_WORKDIR=$(pwd)

# instructions from https://maddmhep.github.io/maddm/dev/index.html
# and https://github.com/dimauromattia/darktools/tree/main/maddm [working]
# and https://github.com/maddmhep/maddm/tree/rc/3.3 [updated MG versions]

# download MadGraph first
echo "Downloading MadGraph5_aMC@NLO v${MG_VERSION} from ${URL} ..."
wget $URL
tar -xzf MG5_aMC_v${MG_VERSION}.tar.gz

echo "MadGraph5_aMC@NLO v${MG_VERSION} downloaded and extracted."
ls -altr

# move into the MadGraph directory
cd MG5_aMC_v${MG_VERSION_SCORE}

echo "Installing MadDM..."
cd PLUGIN
git clone -b rc/3.3 --depth 1 --recurse-submodules --shallow-submodules https://github.com/maddmhep/maddm.git
mv maddm/maddm ../bin/maddm.py 
cd .. # MG5 directory
cd .. # back to working directory

# install MadDM dependencies
cd ..
echo "MadDM installed."
echo "Installing MadDM dependencies..."
echo "install pythia8" > install_script.txt
echo "install PPPC4DMID" >> install_script.txt # append
echo "set auto_update 0" >> install_script.txt # append to avoid auto updates
python $ABS_WORKDIR/MG5_aMC_v${MG_VERSION_SCORE}/bin/maddm.py install_script.txt
rm install_script.txt # remove tmp installation script

echo "MadDM dependencies installed."

# now delete the MG5 tarball to save space
rm -f MG5_aMC_v${MG_VERSION}.tar.gz

# return to the original script directory
cd $SCRIPT_DIR