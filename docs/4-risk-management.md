# Risk assessment and management plan

How the migration keeps costs under control and what is done about the things that usually go
wrong. The numbers refer to the [cost analysis](3-cost-analysis.md). The services are described in
the [provider comparison](2-provider-comparison.md).

## 1. Cost management controls

### Budgets and alerts (set up before the first resource)

| Scope | Monthly budget | Alerts | AWS | Google Cloud |
|---|---|---|---|---|
| Whole organisation / billing account | estimate + 20% | 50%, 80%, 100% of actual; 100% of forecast | AWS Budgets in the management account | Budget on the billing account |
| `prod` | prod estimate + 15% | 80% and 100% actual, 100% forecast | Budget filtered by linked account | Budget filtered by project |
| `test` | test estimate | 80% actual; 100% forecast | same | same |
| `shared` | shared estimate + 10% | 100% actual | same | same |
| Anomalies | — | spend that jumps above the usual pattern | Cost Anomaly Detection monitor per account, e-mail and Slack via SNS | Budget alerts to Pub/Sub; billing export to BigQuery with a daily query |

- Alerts go to a team mailing list and a chat channel, not to one person.
- The forecast alert is the important one: it fires in the first days of a month that is going to
  overrun, while the actual-spend alert fires only when the money is already spent.
- Budgets don't stop anything by themselves. On AWS a budget action can apply an SCP that blocks
  new instances in `test`. On Google a budget notification can trigger a function that scales the
  test node pools to zero. Both are only for test, never for prod.

### Visibility

- **Cost allocation by tags and labels** (section 4): every report can be cut by environment,
  component and owner.
  - AWS: activate the tags as cost allocation tags in the Billing console. They apply from that day
    on, not retroactively, so do it before migrating.
  - Google: labels flow into the billing export automatically.
- **Inside the clusters**:
  - AWS: EKS split cost allocation data in CUR 2.0 shows cost per namespace.
  - Google: GKE cost allocation shows the same.
- **Monthly review**, 30 minutes. Compare actual cost with this estimate by category, look at the
  biggest movers, check the hidden-cost items from the cost analysis (egress, NAT data, log
  accumulation) and adjust the estimate.

### Guard rails

| Guard rail | AWS | Google Cloud |
|---|---|---|
| Only the chosen region | SCP denying actions outside eu-north-1 (global services excepted) | Organization policy `gcp.resourceLocations` = europe-north1 |
| No expensive surprises | SCP denying instance families not in the design (GPU, metal) in all accounts | Org policy restricting machine types; quotas lowered per project |
| No public IPs on nodes/DB | SCP / Config rule against `AssociatePublicIpAddress` and public RDS | Org policies `compute.vmExternalIpAccess` and `sql.restrictPublicIp` |
| Encryption at rest | EBS encryption by default (per region account setting), S3 default encryption, RDS `StorageEncrypted=true` enforced by SCP | On by default; CMEK only if required |
| Infrastructure only through code | Terraform in GitLab CI with plan/apply review; console access read-only for most people | same |

## 2. Resource optimisation strategy

**Start small, measure, then grow.** The sizes in the estimate come from the local baseline. After
the first two weeks in the cloud, Prometheus shows the real usage. Each node group and the database
are then resized to the measured p95 plus 30–50% headroom.

| Lever | Where | Effect in the estimate |
|---|---|---|
| Spot / Spot VMs | All test nodes, CI build nodes | test compute −68…−83% (AWS), −70% (Google) |
| Scale to zero outside working hours | Test node groups at 12 h × 22 days: a GitLab pipeline schedule sets the node groups' minimum and desired size to 0 at 20:00 and back at 08:00. RDS is stopped (up to 7 days at a time) and Cloud SQL's activation policy is set to `NEVER` | test VM and DB hours −64% |
| 1-year commitments | Prod nodes at their minimum count, prod database, GitLab VM. Bought only after 1–2 months of stable usage | −18…−37% on those lines |
| Right-sized disks | 20–30 GB node disks (GKE's default 100 GB would cost $55/month in prod), Prometheus volume sized from the measured growth | avoids ~$60/month |
| Lifecycle rules | S3 / Cloud Storage: Loki objects deleted after 395 days. ECR / Artifact Registry: untagged images after 7 days, keep the last 30 tags. EBS/PD snapshots: 7 days | keeps storage flat after the first year |
| Cheaper NAT for test | NAT instance (t4g.nano) instead of a NAT gateway in AWS test | −$37/month |
| Autoscaling | Cluster autoscaler on every node group; HPA on frontend and backend, 2 → N replicas at 70% CPU | pay for peak capacity only at peak |
| Clean-up of idle resources | Weekly job that lists unattached volumes, unused IPs, load balancers without targets, snapshots older than 7 days. AWS Trusted Advisor / Compute Optimizer, Google Recommender | prevents slow leakage |
| Graviton (AWS) | arm64 nodes; images built for amd64 and arm64 | ~20% cheaper than t3 |

## 3. Risk mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Costs higher than estimated** (traffic, logs, forgotten resources) | medium | medium | Budgets and anomaly alerts from day one; the estimate keeps 15–20% headroom; monthly review against the line items |
| **Egress grows with users**: it is the largest variable cost. Measured: 3.7 MB per user-hour, 95% of it the uncompressed JS bundle | medium | medium | gzip in nginx (egress −57%, −$66 / −$87 a month); the static files already have one-year cache headers; a CDN (CloudFront / Cloud CDN) if traffic grows |
| **Log volume explodes** (debug logging left on, a crash loop) | medium | medium | Loki per-tenant ingestion limits; alert on `loki_distributor_bytes_received_total` rate; log level `info` in prod |
| **Database migration loses or corrupts data** | low | high | Rehearse in test: `pg_dump`/`pg_restore` or AWS DMS / Database Migration Service with continuous replication; checksum row counts; keep the source read-only until verified |
| **Downtime at the switch-over** | medium | medium | Lower DNS TTL to 60 s a day before; switch in a low-traffic window; old setup kept running for a week for rollback |
| **Services behave differently in the cloud** (latency to the managed DB, load balancer timeouts, Pod Security, arm64 images) | medium | medium | Full load test in test with the same Locust scenario before prod; compare with the local baseline |
| **The backend cannot reach a managed database**: it connects with `sslmode=disable`, and RDS (PostgreSQL 15+) and Cloud SQL as designed require TLS | certain without a fix | high | One-line app change (`sslmode=verify-full` and the provider's CA certificate) before step 3 of the migration; never switch TLS enforcement off instead |
| **Registrations exhaust the database connections**: each one leaves a connection open (measured: 1.0 per sign-up), so ~95 sign-ups after a backend restart fill `max_connections` | certain once users sign up | high: every API call fails | Fix in the app (close the query result) before go-live; meanwhile an alert on `pg_stat_activity` connections above 80% of the limit and a backend restart. A pooler (RDS Proxy, PgBouncer) does not help, because the leaked connection stays checked out |
| **Login storms**: every login is a bcrypt check of ~80 ms of CPU, so a burst of logins (after an outage, or password guessing) saturates the backend. Measured: every step's ramp slowed even `/api/session` to ~1 s | medium | medium | HPA on CPU with a minimum of 2 replicas; `GOMAXPROCS` equal to the CPU limit; a rate limit on `/api/login` in the backend. A WAF rule would cost ~$600/month at this request volume, because AWS WAF bills every request. Keep bcrypt's cost, because lowering it weakens the password hashes |
| **The database pool has no limit**: under load the backend opens ~50 connections a second and, at 1,500 users, filled `max_connections` (5,614 refusals in 10 minutes). The app reports these as wrong passwords (401) | high above ~1,000 users | high: logins fail, and monitoring of 5xx sees nothing | `SetMaxIdleConns` = `SetMaxOpenConns` per replica, sized so that replicas × pool < `max_connections`; return 5xx on database errors; alert on refused connections |
| **A zone fails** | low | high | Prod nodes, database (Multi-AZ / HA) and NAT in 3 zones; PodDisruptionBudgets and topology spread for the app. Monitoring is single-zone, and losing it does not stop the app |
| **Spot capacity taken back** | high (test) | low | Only test and CI on Spot; several instance types per node group; jobs retry |
| **Security misconfiguration** (public bucket, open security group, leaked key) | medium | high | No long-lived keys (OIDC for CI, Pod Identity / Workload Identity for pods); org guard rails; private endpoints; IaC review; GuardDuty / Security Command Center basic findings |
| **Kubernetes version falls out of support** | medium | medium | EKS extended support costs 6× ($0.60/h per cluster); upgrade twice a year, test first |
| **Vendor lock-in** | medium | low | Kubernetes, Helm, Argo CD, Prometheus, Loki and PostgreSQL are portable; provider-specific parts are the load balancer controller, IAM bindings and the managed database |
| **Key person dependency** | medium | medium | Everything in Git (Terraform, Helm, Argo CD apps), runbooks next to the code |

### Migration plan in short

1. **Foundation.** Organisation and accounts/projects, SSO, budgets, guard rails, networks, DNS
   zones, the VPN. Terraform from the first resource.
2. **Shared services.** GitLab, the registry, CI pipelines that build and push images.
3. **Test environment.** Cluster, node groups, managed database, monitoring, Argo CD. Deploy the
   app, rehearse the data migration, run the Locust load test and compare with the local baseline.
4. **Prod environment.** Same as test plus HA, backups and PITR checked by a restore drill.
5. **Switch-over.** Final data sync, DNS change, watch dashboards; rollback plan ready.
6. **First month.** Daily cost check in week one, resize from real metrics, then commitments.

## 4. Resource tagging strategy

Tags (AWS) and labels (Google, Kubernetes) are applied from the first resource, by Terraform's
default tags and by Helm chart labels, so nothing is created untagged.

| Key | Values | Purpose |
|---|---|---|
| `project` | `cloud-cartographer` | separate this system from anything else on the bill |
| `environment` | `prod`, `test`, `shared` | cost per environment; policies differ per environment |
| `component` | `frontend`, `backend`, `database`, `monitoring`, `tools`, `network`, `ci` | cost per part of the system |
| `owner` | team or e-mail alias, e.g. `platform-team` | who to ask before deleting |
| `cost-center` | e.g. `cc-1234` | charge-back to a budget |
| `managed-by` | `terraform`, `argocd`, `manual` | anything `manual` is suspicious in a review |
| `data-classification` | `public`, `internal`, `confidential` | backup and encryption rules (databases and buckets) |
| `expires` (optional) | date | temporary resources, removed by the clean-up job |

- Google labels allow only lowercase letters, digits, `-` and `_`, so the same keys and values are
  used everywhere.
- **AWS enforcement**:
  - a tag policy in AWS Organizations defines the allowed keys and values;
  - an SCP denies `ec2:RunInstances`, `rds:CreateDBInstance` and `s3:CreateBucket` without
    `environment` and `owner`;
  - Terraform `default_tags` sets them anyway.
- **Google enforcement**: labels are set by Terraform modules, and a CI check (OPA/Conftest on
  `terraform plan`) rejects resources without the required labels. Google can enforce tags (not
  labels) by org policy where needed.
- **Kubernetes**: every workload has `app.kubernetes.io/name`, `app.kubernetes.io/part-of` and
  `environment` labels. EKS split cost allocation and GKE cost allocation map them to cost per
  namespace and label.
- **Cost reports**: activate `project`, `environment`, `component`, `owner` as cost allocation tags
  in AWS Billing on day one. Google's billing export has labels from the start.
