# copy files to the run/ directory
echo "Copying necessary scripts and templates to run/ directory..."
cp modules/generate.sh run/generate.sh
cp modules/submit_jobs.py run/submit_jobs.py
cp modules/condor_submit_template.txt run/condor_submit_template.txt
cp modules/generate_dmsimp_template.txt run/generate_dmsimp_template.txt

# make the generation script executable
echo "Making generation script executable..."
chmod +x run/generate.sh

# change to run/ directory
echo "Changing to run/ directory..."
cd run/

# submit the jobs via the submission script
echo "Submitting jobs via submit_jobs.py..."

# parse -m/--mass-points and -n/--nevents and remove them from "$@"
MASS_POINTS=""
NEVENTS=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--mass-points)
            if [[ -n "$2" && "$2" != -* ]]; then MASS_POINTS="$2"; shift 2; else echo "Error: $1 requires a value"; exit 1; fi;;
        -n|--nevents)
            if [[ -n "$2" && "$2" != -* ]]; then NEVENTS="$2"; shift 2; else echo "Error: $1 requires a value"; exit 1; fi;;
        --) shift; while [[ $# -gt 0 ]]; do ARGS+=("$1"); shift; done; break;;
        *) ARGS+=("$1"); shift;;
    esac
done

# replace positional parameters with remaining args
set -- "${ARGS[@]}"

# rebuild positional parameters to contain only -m/--mass-points and -n/--nevents (short form used)
NEWARGS=()
if [[ -n "$MASS_POINTS" ]]; then NEWARGS+=("-m" "$MASS_POINTS"); fi
if [[ -n "$NEVENTS" ]]; then NEWARGS+=("-n" "$NEVENTS"); fi
set -- "${NEWARGS[@]}"

echo "Final argument list for submit_jobs.py: ${NEWARGS[@]}"
# run submit_jobs.py using the NEWARGS array
python3 submit_jobs.py --condor-template condor_submit_template.txt --mg5-instructions generate_dmsimp_template.txt --job-id dmsimp "${NEWARGS[@]}"

