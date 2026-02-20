import os
import importlib
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

################################################################
##### Global variables for the script are configured here

SAMPLES = [
    f"DMsimp_mmed{mass}"
    for mass in [
        600,
        700, 800, 900, 1000, 
        1100, 1200, 1300, 1400, 
        1500, 1600, 1700, 1800
    ]
]

ANALYSIS_NAME = "run2_atlas_tla_dijet"

METHODS = [
    "default",
    "quantile",
    "mode",
]
METHOD_NAMES = [
    "Default",
    "Quantiles",
    "Mode",
]

NUM_PROCESSES = 8

SKIP_PRODUCTION = False

################################################################

def execute_method(
    truncation_method:str,
    sample:str,
    analysis_name:str="",
):
    # run the histogramming code for the sample for all signal regions
    # no reinterpretation is run here
    os.system(
        f"python modules/process_sample.py -s {sample} -a {analysis_name} --skip-store-cutflows --file-prefix MASS_WINDOW_CHECKS"
    )

    data_dict = dict()

    # load the analysis module so that the RDF objects can be retrieved
    # for each signal region and different truncation methods
    # can be compared
    analysis_module = importlib.import_module(f"analyses.{analysis_name}")

    # load the RDF for this sample
    sample_rdf = ct.load_delhes_rdf(
        sample, 
        samples[sample]["ntuple"], 
        samples[sample]["metadata"]
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
                    results[method][sample] = pool.apply_async(
                        execute_method,
                        args=(
                            method,
                            sample,
                            ANALYSIS_NAME,
                        )
                    )
                    results[method][sample].get()

    # get list of signal regions for this analysis
    # to be used for plotting
    signal_regions = list(results[METHODS[0]][SAMPLES[0]].keys())

    # now plot the results for each sample
    with PdfPages("outputs/mass_window_validation.pdf") as pdf:
        for sample in SAMPLES:
            for sr in signal_regions:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.set_xlabel(r"$m_{\mathrm{jj}}$ [GeV]", fontsize=28)
                ax.set_ylabel("Entries", fontsize=28)

                # retrieve and plot the mjj histogram for this sample
                with uproot.open(
                    f"outputs/MASS_WINDOW_CHECKS_histograms_{sample}_{ANALYSIS_NAME}.root"
                ) as f:
                    mjj_hist = f["mjj"].to_boost()
                    # use 10 GeV bin widths
                    mjj_hist = mjj_hist[::bh.rebin(10)]
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
                    plt.Line2D([], [], color="k", lw=6, ls="--")
                    plt.Line2D([], [], color="k", lw=7, ls="-")
                    plt.Line2D([], [], color="k", lw=5.5, ls=":")
                ]
                labels = [
                    "Mean",
                    "Window edges",
                    r"$\pm 1\sigma$ points",
                ]
                for idx, method in enumerate(METHODS):
                    handles.append(
                        plt.Line2D([], [], color=f"C{idx}", lw=10, ls="-")
                    )
                    labels.append(METHOD_NAMES[idx])
                ax.legend(
                    handles[::-1],
                    labels[::-1],
                    fontsize=28,
                    loc="upper right",
                    title=f"Region: {sr}\nTruncation method:",
                    title_fontsize=28,
                    labelspacing=0.5,
                    bbox_to_anchor=(0.97, 1),
                    title_fontproperties={"ha": "center"}
                )
                pdf.savefig(fig)
                plt.close(fig)

if __name__ == "__main__":
    main()