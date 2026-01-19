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

# enter the run directory
cd run

# download MadGraph first
echo "Downloading MadGraph5_aMC@NLO v${MG_VERSION} from ${URL}..."
wget $URL
echo "Extracting MadGraph5_aMC@NLO v${MG_VERSION}..."
tar -xzf MG5_aMC_v${MG_VERSION}.tar.gz

echo "MadGraph5_aMC@NLO v${MG_VERSION} downloaded and extracted."
ls -altr

# move into the MadGraph directory
cd MG5_aMC_v${MG_VERSION_SCORE}

# MadGraph specific installation
# install dependencies (pythia and delphes)
# install models (HAHM and DMsimp)
echo "Installing MadGraph5_aMC@NLO dependencies and models..."

echo "install pythia8" > install_script.txt
echo "install mg5amc_py8_interface" >> install_script.txt
echo "install Delphes" >> install_script.txt
echo "set auto_update 0" >> install_script.txt # append to avoid auto updates
echo "set auto_convert_model T" >> install_script.txt
echo "import model DMsimp_s_spin1" >> install_script.txt
echo "quit" >> install_script.txt
./bin/mg5_aMC install_script.txt
rm install_script.txt

# setup the HAHM model
cp -r ../../HAHM_variableMW_v5_UFO models/HAHM_variableMW_v5_UFO
cp -r ../../HAHM_variableMW_v3_UFO models/HAHM_variableMW_v3_UFO
cd models/HAHM_variableMW_v5_UFO
python write_param_card.py
cd ../../
cd models/HAHM_variableMW_v3_UFO
python write_param_card.py
cd ../../

# return to the original script directory
cd ../..