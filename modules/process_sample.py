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
import re
import array
import datetime

# NOTE add more methods here as they are implemented
TRUNCATION_METHODS = [
    "default",
    "generic_30",
    "generic_15",
    "generic_10",
    "generic_5",
    "quantile",
    "mode",
]

class TruncationWindow:
    """
    Class to define the mass window to use for truncating the signal sample when running the reinterpretation.
     - the default method uses a window of [0.8 * M, 1.2 * M] where M is the signal mass, as suggested in Appendix A.1 of arXiv:1407.1376
     - the generic method uses a window of [(1 - factor) * M, (1 + factor) * M] where factor is a user-defined parameter, which could be set to 0.2 to match the default method, but could also be varied to study the impact of the mass window choice on the limits
     - the quantile method uses the +/- 2 sigma quantiles to define the window, half of the +/- 1 sigma quantiles window to define sigma, and the median in the truncated window to estimate the mean mass
     - the mode method defines the window around the peak of the mjj spectrum. The width of the window on each side of the peak is twice the distance between the peak and the point that encloses 34.13% of the distribution (measured wrt the peak) calculated on the side of the distribution with the largest tail. The mean mass is estimated as the mode of the truncated distribution.

    """

    def __init__(self, method_name:str, signal_mass:float, rdf):
        self.method_name = method_name
        self.signal_mass = signal_mass
        self.rdf = rdf

        # initialise attributes that are returned
        # by get_* functions 
        self.mean = None
        self.sigma = None
        self.window = None
        self.hist = None

        # fill the mjj histogram for the whole sample (no truncation)
        # in case it is needed for calculating anything
        self.total_mjj = None
        if "quantile" in method_name or "mode" in method_name:
            self.total_mjj = self.__get_total_hist()

        # compute the parameters for each method at initialisation
        # so this is only done once and not every time the get_* 
        # functions are called
        if self.method_name == "default":
            logger.info(f"using default truncation method for signal mass {self.signal_mass}")
            self.window = self.__get_generic_window(factor=0.2)
            self.sigma = self.__get_generic_sigma(window=self.window)
            self.mean, self.hist = self.__get_generic_mean(window=self.window)
        elif "generic" in self.method_name:
            factor = float(re.findall(r"generic_(\d+)", self.method_name)[0]) / 100.0
            logger.info(f"using generic ({factor*100}%) truncation method for signal mass {self.signal_mass}")
            self.window = self.__get_generic_window(factor=factor)
            self.sigma = self.__get_generic_sigma(window=self.window)
            self.mean, self.hist = self.__get_generic_mean(window=self.window)
        elif "quantile" in self.method_name:
            logger.info(f"using quantile truncation method for signal mass {self.signal_mass}")
            self.window = self.__get_quantile_window()
            self.sigma = self.__get_quantile_sigma()
            self.mean, self.hist = self.__get_quantile_mean()
        elif self.method_name == "mode":
            logger.info(f"using mode truncation method for signal mass {self.signal_mass}")
            self.mean, self.hist, self.sigma, self.window = self.__get_mode_parameters()
        else:
            raise ValueError(f"truncation method {self.method_name} not recognised, should be one of {TRUNCATION_METHODS}")
        
        logger.info(
            f"window = {self.window}"
            f", mean = {self.mean}"
            f", sigma = {self.sigma}"
        )

    def get_window(self):
        return self.window

    def get_sigma(self):
        return self.sigma

    def get_mean(self):
        return self.mean
    
    def get_hist(self):
        return self.hist
       
    ################################################################################
    ##### Generic window methods (i.e. a window around the signal pole mass value)
    def __get_generic_window(self, factor:float=0.2):
        return [ceil(self.signal_mass*(1-factor)), floor(self.signal_mass*(1+factor))]

    def __get_generic_sigma(self, window:list):
        # divide by 5 to get an approximate sigma value, since the window 
        # is roughly +/- 2 sigma around the mean
        return (window[1] - window[0]) / 5.0

    def __get_generic_mean(self, window:list):
        # get histogram in window
        hist = self.__get_truncated_hist(window)
        # calculate mean
        mean = hist.GetMean() if hist.GetEntries() > 0 else 0.0

        # return mean and histogram
        return mean, hist

    ################################################################################
    ##### Quantile window methods
    def __get_quantile_window(self, quantile:float=0.9545):
        quantile_left = (1 - quantile) / 2
        # assumes symmetric distribution
        quantile_right = 1 - quantile_left

        # get the quantiles of the distribution
        quantiles = array.array('d', [quantile_left, quantile_right])
        quantiles_values = array.array('d', [0.0, 0.0])
        self.total_mjj.GetQuantiles(2, quantiles_values, quantiles)

        # return the quantiles as the window
        return [quantiles_values[0], quantiles_values[1]]

    def __get_quantile_sigma(self, quantile:float=0.6826):
        # calculate the approximated Gaussian width in GeV for the quantile window
        window = self._get_quantile_window(quantile=quantile)
        # divide by 2 to get an approximate sigma value, since the window 
        # is roughly +/- 1 sigma around the mean for a 68% quantile
        return (window[1] - window[0]) / 2.0

    def __get_quantile_mean(self):
        # get window 
        window = self._get_quantile_window()
        # get histogram in window
        hist = self.__get_truncated_hist(window)
        # calculate the median as an approximation for the mean
        quantiles = array.array('d', [0.5])
        quantiles_values = array.array('d', [0.0])
        hist.GetQuantiles(1, quantiles_values, quantiles)
        mean = float(quantiles_values[0]) if hist.GetEntries() > 0 else 0.0
        # return mean and histogram
        return mean, hist

    ################################################################################
    ##### Mode window methods
    def __get_mode_parameters(self, rebin_factor:int=10):
        # rebin the total mjj histogram to get a smoother distribution
        # for the mode finding
        # come up with a unique name to avoid conflicts when running this 
        # multiple times in the same job
        temp_hist = self.total_mjj.Clone(f"rebinned_mjj_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        temp_hist.Rebin(rebin_factor)

        # find the mode of the distribution
        mode_bin = temp_hist.GetMaximumBin()
        # integrate from the mode bin to the left and right and determine
        # which side has the larger tail
        integral_left = temp_hist.Integral(1, mode_bin-1)
        integral_right = temp_hist.Integral(mode_bin+1, temp_hist.GetNbinsX())
        integral_total = temp_hist.Integral()
        if integral_total > 0:
            integral_left_fraction = integral_left / integral_total
            integral_right_fraction = integral_right / integral_total

        direction = "left" if integral_left > integral_right else "right"
        one_sigma_bin, integral = self.__get_integral_fraction(
            temp_hist, mode_bin, 0.3413, direction=direction
        )
        logger.debug(
            "mode found at bin %s with integral to the left %s and to the right %s, using direction %s to find the one sigma point at bin %s with integral %s",
            mode_bin, integral_left, integral_right, direction, one_sigma_bin, integral
        )
        # define the window size as twice the distance between the mode and the one sigma point on the side with the larger tail
        sigma = abs(temp_hist.GetBinCenter(mode_bin) - temp_hist.GetBinCenter(one_sigma_bin))
        window = [
            ceil(temp_hist.GetBinCenter(mode_bin) - 2*sigma), 
            floor(temp_hist.GetBinCenter(mode_bin) + 2*sigma)
        ]
        mode = temp_hist.GetBinCenter(mode_bin)
        # get histogram in window
        hist = self.__get_truncated_hist(window)        
        return (mode, hist, sigma, window)
 
    ################################################################################
    ##### Other helper functions
    def __get_truncated_hist(
        self, 
        window:list, 
        mjj_column:str="mjj", 
        weight_column:str="mcEventWeight", 
        nbins:int=6000, 
        min_mass:float=0.0, 
        max_mass:float=6000.0
    ):
        # fill a histogram with the events in the mass window and return it
        h_mjj = ct.bookHistWeighted(
            self.rdf.Filter(f"{mjj_column} > {window[0]} && {mjj_column} < {window[1]}"),
            "h_mjj_window",
            "Dijet mass in window;M_{jj} [GeV];Events",
            nbins, min_mass, max_mass,
            mjj_column,
            weight_column
        ).GetValue()
        return h_mjj
    
    def __get_total_hist(
        self,
        mjj_column:str="mjj",
        weight_column:str="mcEventWeight",
        nbins:int=6000,
        min_mass:float=0.0,
        max_mass:float=6000.0
    ):
        # fill a histogram with all the events and return it
        h_mjj = ct.bookHistWeighted(
            self.rdf,
            "h_mjj_total",
            "Dijet mass;M_{jj} [GeV];Events",
            nbins, min_mass, max_mass,
            mjj_column,
            weight_column
        ).GetValue()
        return h_mjj

    def __get_integral_fraction(self, hist, start_bin:int, threshold:float, direction:str="left"):
        # find the bin that encloses the given threshold fraction of the distribution 
        # starting from start_bin and moving in the given direction (left or right)
        if hist.GetEntries() == 0:
            return -1
        elif hist.Integral() != 1.0:
            logger.debug(
                "histogram integral is not unity, normalising to unit area for calculating quantiles and integrals"
            )
            # normalise to unit area for calculating quantiles and integrals
            hist.Scale(1.0 / hist.Integral())

        if direction not in ["left", "right"]:
            raise ValueError(f"direction {direction} not recognised, should be 'left' or 'right'")

        bin_index = start_bin
        integral = float()
        while bin_index > 0 and bin_index <= hist.GetNbinsX():
            if bin_index > start_bin:
                integral = hist.Integral(start_bin, bin_index)
            else:
                integral = hist.Integral(bin_index, start_bin)
            
            if integral >= threshold:
                break
            
            if direction == "left":
                bin_index -= 1
            elif direction == "right":
                bin_index += 1        

        return bin_index, integral

def run_reinterpretation(
    rdf,
    gauss_limit,
    signal_region:str,
    signal_mass:float,
    data_dict:dict,
    histogram_file:str,
    truncation_method="default",
    weight_column:str="mcEventWeight",
    save_histograms:bool=True,
):
    # retrieve the mass window for this interpretation method
    truncation = TruncationWindow(truncation_method, signal_mass, rdf)
    # calculate parameters needed for this truncation method
    mass_window = truncation.get_window()
    sigma = truncation.get_sigma()
    mean_mass = truncation.get_mean()

    # write truncated histogram to the (existing) histogram file
    if save_histograms:
        truncated_hist = truncation.get_hist()
        with ROOT.TFile.Open(
            histogram_file,
            "UPDATE"
        ) as outfile:
            outfile.cd(signal_region)
            truncated_hist.Write()

    # compute the fraction of events in the mass window
    tmp_df = rdf.Filter(
        f"mjj > {mass_window[0]} && mjj < {mass_window[1]}"
    )
    sumW_mass_window = tmp_df.Sum(weight_column).GetValue()
    sumW_total = rdf.Sum(weight_column).GetValue()
    fraction_in_window = sumW_mass_window / sumW_total if sumW_total > 0 else 0.0

    logger.info(
        "fraction of events in mass window between %s GeV and %s GeV is %s",
        mass_window[0], mass_window[1], fraction_in_window
    )

    # store the modified acceptance and other information
    data_dict["mjj_window_acceptance"] = fraction_in_window
    data_dict["mjj_window"] = mass_window
    if "expected_xsec_pb" in data_dict:
        modified_acceptance_xsec = data_dict["expected_xsec_pb"] * fraction_in_window
    else:
        modified_acceptance_xsec = None
        logger.warning("expected_xsec_pb not found in data_dict, cannot calculate modified expected cross-section!")
    data_dict["truncation_method"] = truncation_method
    data_dict["mean_window_mass"] = mean_mass
    data_dict["modified_expected_xsec_pb"] = modified_acceptance_xsec
    
    # get the widths available for this signal region
    limit_widths = gauss_limit["width"].unique()
    limit_widths = np.sort(limit_widths)

    # calculate the width/mass ratio to match to the gaussian limits
    width = (sigma / mean_mass) * 100.0 if mean_mass > 0 else 0.0 # in percent

    # round up to the nearest value in widths
    if width not in limit_widths:
        if width > np.max(limit_widths):
            logger.warning(
                "calculated width/mass ratio of %s pc. is larger than the maximum width available in the limits, using maximum width %s pc. for limit calculation",
                width, np.max(limit_widths)
            )
            width = np.max(limit_widths)
        elif width < np.min(limit_widths):
            logger.warning(
                "calculated width/mass ratio of %s pc. is smaller than the minimum width available in the limits, using minimum width %s pc. for limit calculation",
                width, np.min(limit_widths)
            )
            width = np.min(limit_widths)
        else:
            diff = width - limit_widths
            mask = diff < 0
            width = limit_widths[mask][np.argmin(diff[mask] * -1)]
    # ensure width is a float for later saving in json
    width = float(width) 
    data_dict["width_pc"] = width

    # retrieve the limits for this width
    gauss_limit = gauss_limit.loc[gauss_limit["width"] == int(width)]
    if gauss_limit.empty:
        logger.warning(
            "no Gaussian limits found for width %s pc., skipping limit calculation",
            width
        )
        data_dict["excluded_xsec_pb"] = np.nan
        return

    excluded_xsec = float()
    if np.any(gauss_limit["mass"] == mean_mass):
        logger.info(
            "exact mass point %s GeV found with width %s pc., using corresponding observed limit",
            mean_mass, width
        )
        excluded_xsec = gauss_limit.loc[gauss_limit["mass"] == mean_mass, "observed_limit"].values[0]
    else:
        # find the closest mass points above and below the mean mass
        mass_below = gauss_limit["mass"][gauss_limit["mass"] < mean_mass]
        mass_above = gauss_limit["mass"][gauss_limit["mass"] > mean_mass]
        if mass_below.empty and mass_above.empty:
            logger.warning(
                "no suitable mass points found for width %s pc. with mean mass %s GeV, skipping limit calculation",
                width, mean_mass
            )
            excluded_xsec = np.nan
        elif mass_below.empty or mass_above.empty:
            logger.warning("the mean mass %s GeV is outside the mass range for width %s pc. limits, skipping limit calculation", mean_mass, width)
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
                "interpolated mass point for width %s pc. with mean mass %s GeV between %s GeV and %s GeV, using more conservative observed limit %s pb.",
                width, mean_mass, closest_below, closest_above, excluded_xsec
            )

    # store the reinterpretation results in the data dictionary
    data_dict["excluded_xsec_pb"] = excluded_xsec

    return

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
    parser.add_argument(
        "--skip-histograms",
        action="store_true",
        help="Whether to skip the histogram creation for running the analysis in case only the reinterpretation is needed",
        default=False
    )
    parser.add_argument(
        "--skip-store-cutflows",
        action="store_true",
        help="Whether to skip storing the cutflows in JSON files in the output directory",
        default=False
    )
    parser.add_argument(
        "--file-prefix",
        type=str,
        default="",
        help="Prefix to add to the output files, e.g. to distinguish between different sets of jobs (if empty string, no prefix is added)"
    )

    return parser.parse_args()

def main():
    args = get_args()

    if not args.output_dir.exists():
        logger.error("output directory %s does not exist", args.output_dir)
        return 1

    if args.skip_histograms and not args.do_reinterpretation:
        logger.error("cannot skip histogram creation if not running reinterpretation!")
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
            histogram_file = args.output_dir / f"{args.file_prefix + '_' if args.file_prefix != '' else ''}histograms_{sample_name}_{analysis_name}.root"
            if not args.skip_histograms:
                for sr in sr_dfs:
                    sr_histograms[sr] = analysis_modules[analysis_name].histograms(sr_dfs[sr])

                # run the analysis histogram event loops via RunGraphs
                print(ROOT.RDF.RunGraphs([h for hist_list in sr_histograms.values() for h in hist_list]), file=sys.stderr)

                # save the histograms to a ROOT file with directories for 
                # each signal region
                logger.info("saving histograms to %s in output directory", histogram_file)
                with ROOT.TFile.Open(str(histogram_file), "RECREATE") as outfile:
                    for sr in sr_histograms:
                        outfile.cd() # go back to root directory
                        outfile.mkdir(sr)
                        outfile.cd(sr)
                        for hist in sr_histograms[sr]:
                            hist.Write()

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

            # save the cutflows to a JSON file
            if not args.skip_store_cutflows:
                cutflow_file = args.output_dir / f"{args.file_prefix + '_' if args.file_prefix != '' else ''}cutflows_{sample_name}_{analysis_name}.json"
                logger.info("saving cutflows to %s in output directory", cutflow_file)
                with open(cutflow_file, "w") as cutflow_file:
                    json.dump(sr_cutflows, cutflow_file, indent=4)

            # run the re-interpretation of the sample using Gaussian limits
            # do this for each signal region and then pick out the 
            # result to use in limit plots depending on the mass coverage
            # for each signal region later when plotting
            if args.do_reinterpretation:
                for sr in sr_dfs.keys():
                    run_reinterpretation(
                        sr_dfs[sr],
                        analysis_limits[analysis_name].get_limits(sr),
                        sr,
                        samples[sample_name]["mass"],
                        sr_acceptances[sr],
                        str(histogram_file),
                        truncation_method=args.truncation_method,
                        save_histograms=not args.skip_histograms
                    )

                # save the acceptances to a JSON file
                # only store the acceptance json when doing a reinterpretation
                acceptance_file = args.output_dir / f"{args.file_prefix + '_' if args.file_prefix != '' else ''}acceptances_{sample_name}_{analysis_name}_{args.truncation_method}.json"
                logger.info("saving acceptances to %s in output directory", acceptance_file)
                with open(acceptance_file, "w") as acceptance_file:
                    json.dump(sr_acceptances, acceptance_file, indent=4)
                
    return 0
        
if __name__ == "__main__":
    sys.exit(main())