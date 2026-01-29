import mplhep as hep
import numpy as np
import json
import boost_histogram as bh
import matplotlib.pyplot as plt
from data.samples import samples

hep.style.use("ATLAS")

# this is the quark coupling used to generate
# the DMsimp samples for these studies
GQ_REFERENCE = 0.1

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

signal_regions = ["J50", "J100"]
sample_list = [
    f"DMsimp_mmed{mass}" 
    for mass in [
        375, 400, 450, 500, 550, 600, 700, 800, 900, 1000,
        1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800
    ]
]

limit_curve = {
    sr: {"masses": [], "limits": []}
    for sr in signal_regions
}

acceptance_data = dict()
for sample in sample_list:
    for signal_region in signal_regions:
        with open(f"outputs/acceptances_{sample}_run2_atlas_tla_dijet.json", "r") as f:
            acceptance_data = json.load(f)
        try:
            theory_expected_xsec = acceptance_data[signal_region]["modified_expected_xsec_pb"]
            excluded_xsec = acceptance_data[signal_region]["excluded_xsec_pb"]
        except KeyError:
            continue
        limit_curve[signal_region]["masses"].append(samples[sample]["mass"])
        limit_curve[signal_region]["limits"].append(
            # 1.25 is to convert to limit for udscb decays from udsc only
            np.sqrt(excluded_xsec / (theory_expected_xsec * 1.25)) * GQ_REFERENCE
        )

fig, ax = plt.subplots(2,1, figsize=(8,6), sharex=True, height_ratios=[3,1])
ax[1].set_xlabel(r"$m_{Z'}$ [GeV]")
ax[0].set_ylabel(r"$g_q$")
ax[0].set_title(r"DMsimp $Z' \rightarrow q\bar{q}$ exclusion limits")
ax[1].set_ylabel("Ratio")

handles = []
for signal_region, color in zip(signal_regions, ["C0", "C1", "C2", "C3"]):
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
    # if signal_region == "J50":
    #     mask = masses <= 600
    #     masses = masses[mask]
    #     limits = limits[mask]
    ax[0].plot(
        masses,
        limits,
        # marker="o",
        ls="--",
        # markersize=10,
        # label=f"SR {signal_region}",
        color=color
    )

    ax[0].plot(
        run2_limits[signal_region]["mass"],
        run2_limits[signal_region]["limit"],
        ls="-",
        color=color,
        lw=2.5,
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
        color=color
    )

    handles.append(
        plt.Line2D([], [], color=color, ls="-", lw=10, label=f"SR {signal_region}"),
    )

handles += [
    plt.Line2D([], [], color="black", ls="-", label="Published"),
    plt.Line2D([], [], color="black", ls="--", label="Reinterpretation")
]
ax[0].legend(handles=handles, loc="upper left", fontsize=24)
ax[0].set_ylim(top=0.4)
ax[1].set_ylim(0, 2.5)
ax[1].axhline(1, color="black", ls=":", lw=1)

plt.savefig("outputs/dmsimp_exclusion_limits.pdf")


