#!/usr/bin/env bash
# Checks whether registrations leave PostgreSQL connections open. The backend's register handler
# runs its INSERT with db.Query and never closes the result, so every new account is expected to
# keep one connection busy, and so is every attempt with an e-mail that already exists. This
# registers new accounts, then repeats one taken e-mail, and counts the backend's connections after
# each part. A backend restart closes them.
#
# usage: scripts/registration-leak.sh [registrations]
source "$(dirname "$0")/lib.sh"
use_cluster
N=${1:-30}
OUT=measurements/05-registration-leak
mkdir -p "$OUT"

sql() { kubectl -n app exec postgres-0 -- psql -tA -U app -d app -c "$1" | tr -d '\r'; }
# client connections of the app user, without this psql session
conns() {
    sql "SELECT count(*) FROM pg_stat_activity WHERE usename = 'app'
         AND backend_type = 'client backend' AND pid <> pg_backend_pid()"
}
register() { # register <email>: prints the HTTP status (no -o /dev/null: Windows' curl has no such file)
    local out
    out=$(curl -s -w '\n%{http_code}' -X POST "http://$IP/api/register" \
        -H 'Content-Type: application/json' \
        -d "{\"name\":\"Leak test\",\"email\":\"$1\",\"password\":\"$(gen_password 12)\"}")
    echo "HTTP ${out##*$'\n'}"
}

run=$(date +%s)
max=$(sql "SHOW max_connections")
c0=$(conns)
step "$N new accounts"
for i in $(seq "$N"); do register "leak-$run-$i@example.com"; done | sort | uniq -c
c1=$(conns)
step "$N attempts with an e-mail that is already taken"
for _ in $(seq "$N"); do register "leak-$run-1@example.com"; done | sort | uniq -c
c2=$(conns)
step "Backend restart"
kubectl -n app rollout restart deployment/backend >/dev/null
kubectl -n app rollout status deployment/backend --timeout=5m >/dev/null
c3=$(conns)

per_new=$(python -c "print(round(($c1 - $c0) / $N, 2))")
per_taken=$(python -c "print(round(($c2 - $c1) / $N, 2))")
cat >"$OUT/summary.md" <<MD
# Registration and database connections

Run on $(date -u -d "@$run" '+%Y-%m-%d %H:%M UTC') with \`scripts/registration-leak.sh $N\`.

| Moment | Backend connections to PostgreSQL |
|---|---|
| Before | $c0 |
| After $N new accounts | $c1 |
| After $N attempts with a taken e-mail | $c2 |
| After a backend restart | $c3 |

- Connections left open per new account: **$per_new**.
- Connections left open per attempt with a taken e-mail: **$per_taken**.
- PostgreSQL allows **$max** connections (\`max_connections\`).
MD
cat "$OUT/summary.md"
