import os
import importlib
import json
import mplhep as hep
import uproot
import boost_histogram as bh
import matplotlib.pyplot as plt
from modules.logger_setup import logger
from data.samples import samples
import modules.common_tools as ct
from matplotlib.backends.backend_pdf import PdfPages
import multiprocessing as mp
from modules.process_sample import TruncationWindow
import logging
import contextlib

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

ANALYSIS_NAME = "run2_atlas_tla_dijet"

METHODS = [
    "default",
    "generic_15",
    "quantile",
    "mode",
    "mode_15",
]
METHOD_NAMES = [
    r"Default ($[0.8, 1.2]\times M$)",
    r"$[0.85, 1.15]\times M$",
    "Quantiles",
    r"Mode $\pm 2\sigma$",
    r"Mode in $[0.85, 1.15]\times M$"
]

NUM_PROCESSES = 16

SKIP_PRODUCTION = False

################################################################

@contextlib.contextmanager
def suppress_logging(level=logging.CRITICAL):
    logging.disable(level)
    try:
        yield
    finally:
        logging.disable(logging.NOTSET)  # re-enable logging after


def execute_method(
    truncation_method:str,
    sample:str,
    analysis_name:str="",
):
    # run the histogramming code for the sample for all signal regions
    # no reinterpretation is run here
    # "> /dev/null 2>&1" at the end redirects all output to 
    # /dev/null to avoid cluttering the terminal
    os.system(
        f"python modules/process_sample.py -s {sample} -a {analysis_name} --skip-store-cutflows --file-prefix MASS_WINDOW_CHECKS -o outputs > /dev/null 2>&1"
    )

    data_dict = dict()

    # load the analysis module so that the RDF objects can be retrieved
    # for each signal region and different truncation methods
    # can be compared
    analysis_module = importlib.import_module(f"analyses.{analysis_name}")

    with suppress_logging():
        # load the RDF for this sample
        sample_rdf = ct.load_delhes_rdf(
            sample, 
            samples[sample]["ntuple"], 
            samples[sample]["metadata"],
            progess_bar=False
        )
        sr_dfs = analysis_module.analysis(sample_rdf)[0]

        # get the RDF objects for each signal region and truncation method
        for sr in sr_dfs.keys():
            data_dict[sr] = dict()

            # define new truncation window
            tmp_window = TruncationWindow(
                truncation_method,
                samples[sample]["mass"],
                sr_dfs[sr],
            )

            data_dict[sr] = {
                "mean": tmp_window.get_mean(),
                "sigma": tmp_window.get_sigma(),
                "window": tmp_window.get_window(),
            }

    return data_dict

def main():
    results = {
        method: {}
        for method in METHODS
    }
    if not SKIP_PRODUCTION:
        # run the code to get information about the truncation methods 
        # for each sample and produce histograms
        with mp.Pool(processes=NUM_PROCESSES) as pool:
            for method in METHODS:
                for sample in SAMPLES:
                    logger.info("launching process for truncation method '%s' and sample %s", method, sample)
                    results[method][sample] = pool.apply_async(
                        execute_method,
                        args=(
                            method,
                            sample,
                            ANALYSIS_NAME,
                        )
                    )
            
            # get the results
            for method in METHODS:
                for sample in SAMPLES:
                    results[method][sample] = results[method][sample].get()

        with open("outputs/dmsimp_mass_window_validation_results.json", "w") as f:
            json.dump(results, f, indent=4)
    else:
        with open("outputs/dmsimp_mass_window_validation_results.json", "r") as f:
            results = json.loads(f.read())

    # get list of signal regions for this analysis
    # to be used for plotting
    signal_regions = list(results[METHODS[0]][SAMPLES[0]].keys())

    hep.style.use("ATLAS")
    # now plot the results for each sample
    with PdfPages("outputs/dmsimp_mass_window_validation.pdf") as pdf:
        for sample in SAMPLES:
            for sr in signal_regions:
                logger.info("Plotting mass window validation for sample %s and signal region %s", sample, sr)
                fig, ax = plt.subplots(figsize=(15, 10))
                ax.set_xlabel(r"$m_{\mathrm{jj}}$ [GeV]", fontsize=28)
                ax.set_ylabel("Entries", fontsize=28)
                ax.tick_params(axis='both', which='both', labelsize=28, pad=10)

                # retrieve and plot the mjj histogram for this sample
                with uproot.open(
                    f"outputs/MASS_WINDOW_CHECKS_histograms_{sample}_{ANALYSIS_NAME}.root"
                ) as f:
                    mjj_hist = f[f"{sr}/h_mjj"].to_boost()
                    # use 10 GeV bin widths
                    mjj_hist = mjj_hist[::bh.rebin(20)]
                    hep.histplot(
                        mjj_hist, 
                        ax=ax, 
                        label="mjj distribution",
                        color="k",
                        lw=3,
                        flow=None
                    )

                # retrieve info for each method and plot
                for idx, method in enumerate(METHODS):
                    mean = results[method][sample][sr]["mean"]
                    window = results[method][sample][sr]["window"]
                    sigma = results[method][sample][sr]["sigma"]
                    ax.axvline(mean, ls="--", lw=3, color=f"C{idx}")
                    ax.axvline(window[0], ls="-", lw=3.5, color=f"C{idx}")
                    ax.axvline(window[1], ls="-", lw=3.5, color=f"C{idx}")
                    ax.axvline(mean - sigma, ls=":", lw=2.75, color=f"C{idx}")
                    ax.axvline(mean + sigma, ls=":", lw=2.75, color=f"C{idx}")

                # now add a legend
                handles = [
                    plt.Line2D([], [], color="k", lw=6, ls="--"),
                    plt.Line2D([], [], color="k", lw=7, ls="-"),
                    plt.Line2D([], [], color="k", lw=5.5, ls=":"),
                ]
                labels = [
                    "Mean",
                    "Window edges",
                    r"$\pm 1\sigma$ points",
                ]
                # add a first legend above the axes
                leg = ax.legend(
                    handles,
                    labels,
                    fontsize=30,
                    loc="lower center",
                    bbox_to_anchor=(0.5, 0.96),
                    ncol=3,
                    title=f"Region: {sr}, $m_{{Z'}} = {samples[sample]['mass']}$ GeV",
                    title_fontproperties={"size": 30, "weight": "bold"},
                )
                ax.add_artist(leg)

                handles = list()
                labels = list()
                for idx, method in enumerate(METHODS):
                    handles.append(
                        plt.Line2D([], [], color=f"C{idx}", lw=10, ls="-")
                    )
                    labels.append(
                        METHOD_NAMES[idx] + "\n"
                        + f"Window: [{results[method][sample][sr]['window'][0]:.0f}, {results[method][sample][sr]['window'][1]:.0f}] GeV" + "\n"
                        + f"Mean: {results[method][sample][sr]['mean']:.1f} GeV\n"
                        + f"$\sigma$: {results[method][sample][sr]['sigma']:.1f} GeV"
                    )
                leg2 = ax.legend(
                    handles,
                    labels,
                    fontsize=28,
                    loc="upper left",
                    title="Truncation method:",
                    labelspacing=0.5,
                    bbox_to_anchor=(0.97, 1.4),
                    title_fontproperties={"size": 28, "weight": "bold"},
                )
                leg2.get_title().set_multialignment('center')
                leg2.get_title().set_y(leg.get_title().get_position()[1] - 45)  # Adjust the y position of the title
                for t in leg2.get_texts():
                    t.set_y(t.get_position()[1] - 49)  # Adjust the y position of the text
                ax.set_xlim(
                    samples[sample]["mass"] * 0.4,
                    samples[sample]["mass"] * 1.6,
                )
                ax.yaxis.get_offset_text().set_fontsize(24)
                pdf.savefig(fig, bbox_inches="tight", bbox_extra_artists=(leg,leg2))
                plt.close(fig)

if __name__ == "__main__":
    main()