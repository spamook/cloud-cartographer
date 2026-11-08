#!/usr/bin/env bash
# Starts the Minikube VM for the local setup (creates it on the first run).
source "$(dirname "$0")/lib.sh"

step "Minikube profile $PROFILE"
# VirtualBox: the Windows hypervisor is off on this machine. The host-only network is the one
# that already exists (a new one needs admin rights). 5 GB is enough for the stack (~3.5 GB used)
# and leaves memory on a 16 GB host for the load generator.
minikube start -p "$PROFILE" --driver=virtualbox --host-only-cidr=192.168.56.1/24 \
    --cpus=6 --memory=5g --disk-size=30g \
    --kubernetes-version=v1.35.10 --container-runtime=containerd \
    --addons=metrics-server
use_cluster
echo "node IP: $IP"
