"""

This script checks the acceptance of DMsimp signals for 
the analyses configured in analyses.

Doing this ensures that the analysis selections configured
in each analysis module are correct, by comparing the 
acceptances obtained here to those published in the
auxiliary material of the relevant analysis paper.

"""

analyses_to_run = [
    "run2_atlas_tla_dijet",
]

samples_to_check = [
    "DMsimp_mmed_600",
]