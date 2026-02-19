"""

##### Reinterpretation prototyping #####

This script is used for prototyping the reinterpretation of Gaussian 
resonance limits for $Z'$ searches done as a cross-check for the 
dark photon reinterpretation

The standard reinterpretation recommendations from 
Appendix A.1 of [arXiv:1407.1376](https://arxiv.org/abs/1407.1376) 
suggest to truncate the signal mass spectrum in the range 
$(0.8,\ 1.2) \times M$ where $M$ is the signal mass

This results in a large discrepancy between the reinterpretation 
and the published observed limits because the $Z'$ spectrum is 
not Gaussian enough in shape

This script investigates different truncation approaches to see 
which improves the results and provides best agreement with published results
"""
import json
import matplotlib.pyplot as plt
import numpy as np
import ROOT
from math import ceil, floor
import importlib
import sys
from data.samples import samples
from modules.logger_setup import logger
from matplotlib.backends.backend_pdf import PdfPages
import mplhep as hep
from modules.process_sample import run_reinterpretation

SAMPLES = [
    f"DMsimp_mmed{mass}"
    for mass in [
        600, 700, 800, 900, 1000, 
        1100, 1200, 1300, 1400, 
        1500, 1600, 1700, 1800]
]

SIGNAL_REGION = "J100"

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

JSON_TEMPLATE = "outputs/acceptances_{sample}_run2_atlas_tla_dijet.json"
ROOT_TEMPLATE = "outputs/histograms_{sample}_run2_atlas_tla_dijet.root"

# define a few different mass windows to see how the reinterpreted limit changes
MASS_WINDOWS = [
    (0.8, 1.2), # original window
    (0.85, 1.15), # slightly narrower window
    (0.9, 1.1), # narrower window
    (0.95, 1.05), # even narrower window
    (0.7, 1.3), # wider window (should give worse limit)
]
PLOT_STYLES = [
    {"color": "C0", "marker": "o", "markersize": 10},
    {"color": "C1", "marker": "s", "markersize": 10},
    {"color": "C2", "marker": "D", "markersize": 10},
    {"color": "C3", "marker": "^", "markersize": 10},
    {"color": "C4", "marker": "v", "markersize": 10},
]

REFERENCE_COUPLING = 0.1 # reference coupling used to convert excluded cross-section to excluded coupling

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
    # import the limits module needed to retrieve the gaussian
    # limits 
    sys.path.append("../analyses")
    analysis_limit = importlib.import_module("analyses.run2_atlas_tla_dijet_limits")
    gaussian_limits = analysis_limit.get_limits(SIGNAL_REGION)
    logger.info("retrieved gaussian limits for signal region %s", SIGNAL_REGION)

    # retrieve the different widths for which we have gaussian limits
    limit_widths = gaussian_limits["width"].unique()
    limit_widths = np.sort(limit_widths)
    logger.info("retrieved the following widths for which we have gaussian limits: %s", str(limit_widths.tolist()))

    sample_reinterpretations = dict()
    for sample in SAMPLES:
        # do the interpretation for this sample
        sample_reinterpretations[sample] = dict()

        # load metadata about the sample to get the mass of the signal
        # and the cross-section
        sample_xsec = float()
        sample_mass = samples[sample]["mass"]
        with open(samples[sample]["metadata"]) as f:
            metadata = json.load(f)
            sample_xsec = metadata[sample]["xsec"]

        logger.info("loaded metadata for sample %s with mass %f and cross-section %f pb", sample, sample_mass, sample_xsec)
        
        # load the root file and extract the histogram for mjj
        hist = None
        with ROOT.TFile(ROOT_TEMPLATE.format(sample=sample)) as f:
            hist = f.Get(f"{SIGNAL_REGION}/h_mjj")
            hist.SetDirectory(0)  # detach the histogram from the file
        # normalise the histogram so that we can extract the 
        # acceptance factors for different mjj windows directly
        hist_norm = hist.Clone(f"{hist.GetName()}_norm")
        hist_norm.Scale(1./hist_norm.Integral())

        # load the json file to get information about the sample
        # e.g. acceptance for analysis selection
        sample_info = None
        with open(JSON_TEMPLATE.format(sample=sample)) as f:
            sample_info = json.load(f)

        # loop over the different mass windows and do the reinterpretation for each
        for mass_window in MASS_WINDOWS:
            logger.info("doing reinterpretation for mass window %s", str(mass_window))

            # calculate the acceptance factor for this mass window
            low_edge = ceil(mass_window[0] * sample_mass)
            high_edge = floor(mass_window[1] * sample_mass)
            low_bin = hist_norm.GetXaxis().FindBin(low_edge)
            high_bin = hist_norm.GetXaxis().FindBin(high_edge)
            acceptance_factor = hist_norm.Integral(low_bin, high_bin)
            logger.info("calculated acceptance factor of %f for mass window %s", acceptance_factor, str(mass_window))

            # calculate the average mass in the window 
            # using the original histogram (not normalised) to get the correct average mass
            hist.GetXaxis().SetRange(low_bin, high_bin)
            mean_mass = hist.GetMean()
            logger.info("calculated average mass of %f for mass window %s", mean_mass, str(mass_window))

            # define width needed so that widest width needed so that 
            # the +/- 2 sigma region of the gaussian is contained in the window
            # i.e. this is the window size / 4
            # conventionally this was done with window size / 5
            # so that at least 95% of the gaussian is contained in the window
            width = float((mass_window[1] - mass_window[0]) / 5) * sample_mass
            # calculate ratio to average mass to determine how to pick point
            width_ratio = (width / mean_mass) * 100.

            # round up to the nearest value in widths
            if width_ratio not in limit_widths:
                if width_ratio > np.max(limit_widths):
                    logger.warning(
                        "calculated width/mass ratio of %s pc. for SR %s is larger than the maximum width available in the limits, using maximum width %s pc. for limit calculation",
                        width_ratio, SIGNAL_REGION, np.max(limit_widths)
                    )
                    width_ratio = np.max(limit_widths)
                elif width_ratio < np.min(limit_widths):
                    logger.warning(
                        "calculated width/mass ratio of %s pc. for SR %s is smaller than the minimum width available in the limits, using minimum width %s pc. for limit calculation",
                        width_ratio, SIGNAL_REGION, np.min(limit_widths)
                    )
                    width_ratio = np.min(limit_widths)
                else:
                    diff = width_ratio - limit_widths
                    mask = diff < 0
                    width_ratio = limit_widths[mask][np.argmin(diff[mask] * -1)]
            # ensure width is a float for later saving in json
            width_ratio = float(width_ratio)

            # pick the Gaussian limit point with the right width
            gauss_limit_fixed_width = gaussian_limits[gaussian_limits["width"] == int(width_ratio)]

            # get the observed limit for this mass and width point
            sample_excluded_xsec = float()
            if np.any(gauss_limit_fixed_width["mass"] == mean_mass):
                sample_excluded_xsec = gauss_limit_fixed_width.loc[gauss_limit_fixed_width["mass"] == mean_mass, "observed_limit"].values[0]
            else:
                # find the closest mass points above and below the mean mass
                mass_below = gauss_limit_fixed_width["mass"][gauss_limit_fixed_width["mass"] < mean_mass]
                mass_above = gauss_limit_fixed_width["mass"][gauss_limit_fixed_width["mass"] > mean_mass]
                if mass_below.empty and mass_above.empty:
                    sample_excluded_xsec = np.nan
                elif mass_below.empty or mass_above.empty:
                    sample_excluded_xsec = np.nan
                else:
                    # find the largest mass point in mass_below and smallest in mass_above
                    # and retrieve the observed limit for those points
                    closest_below = mass_below.max()
                    closest_above = mass_above.min()
                    limit_below = gauss_limit_fixed_width.loc[gauss_limit_fixed_width["mass"] == closest_below, "observed_limit"].values[0]
                    limit_above = gauss_limit_fixed_width.loc[gauss_limit_fixed_width["mass"] == closest_above, "observed_limit"].values[0]

                    # take the larger of the two limits to be conservative
                    sample_excluded_xsec = np.max([limit_below, limit_above])
                    # sample_excluded_xsec = np.interp(mean_mass, [closest_below, closest_above], [limit_below, limit_above])

            logger.info("excluded cross-section for mass window %s is %s", str(mass_window), str(sample_excluded_xsec))
            sample_reinterpretations[sample][f"{mass_window[0]}_to_{mass_window[1]}"] = dict(
                acceptance_factor = acceptance_factor,
                total_acceptance = acceptance_factor * sample_info[SIGNAL_REGION]["acceptance"],
                mean_mass = mean_mass,
                true_mass = sample_mass,
                width = width,
                excluded_xsec = sample_excluded_xsec,
                theory_xsec = sample_xsec * 1.25, # correct for BR(Z' -> qq) q = u,d,s,c vs. q = u,d,s,c,b
            )

        
    # make some plots to compare the different mass windows
    hep.style.use("ATLAS") # set ATLAS style for plotting
    with PdfPages("outputs/dmsimp_mass_window_comparisons.pdf") as pdf:

        # 1. plot the excluded cross-section vs. mass for the different mass windows
        plot_limit_comparison(sample_reinterpretations, pdf, coupling_limit=False)

        # 2. plot the gq exclusion limit vs. mass for the different mass windows
        plot_limit_comparison(sample_reinterpretations, pdf, coupling_limit=True)

if __name__ == "__main__":
    main()