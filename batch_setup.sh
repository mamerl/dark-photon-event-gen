# create a new voms proxy for xrootd access in HTCondor
# NOTE change the output path to your private x509up file path on AFS
# make sure this gets propagated to condor_submission.txt via the
# Proxy_path variable

# NOTE change the experiment name if not ATLAS
# change AFS path accordingly if the proxy should
# be stored somewhere else
export EXPERIMENT=atlas
export AFS_PATH=/afs/cern.ch/user/${USER:0:1}/${USER}

echo "Creating new voms proxy for xrootd access..."
voms-proxy-init -voms ${EXPERIMENT} -valid 191:0 -out ${AFS_PATH}/private/x509up || { echo "Failed to create voms proxy"; return 1; }