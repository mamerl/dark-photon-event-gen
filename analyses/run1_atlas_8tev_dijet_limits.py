"""

This helper script parses the Run1 ATLAS 8 TeV dijet limits
from the HEPData record and returns them in a cleaner
dictionary format.

"""
import json
from modules.logger_setup import logger
import pandas as pd
import numpy as np

HEP_DATA_FILE = {
    "SR": "analyses/run1_atlas_8tev_dijet_hepdata.json",
}

def get_limits(sr_name:str)->pd.DataFrame:
    hepdata = dict()
    limits = dict()

    # load the HEPData JSON file
    try:
        with open(HEP_DATA_FILE[sr_name], 'r') as f:
            hepdata = json.load(f)
    except FileNotFoundError:
        logger.error("HEPData file for signal region %s not found", sr_name)
        return pd.DataFrame()
    except KeyError:
        logger.error("Signal region %s not recognized", sr_name)
        return pd.DataFrame()
    
    # initialise the limits dictionary
    limits = {
        "mass": [],
        "width": [],
        "observed_limit": [],
    }

    # parse the HEPData JSON structure into a cleaner dictionary
    for entry in hepdata["values"]:
        # entry will be a dictionary e.g.
        # {
        #   "x":[{"value":"300.0"}],
        #   "y":[
        #       {"errors":[{"hide":true,"symerror":0}],"group":0,"value":"500.0"}, # mjj resolution
        #       {"errors":[{"hide":true,"symerror":0}],"group":1,"value":"380.0"}, # 7% width
        #       {"errors":[{"hide":true,"symerror":0}],"group":2,"value":"-"}, # 10% width
        #       {"errors":[{"hide":true,"symerror":0}],"group":3,"value":"-"} # 15% width
        #   ]
        # }

        limits["mass"].extend([float(entry["x"][0]["value"])]*3)
        limits["width"].extend([7, 10, 15]) # in percent
        limits["observed_limit"].extend([
            float(entry["y"][1]["value"]) if entry["y"][1]["value"] != "-" else np.nan,
            float(entry["y"][2]["value"]) if entry["y"][2]["value"] != "-" else np.nan,
            float(entry["y"][3]["value"]) if entry["y"][3]["value"] != "-" else np.nan,
        ])
       
    limits_df = pd.DataFrame(limits)
    # sort by width, and within each width sort by mass
    limits_df = limits_df.sort_values(by=["width", "mass"]).reset_index(drop=True)

    return limits_df

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import mplhep as hep
    hep.style.use("ATLAS")

    with PdfPages("analyses/plot_run1_atlas_8tev_dijet_limits.pdf") as pdf:
        for sr in HEP_DATA_FILE.keys():
            df_limits = get_limits(sr)
            print(f"Limits for signal region {sr}:")
            # ensure pandas doesn't truncate the output and print entire dataframe
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            print(df_limits.to_string(index=False))

            # plot the limits
            fig, ax = plt.subplots(figsize=(8,6))
            ax.set_xlabel("$m_G$ [GeV]", fontsize=24)
            ax.set_ylabel(r"$\sigma \times B \times A$ [pb]", fontsize=24)
            ax.set_yscale('log')

            for width, c in zip(df_limits["width"].unique().tolist(), ['C0', 'C1', 'C2']):
                df_width = df_limits[df_limits["width"] == width]
                ax.plot(
                    df_width["mass"],
                    df_width["observed_limit"],
                    linestyle='-',
                    color=c,
                    lw=2,
                )
            
            ax.legend(
                handles=[
                    plt.Line2D([], [], color='black', linestyle='-', label='Observed'),
                    plt.Line2D([], [], color='black', linestyle='--', label='Expected'),
                    plt.Line2D([], [], color='C0', linestyle='-', label='$m_G/\sigma_G = 7$%'),
                    plt.Line2D([], [], color='C1', linestyle='-', label='$m_G/\sigma_G = 10$%'),
                    plt.Line2D([], [], color='C2', linestyle='-', label='$m_G/\sigma_G = 15$%'),
                ],
                loc='upper right',
                fontsize=24
            )
            ax.set_ylim(1e-4, 1e3)
            ax.set_xlim(250, 4250)

            pdf.savefig(fig)
            plt.close(fig)
