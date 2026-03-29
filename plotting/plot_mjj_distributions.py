import matplotlib.pyplot as plt
import ROOT
import os
from modules.logger_setup import logger
import mplhep as hep
import uproot

# one mass point for each model
SAMPLES = [
    "DMsimp_mmed1000",
    "HAHM_mmed1000",
    "excited_quark_mmed1000",
]
PLOT_FMT = [
    {"color": "C0", "linestyle": "-", "label": "Axial-vector $Z'$"},
    {"color": "C1", "linestyle": ":", "label": "Dark photon $Z_D$"},
    {"color": "C2", "linestyle": "--", "label": r"Excited quark $q^{\ast}$"},
]
MARKER_FMT = [
    {"marker": "o"},
    {"marker": "s", "fillstyle": "none"},
    {"marker": "^"},
]

SIGNAL_REGION = "J100"
ANALYSIS_NAME = "run2_atlas_tla_dijet"

# os.system(f"python modules/process_sample.py -s {' '.join(SAMPLES)} -a {ANALYSIS_NAME} --file-prefix MJJ_PLOT -o outputs")

# load the histograms from the output files and normalise them
# then store in one file for plotting
output_file = "outputs/signal_mjj_histogram_comparison.root"
logger.info(f"writing normalised histograms to {output_file}")
with ROOT.TFile.Open(output_file, "RECREATE") as f_out:
    for sample in SAMPLES:
        with ROOT.TFile.Open(f"outputs/MJJ_PLOT_histograms_{sample}_{ANALYSIS_NAME}.root") as f_in:
            h = f_in.Get(f"{SIGNAL_REGION}/h_mjj").Clone(f"{SIGNAL_REGION}_{sample}_mjj")
            h.Rebin(20) # rebin to reduce statistical fluctuations
            if h.Integral() > 0:
                h.Scale(1.0 / h.Integral())
            h.SetDirectory(0) # dissociate from the input file
            h.SetDirectory(f_out) # set to output file
            f_out.cd() # force to output file
            h.Write() # write to output file
    
hep.style.use("ATLAS")
fig, ax = plt.subplots(figsize=(15, 10))
ax.set_xlabel(r"$m_{\mathrm{jj}}$ [GeV]", fontsize=32)
ax.set_ylabel("Normalised entries", fontsize=32)
ax.tick_params(axis='both', which='both', labelsize=32, pad=10)

with uproot.open(output_file) as f:
    for sample in SAMPLES:
        h = f[f"{SIGNAL_REGION}_{sample}_mjj"].to_boost()
        hep.histplot(
            h, 
            ax=ax,
            lw=3,
            flow=None,
            **{k: v for k, v in PLOT_FMT[SAMPLES.index(sample)].items() if k != 'label'}
        )
        hep.histplot(
            h, 
            ax=ax,
            flow=None,
            histtype="errorbar",
            color=PLOT_FMT[SAMPLES.index(sample)]["color"],
            markersize=10,
            markeredgewidth=3,
            linestyle="none",
            **MARKER_FMT[SAMPLES.index(sample)],
        )

ax.legend(
    handles=[
        plt.Line2D(
            [], [], 
            lw=8,
            **PLOT_FMT[idx]
        ) for idx in range(len(SAMPLES))
    ],
    fontsize=32,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.97),
    title="Signal model:",
    title_fontsize=32,
    labelspacing=0.5,
    ncol=3,
    columnspacing=0.75,
    handletextpad=0.5,
)
ax.set_xlim(481, 1400)
ax.yaxis.get_offset_text().set_fontsize(30)

ax.text(
    0.03, 0.97,
    r"$\sqrt{s} = 8$-$13$ TeV",
    transform=ax.transAxes,
    fontsize=32,
    va="top",
    ha="left",
)

logger.info("Saving plot to outputs/signal_mjj_histogram_comparison.pdf")
plt.savefig("outputs/signal_mjj_histogram_comparison.pdf", bbox_inches="tight")