"""

This module provides a list of samples for the 
HAHM and DMsimp_s_spin1 models generated with MadGraph5_aMC@NLO.

It is intended to be used to identify the correct ROOT files 
to load for analysis and to locate metadata.

"""

samples = {
    "DMsimp_mmed350": {
        "ntuple": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/outputs/generated_events_dmsimp_mmed350_1.root",
        "metadata": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/data/dmsimp_metadata.json",
        "mass": 350,
    },
    "DMsimp_mmed600": {
        "ntuple": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/outputs/generated_events_dmsimp_mmed600_1.root",
        "metadata": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/data/dmsimp_metadata.json",
        "mass": 600,
    },
    "DMsimp_mmed1000": {
        "ntuple": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/outputs/generated_events_dmsimp_mmed1000_1.root",
        "metadata": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/data/dmsimp_metadata.json",
        "mass": 1000,
    },
    "DMsimp_mmed2000": {
        "ntuple": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/outputs/generated_events_dmsimp_mmed2000_1.root",
        "metadata": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/data/dmsimp_metadata.json",
        "mass": 2000,
    },
}

dark_photon_masses = [
    375, 400, 425, 450, 475, 500, 525, 550, 575, 600,
    650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150,
    1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650,
    1700, 1750, 1800
]
for mass in dark_photon_masses:
    samples[f"HAHM_mmed{mass}"] = {
        "ntuple": f"/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/outputs/generated_events_hahm_mmed{mass}_1.root",
        "metadata": "/eos/user/m/mamerl/PhD/TLA/DijetISR/Interpretations/DMWG-dark-photon-tools/dark-photon-event-gen/data/hahm_metadata.json",
        "mass": mass,
    }