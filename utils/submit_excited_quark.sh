# copy files to the run/ directory
echo "Copying necessary scripts and templates to run/ directory..."
cp utils/pythia_condor_template.txt run/pythia_condor_template.txt
cp utils/generate_excitedquark_template.cmnd run/generate_excitedquark_template.cmnd
cp utils/submit_pythia.py run/submit_pythia.py
cp utils/run_pythia_generation.sh run/run_pythia_generation.sh
cp utils/Makefile run/Makefile
cp utils/pythia_generate.cxx run/pythia_generate.cxx

# change to run/ directory
echo "Changing to run/ directory..."
cd run/

# make the generation script executable
echo "Making generation script executable..."
chmod +x run/run_pythia_generation.sh

# submit the jobs via the submission script
echo "Submitting jobs via submit_pythia.py..."

# parse -m/--mass-points (allowing multiple values), -n/--nevents and -o/--output-dir
MASS_POINTS=()
NEVENTS=""
OUTPUT_DIR=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--mass-points)
            # collect all following non-option arguments as mass points
            shift
            if [[ $# -eq 0 || "$1" == -* ]]; then
                echo "Error: -m/--mass-points requires at least one value"
                exit 1
            fi
            while [[ $# -gt 0 && "$1" != -* ]]; do
                MASS_POINTS+=("$1")
                shift
            done
            ;;
        -n|--nevents)
            if [[ -n "$2" && "$2" != -* ]]; then NEVENTS="$2"; shift 2; else echo "Error: $1 requires a value"; exit 1; fi;;
        -o|--output-dir)
            if [[ -n "$2" && "$2" != -* ]]; then OUTPUT_DIR="$2"; shift 2; else echo "Error: $1 requires a value"; exit 1; fi;;
        --) shift; while [[ $# -gt 0 ]]; do ARGS+=("$1"); shift; done; break;;
        *) ARGS+=("$1"); shift;;
    esac
done

# rebuild argument list to contain only -m/--mass-points, -n/--nevents and -o/--output-dir (short form used)
NEWARGS=()
if [[ ${#MASS_POINTS[@]} -gt 0 ]]; then NEWARGS+=("-m" "${MASS_POINTS[@]}"); fi
if [[ -n "$NEVENTS" ]]; then NEWARGS+=("-n" "$NEVENTS"); fi
if [[ -n "$OUTPUT_DIR" ]]; then NEWARGS+=("-o" "$OUTPUT_DIR"); fi

echo "Final argument list for submit_pythia.py: ${NEWARGS[@]}"
# run submit_pythia.py using the NEWARGS array
python3 submit_pythia.py --condor-template pythia_condor_template.txt -e generate_excitedquark_template.cmnd --job-id excited_quark "${NEWARGS[@]}"

# once everything is submitted cleanup the run/ directory
echo "Cleaning up run/ directory..."
rm pythia_condor_template.txt
rm generate_excitedquark_template.cmnd
rm submit_pythia.py
rm run_pythia_generation.sh
rm Makefile
rm pythia_generate.cxx
echo "Cleanup completed."
# return to original directory
cd ..