"""

Submission script to generate DMsimp_s_spin1 samples used 
for validating analysis code for the ATLAS Run 2 dijet TLA 
search.

See https://arxiv.org/abs/2509.01219 for more details.

NOTE this script should be run inside the run/ directory!

"""
from modules.logger_setup import logger
import argparse
import os
import sys
import pathlib

parser = argparse.ArgumentParser(description="Submit DMsimp_s_spin1 event generation jobs")
parser.add_argument(
    "-m",
    "--mass-points",
    nargs="+",
    type=int,
    help="mediator masses to process",
    # points used for acceptances from Fig 2 of the aux material
    # see https://doi.org/10.17182/hepdata.161624.v1/t7
    default=[350, 600, 1000, 2000]
)
parser.add_argument(
    "-n",
    "--nevents",
    type=int,
    help="number of events per mass point",
    default=10000,
)
parser.add_argument(
    "-o",
    "--output-dir",
    type=pathlib.Path,
    help="output directory for ROOT files containing generated events",
    required=True
)
args = parser.parse_args()

if not args.output_dir.exists():
    logger.error("output directory %s does not exist!", args.output_dir)
    sys.exit(1)

output_path = args.output_dir.resolve()
logger.info("using output directory: %s", output_path)

MMED_VALUES = args.mass_points
NEVENTS_PER_POINT = args.nevents

TEMPLATE_FILE = "generate_dmsimp_template.txt"
MMED_FLAG = "<MMED>"
NEVENTS_FLAG = "<NEVENTS>"

CONDOR_SUBMISSION_TEMPLATE = "condor_submit_dmsimp.txt"

if not os.getcwd().endswith("run"):
    logger.error("This script must be run inside the run/ directory!")
    sys.exit(1)

# create condor submission file
condor_content = str()
with open(CONDOR_SUBMISSION_TEMPLATE, "r") as condor_template:
    condor_content = condor_template.read()
# replace user flag in condor template
# condor_content = condor_content.replace("<USR>", os.environ["USER"])

submission_content = str()
for mmed in MMED_VALUES:
    logger.info("setting up submissing for mmed = %s with %s events", mmed, NEVENTS_PER_POINT)

    # create a new submission file from the template
    with open(TEMPLATE_FILE, "r") as template:
        submission_content = template.read()
        submission_content = submission_content.replace(MMED_FLAG, str(mmed))
        submission_content = submission_content.replace(NEVENTS_FLAG, str(int(NEVENTS_PER_POINT)))

    # write out the new submission file
    submission_filename = f"generate_dmsimp_mmed{mmed}.txt"
    with open(submission_filename, "w") as submission_file:
        submission_file.write(submission_content)
    logger.info("wrote MadGraph instruction file %s", submission_filename)

    # add to condor submission file
    condor_content += ( "\n" + "\t" + 
        f"/afs/cern.ch/user/{os.environ['USER'][0]}/{os.environ['USER']}/private/x509up" + ", " + 
        submission_filename + ", " +
        str(output_path) + ", " +
        f"generated_events_dmsimp_mmed{mmed}_*.root" + ", " + 
        f"xsec_info_dmsimp_mmed{mmed}.txt" + ", " + 
        f"mg5_info_dmsimp_mmed{mmed}.txt"
    )

condor_content += "\n" + ")"
condor_filename = "condor_dmsimp.sub"
with open(condor_filename, "w") as condor_file:
    condor_file.write(condor_content)
logger.info("wrote condor submission file %s", condor_filename)

# submit the condor job
os.system(f"condor_submit -spool {condor_filename}")

        




