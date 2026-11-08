#!/usr/bin/env bash
# Installs the local setup on the Minikube VM: Traefik, PostgreSQL, the monitoring stack
# (Prometheus, Grafana, Loki, Alloy, postgres-exporter) and the sample app.
source "$(dirname "$0")/lib.sh"
use_cluster

step "Helm repositories"
helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null
# the open-source Loki chart moved here from grafana/helm-charts in March 2026
helm repo add grafana-community https://grafana-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null

step "Namespaces"
kubectl apply -f deploy/local/namespaces.yaml

# first, because it brings the ServiceMonitor CRD the other charts use
step "Prometheus and Grafana"
put_secret monitoring grafana-admin admin-user=admin admin-password="$(password grafana-admin)"
helm upgrade --install kps prometheus-community/kube-prometheus-stack --version 93.1.0 \
    -n monitoring -f deploy/values/kube-prometheus-stack.yaml \
    --set prometheus.prometheusSpec.externalUrl="http://$IP/prometheus" --wait --timeout 15m

step "Traefik"
helm upgrade --install traefik traefik/traefik --version 42.3.1 -n ingress \
    -f deploy/values/traefik.yaml --wait --timeout 10m

step "Loki and Alloy"
helm upgrade --install loki grafana-community/loki --version 21.0.0 -n monitoring \
    -f deploy/values/loki.yaml --wait --timeout 10m
helm upgrade --install alloy grafana/alloy --version 1.15.0 -n monitoring \
    -f deploy/values/alloy.yaml --wait --timeout 10m

step "PostgreSQL"
put_secret app postgres password="$(password postgres)" exporter-password="$(password postgres-exporter)"
kubectl apply -f deploy/local/postgres.yaml
kubectl -n app rollout status statefulset/postgres --timeout=10m

step "PostgreSQL exporter"
put_secret monitoring postgres-exporter password="$(password postgres-exporter)"
helm upgrade --install postgres-exporter prometheus-community/prometheus-postgres-exporter \
    --version 8.2.3 -n monitoring -f deploy/values/postgres-exporter.yaml --wait --timeout 10m

step "Ingress for Grafana and Prometheus, baseline dashboard"
kubectl apply -f deploy/local/ingress.yaml
# Grafana's sidecar loads every ConfigMap labelled grafana_dashboard=1
kubectl -n monitoring create configmap dashboard-baseline \
    --from-file=baseline.json=deploy/dashboards/baseline.json --dry-run=client -o yaml |
    kubectl label --local -f - grafana_dashboard=1 -o yaml | kubectl apply -f -

echo
echo "Grafana:    http://$IP/grafana  (admin / password in .secrets/grafana-admin)"
echo "Prometheus: http://$IP/prometheus"
