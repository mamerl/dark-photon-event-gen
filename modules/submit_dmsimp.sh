# copy files to the run/ directory
echo "Copying necessary scripts and templates to run/ directory..."
cp modules/generate.sh run/generate.sh
cp modules/submit_dmsimp.py run/submit_dmsimp.py
cp modules/condor_submit_template.txt run/condor_submit_template.txt
cp modules/generate_dmsimp_template.txt run/generate_dmsimp_template.txt

# make the generation script executable
echo "Making generation script executable..."
chmod +x run/generate.sh

# change to run/ directory
echo "Changing to run/ directory..."
cd run/

# submit the jobs via the submission script
echo "Submitting jobs via submit_dmsimp.py..."
python3 submit_dmsimp.py $@

