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
        375, 400, 450, 500, 550,
        600,
        700, 800, 900, 1000, 
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

run2_xsec_limits = {
    "J50": {
        "mass": [375, 400, 425, 450, 475, 500, 525, 550, 575, 600],
        "limit": [],
    },
    "J100": {
        "mass": [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800],
        "limit": [],
    }
}

SKIP_PRODUCTION = True

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
        # "generic_30",
        "generic_15",
        "generic_10",
        "generic_5",
    ],
    "alternative": [
        "quantile",
        "mode",
        "default",
        "generic_15",
    ]
}

method_names = {
    "default": r"$[0.8, 1.2]\times M$",
    "generic_30": r"$[0.7, 1.3]\times M$",
    "generic_15": r"$[0.85, 1.15]\times M$",
    "generic_10": r"$[0.9, 1.1]\times M$",
    "generic_5": r"$[0.95, 1.05]\times M$",
    "quantile": "Quantile",
    "mode": "Mode",
}

################################################################


#### helper method used for plotting
def plot_limit_comparison(truncation_methods:list, pdf:PdfPages, coupling_limit:bool=False):
    """
    Plot the excluded cross-section vs. mass for the different mass windows
    """
    hep.style.use("ATLAS")
    fig, ax = plt.subplots(2, 1, figsize=(15, 8), layout="constrained", sharex=True, height_ratios=[0.7, 0.3])
    # fig.get_layout_engine().set(hspace=0.001)

    line_formats = [
        dict(ls="-", lw=3, marker="o", markersize=10, color="C0"),
        dict(ls="--", lw=3, marker="s", markersize=10, color="C1"),
        dict(ls="-.", lw=3, marker="^", markersize=10, color="C2"),
        dict(ls=":", lw=3, marker="d", markersize=10, color="C3"),
        dict(ls="-", lw=3, marker="v", markersize=10, color="C4"),
        dict(ls="--", lw=3, marker="P", markersize=10, color="C5"),
        dict(ls="-.", lw=3, marker="X", markersize=10, color="C6"),
        dict(ls=":", lw=3, marker="*", markersize=10, color="C7"),
    ]

    handles = list()
    labels = list()
    data = dict()
    masses = list()
    limit_values = list()
    acceptance_file = "outputs/TRUNCATION_TEST_acceptances_{sample}_run2_atlas_tla_dijet_{method}.json"
    for i, truncation_method in enumerate(truncation_methods):
        for sr in SIGNAL_REGIONS:
            masses = list()
            limit_values = list()
            for sample in SAMPLES:
                with open(acceptance_file.format(sample=sample, method=truncation_method), "r") as f:
                    data = json.load(f)
                
                if np.isnan(data[sr]["modified_expected_xsec_pb"]) or np.isnan(data[sr]["excluded_xsec_pb"]):
                    # skip this point if the limit is not available 
                    # or if the expected cross-section is not a number 
                    continue 
                
                if coupling_limit:
                    # if coupling limit is requested, we need to compute the 
                    # coupling for each sample and truncation method
                    limit_values.append(
                        0.1 * np.sqrt(data[sr]["excluded_xsec_pb"] / (data[sr]["modified_expected_xsec_pb"]))
                    )
                else: # cross-section limit
                    limit_values.append(
                        data[sr]["excluded_xsec_pb"]
                    )
                
                masses.append(samples[sample]["mass"])

            # now plot the limit for this mass window
            style = line_formats[i % len(line_formats)]
            ax[0].plot(masses, limit_values, **style)

            if coupling_limit:
                # now calculate the ratio to the published result
                # for this signal region and plot that too
                ratios_mask = np.full_like(
                    run2_coupling_limits[sr]["mass"] if coupling_limit else run2_xsec_limits[sr]["mass"], 
                    False, 
                    dtype=bool
                )

                for mass in masses:
                    ratios_mask |= np.array(run2_coupling_limits[sr]["mass"] if coupling_limit else run2_xsec_limits[sr]["mass"]) == mass
                
                # calculate the ratio values with the mask applied
                ratio_values = np.array(limit_values) / np.array(run2_coupling_limits[sr]["limit"] if coupling_limit else run2_xsec_limits[sr]["limit"])[ratios_mask]
                ratio_values[np.isinf(ratio_values) | np.isnan(ratio_values)] = np.nan
                ax[1].plot(masses, ratio_values, **style)

    ax[1].set_xlabel(r"$m_{Z'}$ [GeV]", fontsize=28)
    if coupling_limit:
        ax[0].set_ylabel(r"$g_q$", fontsize=28)
        ax[0].set_ylim(0.02, 0.3)
    else:
        ax[0].set_ylabel(r"$\sigma \times A \times \mathrm{BR}$ [pb]", fontsize=28)
        ax[0].set_ylim(bottom=0)
    ax[1].set_ylabel("Ratio\n(to published)", fontsize=28)

    if coupling_limit:
        # also plot the published limits for comparison
        for sr in SIGNAL_REGIONS:
            ax[0].plot(run2_coupling_limits[sr]["mass"], run2_coupling_limits[sr]["limit"], ls=":", lw=4, color="k", marker="o", markersize=10)
    else:
        # plot the cross-section limits for comparison
        pass

    # add legend entry for published limits
    leg = ax[0].legend(
        handles=[
            plt.Line2D([0], [0], ls=":", lw=5, color="k", marker="o", markersize=15, label="Published limits")
        ],
        loc="upper left", 
        bbox_to_anchor=(0.97, 1.1),
        fontsize=28,
    )
    ax[0].add_artist(leg)

    # setup legend
    ax[0].legend(
        handles=[
            plt.Line2D([0], [0], **line_formats[i % len(line_formats)])
            for i in range(len(truncation_methods))
        ],
        labels=[method_names[method] for method in truncation_methods],
        title="Truncation window:",
        title_fontsize=28,
        loc="upper left",
        bbox_to_anchor=(0.97, 0.95),
        fontsize=28,
        labelspacing=0.5,
    )

    ax[0].tick_params(axis="both", which="both", labelsize=28, pad=10)
    ax[1].tick_params(axis="both", which="both", labelsize=28, pad=10)
    
    ax[1].set_xlim(350, 1825)

    pdf.savefig(fig, bbox_inches="tight", bbox_extra_artists=[leg])
    plt.close(fig)

def main():
    ###### run the reinterpretation for all the samples and methods needed
    ###### for comparisons to be made
    if not SKIP_PRODUCTION:
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
    # compare cross-section and coupling limits for each method
    for method_group in methods:
        with PdfPages(f"outputs/TRUNCATION_TEST_acceptances_comparison_{method_group}.pdf") as pdf:
            for coupling_limit in [False, True]:
                data = dict()
                for method in methods[method_group]:
                    method_data = dict()
                    for sample in SAMPLES:
                        with open(JSON_TEMPLATE.format(sample=sample, method=method), "r") as f:
                            method_data[sample] = json.load(f)
                    data[method] = method_data
                plot_limit_comparison(data, pdf, coupling_limit=coupling_limit)


if __name__ == "__main__":
    main()