import mplhep as hep
import numpy as np
import json
import boost_histogram as bh
import matplotlib.pyplot as plt
from data.samples import samples
import os
from modules.logger_setup import logger

USE_TRUNCATION = True
TRUNCATION_METHOD = "default"

hep.style.use("ATLAS")

# this is the quark coupling used to generate
# the DMsimp samples for these studies
GQ_REFERENCE = 0.1

# The limits below are coupling limits 
run2_limits = {
    "J50": {
        "mass": [375, 400, 425, 450, 475, 500, 525, 550, 575, 600],
        "limit": [0.0475, 0.053605, 0.070071, 0.0714, 0.069464, 0.071584, 0.078497, 0.076385, 0.073698, 0.077421],
    },
    "J100": {
        "mass": [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800],
        "limit":  [0.070669, 0.078217, 0.075438, 0.055203, 0.049024, 0.040118, 0.047253, 0.056033, 0.064963, 0.066217, 0.050991, 0.048699, 0.05483, 0.059274, 0.06931, 0.076097, 0.081922, 0.083092, 0.092393, 0.09817, 0.10621, 0.094697, 0.091868, 0.085656, 0.077461],
    }
}

# compute signal strengths for each SR
for sr in run2_limits:
    run2_limits[sr]["signal_strengths"] = (np.array(run2_limits[sr]["limit"]) / GQ_REFERENCE) ** 2

signal_regions = ["J50", "J100"]
sample_list = [
    f"DMsimp_mmed{mass}" 
    for mass in [
        375, 400, 450, 500, 550, 600, 700, 800, 900, 1000,
        1100, 1200, 
        1300, 1400, 1500, 1600, 1700, 1800
    ]
]

# # run the reinterpretation for these samples
# os.system(f"python modules/process_sample.py -s {' '.join(sample_list)} -o outputs/ -w 4 -r -t default -a run2_atlas_tla_dijet")

limit_curve = {
    sr: {"masses": [], "limits": [], "signal_strengths": []}
    for sr in signal_regions
}

acceptance_data = dict()
theory_expected_xsec = float()
excluded_xsec = float()
for sample in sample_list:
    for signal_region in signal_regions:
        # reset variables
        theory_expected_xsec = float()
        excluded_xsec = float()
        # open acceptances file
        with open(f"outputs/acceptances_{sample}_run2_atlas_tla_dijet_{TRUNCATION_METHOD}.json", "r") as f:
            acceptance_data = json.load(f)
        try:
            if USE_TRUNCATION:
                theory_expected_xsec = acceptance_data[signal_region]["modified_expected_xsec_pb"]
            else:
                theory_expected_xsec = acceptance_data[signal_region]["expected_xsec_pb"]
            excluded_xsec = acceptance_data[signal_region]["excluded_xsec_pb"]
        except KeyError as e:
            logger.warning(f"missing key {e} in acceptance data for sample {sample} and signal region {signal_region}, skipping")
            continue
        
        if np.isnan(excluded_xsec) or np.isnan(theory_expected_xsec):
            logger.warning(f"nan value for excluded_xsec or theory_expected_xsec for sample {sample} and signal region {signal_region}, skipping")
            continue
        elif theory_expected_xsec == 0:
            logger.warning(f"theory expected xsec is zero for sample {sample} and signal region {signal_region}, skipping")
            continue

        limit_curve[signal_region]["masses"].append(samples[sample]["mass"])
        limit_curve[signal_region]["limits"].append(
            # 1.25 is to convert to limit for udscb decays from udsc only
            np.sqrt(excluded_xsec / (theory_expected_xsec * 1.25)) * GQ_REFERENCE
        )
        limit_curve[signal_region]["signal_strengths"].append(
            excluded_xsec / (theory_expected_xsec * 1.25) # TODO check with Falk about whether the 1.25 factor was actually applied for the analysis
        )

################################################################
### Coupling limit plot 
fig, ax = plt.subplots(2,1, figsize=(10,8), sharex=True, height_ratios=[3,1])
plt.subplots_adjust(hspace=0.05)
ax[1].set_xlabel(r"$m_{Z'}$ [GeV]", fontsize=28)
ax[0].set_ylabel(r"$g_q$", fontsize=28)
ax[1].set_ylabel("Ratio", fontsize=28)

handles = []
for signal_region, color in zip(signal_regions, ["C0", "C1"]):
    # for each signal region sort the limit curve by mass
    masses = np.array(limit_curve[signal_region]["masses"])
    limits = np.array(limit_curve[signal_region]["limits"])
    sorted_indices = np.argsort(masses)
    masses = masses[sorted_indices]
    limits = limits[sorted_indices]
    # mask out any nan values
    mask = ~np.isnan(limits)
    masses = masses[mask]
    limits = limits[mask]
    ax[0].plot(
        masses,
        limits,
        marker="s",
        ls="--",
        markersize=10,
        fillstyle="none",
        # label=f"SR {signal_region}",
        color=color,
        lw=3,
    )

    ax[0].plot(
        run2_limits[signal_region]["mass"],
        run2_limits[signal_region]["limit"],
        ls="-",
        color=color,
        lw=3,
        marker="o",
        markersize=10,
    )

    # calculate the difference between the published and reinterpretation limits
    # at each mass point in the reinterpretation
    run2_masses_mask = np.full_like(run2_limits[signal_region]["mass"], False, dtype=bool)
    for mass in masses:
        run2_masses_mask |= np.array(run2_limits[signal_region]["mass"]) == mass
    ratio = limits / np.array(run2_limits[signal_region]["limit"])[run2_masses_mask]
    ratio[np.isinf(ratio)] = np.nan

    ax[1].plot(
        masses,
        ratio,
        ls="--",
        color=color,
        marker="s",
        markersize=10,
        fillstyle="none",
        lw=3,
    )

    handles.append(
        plt.Line2D([], [], color=color, ls="-", lw=10, label=signal_region),
    )

handles += [
    plt.Line2D([], [], color="black", ls="-", lw=5, marker="o", markersize=15, label="Published"),
    plt.Line2D([], [], color="black", ls="--", lw=5, marker="s", fillstyle="none", markersize=15, label="Reinterpretation")
]
ax[0].set_ylim(0.02, 0.4)
ax[1].set_ylim(0.8, 2.5)
ax[1].axhline(1, color="black", ls=":", lw=2)
ax[1].set_xlim(325, 1850)
ax[1].set_xticks([400, 600, 800, 1000, 1200, 1400, 1600, 1800])
ax[0].legend(
    handles=handles,
    handlelength=2.5, 
    loc="lower center", 
    fontsize=28, 
    labelspacing=0.5, 
    ncols=2,
    bbox_to_anchor=(0.5, 0.4)
)
ax[0].text(
    0.03, 0.97,
    r"$\sqrt{s} = 13$ TeV, 139 fb$^{-1}$" + "\n" + r"$Z' \rightarrow q\bar{q}$, $g_\chi = 1$, $m_\chi = 10$ TeV",
    transform=ax[0].transAxes,
    fontsize=28,
    va="top",
    ha="left",
)
for a in ax:
    a.tick_params(axis="both", which="major", labelsize=28, pad=10)

logger.info("saving coupling limit plot to outputs/dmsimp_gq_exclusion_limits.pdf")
plt.savefig("outputs/dmsimp_gq_exclusion_limits.pdf")

################################################################
### Cross-section limit plot

# TODO pending limits 

################################################################
### Signal strength plot
fig, ax = plt.subplots(2,1, figsize=(10,8), sharex=True, height_ratios=[3,1])
plt.subplots_adjust(hspace=0.05)
ax[1].set_xlabel(r"$m_{Z'}$ [GeV]", fontsize=28)
ax[0].set_ylabel(r"$\mu = \sigma_{\mathrm{obs.}} / (\sigma_{\mathrm{th.}} \times A \times BR)$", fontsize=28)
ax[1].set_ylabel("Ratio", fontsize=28)

handles = []
for signal_region, color in zip(signal_regions, ["C0", "C1"]):
    # for each signal region sort the limit curve by mass
    masses = np.array(limit_curve[signal_region]["masses"])
    limits = np.array(limit_curve[signal_region]["signal_strengths"])
    sorted_indices = np.argsort(masses)
    masses = masses[sorted_indices]
    limits = limits[sorted_indices]
    # mask out any nan values
    mask = ~np.isnan(limits)
    masses = masses[mask]
    limits = limits[mask]
    ax[0].plot(
        masses,
        limits,
        marker="s",
        ls="--",
        markersize=10,
        fillstyle="none",
        # label=f"SR {signal_region}",
        color=color,
        lw=3,
    )

    ax[0].plot(
        run2_limits[signal_region]["mass"],
        run2_limits[signal_region]["signal_strengths"],
        ls="-",
        color=color,
        lw=3,
        marker="o",
        markersize=10,
    )

    # calculate the difference between the published and reinterpretation limits
    # at each mass point in the reinterpretation
    run2_masses_mask = np.full_like(run2_limits[signal_region]["mass"], False, dtype=bool)
    for mass in masses:
        run2_masses_mask |= np.array(run2_limits[signal_region]["mass"]) == mass
    ratio = limits / np.array(run2_limits[signal_region]["signal_strengths"])[run2_masses_mask]
    ratio[np.isinf(ratio)] = np.nan

    ax[1].plot(
        masses,
        ratio,
        ls="--",
        color=color,
        marker="s",
        markersize=10,
        fillstyle="none",
        lw=3,
    )

    handles.append(
        plt.Line2D([], [], color=color, ls="-", lw=10, label=signal_region),
    )

handles += [
    plt.Line2D([], [], color="black", ls="-", lw=5, marker="o", markersize=15, label="Published"),
    plt.Line2D([], [], color="black", ls="--", lw=5, marker="s", fillstyle="none", markersize=15, label="Reinterpretation")
]
ax[0].set_ylim(0.0, 5)
ax[1].set_ylim(0, 6)
ax[1].axhline(1, color="black", ls=":", lw=2)
ax[1].set_xlim(325, 1850)
ax[1].set_xticks([400, 600, 800, 1000, 1200, 1400, 1600, 1800])
ax[0].legend(
    handles=handles,
    handlelength=2.5, 
    loc="lower center", 
    fontsize=28, 
    labelspacing=0.5, 
    ncols=2,
    bbox_to_anchor=(0.5, 0.4)
)
ax[0].text(
    0.03, 0.97,
    r"$\sqrt{s} = 13$ TeV, 139 fb$^{-1}$" + "\n" + r"$Z' \rightarrow q\bar{q}$, $g_\chi = 1$, $m_\chi = 10$ TeV",
    transform=ax[0].transAxes,
    fontsize=28,
    va="top",
    ha="left",
)
for a in ax:
    a.tick_params(axis="both", which="major", labelsize=28, pad=10)

logger.info("saving signal strength plot to outputs/dmsimp_mu_exclusion_limits.pdf")
plt.savefig("outputs/dmsimp_mu_exclusion_limits.pdf")