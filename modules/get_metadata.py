"""

Helper script for retrieving sum of weights metadata.

"""
import sys
import json
import ROOT
import argparse
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

    df = None
    file_path = str()
    metadata = dict()
    for sample in args.samples:
        if sample not in samples:
            logger.error("sample ID %s not found in samples dictionary in samples.py", sample)
            continue
        
        # load the sample rdf
        file_path = samples[sample]['ntuple']
        df = ROOT.RDataFrame("Delphes", file_path)
        metadata[sample] = df.Sum("Event.Weight").GetValue()

    # print out the metadata so this can be copied into a 
    # separate json file
    logger.info("sum of weights metadata:")
    print(json.dumps(metadata, indent=4))
    logger.info("don't forget to copy this information into the appropriate metadata json file into the data directory!")

    return

if __name__ == "__main__":
    main()

