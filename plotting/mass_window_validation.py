from math import ceil, floor
import ROOT
import mplhep as hep
import uproot
import boost_histogram as bh
import matplotlib.pyplot as plt
from modules.logger_setup import logger
from data.samples import samples
from matplotlib.backends.backend_pdf import PdfPages

hep.style.use("ATLAS")

signal_regions = ["J50", "J100"]
sample_list = [
    "DMsimp_mmed350",
    "DMsimp_mmed600",
    "DMsimp_mmed1000",
    "DMsimp_mmed2000",
]

mjj_hist = None
with PdfPages("outputs/mass_window_validation_plots.pdf") as pdf:
    for signal_region in signal_regions:
        for sample in sample_list:
            logger.info("========================================"*2)
            logger.info(f"Processing sample {sample}, signal region {signal_region}")
            fig, ax = plt.subplots(figsize=(8,6))

            ax.set_xlabel("$m_{\mathrm{jj}}$ [GeV]")
            ax.set_ylabel("Events")
            ax.set_title(fr"SR {signal_region}, $Z'\rightarrow q\bar{{q}}$ $m_{{Z'}}={samples[sample]['mass']}$ GeV")

            mass_window = [
                ceil(samples[sample]['mass']*0.8),
                floor(samples[sample]['mass']*1.2)
            ]
            
            # retrieve histograms from the output ROOT files
            # and rebin
            with uproot.open(f"outputs/histograms_{sample}_run2_atlas_tla_dijet.root") as f:
                mjj_hist = f[f"{signal_region}/h_mjj"].to_boost()
                mjj_hist = mjj_hist[::bh.rebin(10)]

            # calculate FW60M mass window
            fw60m_low = float()
            fw60m_high = float()
            with ROOT.TFile.Open(f"outputs/histograms_{sample}_run2_atlas_tla_dijet.root", "READ") as f_root:
                h_mjj = f_root.Get(f"{signal_region}/h_mjj")
                h_mjj.Rebin(10) # rebinned to 10 GeV bins for smoother distribution
                # get the bin centre with the largest value
                max_bin = h_mjj.GetMaximumBin()
                max_bin_center = h_mjj.GetBinCenter(max_bin)
                dynamic_mass_window = [
                    ceil(max_bin_center * 0.8),
                    floor(max_bin_center * 1.2)
                ]
                avg_mass = h_mjj.GetMean()
                fw60m_low = h_mjj.GetBinLowEdge(h_mjj.FindFirstBinAbove(h_mjj.GetMaximum() * 0.6))
                fw60m_high = h_mjj.GetBinLowEdge(h_mjj.FindLastBinAbove(h_mjj.GetMaximum() * 0.6)+1)
                fw14m_low = h_mjj.GetBinLowEdge(h_mjj.FindFirstBinAbove(h_mjj.GetMaximum() * 0.14))
                fw14m_high = h_mjj.GetBinLowEdge(h_mjj.FindLastBinAbove(h_mjj.GetMaximum() * 0.14)+1)
                logger.info(f"\tFW60M mass window: [{fw60m_low}, {fw60m_high}] GeV")
                logger.info(f"\tFW14M mass window: [{fw14m_low}, {fw14m_high}] GeV")
                logger.info(f"\tRecommended mass window: [{mass_window[0]}, {mass_window[1]}] GeV")
                logger.info(f"\tDynamic mass window (from max bin {max_bin_center} GeV): [{dynamic_mass_window[0]}, {dynamic_mass_window[1]}] GeV")

                # define mass window
                h_mjj.GetXaxis().SetRangeUser(fw14m_low, fw14m_high)
                # calculate avg mass in FW14M window
                mass_in_window = h_mjj.GetMean()
                logger.info(f"\tAverage mass in FW14M window: {mass_in_window} GeV")
                logger.info(f"\tTrue average mass: {avg_mass} GeV")

                # recommended mass window
                h_mjj.GetXaxis().SetRangeUser(mass_window[0], mass_window[1])
                mass_in_recommended_window = h_mjj.GetMean()
                logger.info(f"\tAverage mass in recommended window: {mass_in_recommended_window} GeV")

                h_mjj.GetXaxis().SetRangeUser(dynamic_mass_window[0], dynamic_mass_window[1])
                mass_in_dynamic_window = h_mjj.GetMean()
                logger.info(f"\tAverage mass in dynamic window: {mass_in_dynamic_window} GeV")

                # calculate width/mass ratio
                width = (fw60m_high - fw60m_low)/2
                width_mass_ratio = width / mass_in_window * 100.0 if mass_in_window > 0 else 0.0

                recom_width = (mass_window[1] - mass_window[0])/5
                recom_width_mass_ratio = recom_width / mass_in_recommended_window * 100.0 if mass_in_recommended_window > 0 else 0.0

                dynamic_width = (dynamic_mass_window[1] - dynamic_mass_window[0])/5
                dynamic_width_mass_ratio = dynamic_width / mass_in_dynamic_window * 100.0 if mass_in_dynamic_window > 0 else 0.0
                logger.info(f"\tWidth/mass ratio in FW60M window: {width_mass_ratio:.2f} %")
                logger.info(f"\tWidth/mass ratio in recommended window: {recom_width_mass_ratio:.2f} %")
                logger.info(f"\tWidth/mass ratio in dynamic window: {dynamic_width_mass_ratio:.2f} %")

                # determine coverage of the windows
                recom_window_covg = 4 * recom_width / (mass_window[1] - mass_window[0])
                fw60m_window_covg = 4 * width / (fw14m_high - fw14m_low)
                dynamic_window_covg = 4 * dynamic_width / (dynamic_mass_window[1] - dynamic_mass_window[0])
                logger.info(f"\tCoverage of recommended window: {recom_window_covg}")
                logger.info(f"\tCoverage of FW14M window: {fw60m_window_covg}")
                logger.info(f"\tCoverage of dynamic window: {dynamic_window_covg}")

            # plot the histograms
            hep.histplot(
                mjj_hist,
                ax=ax,
                histtype="step",
                flow=None,
                color="C0",
                lw=2
            )

            ax.set_xlim(
                min(samples[sample]['mass']*0.5, mass_window[0]),
                max(samples[sample]['mass']*1.5, mass_window[1]),
            )

            # annotate
            x1 = (mass_window[0] - ax.get_xlim()[0]) / (ax.get_xlim()[1] - ax.get_xlim()[0])
            x2 = (mass_window[1] - ax.get_xlim()[0]) / (ax.get_xlim()[1] - ax.get_xlim()[0])
            ax.axvline(
                mass_window[0],
                color="C1",
                linestyle="-",
                lw=2,
                label=r"$(0.8, 1.2) \times m_{Z'}$",
            )
            ax.axvline(
                mass_window[1],
                color="C1",
                linestyle="-",
                lw=2,
            )
            ax.axvline(
                mass_in_recommended_window,
                color="C1",
                linestyle=":",
                lw=2,
            )


            ax.axvline(
                fw14m_low,
                color="C3",
                linestyle="--",
                lw=2,
                label="FW-14%-M",
            )
            ax.axvline(
                fw14m_high,
                color="C3",
                linestyle="--",
                lw=2,
            )
            ax.axvline(
                mass_in_window,
                color="C3",
                linestyle=":",
                lw=2,
            )

            ax.axvline(
                dynamic_mass_window[0],
                color="C2",
                linestyle="-.",
                lw=2,
                label=r"$(0.8, 1.2) \times$ max.",
            )
            ax.axvline(
                dynamic_mass_window[1],
                color="C2",
                linestyle="-.",
                lw=2,
            )
            ax.axvline(
                mass_in_dynamic_window,
                color="C2",
                linestyle=":",
                lw=2,
            )
            
            handles, labels = ax.get_legend_handles_labels()
            handles.append(
                plt.Line2D([], [], linestyle=":", color="k", lw=2)
            )
            labels.append("Mean mass in window")
            

            ax.legend(
                handles,
                labels,
                loc="upper left",
                fontsize=20,
                bbox_to_anchor=(0.97, 1),
            )

            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)