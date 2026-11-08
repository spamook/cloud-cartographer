#!/usr/bin/env bash
# Log volume test: a generator writes JSON access-log lines at a fixed rate and Alloy ships them to
# Loki. It measures the two numbers the log storage estimate depends on: Loki's and Alloy's
# resources per MB/s of logs, and how much Loki's chunks really compress.
#
# usage: scripts/log-benchmark.sh [minutes]
source "$(dirname "$0")/lib.sh"
use_cluster
MINUTES=${1:-15}
NAME=03-log-volume

step "Log generator for $MINUTES minutes"
kubectl apply -f deploy/local/log-generator.yaml
kubectl -n app rollout status deploy/log-generator --timeout=180s
start=$(date +%s)
sleep $((MINUTES * 60))
end=$(date +%s)
kubectl -n app delete -f deploy/local/log-generator.yaml --wait=false

step "Flushing Loki's open chunks, so their compression is recorded"
kubectl -n monitoring run loki-flush --rm -i --restart=Never --image=curlimages/curl:8.23.0 -- \
    curl -s -X POST http://loki.monitoring.svc.cluster.local:3100/flush
sleep 60

step "Measurements"
python -I scripts/measure.py --name "$NAME" --start "$start" --end "$end" \
    --note "Log generator at ~300 JSON lines/s through Alloy into Loki for $MINUTES minutes: Loki's and Alloy's cost per MB/s of logs." >/dev/null

q() {
    curl -sg -m 30 --data-urlencode "query=$1" "http://$IP/prometheus/api/v1/query" |
        python -I -c "import json,sys; r=json.load(sys.stdin)['data']['result']; print(r[0]['value'][1] if r else 'n/a')"
}
window="$(( $(date +%s) - start ))s"
ratio=$(q "sum(increase(loki_ingester_chunk_compression_ratio_sum[$window])) / sum(increase(loki_ingester_chunk_compression_ratio_count[$window]))")
stored=$(q "sum(increase(loki_ingester_chunk_stored_bytes_total[$window]))")
chunks=$(q "sum(increase(loki_ingester_chunks_stored_total[$window]))")
received=$(q "sum(increase(loki_distributor_bytes_received_total[$window]))")
{
    echo
    echo "## Loki chunks stored during the run (after a flush)"
    echo
    echo "- Compression ratio (mean of stored chunks): $ratio"
    echo "- Chunks stored: $chunks; compressed bytes stored: $stored; raw log bytes received: $received"
} >> "measurements/$NAME/summary.md"
tail -25 "measurements/$NAME/summary.md"
