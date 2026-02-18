"""

This script checks the acceptance of DMsimp signals for 
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

analyses_to_run = [
    "run2_atlas_tla_dijet",
]

samples_to_check = [
    "DMsimp_mmed350",
    "DMsimp_mmed600",
    "DMsimp_mmed1000",
    "DMsimp_mmed2000",
]
sample_masses = [
    350,
    600,
    1000,
    2000,
]

# process the samples for each analysis
job_command = "python modules/process_sample.py -s {samples} -a {analyses} -o outputs -w 8"
logger.info(f"Running job command: {job_command.format(samples=' '.join(samples_to_check), analyses=' '.join(analyses_to_run))}")
os.system(
    job_command.format(
        samples=" ".join(samples_to_check),
        analyses=" ".join(analyses_to_run),
    )
)

# HEPData acceptance values for comparison
hepdata_acceptances = {
    "run2_atlas_tla_dijet": {
        "J50": {
            "DMsimp_mmed350": 0.071744,
            "DMsimp_mmed600": 0.22059,
            "DMsimp_mmed1000": 0.26404,
            "DMsimp_mmed2000": 0.32477,
        },
        "J100": {
            "DMsimp_mmed350": 0.0045687,
            "DMsimp_mmed600": 0.16642,
            "DMsimp_mmed1000": 0.25568,
            "DMsimp_mmed2000": 0.32337,
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
for analysis in analyses_to_run:
    acceptances = []

    acceptance_data = dict()
    for sample in samples_to_check:
        with open(
            acceptance_files.format(
                sample=sample,
                analysis=analysis,
            ),
            'r'
        ) as f:
            acceptance_data[sample] = json.load(f)

    
    fig, ax = plt.subplots(2,1, figsize=(10, 8), sharex=True, height_ratios=[2,1])
    ax[0].set_ylabel("Acceptance", fontsize=24)
    ax[1].set_ylabel("Difference", fontsize=24)
    ax[1].set_xlabel("$m_{Z'}$ [GeV]", fontsize=24)
    ax[1].set_xlim(sample_masses[0]-50, sample_masses[-1]+50)
    ax[0].set_ylim(0, 0.5)
    ax[0].text(
        0.03, 0.97,
        "Delphes ATLAS simulation" + "\n" + r"$Z' \rightarrow q\bar{q}$ events, $q = u,\ d,\ s,\ c$" + "\n" + r"$g_q = 0.1,\ g_\chi = 1,\ m_\chi = 10$ TeV",
        ha='left', va='top', transform=ax[0].transAxes, fontsize=24
    )
    ax[0].text(
        0.01, 1.01,
        "HEPData source: https://doi.org/10.17182/hepdata.161624.v1/t7",
        ha='left', va='bottom', transform=ax[0].transAxes, fontsize=15
    )

    # increase tick label sizes
    for a in ax:
        a.tick_params(axis='both', which='major', labelsize=24, pad=7)
    
    ax[1].axhline(0, color='k', lw=1, linestyle='--')

    for sr, c in zip(list(hepdata_acceptances[analysis].keys()), ["C0", "C1", "C2", "C3"]):
        acceptances = [
            acceptance_data[sample][sr]["acceptance"]
            for sample in samples_to_check
        ]
        analysis_acceptances = [
            hepdata_acceptances[analysis][sr][sample]
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
        sr_handles.append(plt.Line2D([0], [0], color=c, lw=4, linestyle='-'))
        sr_labels.append(sr + " region")
    
    ax[0].legend(
        handles=[
            plt.Line2D([0], [0], marker='o', color='k', markersize=10, lw=2, linestyle='-'),
            plt.Line2D([0], [0], marker='s', color='k', markersize=10, lw=2, fillstyle='none', linestyle='--'),
        ] + sr_handles,
        labels=["Computed", "HEPData"] + sr_labels,
        loc="lower right", fontsize=24,
        bbox_to_anchor=(1, -0.1)
    )
    
    logger.info(f"Saving acceptance comparison plot for {analysis} to outputs/acceptance_comparison_{analysis}.pdf")
    plt.savefig(f"outputs/acceptance_comparison_{analysis}.pdf")
    plt.close(fig)