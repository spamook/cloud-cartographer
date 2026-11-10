#!/usr/bin/env bash
# Where everything is: URLs of the local setup and where the generated passwords are kept.
source "$(dirname "$0")/lib.sh"
use_cluster

cat <<EOF
App:         http://$IP/   load-test accounts loaduser1..2000@example.com, password in .secrets/load-users
Grafana:     http://$IP/grafana   user admin, password: $(cat .secrets/grafana-admin 2>/dev/null || echo "run scripts/setup.sh")
             dashboard "Cloud Cartographer: baseline"
Prometheus:  http://$IP/prometheus
PostgreSQL:  postgres.app.svc.cluster.local:5432, database/user app, password in .secrets/postgres

Measure the last 15 minutes:   python scripts/measure.py --name <run> --last 15m
Load test, 100 → 1,500 users:  scripts/load-test.sh 04-app 2
Registration leak check:       scripts/registration-leak.sh
Recalculate the costs:         python cost-model/calc.py --write
EOF
