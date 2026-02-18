"""

Common tools needed for multiple analyses.

This code mainly parses Delphes output files to extract 
relevant information in a form that is useable for downstream
analyses.

"""
import ROOT
import json
from data.samples import samples
from modules.logger_setup import logger

# load Delphes library
ROOT.gSystem.Load("libDelphes.so")

def load_delhes_rdf(sample_id:str, file_path:str, metadata_path:str, tree_name="Delphes"):
    """
    Load a Delphes ROOT file as a RDataFrame.

    Parameters
    ----------
    tree_name : str
        Name of the Delphes tree in the ROOT file.

    Returns
    -------
    ROOT.RDataFrame
        RDataFrame corresponding to the Delphes tree.
    """

    rdf = ROOT.RDataFrame(tree_name, file_path)
    ROOT.RDF.Experimental.AddProgressBar(rdf)

    # load the metadata file to get the sum of weights
    # and cross-section information
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # calculate the weight factor for normalising the event weights
    # include the BR where this is defined in the metadata file, otherwise assume it is 1
    # (i.e. the cross-section already includes the BR)
    weight_factor = (metadata[sample_id]['xsec'] * metadata[sample_id].get('br', 1.0)) / metadata[sample_id]['sumW']
    if not samples[sample_id].get("uses_pythia8", False):
        weight_factor = weight_factor * metadata[sample_id].get('filter_eff', 1.0)
    logger.info("calculated weight factor for sample %s of %f", sample_id, weight_factor)
    
    # define a new column with normalised event weights
    rdf = rdf.Define(
        "mcEventWeight",
        f"return {weight_factor} * Event.Weight;"
    )

    return rdf

# histogramming
def bookHist(df, name, title, nBinsX, binLow, binHigh, var):
    h = df.Histo1D((name, title, nBinsX, binLow, binHigh), var)
    return h

def bookHistWeighted(df, name, title, nBinsX, binLow, binHigh, var, weight):
    h = df.Histo1D((name, title, nBinsX, binLow, binHigh), var, weight)
    return h

def bookHistWeighted2D(df, name, title, nBinsX, xBinLow, xBinHigh, nBinsY, yBinLow, yBinHigh, xVar, yVar, weight):
    h = df.Histo2D((name, title, nBinsX, xBinLow, xBinHigh, nBinsY, yBinLow, yBinHigh), xVar, yVar, weight)
    return h

def fillHistWeighted(outfile, df, name, title, nBinsX, binLow, binHigh, var, weight):
    h = df.Histo1D((name, title, nBinsX, binLow, binHigh), var, weight)
    outfile.cd()
    h.Write()
    del h

def fillHistWeighted2D(outfile, df, name, title, nBinsX, xBinLow, xBinHigh, nBinsY, yBinLow, yBinHigh, xVar, yVar, weight):
    h = df.Histo2D((name, title, nBinsX, xBinLow, xBinHigh, nBinsY, yBinLow, yBinHigh), xVar, yVar, weight)
    outfile.cd()
    h.Write()
    del h

