"""

Analysis code corresponding to the ATLAS Run 2 dijet TLA search
See https://arxiv.org/abs/2509.01219 for details.

"""
import analyses.common_tools as ct

def analysis():
    # initialise dictionary to hold rdfs for each signal region
    region_dict = {"J100": None, "J50": None}

    return 