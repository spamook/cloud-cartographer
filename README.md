# Cloud Cartographer

A cost analysis for moving a three-tier application to the cloud. The application has a React
frontend, a Go backend and PostgreSQL, and comes with a monitoring stack (Prometheus, Grafana, Loki,
Alloy, postgres-exporter) and CI/CD (GitLab, Helm, Argo CD).

The work measures a local baseline, maps the infrastructure to **AWS** and **Google Cloud**, and
prices both for two environments, `test` and `prod`, sized for 1,000 simultaneous users.

## Reports

| Report | Contents |
|---|---|
| [1. Infrastructure analysis](docs/1-infrastructure-analysis.md) | Measured resource usage per component (CPU, RAM, disk, network, database), bottlenecks, dependency and data-flow maps, security requirements, the cloud infrastructure specification |
| [2. Provider comparison](docs/2-provider-comparison.md) | Service mapping AWS ↔ Google Cloud, free tiers, on-demand / Spot / committed pricing, supplementary costs, official pricing pages |
| [3. Cost analysis](docs/3-cost-analysis.md) | Monthly cost per environment, component and line item for both providers, hidden costs (data transfer, backups, log accumulation), alternatives, recommendation |
| [4. Risk and management plan](docs/4-risk-management.md) | Budgets and alerts, optimisation levers, risks and mitigations, migration steps, tagging strategy |

## Results at a glance

| | AWS (eu-north-1) | Google Cloud (europe-north1) |
|---|---|---|
| On-demand, per month | $1,052 | $923 |
| Optimised, per month | $821 | $676 |

- *Optimised* means:
  - test runs on Spot capacity and only in working hours;
  - the always-on prod capacity and the GitLab VM use 1-year commitments.
- Prices were checked on 2026-11-08 from the providers' official pricing pages.
- The application-dependent quantities (egress, log volume) are provisional until the application
  load test; see [the analysis](docs/1-infrastructure-analysis.md#application-under-load).

## Repository layout

```
docs/                 the four reports
cost-model/           prices.toml (unit prices + sources), bom.toml (what runs where), calc.py
measurements/         one folder per measured run: summary.md, summary.json, samples.csv
scripts/              cluster-up.sh, setup.sh, measure.py, db-benchmark.sh, load-test.sh
load/                 Locust scenario with the user steps
deploy/local/         namespaces, PostgreSQL, ingress for Grafana and Prometheus
deploy/values/        Helm values: kube-prometheus-stack, Loki, Alloy, postgres-exporter, Traefik
deploy/dashboards/    Grafana dashboard "Cloud Cartographer: baseline"
app/                  the sample application
```

## Running the local setup

Requirements:

- [Minikube](https://minikube.sigs.k8s.io/) with VirtualBox, kubectl and Helm 4;
- Python 3.11+;
- Git Bash on Windows, or any shell on Linux/macOS.

Steps:

1. Start the VM: 6 vCPU, 5 GB RAM, Kubernetes 1.35.

   ```bash
   scripts/cluster-up.sh
   ```

2. Install Traefik, PostgreSQL and the monitoring stack.

   ```bash
   scripts/setup.sh
   ```

3. Open the UIs:
   - Grafana: `http://<minikube ip>/grafana` (user `admin`, password in `.secrets/grafana-admin`)
   - Prometheus: `http://<minikube ip>/prometheus`

## Measuring

Measure any time window, for example the last 15 minutes:

```bash
python scripts/measure.py --name my-run --last 15m
```

Or give the window explicitly:

```bash
python scripts/measure.py --name my-run --start 2026-11-09T10:00:00 --end 2026-11-09T10:10:00
```

Run the database capacity test (pgbench, 16 clients, 5 minutes):

```bash
scripts/db-benchmark.sh
```

Run the stepped load test (100 → 1,500 users, 10 minutes per step), with the app's routes in
`CC_FRONTEND_PATHS` and `CC_API_PATHS`:

```bash
scripts/load-test.sh 03-app
```

The results land in `measurements/<name>/`. The Grafana dashboard *Cloud Cartographer: baseline*
shows the same numbers live.

## Recalculating the costs

Change a price in `cost-model/prices.toml` or an assumption in `cost-model/bom.toml`, then run:

```bash
python cost-model/calc.py --write
```

This prints the tables, rewrites the generated part of the cost analysis, and writes
`cost-model/line-items.csv`.
