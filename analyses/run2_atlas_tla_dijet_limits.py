"""

This helper script parses the Run2 ATLAS TLA dijet limits
from the HEPData record and returns them in a cleaner
dictionary format.

"""
import json
from modules.logger_setup import logger
import pandas as pd
import numpy as np

HEP_DATA_FILE = {
    "J50": "analyses/run2_atlas_tla_dijet_J50_hepdata.json",
    "J100": "analyses/run2_atlas_tla_dijet_J100_hepdata.json",
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
        "expected_limit": [],
        "observed_limit": [],
        "down_1sigma": [],
        "up_1sigma": [],
        "down_2sigma": [],
        "up_2sigma": []
    }

    # parse the HEPData JSON structure into a cleaner dictionary
    for entry in hepdata["values"]:
        # entry will be a dictionary e.g.
        # {
        #   "x":[{"value":"375.0"}],
        #   "y":[
        #         {"errors":[{"hide":true,"symerror":0}],"group":0,"value":"2.313"},
        #         {"errors":[{"hide":true,"symerror":0}],"group":1,"value":"5.5764"},
        #         {"errors":[{"hide":true,"symerror":0}],"group":2,"value":"12.762"},
        #         {"errors":[{"asymerror":{"minus":"-1.1203","plus":"1.5126"},"label":"1 sigma"}, {"asymerror":{"minus":"-1.8573","plus":"3.5246"},"label":"2 sigma"}],"group":3,"value":"4.0091"},
        #         {"errors":[{"hide":true,"symerror":0}],"group":4,"value":"8.5317"},
        #         {"errors":[{"hide":true,"symerror":0}],"group":5,"value":"14.946"}
        #       ]
        # }
        limits["mass"].extend([float(entry["x"][0]["value"])]*3)
        limits["width"].extend([5, 10, 15]) # in percent
        limits["observed_limit"].extend([
            float(entry["y"][0]["value"]),
            float(entry["y"][1]["value"]),
            float(entry["y"][2]["value"])
        ])
        limits["expected_limit"].extend(
            [
                float(entry["y"][3]["value"]),
                float(entry["y"][4]["value"]),
                float(entry["y"][5]["value"])
            ]
        )
        limits["down_1sigma"].extend([
            float(entry["y"][3]["value"]) + float(entry["y"][3]["errors"][0]["asymerror"]["minus"]),
            np.nan,
            np.nan,
        ])
        limits["up_1sigma"].extend([
            float(entry["y"][3]["value"]) + float(entry["y"][3]["errors"][0]["asymerror"]["plus"]),
            np.nan,
            np.nan,
        ])
        limits["down_2sigma"].extend([
            float(entry["y"][3]["value"]) + float(entry["y"][3]["errors"][1]["asymerror"]["minus"]),
            np.nan,
            np.nan,
        ])
        limits["up_2sigma"].extend([
            float(entry["y"][3]["value"]) + float(entry["y"][3]["errors"][1]["asymerror"]["plus"]),
            np.nan,
            np.nan,
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

    with PdfPages("analyses/plot_run2_atlas_tla_dijet_limits.pdf") as pdf:
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
            ax.set_title(f"{sr} region", fontsize=20)

            for width, c in zip(df_limits["width"].unique().tolist(), ['C0', 'C1', 'C2']):
                df_width = df_limits[df_limits["width"] == width]
                ax.plot(
                    df_width["mass"],
                    df_width["observed_limit"],
                    linestyle='-',
                    color=c,
                    lw=2,
                )
                ax.plot(
                    df_width["mass"],
                    df_width["expected_limit"],
                    linestyle='--',
                    color=c,
                    lw=2,
                )
                if width == 5:
                    ax.fill_between(
                        df_width["mass"],
                        df_width["down_1sigma"],
                        df_width["up_1sigma"],
                        color='green',
                        alpha=0.5,
                        label='1 sigma',
                    )
                    ax.fill_between(
                        df_width["mass"],
                        df_width["down_2sigma"],
                        df_width["up_2sigma"],
                        color='yellow',
                        alpha=0.5,
                        label='2 sigma',
                    )
            
            ax.legend(
                handles=[
                    plt.Line2D([], [], color='black', linestyle='-', label='Observed'),
                    plt.Line2D([], [], color='black', linestyle='--', label='Expected'),
                    plt.Line2D([], [], color='C0', linestyle='-', label='$m_G/\sigma_G = 5$% ($\pm1-2\sigma$)'),
                    plt.Line2D([], [], color='C1', linestyle='-', label='$m_G/\sigma_G = 10$%'),
                    plt.Line2D([], [], color='C2', linestyle='-', label='$m_G/\sigma_G = 15$%'),
                ],
                loc='upper right',
                fontsize=24
            )
            ax.set_ylim(1e-2, 1e3)
            ax.set_xlim(350, 1850)

            pdf.savefig(fig)
            plt.close(fig)
