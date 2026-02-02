#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC2.h" // Use HepMC2
#include <fstream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <pythia_settings_file> <output_hepmc_file> <output_xsec_file>\n";
        return 1;
    }

    Pythia8::Pythia pythia;
    // Read settings from file
    // The first argument is the name of the input settings file
    pythia.readFile(argv[1]); 
    pythia.init();

    // Interface to write HepMC file
    // The second argument is the name of the output HepMC file
    Pythia8::Pythia8ToHepMC tophepmc(argv[2]);

    int nEvent = pythia.mode("Main:numberOfEvents");
    for (int iEvent = 0; iEvent < nEvent; ++iEvent) {
        if (!pythia.next()) continue;
        
        // Convert and write the event
        tophepmc.fillNextEvent(pythia);
    }

    // write cross section (mb) and its error to "<output_hepmc>.xsec"
    std::string xsecFile = argv[3];
    std::ofstream ofs(xsecFile);
    if (!ofs) {
        std::cerr << "Error: cannot open cross-section file " << xsecFile << '\n';
    } else {
        double sigma_mb = pythia.info.sigmaGen();
        double sigma_err_mb = pythia.info.sigmaErr();
        int nSelected = pythia.info.nSelected();
        int nTried = pythia.info.nTried();
        int nAccepted = pythia.info.nAccepted();
        double weight_sum = pythia.info.weightSum();

        ofs << "# sigma (mb) sigmaErr (mb) nTried nSelected nAccepted sumW\n"
            << sigma_mb << ' ' << sigma_err_mb << ' ' << nTried << ' ' << nSelected << ' ' << nAccepted << ' ' << weight_sum << '\n';
    }

    pythia.stat();
    return 0;
}