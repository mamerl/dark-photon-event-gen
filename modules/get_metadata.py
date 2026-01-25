"""

Helper script for retrieving sum of weights metadata.

"""
import pathlib
import json
import ROOT
import argparse
import re
from data.samples import samples
from modules.logger_setup import logger

# load Delphes library
ROOT.gSystem.Load("libDelphes.so")

def main():
    parser = argparse.ArgumentParser(description="Get sum of weights metadata from Delphes output files.")
    parser.add_argument(
        "-s",
        "--samples",
        nargs='+',
        required=True,
        help="List of sample IDs to retrieve metadata for."
    )

    args = parser.parse_args()

    samples_to_check = list(args.samples)
    if "all" in samples_to_check:
        samples_to_check = list(samples.keys())

    df = None
    file_path = str()
    metadata = dict()
    xsec_info = str()
    xsec = float()
    xsec_uncert = float()
    for sample in samples_to_check:
        if sample not in samples:
            logger.error("sample ID %s not found in samples dictionary in samples.py", sample)
            continue
        logger.info("processing sample ID: %s", sample)
        
        # load the sample rdf
        file_path = samples[sample]['ntuple']
        df = ROOT.RDataFrame("Delphes", file_path)
        metadata[sample] = {"sumW": df.Sum("Event.Weight").GetValue()}

        # retrieve cross-section metadata from 
        # run/xsec_info_<sample>.txt
        if pathlib.Path(f"run/xsec_info_{sample.lower()}.txt").is_file():
            with open(f"run/xsec_info_{sample.lower()}.txt", "r") as f:
                xsec_info = f.read().strip()
            matches = re.findall(r"(?:&nbsp;){6}<b>s= (\d+\.\d+.*) &#177 (\d+\.\d+.*) \Wpb\W.{12}", xsec_info)
            xsec = float(matches[0][0])
            xsec_uncert = float(matches[0][1])
            metadata[sample]["xsec"] = xsec
            metadata[sample]["xsec_uncert"] = xsec_uncert
        else:
            logger.warning("cross-section info file run/xsec_info_%s.txt not found, skipping xsec metadata for this sample", sample)

    # print out the metadata so this can be copied into a 
    # separate json file
    logger.info("sum of weights metadata:")
    print(json.dumps(metadata, indent=4))
    logger.info("don't forget to copy this information into the appropriate metadata json file into the data directory!")

    return

if __name__ == "__main__":
    main()

