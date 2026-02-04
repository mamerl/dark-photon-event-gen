"""

Helper script for retrieving sum of weights metadata.

"""
import pathlib
import json
import ROOT
import argparse
import re
from bs4 import BeautifulSoup
from data.samples import samples
from modules.logger_setup import logger

# load Delphes library
ROOT.gSystem.Load("libDelphes.so")

def extract_unwgt(html):
    soup = BeautifulSoup(html, 'html.parser')
    unwgt_values = []
    
    # Locate the table by its ID or class
    table = soup.find('table', {'id': 'tablesort'})
    
    if table:
        # Find all rows, skipping the header (first <tr>)
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                # Column index 4 is 'Unwgt'
                val = cols[4].get_text(strip=True)
                unwgt_values.append(float(val))
    # sum up the unwgt values from all rows
    # since the HTML table can include multiple rows
    # for different subprocesses
    unwgt_count = sum(unwgt_values)
    return unwgt_count

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
    tmp_md = list()
    for sample in samples_to_check:
        if sample not in samples:
            logger.error("sample ID %s not found in samples dictionary in samples.py", sample)
            continue
        logger.info("processing sample ID: %s", sample)
        
        # load the sample rdf
        file_path = samples[sample]['ntuple']
        df = ROOT.RDataFrame("Delphes", file_path)
        metadata[sample] = {"sumW": df.Sum("Event.Weight").GetValue()}
        num_events = df.Count().GetValue()

        # retrieve cross-section metadata from 
        # run/xsec_info_<sample>.txt
        if pathlib.Path(f"run/xsec_info_{sample.lower()}.txt").is_file():
            with open(f"run/xsec_info_{sample.lower()}.txt", "r") as f:
                xsec_info = f.read().strip()

            if not samples[sample].get("uses_pythia8", False):
                matches = re.findall(r"(?:&nbsp;){6}<b>s= (\d+\.\d+.*) &#177 (\d+\.\d+.*) \Wpb\W.{12}", xsec_info)
                xsec = float(matches[0][0])
                xsec_uncert = float(matches[0][1])
                # TODO get the filter efficiency here!
                filter_eff = float(num_events) / extract_unwgt(xsec_info)
            else:
                # different handling for excited quark samples
                # which are generated with pythia8
                tmp_md = [float(val) for val in xsec_info.split("\n")[1].split(" ")]
                xsec = float(tmp_md[0]) * 1e9  # convert from mb to pb
                xsec_uncert = tmp_md[1] * 1e9  # convert from mb to pb
                filter_eff = tmp_md[4] / tmp_md[2]
                # override sumW with the one from pythia8
                metadata[sample]["sumW"] = tmp_md[-1]

            metadata[sample].update({
                "xsec": xsec,
                "xsec_uncert": xsec_uncert,
                "filter_eff": filter_eff
            })
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