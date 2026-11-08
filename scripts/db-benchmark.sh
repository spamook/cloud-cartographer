#!/usr/bin/env bash
# Database capacity test with pgbench (TPC-B-like transactions) against the local PostgreSQL, in a
# separate database `bench`. It shows what the database itself can do on this hardware and checks
# the database metrics; it is not the application's workload (load-test.sh measures that).
#
# usage: scripts/db-benchmark.sh [clients] [seconds] [scale]
source "$(dirname "$0")/lib.sh"
use_cluster
CLIENTS=${1:-16}
SECONDS_=${2:-300}
SCALE=${3:-20}   # 20 ≈ 300 MB of data

pg() { kubectl -n app exec postgres-0 -c postgres -- "$@"; }

step "Preparing database bench (scale $SCALE)"
pg psql -U app -d app -tc "SELECT 1 FROM pg_database WHERE datname = 'bench'" | grep -q 1 ||
    pg createdb -U app bench
pg pgbench -U app -i -q -s "$SCALE" bench

step "pgbench: $CLIENTS clients for $SECONDS_ s"
start=$(date +%s)
pg pgbench -U app -c "$CLIENTS" -j 4 -T "$SECONDS_" -P 60 bench | tee ".db-benchmark.log"
end=$(date +%s)

step "Measurements"
python -I scripts/measure.py --name 02-db-benchmark --db bench --start "$start" --end "$end" \
    --note "pgbench, $CLIENTS clients, scale $SCALE, against a separate database: the database's own capacity on this VM, not the app's workload."
cp .db-benchmark.log measurements/02-db-benchmark/pgbench.txt
