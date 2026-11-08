#!/usr/bin/env bash
# Stepped load test with Locust from this machine through the node IP (like real users), then the
# measurements of every step and of the whole run.
#
# usage: scripts/load-test.sh <run-name> [workers]
#   CC_FRONTEND_PATHS, CC_API_PATHS, CC_STEPS, CC_STEP_SECONDS: see load/locustfile.py
#
# Locust's --processes needs fork(), which Windows doesn't have, so the master and the workers are
# started as separate processes.
source "$(dirname "$0")/lib.sh"
use_cluster
NAME=${1:?run name, e.g. 04-app}
WORKERS=${2:-4}
export CC_STEPS=${CC_STEPS:-100,250,500,1000,1500}
export CC_STEP_SECONDS=${CC_STEP_SECONDS:-600}
LOCUST=.venv/Scripts/locust
[ -x "$LOCUST" ] || LOCUST=.venv/bin/locust
OUT=measurements/$NAME
mkdir -p "$OUT"

step "Locust: $WORKERS workers, steps $CC_STEPS users, ${CC_STEP_SECONDS}s each, against http://$IP"
pids=()
for _ in $(seq "$WORKERS"); do
    "$LOCUST" -f load/locustfile.py --worker --master-host 127.0.0.1 >/dev/null 2>&1 &
    pids+=($!)
done
trap 'kill "${pids[@]}" 2>/dev/null || true' EXIT
start=$(date +%s)
"$LOCUST" -f load/locustfile.py --master --headless --expect-workers "$WORKERS" \
    --host "http://$IP" --csv "$OUT/locust" --html "$OUT/locust-report.html" --only-summary
end=$(date +%s)

step "Measurements per step"
IFS=, read -ra users <<<"$CC_STEPS"
for i in "${!users[@]}"; do
    # skip the first minute of each step: users are still being started
    s=$((start + i * CC_STEP_SECONDS + 60))
    e=$((start + (i + 1) * CC_STEP_SECONDS))
    python -I scripts/measure.py --name "$NAME/step-${users[$i]}" --start "$s" --end "$e" --no-du \
        --note "${users[$i]} simultaneous users (Locust), measured after a 60 s ramp" >/dev/null
    echo "  step ${users[$i]} users → $OUT/step-${users[$i]}/summary.md"
done
python -I scripts/measure.py --name "$NAME/whole-run" --start "$start" --end "$end" \
    --note "The whole stepped run: ${CC_STEPS} users, ${CC_STEP_SECONDS} s per step." >/dev/null
echo "  whole run → $OUT/whole-run/summary.md, Locust report → $OUT/locust-report.html"
