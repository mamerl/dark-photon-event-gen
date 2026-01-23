# copy files to the run/ directory
echo "Copying necessary scripts and templates to run/ directory..."
cp modules/generate.sh run/generate.sh
cp modules/submit_jobs.py run/submit_jobs.py
cp modules/condor_submit_template.txt run/condor_submit_template.txt
cp modules/generate_hahm_v5_template.txt run/generate_hahm_v5_template.txt
# make the generation script executable
echo "Making generation script executable..."
chmod +x run/generate.sh

# change to run/ directory
echo "Changing to run/ directory..."
cd run/

# submit the jobs via the submission script
echo "Submitting jobs via submit_jobs.py..."

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

echo "Final argument list for submit_jobs.py: ${NEWARGS[@]}"
# run submit_jobs.py using the NEWARGS array
python3 submit_jobs.py --condor-template condor_submit_template.txt -e generate_hahm_v5_template.txt --job-id hahm "${NEWARGS[@]}"
