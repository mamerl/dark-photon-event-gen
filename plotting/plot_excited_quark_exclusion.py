import mplhep as hep
import numpy as np
import json
import matplotlib.pyplot as plt
from data.samples import samples
from modules.logger_setup import logger
import os

hep.style.use("ATLAS")

sample_list = [
    f"excited_quark_mmed{mass}" 
    for mass in [
        1000, 2000, 3000, 4000, 5000
    ]
]

# digitised with https://pdfdigitiser.app.cern.ch/
# since the limits are not available in HEPData
run1_limits = {
    "mass": [1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3250, 3500, 3750, 4000, 4250, 4500, 4750, 5000, 5250, 5500],
    "limit": [
        0.36094515458896503, 
        0.18311859879537784, 
        0.14974653741377292, 
        0.13741974966569967, 
        0.05539183750097011, 
        0.04125851571249388,
        0.021773094548268868,
        0.014257287391492943,
        0.007103461699659337,
        0.004836549643559437,
        0.003265201568850627,
        0.0022702350412257483,
        0.0019959416951278227,
        0.0016308624682055616,
        0.0013498231225256975,
        0.0011091107822347641,
        0.0010130011270964732,
        0.0011429546327802011,
        0.0016737649058480772
    ],
    # remaining information is from HEPData entry for excited quark search
    # https://doi.org/10.17182/hepdata.66572.v1/t3

    # xec in nb
    "xsec": [
        0.27, 0.077, 0.026, 0.0093, 0.0036, 0.0015, 0.00061, 
        0.00026, 0.00011, 4.8e-05, 2.1e-05, 9.3e-06, 4.0e-06,
        1.8e-06, 8.1e-07, 3.7e-07, 1.8e-07, 9.5e-08, 5.4e-08
    ],
    "br": [
        0.83, 0.83, 0.83, 0.83, 0.82, 0.82, 0.82, 0.81, 0.81,
        0.81, 0.81, 0.8, 0.8, 0.8, 0.8, 0.8, 0.82, 0.82, 0.82
    ],
    "acceptance": [
        0.59, 0.59, 0.59, 0.59, 0.59, 0.58, 0.58, 0.58, 0.58, 
        0.58, 0.58, 0.58, 0.58, 0.58, 0.57, 0.59, 0.58, 0.59, 0.59,
    ]
}
for k in run1_limits:
    run1_limits[k] = np.array(run1_limits[k])
# calculate the strength limits
# do this also by converting the xsec from nb to pb
# first for the Run 1 limits (multiply the xsec by 1000 to convert from nb to pb 
# and also include branching ratio and acceptance)
run1_limits["strength"] = run1_limits["limit"] / (run1_limits["xsec"] * 1000 * run1_limits["br"] * run1_limits["acceptance"])

# # run the reinterpretation for these samples
# os.system(f"python modules/process_sample.py -s {' '.join(sample_list)} -o outputs/ -w 4 -r -a run1_atlas_8tev_dijet")

limit_curve = {
    "masses": [], "limits": [], "strengths": [], "theory_xsec": [], "theory_xsec_truncated": []
}

acceptance_data = dict()
for sample in sample_list:
    with open(f"outputs/acceptances_{sample}_run1_atlas_8tev_dijet.json", "r") as f:
        acceptance_data = json.load(f)
    try:
        # the theory_expected_xsec is the product of the theory cross-section and the 
        # analysis acceptance excluding the truncation 
        theory_expected_xsec = acceptance_data["SR"]["expected_xsec_pb"]
        # the theory_expected_xsec_truncated is the product of the theory cross-section and the
        # analysis acceptance including the truncation
        theory_expected_xsec_truncated = acceptance_data["SR"]["modified_expected_xsec_pb"]
        excluded_xsec = acceptance_data["SR"]["excluded_xsec_pb"]
    except KeyError:
        continue
    limit_curve["masses"].append(samples[sample]["mass"])
    limit_curve["limits"].append(
        excluded_xsec
    )
    limit_curve["theory_xsec"].append(
        theory_expected_xsec
    )
    limit_curve["theory_xsec_truncated"].append(
        theory_expected_xsec_truncated
    )

# for each signal region sort the limit curve by mass
masses = np.array(limit_curve["masses"])
reinterpreted_limits = np.array(limit_curve["limits"])
theory_xsec = np.array(limit_curve["theory_xsec"])
theory_xsec_truncated = np.array(limit_curve["theory_xsec_truncated"])
# sort by mass
sorted_indices = np.argsort(masses)
masses = masses[sorted_indices]
reinterpreted_limits = reinterpreted_limits[sorted_indices]
theory_xsec = theory_xsec[sorted_indices]
theory_xsec_truncated = theory_xsec_truncated[sorted_indices]
# mask out any nan values
mask = ~np.isnan(reinterpreted_limits)
masses = masses[mask]
reinterpreted_limits = reinterpreted_limits[mask]
theory_xsec = theory_xsec[mask]
theory_xsec_truncated = theory_xsec_truncated[mask]
# define a mask for the run1 masses to only include those present in the reinterpretation
run1_masses_mask = np.full_like(run1_limits["mass"], False, dtype=bool)
for mass in masses:
    run1_masses_mask |= np.array(run1_limits["mass"]) == mass

# calculate the strength limits for the reinterpretation
# no extra factors for BR, etc. needed here since they are applied upstream
# in modules/process_sample.py
reinterpreted_strengths = reinterpreted_limits / np.array(theory_xsec)
reinterpreted_strengths_truncated = reinterpreted_limits / np.array(theory_xsec_truncated)

######################################################
#### Plot the reinterpreted observed cross-section 
#### limits compared to published Run 1 limits
######################################################
fig, ax = plt.subplots(2,1, figsize=(10,8), sharex=True, height_ratios=[3,1])
ax[1].set_xlabel(r"$m_{q^{\ast}}$ [GeV]", fontsize=28)
ax[0].set_ylabel(r"$\sigma \times A \times BR$ [pb]", fontsize=28)
ax[0].set_title(r"$pp \rightarrow q^{\ast} \rightarrow qg$ exclusion limits", fontsize=28)
ax[1].set_ylabel("Ratio", fontsize=28)
plt.subplots_adjust(hspace=0.04)

handles = []
ax[0].plot(
    masses,
    reinterpreted_limits,
    marker="o",
    ls="--",
    markersize=10,
    color="C0",
    lw=2.5,
)

ax[0].plot(
    run1_limits["mass"],
    run1_limits["limit"],
    marker="s",
    fillstyle="none",
    ls="-",
    color="C1",
    markersize=10,
    lw=2.5,
)

# calculate the difference between the published and reinterpretation limits
# at each mass point in the reinterpretation
ratio = reinterpreted_limits / np.array(run1_limits["limit"])[run1_masses_mask]
ratio[np.isinf(ratio)] = np.nan

ax[1].plot(
    masses,
    ratio,
    marker="o",
    markersize=10,
    ls="--",
    color="k"
)

handles += [
    plt.Line2D([], [], marker="s", markersize=15, lw=3, fillstyle="none", color="C1", ls="-", label="Published"),
    plt.Line2D([], [], marker="o", markersize=15, lw=3, color="C0", ls="--", label="Reinterpretation")
]
ax[0].legend(handles=handles, loc="upper right", fontsize=28, labelspacing=0.5)
ax[1].set_ylim(0.6, 1.25)
ax[0].set_ylim(5e-4, 10)
ax[0].set_yscale("log")
ax[0].set_xlim(950, 5300)
ax[1].axhline(1, color="black", ls=":", lw=1)
# ax[1].axhline(0.8, color="red", ls=":", lw=1.5)
# ax[1].axhline(1.2, color="red", ls=":", lw=1.5)
ax[1].tick_params(axis='both', which='both', labelsize=28, pad=10)
ax[0].tick_params(axis='both', which='both', labelsize=28, pad=10)

logger.info("Saving excited quark cross-section exclusion limit plot to outputs/excited_quark_xsec_exclusion_limits.pdf")
plt.savefig("outputs/excited_quark_xsec_exclusion_limits.pdf")


######################################################
#### Plot the reinterpreted observed signal strength
#### limits compared to published Run 1 limits
######################################################
fig, ax = plt.subplots(2,1, figsize=(10,10), sharex=True, height_ratios=[3,1])
ax[1].set_xlabel(r"$m_{q^{\ast}}$ [GeV]", fontsize=28)
ax[0].set_ylabel(r"$\mu = \sigma_{\mathrm{obs.}} / (\sigma_{\mathrm{th.}} \times A \times BR)$", fontsize=28)
ax[0].set_title(r"$pp \rightarrow q^{\ast} \rightarrow qg$ exclusion limits", fontsize=28)
ax[1].set_ylabel("Ratio", fontsize=28)
plt.subplots_adjust(hspace=0.1)

handles = []
ax[0].plot(
    masses,
    reinterpreted_strengths,
    marker="o",
    ls="--",
    markersize=10,
    color="C0",
    lw=2.5,
)
ax[0].plot(
    masses,
    reinterpreted_strengths_truncated,
    marker="^",
    ls=":",
    markersize=10,
    color="C1",
    lw=2.5,
)

ax[0].plot(
    run1_limits["mass"],
    run1_limits["strength"],
    marker="s",
    fillstyle="none",
    ls="-",
    color="C2",
    markersize=10,
    lw=2.5,
)

# calculate the difference between the published and reinterpretation limits
# at each mass point in the reinterpretation
ratio = reinterpreted_strengths / np.array(run1_limits["strength"])[run1_masses_mask]
ratio_truncated = reinterpreted_strengths_truncated / np.array(run1_limits["strength"])[run1_masses_mask]
ratio[np.isinf(ratio)] = np.nan
ratio_truncated[np.isinf(ratio_truncated)] = np.nan

ax[1].plot(
    masses,
    ratio,
    marker="o",
    markersize=10,
    ls="--",
    color="C0",
    lw=2.5,
)
ax[1].plot(
    masses,
    ratio_truncated,
    marker="^",
    markersize=10,
    ls=":",
    color="C1",
    lw=2.5,
)

handles += [
    plt.Line2D([], [], marker="s", markersize=15, lw=3, fillstyle="none", color="C2", ls="-", label="Published"),
    plt.Line2D([], [], marker="o", markersize=15, lw=3, color="C0", ls="--", label="Reinterpretation"),
    plt.Line2D([], [], marker="^", markersize=15, lw=3, color="C1", ls=":", label="Reinterpretation\n(truncated)"),

]
ax[0].legend(handles=handles, loc="upper left", fontsize=28, labelspacing=0.5)
ax[1].set_ylim(0, 2)
ax[0].set_yscale("log")
ax[0].set_ylim(top=1e4)
ax[0].set_xlim(950, 5300)
# ax[1].axhline(1, color="black", ls=":", lw=1)
ax[1].tick_params(axis='both', which='both', labelsize=28, pad=10)
ax[0].tick_params(axis='both', which='both', labelsize=28, pad=10)

logger.info("Saving excited quark cross-section exclusion limit plot to outputs/excited_quark_mu_exclusion_limits_logy.pdf")
plt.savefig("outputs/excited_quark_mu_exclusion_limits_logy.pdf")
ax[0].set_yscale("linear")
ax[1].set_ylim(0, 2)
ax[0].set_ylim(0, 3)
logger.info("Saving excited quark cross-section exclusion limit plot to outputs/excited_quark_mu_exclusion_limits.pdf")
plt.savefig("outputs/excited_quark_mu_exclusion_limits.pdf")