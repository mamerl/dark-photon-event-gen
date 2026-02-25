"""

This script runs the reinterpretation and plots the reinterpreted
exclusion limits for the dark photon HAHM.

Currently, the ATLAS Run 2 dijet TLA is the only supported analysis
for HAHM reinterpretations.

For computing the limits we assume that the coupling of the dark
to quarks scales with the square of the kinetic mixing parameter
epsilon. Then the constraint on epsilon can be obtained from:

epsilon_limit = epsilon_reference * sqrt(limit_on_signal_strength)

where limit_on_signal_strength is the ratio of the observed
cross-section limit from a Gaussian reinterpretation to the 
expected theory cross-section for the HAHM signal samples.


"""

from modules.logger_setup import logger
import os
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import json
import multiprocessing as mp
from data.samples import samples


analysis_name = "run2_atlas_tla_dijet"

signal_regions = [
    "J50",
    "J100",
]

truncation_methods = [
    "default",
    "generic_15",
    "mode_15",
]
truncation_labels = [
    r"$[0.8, 1.2] \times m_{Z_D}$",
    r"$[0.85, 1.15] \times m_{Z_D}$",
    "Mode and\n" + r"$[0.85, 1.15] \times m_{Z_D}$",
]

EPSILON_REFERENCE = 0.01

samples_to_check = [
    f"HAHM_mmed{mass}"
    for mass in 
    [
        375, 400, 425, 450, 475, 500, 525, 550, 575, 
        600,
        650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150,
        1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650,
        1700, 1750, 1800
    ]
]

def mp_target(sample_list:list, analysis:str, truncation:str):
    job_command = "python modules/process_sample.py -s {samples} -a {analyses} -o outputs -w 1 -r -t {truncation} > /dev/null 2>&1"
    os.system(
        job_command.format(
            samples=" ".join(sample_list),
            analyses=analysis,
            truncation=truncation,
        )
    )
    return 0

# # process the samples for each analysis
# results = list()
# with mp.Pool(processes=16) as pool:
#     for truncation_method in truncation_methods:
#         for sample in samples_to_check:
#             logger.info("launching process for sample %s with truncation %s", sample, truncation_method)
#             results.append(pool.apply_async(
#                 mp_target,
#                 args=(
#                     [sample],
#                     analysis_name,
#                     truncation_method,
#                 )
#             ))
#     results = [res.get() for res in results]

# compute the limits for each signal region and truncation method
limit_curves = {
    truncation: {
        sr: {"masses": [], "limits": []}
        for sr in signal_regions
    }
    for truncation in truncation_methods
}

acceptance_data = dict()
theory_expected_xsec = float()
excluded_xsec = float()
for truncation_method in truncation_methods:
    for signal_region in signal_regions:
        for sample in samples_to_check:
            # reset variables
            theory_expected_xsec = float()
            excluded_xsec = float()

            # open acceptances file
            with open(f"outputs/acceptances_{sample}_{analysis_name}_{truncation_method}.json", "r") as f:
                acceptance_data = json.load(f)
            
            try:
                theory_expected_xsec = acceptance_data[signal_region]["modified_expected_xsec_pb"]
                excluded_xsec = acceptance_data[signal_region]["excluded_xsec_pb"]
            except KeyError as e:
                logger.warning(f"missing key {e} in acceptance data for sample {sample}, signal region {signal_region}, and truncation method {truncation_method}, skipping")
                continue
            
            if np.isnan(excluded_xsec) or np.isnan(theory_expected_xsec):
                logger.debug(f"nan value for excluded_xsec or theory_expected_xsec for sample {sample} and signal region {signal_region}, skipping")
                continue
            elif theory_expected_xsec == 0:
                logger.debug(f"theory expected xsec is zero for sample {sample} and signal region {signal_region}, skipping")
                continue

            limit_curves[truncation_method][signal_region]["masses"].append(samples[sample]["mass"])
            limit_curves[truncation_method][signal_region]["limits"].append(
                # square the result of the calculation to get 
                # a limit on epsilon^2 instead of epsilon
                (np.sqrt(excluded_xsec / theory_expected_xsec) * EPSILON_REFERENCE)**2
            )

        # sort the limit curve by mass
        sorted_indices = np.argsort(limit_curves[truncation_method][signal_region]["masses"])
        limit_curves[truncation_method][signal_region]["masses"] = np.array(limit_curves[truncation_method][signal_region]["masses"])[sorted_indices].tolist()
        limit_curves[truncation_method][signal_region]["limits"] = np.array(limit_curves[truncation_method][signal_region]["limits"])[sorted_indices].tolist()

# save the reinterpreted limits to a json file
# so that they can be used by other code
with open("outputs/hahm_v5_exclusion_limits.json", "w") as f:
    json.dump(limit_curves, f, indent=4)

# plot the results
hep.style.use("ATLAS")
fig, ax = plt.subplots(figsize=(15, 10))
ax.set_ylabel(r"$\epsilon^2$", fontsize=28)
ax.set_xlabel(r"$m_{Z_D}$ [GeV]", fontsize=28)
# ax.set_xlim(sample_masses[0]-50, sample_masses[-1]+50)
ax.set_xlim(350, 1825)
ax.text(
    0.03, 0.97,
    r"$\sqrt{s} = 13$ TeV, Delphes ATLAS simulation" + "\n" + r"$Z_D \rightarrow q\bar{q}$ events, $q = u,\ d,\ s,\ c$",
    ha='left', va='top', transform=ax.transAxes, fontsize=28
)
ax.tick_params(axis='both', which='both', labelsize=28, pad=10)

for truncation_method, fmt in zip(truncation_methods, [{"color": "C0", "linestyle": "-", "marker": "o"}, {"color": "C1", "linestyle": "--", "marker": "s"}, {"color": "C2", "linestyle": "-.", "marker": "^"}]):
    for signal_region in signal_regions:
        ax.plot(
            limit_curves[truncation_method][signal_region]["masses"],
            limit_curves[truncation_method][signal_region]["limits"],
            linewidth=2.5,
            markersize=10,
            **fmt
        )

# add legend
ax.legend(
    handles=[
        plt.Line2D([0], [0], markersize=10, linewidth=5, **fmt)
        for fmt in [{"color": "C0", "linestyle": "-", "marker": "o"}, {"color": "C1", "linestyle": "--", "marker": "s"}, {"color": "C2", "linestyle": "-.", "marker": "^"}]
    ],
    labels=truncation_labels,
    fontsize=28,
    title_fontproperties={"size": 28, "weight": "bold"},
    title="Truncation method:",
    loc="lower center",
    bbox_to_anchor=(0.5, 0.96),
    ncol=3,
    columnspacing=0.5,
    handlelength=2.5
)
logger.info("saving coupling limit plot to outputs/hahm_v5_eps_squared_exclusion_limits.pdf")
plt.savefig("outputs/hahm_v5_eps_squared_exclusion_limits.pdf", bbox_inches="tight")