"""

Analysis code corresponding to the ATLAS Run 2 dijet TLA search
See https://arxiv.org/abs/2509.01219 for details.

"""
from modules.common_tools import bookHistWeighted

def analysis(dataframe):
    cutflow_dict = dict()
    cutflow_dict["J50"] = dict()
    cutflow_dict["J100"] = dict()

    # initialise dictionary to hold rdfs for each signal region
    region_dict = {"J100": None, "J50": None}

    initial_yield = dataframe.Sum("mcEventWeight")
    cutflow_dict["J50"]["initial"] = initial_yield
    cutflow_dict["J100"]["initial"] = initial_yield

    # make a multiplicity cut requiring 2 jets / event
    dataframe = dataframe.Filter("Jet_size >= 2", "At least 2 jets")
    cutflow_dict["J50"]["At least 2 jets"] = dataframe.Sum("mcEventWeight")
    cutflow_dict["J100"]["At least 2 jets"] = dataframe.Sum("mcEventWeight")

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
    
    # now apply eta and pT cuts for the two leading jets
    dataframe = dataframe.Filter(
        "Jet0_pt > 85. && Jet1_pt > 85. && fabs(Jet0_eta) < 2.4 && fabs(Jet1_eta) < 2.4", 
        "Jet pT and eta cuts"
    )
    cutflow_dict["J50"]["Jet pT and eta cuts"] = dataframe.Sum("mcEventWeight")
    cutflow_dict["J100"]["Jet pT and eta cuts"] = dataframe.Sum("mcEventWeight")

    # apply TileGap veto
    dataframe = dataframe.Filter(
        "!( (fabs(Jet0_eta) > 1 && fabs(Jet0_eta) < 1.6) || (fabs(Jet1_eta) > 1 && fabs(Jet1_eta) < 1.6) )",
        "TileGap veto"
    )
    cutflow_dict["J50"]["TileGap veto"] = dataframe.Sum("mcEventWeight")
    cutflow_dict["J100"]["TileGap veto"] = dataframe.Sum("mcEventWeight")

    # define the mjj variable from 4-vectors of the two leading jets
    # ROOT::Math::PtEtaPhiMVector v1(10. /*pt*/, 0.1 /*eta*/, 0.24 /*phi*/, 5 /*M*/);
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

    # apply rapidity difference cut
    dataframe = dataframe.Define(
        "y_star",
        "return 0.5 * fabs(Jet0_p4.Rapidity() - Jet1_p4.Rapidity());"
    )
    dataframe = dataframe.Filter(
        "y_star < 0.6",
        "y_star cut"
    )
    cutflow_dict["J50"]["y_star cut"] = dataframe.Sum("mcEventWeight")
    cutflow_dict["J100"]["y_star cut"] = dataframe.Sum("mcEventWeight")

    # define the dijet invariant mass
    dataframe = dataframe.Define(
        "mjj",
        "return (Jet0_p4 + Jet1_p4).M();"
    )

    # now apply the mjj cut that determines the signal region
    region_dict["J100"] = dataframe.Filter(
        "mjj > 481.",
        "mjj > 481 GeV for J100 SR"
    )
    cutflow_dict["J100"]["mjj cut"] = region_dict["J100"].Sum("mcEventWeight")
    
    region_dict["J50"] = dataframe.Filter(
        "mjj > 344.",
        "mjj > 344 GeV for J50 SR"
    )
    cutflow_dict["J50"]["mjj cut"] = region_dict["J50"].Sum("mcEventWeight")        

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
        4000,
        0.,
        4000.,
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
        "HAHM_mzp600",
        samples["HAHM_mzp600"]["ntuple"],
        samples["HAHM_mzp600"]["metadata"],
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
    outfile = ROOT.TFile.Open("run/run2_atlas_tla_dijet_HAHM_mzp600.root", "RECREATE")
    for region_name in region_hists:
        region_hists[region_name].Write()
    outfile.Close()

    


    



