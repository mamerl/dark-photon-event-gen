"""

Submission script for DMsimp_s_spin1 samples used for validating
analysis code for the ATLAS Run 2 dijet TLA search
See https://arxiv.org/abs/2509.01219 for more details.

"""
from logger_setup import logger

TEMPLATE_FILE = "generate_dmsimp_template.txt"
MMED_FLAG = "<MMED>"

# points used for acceptances from Fig 2 of the aux material
# see https://doi.org/10.17182/hepdata.161624.v1/t7
MMED_VALUES = [350, 600, 1000, 2000]

submission_content = str()
for mmed in MMED_VALUES:
    # create a new submission file from the template
    with open(TEMPLATE_FILE, "r") as template:
        submission_content = template.read()
        submission_content = submission_content.replace(MMED_FLAG, str(mmed))
    
    # write out the new submission file
    submission_filename = f"generate_dmsimp_mmed{mmed}.txt"
    with open(submission_filename, "w") as submission_file:
        submission_file.write(submission_content)

