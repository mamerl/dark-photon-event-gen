"""

This script checks the acceptance of excited quark signals for 
the analyses configured in analyses.

Doing this ensures that the analysis selections configured
in each analysis module are correct, by comparing the 
acceptances obtained here to those published in the
auxiliary material of the relevant analysis paper.

"""
from modules.logger_setup import logger
import os
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import json

# set ATLAS formatting for plots
hep.style.use(hep.style.ATLAS)

analysis_name = "run1_atlas_8tev_dijet"

samples_to_check = [
    "excited_quark_mmed1000",
    "excited_quark_mmed2000",
    "excited_quark_mmed3000",
    "excited_quark_mmed4000",
    "excited_quark_mmed5000",
]
sample_masses = [
    1000,
    2000,
    3000,
    4000,
    5000,
]

# process the samples for each analysis
job_command = "python modules/process_sample.py -s {samples} -a {analyses} -o outputs -w 8"
logger.info(f"Running job command: {job_command.format(samples=' '.join(samples_to_check), analyses=analysis_name)}")
os.system(
    job_command.format(
        samples=" ".join(samples_to_check),
        analyses=analysis_name,
    )
)

# HEPData acceptance values for comparison
hepdata_acceptances = {
    "run1_atlas_8tev_dijet": {
        "SR": {
            "excited_quark_mmed1000": 0.59,
            "excited_quark_mmed2000": 0.59,
            "excited_quark_mmed3000": 0.58,
            "excited_quark_mmed4000": 0.58,
            "excited_quark_mmed5000": 0.58,
        },
    }
}

# now read back the acceptances and compare to published values
acceptance_files = "outputs/acceptances_{sample}_{analysis}.json"

# make a plot for each analysis
acceptances = []
acceptance_data = dict()
acc = float()
sr_handles = list()
sr_labels = list()
acceptances = []

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


fig, ax = plt.subplots(2,1, figsize=(12, 8), sharex=True, height_ratios=[2,1])
plt.subplots_adjust(hspace=0.15)
ax[0].set_ylabel("Acceptance", fontsize=28)
ax[1].set_ylabel("Difference", fontsize=28)
ax[1].set_xlabel("$m_{\mathrm{jj}}$ [GeV]", fontsize=28)
ax[1].set_xlim(sample_masses[0]-50, sample_masses[-1]+50)
ax[0].set_ylim(0, 0.85)
ax[0].text(
    0.03, 0.97,
    r"$\sqrt{s} = 8$ TeV, Delphes ATLAS simulation" + "\n" + r"$q^{\ast} \rightarrow qg$ events",
    ha='left', va='top', transform=ax[0].transAxes, fontsize=28
)
ax[0].text(
    0.01, 1.01,
    "HEPData source: https://doi.org/10.17182/hepdata.66572.v1/t3",
    ha='left', va='bottom', transform=ax[0].transAxes, fontsize=20
)

# increase tick label sizes
for a in ax:
    a.tick_params(axis='both', which='major', labelsize=28, pad=10)

ax[1].axhline(0, color='k', lw=1, linestyle='--')

for sr, c in zip(list(hepdata_acceptances[analysis_name].keys()), ["C0", "C1", "C2", "C3"]):
    acceptances = [
        acceptance_data[sample][sr]["acceptance"]
        for sample in samples_to_check
    ]
    analysis_acceptances = [
        hepdata_acceptances[analysis_name][sr][sample]
        for sample in samples_to_check
    ]

    ax[0].plot(
        sample_masses,
        acceptances,
        marker='o',
        linestyle="-",
        color=c,
        markersize=10,
        lw=2,
    )
    ax[0].plot(
        sample_masses,
        analysis_acceptances,
        marker='s',
        fillstyle='none',
        linestyle="--",
        color=c,
        markersize=10,
        lw=2,
    )

    ax[1].plot(
        sample_masses,
        np.array(acceptances) - np.array(analysis_acceptances),
        marker='o',
        linestyle='-',
        color=c,
        lw=2,
        markersize=10,
    )

ax[0].legend(
    handles=[
        plt.Line2D([0], [0], marker='o', color='C0', markersize=15, lw=5, linestyle='-'),
        plt.Line2D([0], [0], marker='s', color='C0', markersize=15, lw=5, fillstyle='none', linestyle='--'),
    ],
    labels=["Computed", "HEPData"],
    loc="lower right", fontsize=28,
)
ax[1].yaxis.get_offset_text().set_fontsize(24)

logger.info(f"Saving acceptance comparison plot for {analysis_name} to outputs/acceptance_comparison_{analysis_name}.pdf")
plt.savefig(f"outputs/acceptance_comparison_{analysis_name}.pdf")
plt.close(fig)

