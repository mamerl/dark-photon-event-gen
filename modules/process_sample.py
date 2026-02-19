"""

This module runs analyses for a given set of samples.

The outputs consist of:
- Histograms saved in ROOT files
- JSON dictionaries with cutflow information specific to each analysis
- JSON dictionaries storing the acceptance of the selection for each sample
- JSON dictionaries storing the expected signal cross-section accounting
  for the acceptance

"""
from math import floor, ceil
import numpy as np
import sys
import argparse
import importlib
import json
import ROOT
import pathlib
from data.samples import samples
from modules.logger_setup import logger
import modules.common_tools as ct

# NOTE add more methods here as they are implemented
TRUNCATION_METHODS = {
    "default"
}

class TruncationWindow:
    """
    Class to define the mass window to use for truncating the signal sample when running the reinterpretation.
     - the default method uses a window of [0.8 * M, 1.2 * M] where M is the signal mass, as suggested in Appendix A.1 of arXiv:1407.1376

    """

    def __init__(self, method_name:str, signal_mass:float):
        self.method_name = method_name
        self.signal_mass = signal_mass

    def get_window(self):
        if self.method_name == "default":
            return self._get_default(self.signal_mass)
        else:
            raise ValueError(f"truncation method {self.method_name} not recognised")

    def _get_default(self, signal_mass:float):
        return [ceil(signal_mass*0.8), floor(signal_mass*1.2)]

def get_args():
    parser = argparse.ArgumentParser(
        description="Run analyses for a given set of samples",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--samples",
        type=str,
        nargs="+",
        required=True,
        help="Names of the samples to process, as given in data/samples.py",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=pathlib.Path,
        required=True,
        help="Directory to save output files",
    )
    parser.add_argument(
        "-a",
        "--analyses",
        type=str,
        nargs="+",
        help="List of analyses to run (corresponding to module names in analyses/)",
        default=["run2_atlas_tla_dijet"]
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=1,
        help="Number of worker threads to use for ROOT RDataFrame",
    )
    parser.add_argument(
        "-r",
        "--do-reinterpretation",
        action="store_true",
        help="Whether to run the re-interpretation to get exclusion limits",
        default=False
    )
    parser.add_argument(
        "-t",
        "--truncation-method",
        choices=TRUNCATION_METHODS,
        default="default",
        type=str,
        help="Method to use for truncating the signal sample when running the reinterpretation"
    )

    return parser.parse_args()

def main():
    args = get_args()

    if not args.output_dir.exists():
        logger.error("output directory %s does not exist", args.output_dir)
        return 1
    
    analysis_modules = dict()
    analysis_limits = dict()
    # load the analysis modules and make sure they contain the necessary functions
    for analysis_name in args.analyses:
        analysis_module = importlib.import_module(f"analyses.{analysis_name}")
        required_functions = ["analysis", "histograms"]
        bad_module = False
        for func in required_functions:
            if not hasattr(analysis_module, func):
                logger.error(
                    "analysis module %s is missing required function %s",
                    analysis_name,
                    func
                )
                bad_module = True
                break
        if not bad_module:
            analysis_modules[analysis_name] = analysis_module

        # now also load the limits module if it exists
        analysis_limit = None
        try:
            analysis_limit = importlib.import_module(f"analyses.{analysis_name}_limits")
        except ModuleNotFoundError:
            logger.warning(
                "no limits module found for analysis %s!",
                analysis_name
            )
        except FileNotFoundError:
            logger.warning(
                "no limits module found for analysis %s!",
                analysis_name
            )
        if analysis_limit is not None:
            if hasattr(analysis_limit, "get_limits"):
                analysis_limits[analysis_name] = analysis_limit
            else:
                logger.error(
                    "limits module for analysis %s is missing required function get_limits",
                    analysis_name
                )
    
    if len(analysis_modules) != len(args.analyses) or (args.do_reinterpretation and len(analysis_limits) != len(args.analyses)):
        logger.error("not all analysis modules could be loaded, exiting!")
        return 1

    logger.info("successfully loaded all analysis modules for analyses:\n%s", "\n".join(analysis_modules.keys()))
    
    if args.workers > 1:
        logger.info("setting up ROOT RDataFrame with %d workers", args.workers)
        ROOT.ROOT.EnableImplicitMT(args.workers)
    else:
        logger.info("setting up ROOT RDataFrame with maximum possible workers")
        ROOT.ROOT.DisableImplicitMT()
    
    sr_dfs = dict()
    sr_histograms = dict()
    sr_cutflows = dict()
    sr_acceptances = dict()
    sample_metadata = dict()
    for sample_name in args.samples:
        if sample_name not in samples:
            logger.error("sample %s not found in data/samples.py, skipping", sample_name)
            continue

        # load the RDF for this sample
        sample_rdf = ct.load_delhes_rdf(
            sample_name, 
            samples[sample_name]["ntuple"], 
            samples[sample_name]["metadata"]
        )

        # load the same metadata to get cross-section information
        with open(samples[sample_name]["metadata"], 'r') as f:
            sample_metadata = json.load(f)[sample_name]

        sr_dfs = dict() # clear for each iteration
        sr_histograms = dict()
        sr_cutflows = dict()
        sr_acceptances = dict()
        tmp_df = None
        for analysis_name in analysis_modules:
            logger.info("processing sample %s for analysis %s", sample_name, analysis_name)

            # run the analysis / selection on the RDF
            sr_dfs, sr_cutflows = analysis_modules[analysis_name].analysis(sample_rdf)
            
            # make the histograms
            for sr in sr_dfs:
                sr_histograms[sr] = analysis_modules[analysis_name].histograms(sr_dfs[sr])

            # run the analysis histogram event loops via RunGraphs
            print(ROOT.RDF.RunGraphs([h for hist_list in sr_histograms.values() for h in hist_list]), file=sys.stderr)

            # extract cutflow information
            for sr in sr_cutflows:
                for cut in sr_cutflows[sr]:
                    if not isinstance(sr_cutflows[sr][cut], (float, int)):
                        sr_cutflows[sr][cut] = sr_cutflows[sr][cut].GetValue()

                # calculate acceptance from the cutflow
                initial_events = sr_cutflows[sr]["initial"]
                final_events = sr_cutflows[sr][(list(sr_cutflows[sr].keys()))[-1]] # last cut
                # in the acceptance calculation all factors of the cross-section, BR, etc
                # should cancel out, so they need to be applied to the signal cross-section 
                # again later on
                acceptance = final_events / initial_events if initial_events > 0 else 0.0

                # initialise extra factors to apply to the cross-section
                # so that the expected MC yield is normalised correctly
                extra_factors = sample_metadata.get("br", 1.0)
                # Pythia8 accounts for the "filter efficiency" but not the branching ratio internally 
                # in the cross-section calculations
                # i.e.
                # double Info::sigmaGen(int i = 0)  
                # double Info::sigmaErr(int i = 0)
                # the estimated cross section and its estimated error, summed over all allowed 
                # processes (i = 0) or for the given process, in units of mb. The numbers refer 
                # to the accepted event sample above, i.e. after any user veto.
                if not samples[sample_name].get("uses_pythia8", False):
                    extra_factors *= sample_metadata.get("filter_eff", 1.0)
                
                sr_acceptances[sr] = {
                    "acceptance": acceptance,
                    # include factors for the branching ratio and filter efficiency multiplying the cross-section 
                    # to correctly determine the expected cross-section of the signal sample
                    "expected_xsec_pb": acceptance * sample_metadata["xsec"] * extra_factors,
                }

            # save the histograms to a ROOT file with directories for 
            # each signal region
            logger.info("saving histograms to %s in output directory", f"histograms_{sample_name}_{analysis_name}.root")
            with ROOT.TFile.Open(
                str(args.output_dir / f"histograms_{sample_name}_{analysis_name}.root"),
                "RECREATE"
            ) as outfile:
                for sr in sr_histograms:
                    outfile.cd() # go back to root directory
                    outfile.mkdir(sr)
                    outfile.cd(sr)
                    for hist in sr_histograms[sr]:
                        hist.Write()

            # save the cutflows to a JSON file
            logger.info("saving cutflows to %s in output directory", f"cutflows_{sample_name}_{analysis_name}.json")
            with open(
                args.output_dir / f"cutflows_{sample_name}_{analysis_name}.json",
                "w"
            ) as cutflow_file:
                json.dump(sr_cutflows, cutflow_file, indent=4)

            # run the re-interpretation of the sample using Gaussian limits
            # do this for each signal region and then pick out the 
            # result to use in limit plots depending on the mass coverage
            # for each signal region later when plotting
            if args.do_reinterpretation:
                for sr in sr_dfs.keys():
                    # compute the fraction of events in the range between
                    # 0.8 * M and 1.2 * M for each signal region
                    # and compute the mean mass for that region
                    mass_window = TruncationWindow(args.truncation_method, samples[sample_name]['mass']).get_window()
                    tmp_df = sr_dfs[sr].Filter(
                        f"mjj > {mass_window[0]} && mjj < {mass_window[1]}"
                    )
                    sumW_mass_window = tmp_df.Sum("mcEventWeight").GetValue()
                    sumW_total = sr_dfs[sr].Sum("mcEventWeight").GetValue()
                    fraction_in_window = sumW_mass_window / sumW_total if sumW_total > 0 else 0.0
                    logger.info(
                        "for sample %s in region %s, fraction of events in mass window between %s GeV and %s GeV is %s",
                        sample_name, sr, mass_window[0], mass_window[1], fraction_in_window
                    )

                    # store the modified acceptance
                    sr_acceptances[sr]["mjj_window_acceptance"] = fraction_in_window
                    sr_acceptances[sr]["mjj_window"] = mass_window
                    modified_acceptance_xsec = sr_acceptances[sr]["expected_xsec_pb"] * fraction_in_window

                    # fill an mjj histogram and get the mean mass
                    h_mjj = ct.bookHistWeighted(
                        tmp_df,
                        "h_mjj_window",
                        "Dijet mass in window;M_{jj} [GeV];Events",
                        6000, 0, 6000,
                        "mjj",
                        "mcEventWeight"
                    ).GetValue()
                    mean_mass = h_mjj.GetMean() if h_mjj.GetEntries() > 0 else 0.0

                    # write the new mjj histogram to the histogram output file
                    with ROOT.TFile.Open(
                        str(args.output_dir / f"histograms_{sample_name}_{analysis_name}.root"),
                        "UPDATE"
                    ) as outfile:
                        outfile.cd(sr)
                        h_mjj.Write()

                    # retrieve the limits for this signal region
                    gauss_limit = (analysis_limits[analysis_name].get_limits(sr))
                    # get the widths available for this signal region
                    limit_widths = gauss_limit["width"].unique()
                    limit_widths = np.sort(limit_widths)

                    # calculate the width/mass ratio to match to the gaussian limits
                    width = float(floor(samples[sample_name]['mass']*1.2) - ceil(samples[sample_name]['mass']*0.8)) / float(5)
                    width = width / mean_mass * 100.0 if mean_mass > 0 else 0.0 # in percent

                    # round up to the nearest value in widths
                    if width not in limit_widths:
                        if width > np.max(limit_widths):
                            logger.warning(
                                "calculated width/mass ratio of %s pc. for SR %s is larger than the maximum width available in the limits, using maximum width %s pc. for limit calculation",
                                width, sr, np.max(limit_widths)
                            )
                            width = np.max(limit_widths)
                        elif width < np.min(limit_widths):
                            logger.warning(
                                "calculated width/mass ratio of %s pc. for SR %s is smaller than the minimum width available in the limits, using minimum width %s pc. for limit calculation",
                                width, sr, np.min(limit_widths)
                            )
                            width = np.min(limit_widths)
                        else:
                            diff = width - limit_widths
                            mask = diff < 0
                            width = limit_widths[mask][np.argmin(diff[mask] * -1)]
                    # ensure width is a float for later saving in json
                    width = float(width) 
                                
                    # retrieve the limits for this width
                    gauss_limit = gauss_limit.loc[gauss_limit["width"] == int(width)]
                    if gauss_limit.empty:
                        logger.warning(
                            "no Gaussian limits found for SR %s with width %s pc., skipping limit calculation",
                            sr, width
                        )
                        continue

                    excluded_xsec = None
                    if np.any(gauss_limit["mass"] == mean_mass):
                        logger.info(
                            "exact mass point %s GeV found for SR %s with width %s pc., using corresponding observed limit",
                            mean_mass, sr, width
                        )
                        excluded_xsec = gauss_limit.loc[gauss_limit["mass"] == mean_mass, "observed_limit"].values[0]
                    else:
                        # find the closest mass points above and below the mean mass
                        mass_below = gauss_limit["mass"][gauss_limit["mass"] < mean_mass]
                        mass_above = gauss_limit["mass"][gauss_limit["mass"] > mean_mass]
                        if mass_below.empty and mass_above.empty:
                            logger.warning(
                                "no suitable mass points found for SR %s with mean mass %s GeV, skipping limit calculation",
                                sr, mean_mass
                            )
                            excluded_xsec = np.nan
                        elif mass_below.empty or mass_above.empty:
                            logger.warning("the mean mass %s GeV is outside the mass range for SR %s limits, skipping limit calculation", mean_mass, sr)
                            excluded_xsec = np.nan
                        else:
                            # find the largest mass point in mass_below and smallest in mass_above
                            # and retrieve the observed limit for those points
                            closest_below = mass_below.max()
                            closest_above = mass_above.min()
                            limit_below = gauss_limit.loc[gauss_limit["mass"] == closest_below, "observed_limit"]
                            limit_above = gauss_limit.loc[gauss_limit["mass"] == closest_above, "observed_limit"]

                            # take the larger of the two limits to be conservative
                            excluded_xsec = np.max([limit_below.values[0], limit_above.values[0]])

                            logger.info(
                                "interpolated mass point for SR %s with mean mass %s GeV between %s GeV and %s GeV, using more conservative observed limit %s pb.",
                                sr, mean_mass, closest_below, closest_above, excluded_xsec
                            )

                    logger.info(
                        "SR %s: mean mass = %s GeV, width = %s pc., acceptance in mjj window = %s, excluded xsec = %s pb.",
                        sr, mean_mass, width, fraction_in_window, excluded_xsec
                    )
                    sr_acceptances[sr]["mean_window_mass"] = mean_mass
                    sr_acceptances[sr]["width_pc"] = width
                    sr_acceptances[sr]["excluded_xsec_pb"] = excluded_xsec
                    sr_acceptances[sr]["modified_expected_xsec_pb"] = modified_acceptance_xsec

            # save the acceptances to a JSON file
            logger.info("saving acceptances to %s in output directory", f"acceptances_{sample_name}_{analysis_name}_{args.truncation_method}.json")
            with open(
                args.output_dir / f"acceptances_{sample_name}_{analysis_name}_{args.truncation_method}.json",
                "w"
            ) as acceptance_file:
                json.dump(sr_acceptances, acceptance_file, indent=4)
                
    return 0
        
if __name__ == "__main__":
    sys.exit(main())