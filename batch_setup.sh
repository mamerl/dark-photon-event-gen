# create a new voms proxy for xrootd access in HTCondor
# NOTE change the output path to your private x509up file path on AFS
# make sure this gets propagated to condor_submission.txt via the
# Proxy_path variable
echo "Creating new voms proxy for xrootd access..."
voms-proxy-init -voms atlas -valid 191:0 -out /afs/cern.ch/user/${USER:0:1}/${USER}/private/x509up || { echo "Failed to create voms proxy"; return 1; }