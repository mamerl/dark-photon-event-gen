import os
import json
import matplotlib.pyplot as plt
import numpy as np
import importlib
import sys
from data.samples import samples
from modules.logger_setup import logger
from matplotlib.backends.backend_pdf import PdfPages
import mplhep as hep

################################################################
##### Global variables for the script are configured here

SAMPLES = [
    f"DMsimp_mmed{mass}"
    for mass in [
        600, 700, 800, 900, 1000, 
        1100, 1200, 1300, 1400, 
        1500, 1600, 1700, 1800
    ]
]

SIGNAL_REGIONS = ["J50", "J100"]

run2_coupling_limits = {
    "J50": {
        "mass": [375, 400, 425, 450, 475, 500, 525, 550, 575, 600],
        "limit": [0.0475, 0.053605, 0.070071, 0.0714, 0.069464, 0.071584, 0.078497, 0.076385, 0.073698, 0.077421],
    },
    "J100": {
        "mass": [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800],
        "limit":  [0.070669, 0.078217, 0.075438, 0.055203, 0.049024, 0.040118, 0.047253, 0.056033, 0.064963, 0.066217, 0.050991, 0.048699, 0.05483, 0.059274, 0.06931, 0.076097, 0.081922, 0.083092, 0.092393, 0.09817, 0.10621, 0.094697, 0.091868, 0.085656, 0.077461],
    }
}

# output file template
# use a different file name format to avoid overwriting
# existing results used for other studies
JSON_TEMPLATE = "outputs/TRUNCATION_TEST_acceptances_{sample}_run2_atlas_tla_dijet_{method}.json"

# define groups of methods to be compared
# the keys can be used in filenames for plots
# to distinguish between different results
# the values list all the methods that should be tested
methods = {
    "traditional": [
        "default",
        "generic_30",
        "generic_15",
        "generic_10",
        "generic_5",
    ],
    "alternative": [
        "quantile",
        "mode",
        "default",
    ]
}

################################################################


#### helper method used for plotting
def plot_limit_comparison(data:dict, pdf:PdfPages, coupling_limit:bool=False):
    """
    Plot the excluded cross-section vs. mass for the different mass windows
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    masses = list()
    limit_values = list()

    handles = list()
    labels = list()
    for mass_window, style in zip(MASS_WINDOWS, PLOT_STYLES):
        mass_window_key = f"{mass_window[0]}_to_{mass_window[1]}"
        masses = list()
        limit_values = list()
        for sample in SAMPLES:
            if mass_window_key in data[sample]:
                masses.append(data[sample][mass_window_key]["true_mass"])
                if coupling_limit:
                    # convert excluded cross-section to excluded coupling using the theory cross-section
                    limit_values.append(
                        # NOTE BR is already accounted for in the theory_xsec value, and there is no need to account for filter efficiency
                        REFERENCE_COUPLING * np.sqrt(data[sample][mass_window_key]["excluded_xsec"] / (data[sample][mass_window_key]["theory_xsec"] * data[sample][mass_window_key]["total_acceptance"]))
                    )
                else:
                    limit_values.append(data[sample][mass_window_key]["excluded_xsec"])
        
        # now plot the limit for this mass window
        ax.plot(masses, limit_values, ls="-", lw=3, **style)
        labels.append(fr"$[{mass_window[0]}, {mass_window[1]}] \times M$")
        handles.append(plt.Line2D([0], [0], ls="-", lw=4, **style))

    ax.set_xlabel(r"$m_{Z'}$ [GeV]", fontsize=28)
    if coupling_limit:
        ax.set_ylabel(r"$g_q$", fontsize=28)
        ax.set_ylim(0.02, 0.3)
    else:
        ax.set_ylabel(r"$\sigma \times A \times BR$ [pb]", fontsize=28)
        ax.set_ylim(bottom=0, top=3)

    if coupling_limit:
        # also plot the published limits for comparison
        ax.plot(run2_coupling_limits[SIGNAL_REGION]["mass"], run2_coupling_limits[SIGNAL_REGION]["limit"], ls="-", lw=3, color="k", marker="o", markersize=10)
        labels.append("Published limits")
        handles.append(plt.Line2D([0], [0], ls="--", lw=5, color="k", marker="o", markersize=15))

    ax.legend(handles, labels, title="Truncation window:", title_fontsize=28, loc="upper left", fontsize=28, labelspacing=0.5, bbox_to_anchor=(0.97, 1))
    ax.tick_params(axis="both", which="both", labelsize=28, pad=10)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)

def main():
    ###### run the reinterpretation for all the samples and methods needed
    ###### for comparisons to be made
    truncation_methods = list()
    for method_group in methods:
        truncation_methods.extend(methods[method_group])
    truncation_methods = list(set(truncation_methods)) # remove duplicates

    for method in truncation_methods:
        logger.info("running interpretation for truncation method: %s", method)
        os.system(
            f"python modules/process_sample.py -s {' '.join(SAMPLES)} -o outputs/ -w 4 -r -t {method} -a run2_atlas_tla_dijet --file-prefix TRUNCATION_TEST --skip-store-cutflows --skip-histograms"
        )

    # once finished plot the results in a loop over the methods

if __name__ == "__main__":
    main()