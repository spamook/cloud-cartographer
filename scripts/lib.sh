# Common settings for the scripts in this directory (sourced, not run).
set -euo pipefail
# Git Bash turns arguments such as "/grafana" into Windows paths; keep them as they are
export MSYS_NO_PATHCONV=1
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PROFILE=${MINIKUBE_PROFILE:-cloud-cartographer}

step() { printf '\n==> %s\n' "$*"; }

# Points kubectl and helm at this project's cluster and sets IP to the node address.
use_cluster() {
    kubectl config use-context "$PROFILE" >/dev/null
    IP=$(minikube -p "$PROFILE" ip)
}

# Random password for generated credentials (letters and digits only, safe in URLs and YAML)
gen_password() {
    local chars
    # a fixed amount of input: "tr </dev/urandom | head" ends tr with SIGPIPE, a failure under pipefail
    chars=$(head -c 512 /dev/urandom | LC_ALL=C tr -dc 'A-Za-z0-9')
    printf '%s' "${chars:0:${1:-24}}"
}

# Password kept in .secrets/<name> (gitignored), generated on first use
password() {
    mkdir -p .secrets
    [ -s ".secrets/$1" ] || gen_password > ".secrets/$1"
    cat ".secrets/$1"
}

# Creates or updates a Secret from key=value pairs: put_secret <namespace> <name> key=value...
put_secret() {
    local ns=$1 name=$2 kv args=()
    shift 2
    for kv in "$@"; do args+=(--from-literal="$kv"); done
    kubectl -n "$ns" create secret generic "$name" "${args[@]}" --dry-run=client -o yaml |
        kubectl apply -f - >/dev/null
}
