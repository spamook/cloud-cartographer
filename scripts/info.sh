#!/usr/bin/env bash
# Where everything is: URLs of the local setup and where the generated passwords are kept.
source "$(dirname "$0")/lib.sh"
use_cluster

cat <<EOF
Grafana:     http://$IP/grafana   user admin, password: $(cat .secrets/grafana-admin 2>/dev/null || echo "run scripts/setup.sh")
             dashboard "Cloud Cartographer: baseline"
Prometheus:  http://$IP/prometheus
PostgreSQL:  postgres.app.svc.cluster.local:5432, database/user app, password in .secrets/postgres

Measure the last 15 minutes:   python scripts/measure.py --name <run> --last 15m
Load test (needs the app):     scripts/load-test.sh 04-app
Recalculate the costs:         python cost-model/calc.py --write
EOF
