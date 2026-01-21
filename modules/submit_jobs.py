"""

Submission script to generate MadGraph samples used for 
interpretation studies.

NOTE this script should be run inside the run/ directory!

"""
from modules.logger_setup import logger
import argparse
import os
import sys
import pathlib

parser = argparse.ArgumentParser(description="Submit MadGraph event generation jobs")
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
    help="output directory for ROOT files containing generated events (absolute or relative to run/ directory)",
    required=True
)
parser.add_argument(
    "-c",
    "--condor-template",
    type=pathlib.Path,
    help="path to condor submission template file",
    default=pathlib.Path("condor_submit_template.txt")
)
parser.add_argument(
    "-e",
    "--event-gen",
    type=pathlib.Path,
    help="path to MadGraph5 instruction file",
    required=True
)
parser.add_argument(
    "-id",
    "--job-id",
    type=str,
    help="job ID string to identify this submission",
    required=True,
)

args = parser.parse_args()

logger.info("starting MadGraph5_aMC@NLO event generation job submission...")
logger.info("running from directory: %s", os.getcwd())

if not args.output_dir.exists():
    logger.error("output directory %s does not exist!", args.output_dir)
    sys.exit(1)

if not args.condor_template.exists():
    logger.error("condor submission template file %s does not exist!", args.condor_template)
    sys.exit(1)

if not args.event_gen.exists():
    logger.error("MadGraph5 instruction file %s does not exist!", args.event_gen)
    sys.exit(1)

if len(args.job_id.strip()) == 0:
    logger.error("job ID string cannot be empty!")
    sys.exit(1)

output_path = args.output_dir.resolve()
if "home-" + os.environ["USER"][0] in str(output_path):
    output_path = pathlib.Path(f"/eos/user/{os.environ['USER'][0]}/{os.environ['USER']}{str(output_path).split(os.environ['USER'])[1]}")
logger.info("using output directory: %s", output_path)

MMED_VALUES = args.mass_points
NEVENTS_PER_POINT = args.nevents

TEMPLATE_FILE = args.event_gen
MMED_FLAG = "<MMED>"
NEVENTS_FLAG = "<NEVENTS>"

CONDOR_SUBMISSION_TEMPLATE = args.condor_template

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
    submission_filename = f"generate_{args.job_id}_mmed{mmed}.txt"
    with open(submission_filename, "w") as submission_file:
        submission_file.write(submission_content)
    logger.info("wrote MadGraph instruction file %s", submission_filename)

    # add to condor submission file
    condor_content += ( "\n" + "\t" + 
        f"/afs/cern.ch/user/{os.environ['USER'][0]}/{os.environ['USER']}/private/x509up" + ", " + 
        submission_filename + ", " +
        str(output_path) + ", " +
        f"generated_events_{args.job_id}_mmed{mmed}_*.root" + ", " + 
        f"xsec_info_{args.job_id}_mmed{mmed}.txt" + ", " + 
        f"mg5_info_{args.job_id}_mmed{mmed}.txt"
    )

condor_content += "\n" + ")"
condor_filename = f"condor_{args.job_id}.sub"
with open(condor_filename, "w") as condor_file:
    condor_file.write(condor_content)
logger.info("wrote condor submission file %s", condor_filename)

# submit the condor job
os.system(f"condor_submit -spool {condor_filename}")