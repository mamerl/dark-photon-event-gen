"""

Analysis code corresponding to the ATLAS Run 1 high-mass dijet search
See https://arxiv.org/abs/1407.1376 for details.

"""
from modules.common_tools import bookHistWeighted

def analysis(dataframe):
    cutflow_dict = dict()
    cutflow_dict["SR"] = dict()

    # initialise dictionary to hold rdfs for each signal region
    region_dict = {"SR": None}

    initial_yield = dataframe.Sum("mcEventWeight")
    cutflow_dict["SR"]["initial"] = initial_yield

    # make a multiplicity cut requiring 2 jets / event
    dataframe = dataframe.Filter("Jet_size >= 2", "At least 2 jets")
    cutflow_dict["SR"]["At least 2 jets"] = dataframe.Sum("mcEventWeight")

    # define per jet quantities for the leading 2 jets
    for i_jet in range(0, 2):
        dataframe = dataframe.Define(
            f"Jet{i_jet}_pt", f"Jet.PT[{i_jet}]"
        )
        dataframe = dataframe.Define(
            f"Jet{i_jet}_eta", f"Jet.Eta[{i_jet}]"
        )
        dataframe = dataframe.Define(
            f"Jet{i_jet}_phi", f"Jet.Phi[{i_jet}]"
        )
        dataframe = dataframe.Define(
            f"Jet{i_jet}_mass", f"Jet.Mass[{i_jet}]"
        )
    
    # define the mjj variable from 4-vectors of the two leading jets
    dataframe = dataframe.Define(
        "Jet0_p4",
        """
        ROOT::Math::PtEtaPhiMVector tmp(Jet0_pt, Jet0_eta, Jet0_phi, Jet0_mass);
        return tmp;
        """
    )
    dataframe = dataframe.Define(
        "Jet1_p4",
        """
        ROOT::Math::PtEtaPhiMVector tmp(Jet1_pt, Jet1_eta, Jet1_phi, Jet1_mass);
        return tmp;
        """
    )

    # define rapidity of the two leading jets
    dataframe = dataframe.Define(
        "Jet0_rapidity",
        "return Jet0_p4.Rapidity();"
    )
    dataframe = dataframe.Define(
        "Jet1_rapidity",
        "return Jet1_p4.Rapidity();"
    )

    # now apply eta and pT cuts for the two leading jets
    dataframe = dataframe.Filter(
        "Jet0_pt > 50. && Jet1_pt > 50. && fabs(Jet0_rapidity) < 2.8 && fabs(Jet1_rapidity) < 2.8", 
        "Jet pT and rapidity cuts"
    )
    cutflow_dict["SR"]["Jet pT and rapidity cuts"] = dataframe.Sum("mcEventWeight")
    
    # apply rapidity difference cut
    dataframe = dataframe.Define(
        "y_star",
        "return 0.5 * fabs(Jet0_rapidity - Jet1_rapidity);"
    )
    dataframe = dataframe.Filter(
        "y_star < 0.6",
        "y_star cut"
    )
    cutflow_dict["SR"]["y_star cut"] = dataframe.Sum("mcEventWeight")

    # define the dijet invariant mass
    dataframe = dataframe.Define(
        "mjj",
        "return (Jet0_p4 + Jet1_p4).M();"
    )

    # now apply the mjj cut that determines the signal region
    region_dict["SR"] = dataframe.Filter(
        "mjj > 250.",
        "mjj > 250 GeV for SR"
    )
    cutflow_dict["SR"]["mjj cut"] = region_dict["SR"].Sum("mcEventWeight")
    
    return region_dict, cutflow_dict

def histograms(dataframe):
    """
    Book histograms for the ATLAS Run 2 dijet TLA analysis. 
    Returns a list of RDF histogram pointers that can be 
    written to a file.
    """
    histograms = list()

    # fill histograms for jet kinematics 
    for i_jet in range(0, 2):
        # jet pT
        histograms.append(bookHistWeighted(
            dataframe,
            f"h_jet{i_jet}_pt",
            f"Jet {i_jet} pT distribution; Jet {i_jet} pT [GeV]; Entries",
            600,
            0.,
            3000.,
            f"Jet{i_jet}_pt",
            "mcEventWeight"
        ))

        # jet eta
        histograms.append(bookHistWeighted(
            dataframe,
            f"h_jet{i_jet}_eta",
            f"Jet {i_jet} eta distribution; Jet {i_jet} eta; Entries",
            60,
            -3.,
            3.,
            f"Jet{i_jet}_eta",
            "mcEventWeight"
        ))

        # jet phi
        histograms.append(bookHistWeighted(
            dataframe,
            f"h_jet{i_jet}_phi",
            f"Jet {i_jet} phi distribution; Jet {i_jet} phi; Entries",
            64,
            -3.2,
            3.2,
            f"Jet{i_jet}_phi",
            "mcEventWeight"
        ))

    # y_star
    histograms.append(bookHistWeighted(
        dataframe,
        "h_y_star",
        "y* distribution; y*; Entries",
        60,
        0.,
        3.,
        "y_star",
        "mcEventWeight"
    ))

    # mjj
    histograms.append(bookHistWeighted(
        dataframe,
        "h_mjj",
        "mjj distribution; m_jj [GeV]; Entries",
        6000,
        0.,
        6000.,
        "mjj",
        "mcEventWeight"
    ))

    return histograms

if __name__ == "__main__":
    import ROOT
    import modules.common_tools as ct
    from data.samples import samples
    from modules.logger_setup import logger
    rdf = ct.load_delhes_rdf(
        "excited_quark_mmed1000",
        samples["excited_quark_mmed1000"]["ntuple"],
        samples["excited_quark_mmed1000"]["metadata"],
    )

    regions, _ = analysis(rdf)
    region_hists = dict()
    for region_name in regions:
        region_hists[region_name] = ct.bookHistWeighted(
            regions[region_name],
            f"h_mjj_{region_name}",
            f"mjj distribution in {region_name} region; m_jj [GeV]; Events",
            400,
            0.,
            2000.,
            "mjj",
            "mcEventWeight"
        )

    # calculate acceptances 
    total_sumW = rdf.Sum("mcEventWeight").GetValue()
    region_sumW = dict()
    region_acceptance = dict()
    for region_name in regions:
        region_sumW[region_name] = regions[region_name].Sum("mcEventWeight").GetValue()
        if total_sumW > 0:
            region_acceptance[region_name] = region_sumW[region_name] / total_sumW
        else:
            region_acceptance[region_name] = 0.0
        logger.info("Acceptance in region %s: %s", region_name, region_acceptance[region_name])

    # save histograms to file
    # file is in the run directory so it won't be included
    # in git commits
    outfile = ROOT.TFile.Open("run/run1_atlas_8tev_dijet_excited_quark_mmed1000.root", "RECREATE")
    for region_name in region_hists:
        region_hists[region_name].Write()
    outfile.Close()
