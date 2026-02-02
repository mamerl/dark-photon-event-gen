CC       := g++
PY8CONF  := pythia8-config

# HepMC from LCG_106 view
HEPMC_INC := /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/include
HEPMC_LIB := /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/lib

CXXFLAGS := -std=c++17 \
	$(shell $(PY8CONF) --cxxflags) \
	-I$(HEPMC_INC)

LDFLAGS  := $(shell $(PY8CONF) --ldflags) \
	-L$(HEPMC_LIB)

LIBS     := $(shell $(PY8CONF) --libs) \
	-lHepMC -ldl -lpthread

all: pythia_generate

pythia_generate: pythia_generate.o
	$(CC) -o $@ $^ $(LDFLAGS) $(LIBS)

pythia_generate.o: pythia_generate.cxx
	$(CC) $(CXXFLAGS) -c $<

clean:
	rm -f pythia_generate pythia_generate.o