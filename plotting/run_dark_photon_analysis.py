"""

This script computes the acceptance vs. mass profile
for dark photon HAHM v5 signal samples used for
a reinterpretation of the ATLAS Run 2 dijet TLA

"""
from modules.logger_setup import logger
import os
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import json
import multiprocessing as mp

# set ATLAS formatting for plots
hep.style.use(hep.style.ATLAS)

analysis_name = "run2_atlas_tla_dijet"

signal_regions = [
    "J50",
    "J100",
]

samples_to_check = [
    f"HAHM_mmed{mass}"
    for mass in [375, 400, 425, 450, 475, 500, 525, 550, 575, 600,
    650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150,
    1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650,
    1700, 1750, 1800]
]
sample_masses = [
    375, 400, 425, 450, 475, 500, 525, 550, 575, 600,
    650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150,
    1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650,
    1700, 1750, 1800
]

def mp_target(sample_list:list, analysis:str):
    job_command = "python modules/process_sample.py -s {samples} -a {analyses} -o outputs -w 1 --file-prefix SIGNAL_ACC_PLOT > /dev/null 2>&1"
    os.system(
        job_command.format(
            samples=" ".join(sample_list),
            analyses=analysis,
        )
    )
    return 0

# process the samples for each analysis
results = list()
with mp.Pool(processes=16) as pool:
    for sample in samples_to_check:
        logger.info("launching process for sample %s", sample)
        results.append(pool.apply_async(
            mp_target,
            args=(
                [sample],
                analysis_name
            )
        ))
    results = [res.get() for res in results]

# now read back the acceptances and compare to published values
acceptance_files = "outputs/SIGNAL_ACC_PLOT_acceptances_{sample}_{analysis}.json"

# make a plot for each analysis
acceptances = []
acceptance_data = dict()
acc = float()
sr_handles = list()
sr_labels = list()
acceptances = []

# load the acceptance data for this analysis
# saved by modules/process_sample.py jobs
acceptance_data = dict()
for sample in samples_to_check:
    with open(
        acceptance_files.format(
            sample=sample,
            analysis=analysis_name,
        ),
        'r'
    ) as f:
        acceptance_data[sample] = json.load(f)

# plot the acceptance vs. mass for each signal region
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_ylabel("Acceptance", fontsize=28)
ax.set_xlabel(r"$m_{Z_D}$ [GeV]", fontsize=28)
ax.set_xlim(sample_masses[0]-50, sample_masses[-1]+50)
ax.set_ylim(0, 0.4)
ax.text(
    0.03, 0.97,
    r"$\sqrt{s} = 13$ TeV, Delphes ATLAS simulation" + "\n" + r"$Z_D \rightarrow q\bar{q}$ events, $q = u,\ d,\ s,\ c$",
    ha='left', va='top', transform=ax.transAxes, fontsize=28
)

# increase tick label sizes
ax.tick_params(axis='both', which='both', labelsize=28, pad=7)

# loop over signal regions and plot
for sr, fmt in zip(signal_regions, [{"color": "C0", "marker": "o", "linestyle": "-"}, {"color": "C1", "marker": "s", "linestyle": "--"}, {"color": "C2", "marker": "^", "linestyle": "-."}, {"color": "C3", "marker": "D", "linestyle": ":"}]):
    acceptances = [
        acceptance_data[sample][sr]["acceptance"]
        for sample in samples_to_check
    ]
    ax.plot(
        sample_masses,
        acceptances,
        markersize=10,
        lw=2.5,
        **fmt
    )
    
    sr_handles.append(
        plt.Line2D([0], [0], markersize=15, lw=5, **fmt)
    )
    sr_labels.append(sr + " region")

ax.legend(
    handles=sr_handles,
    labels=sr_labels,
    loc="lower right", 
    fontsize=28,
)

logger.info(f"Saving acceptance comparison plot for {analysis_name} to outputs/hahm_v5_acceptance_{analysis_name}.pdf")
plt.savefig(f"outputs/hahm_v5_acceptance_{analysis_name}.pdf")
plt.close(fig)