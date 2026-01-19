"""

Common tools needed for multiple analyses.

This code mainly parses Delphes output files to extract 
relevant information in a form that is useable for downstream
analyses.

"""

import ROOT



def load_delhes_rdf(tree_name="Delphes"):
    
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

    rdf = ROOT.RDataFrame(tree_name)
    ROOT.RDF.Experimental.AddProgressBar(rdf)
    return rdf