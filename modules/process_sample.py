"""

This module runs analyses for a given set of samples.

The outputs consist of:
- Histograms saved in ROOT files
- JSON dictionaries with cutflow information specific to each analysis
- JSON dictionaries storing the acceptance of the selection for each sample
- JSON dictionaries storing the expected signal cross-section accounting
  for the acceptance

TODO extend this script to do directly calculate whether a sample is excluded

"""
import sys
import argparse
import importlib
import json
import ROOT
import pathlib
from data.samples import samples
from modules.logger_setup import logger
import modules.common_tools as ct

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
        help="Names of the samples to process",
        choices=list(samples.keys())
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
    return parser.parse_args()

def main():
    args = get_args()

    if not args.output_dir.exists():
        logger.error("output directory %s does not exist", args.output_dir)
        return 1
    
    analysis_modules = dict()
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
    if len(analysis_modules) != len(args.analyses):
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
                acceptance = final_events / initial_events if initial_events > 0 else 0.0
                sr_acceptances[sr] = {
                    "acceptance": acceptance,
                    "expected_xsec": acceptance * sample_metadata["xsec"]
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

            # save the acceptances to a JSON file
            logger.info("saving acceptances to %s in output directory", f"acceptances_{sample_name}_{analysis_name}.json")
            with open(
                args.output_dir / f"acceptances_{sample_name}_{analysis_name}.json",
                "w"
            ) as acceptance_file:
                json.dump(sr_acceptances, acceptance_file, indent=4)

    return 0
        

if __name__ == "__main__":
    sys.exit(main())