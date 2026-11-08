# Cloud provider comparison: AWS and Google Cloud

How the infrastructure of [the analysis](1-infrastructure-analysis.md) maps to two providers, what
their free tiers and pricing models offer, and which costs are easy to miss. The money itself is in
the [cost analysis](3-cost-analysis.md). Prices were checked on 2026-11-08 and are in USD.

## Why AWS and Google Cloud

The three leading providers by market share are AWS (28%), Microsoft Azure (20%) and Google Cloud
(15%) ([Synergy Research, Q2 2026](https://www.srgresearch.com/articles/q2-cloud-market-passes-143-billion-highest-growth-rate-in-eight-years);
[Statista chart](https://www.statista.com/chart/18819/worldwide-market-share-of-leading-cloud-infrastructure-service-providers/)).
Any two of them can run the design. AWS and Google Cloud were chosen for these reasons:

- **Both offer exactly what the requirements name.** EKS and GKE Standard both give node groups
  that we manage ourselves, which the brief asks for instead of Auto Mode or Autopilot. RDS and
  Cloud SQL are the managed PostgreSQL. ECR and Artifact Registry are the private registries.
- **They are two different pricing philosophies.**
  - AWS charges per resource: every NAT gateway, every public IPv4 address, every cluster.
  - Google prices networking as a regional service with a single NAT and load balancer rules, and
    gives one free cluster.

  Comparing them shows where a design's cost really comes from.
- **There is a region next to Estonia.**
  - AWS eu-north-1 is in Stockholm and Google europe-north1 in Hamina, Finland.
  - Both have three availability zones, which the HA production cluster and database need.
  - Both are among the cheapest European regions of their provider, and Finland's grid is one of
    Google's low-carbon regions.
- **Azure would also fit, but was left out.** AKS has a free control plane, but production needs its
  Standard tier ($0.10/h, the same as EKS and GKE). It offers nothing the other two lack for this
  design.

## Service mapping

| Need | AWS (eu-north-1) | Google Cloud (europe-north1) |
|---|---|---|
| Separate environments | AWS Organizations with `management` (billing only), `shared`, `test` and `prod` accounts | Organization → folder → projects `cc-shared`, `cc-test`, `cc-prod`, one billing account |
| People's access | IAM Identity Center: SSO, MFA, permission sets per account | Cloud Identity groups with IAM roles per project |
| Kubernetes | EKS Standard; managed node groups `main`, `monitoring`, `tools` | GKE Standard; node pools `main`, `monitoring`, `tools` |
| Cluster topology | Prod: private endpoint, node groups in 3 AZs. Test: 2 AZs (EKS needs two subnets), nodes in one | Prod: regional cluster (control plane and nodes in 3 zones). Test: zonal cluster |
| Node autoscaling | Cluster Autoscaler, one node group per AZ for groups with zonal volumes | GKE cluster autoscaler per node pool |
| Compute (nodes) | Graviton t4g.medium (2 vCPU, 4 GiB) and t4g.large (2 vCPU, 8 GiB) | e2-medium (2 shared vCPU, 4 GB) and e2-standard-2 (2 vCPU, 8 GB) |
| Block storage | EBS gp3: 3,000 IOPS and 125 MB/s included; encrypted by default (account setting) | Persistent Disk balanced; always encrypted |
| Managed PostgreSQL | RDS for PostgreSQL 18. Prod: db.t4g.medium Multi-AZ. Test: db.t4g.small Single-AZ | Cloud SQL for PostgreSQL 18, Enterprise edition. Prod: 1 vCPU / 3.75 GB HA. Test: db-g1-small zonal |
| Backups and PITR (prod) | Automated backups with 30-day retention. PITR covers the whole window, so 7 days of logs and 30 daily backups both hold | 30 retained daily backups plus 7 days of transaction logs: Cloud SQL's two settings match the requirement one to one |
| Private registry | ECR in `shared`; repository policy lets the test and prod node roles pull | Artifact Registry in `cc-shared`; the node service accounts of test and prod get Reader |
| Log storage (Loki) | S3 bucket per environment; lifecycle rule deletes after 395 days | Cloud Storage bucket per environment, same lifecycle |
| Networks | VPC per account; public subnets only for load balancers and NAT; private subnets for nodes and database | VPC per project; one regional subnet with secondary ranges for pods and services |
| Outbound internet for private nodes | NAT gateway per AZ in prod (one in test); S3 gateway endpoint (free) for images and Loki | Cloud NAT (regional, HA by design); Private Google Access for Artifact Registry and Cloud Storage |
| External load balancer | ALB, created by the AWS Load Balancer Controller from the frontend Ingress | Global external Application Load Balancer from a GKE Ingress/Gateway |
| Internal load balancer | Internal NLB → in-cluster ingress for Grafana, Prometheus, Argo CD | Internal passthrough NLB → the same in-cluster ingress |
| Public DNS | Route 53 public hosted zone in `shared` | Cloud DNS public zone in `cc-shared` |
| Private DNS | Route 53 private hosted zone per environment, attached to its VPC | Cloud DNS private zone per environment, visible to its VPC |
| TLS certificates | ACM certificate on the ALB (free); cert-manager with Let's Encrypt DNS-01 inside the cluster | Google-managed certificate on the load balancer (free); cert-manager inside |
| VPN to private services | WireGuard on a t4g.nano in `shared`, peered with test and prod (AWS Client VPN costs ~$110+/month) | WireGuard on an e2-micro in `cc-shared` (Google has no managed client VPN) |
| Pods calling cloud APIs | EKS Pod Identity: Loki → S3, ExternalDNS → Route 53, External Secrets → Secrets Manager | Workload Identity Federation for GKE: the same pods with Google service accounts |
| Secrets | Secrets Manager, synced into the cluster by External Secrets | Secret Manager, the same way |
| CI | GitLab CE on an m7g.xlarge in `shared`; runners (Kubernetes executor) in the test cluster's `tools` pool | GitLab CE on an e2-standard-4 in `cc-shared`; runners the same way |
| Deployment | Argo CD in each cluster's `tools` pool, pulling Helm charts from GitLab | same |
| Cost control | AWS Budgets per account, Cost Anomaly Detection, cost allocation tags, CUR 2.0 | Budgets per project with alerts, billing export to BigQuery, labels |

## Free tiers

| | AWS | Google Cloud |
|---|---|---|
| New-customer credit | $100 at sign-up, plus up to $100 for completing set-up activities ([free plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html)) | $300 for 90 days ([free program](https://cloud.google.com/free/docs/free-cloud-features)) |
| How long | The Free plan ends after 6 months or when the credits are used up. Then the account closes unless it is upgraded within 90 days | 90 days; resources stop when the trial ends unless the account is upgraded |
| Limits | The Free plan blocks services that could exceed the credits, and Savings Plans and Reserved Instances. **Joining AWS Organizations upgrades the account to the Paid plan automatically**, so the multi-account design runs on a Paid plan from the start (credits are kept) | During the trial: no GPUs and quota limits; afterwards normal billing |
| Always free (relevant here) | 100 GB/month internet egress, aggregated across the organisation; CloudWatch basic metrics; ACM public certificates; budget alerts | **GKE free tier: $74.40/month, one zonal (or Autopilot) cluster per billing account, so the test cluster's fee is free for good**. Also: Artifact Registry 0.5 GB, Cloud Logging 50 GiB per project/month, 6 Secret Manager versions, 200 GiB/month Standard Tier egress. The e2-micro and 5 GB Cloud Storage are free only in US regions, not in Finland |
| Kubernetes | No free tier for EKS | Zonal cluster fee covered (above). The regional prod cluster pays $0.10/h |

The credits pay for the first days of a migration, not for the setup. This design costs ~$35 a day
on AWS and ~$30 on Google Cloud, so the AWS credit lasts about a week and the Google credit about
10 days. Only the permanent offers lower the steady cost: Google's free zonal cluster is worth
$73 a month, and AWS's free 100 GB of egress is worth $9.

## Pricing models

### On-demand
Both bill VMs per second and storage per GB-month.

| Same shape | AWS on-demand | Google on-demand |
|---|---|---|
| 2 vCPU burstable, 4 GB (app nodes) | t4g.medium $0.0344/h | e2-medium $0.0369/h |
| 2 vCPU, 8 GB (monitoring) | t4g.large $0.0688/h | e2-standard-2 $0.0738/h |
| 4 vCPU, 16 GB (GitLab) | m7g.xlarge $0.1734/h | e2-standard-4 $0.1476/h |
| Smallest VM (VPN) | t4g.nano $0.0043/h | e2-micro $0.0092/h |
| Kubernetes control plane | EKS $0.10/h per cluster ($0.60/h on a version in extended support) | GKE $0.10/h per cluster, one zonal cluster free |
| PostgreSQL, prod | db.t4g.medium Multi-AZ $0.130/h | 1 vCPU + 3.75 GB HA $0.149/h |

AWS Graviton (arm64) instances are ~20% cheaper than the x86 t3 family, but the images must be
built for arm64. Go and nginx build for both architectures without changes, so CI builds
multi-architecture images. Google's x86 E2 is its cheapest general-purpose family.

### Spot
Spare capacity at a deep discount. The provider can take a node back at short notice: two minutes
on AWS, 30 seconds on Google.

| | AWS Spot (eu-north-1, current) | Google Spot VM (europe-north1, current) |
|---|---|---|
| 2 vCPU, 4 GB | t4g.medium $0.0111/h (−68%) | — (no Spot price for shared-core e2-medium) |
| 2 vCPU, 8 GB | t4g.large $0.0119/h (−83%) | e2-standard-2 $0.0223/h (−70%) |

Used for the test environment and CI build nodes, where an interruption only delays a job. Not used
for the production nodes or the stateful monitoring node of prod.

### Long-term commitments

| | AWS | Google Cloud |
|---|---|---|
| VMs, 1 year | Compute Savings Plan, no upfront: t4g −18%, m7g −24% ([rates](https://aws.amazon.com/savingsplans/compute-pricing/)) | Resource-based CUD: E2 −37%. Flexible (spend-based) CUD: −28% ([prices](https://cloud.google.com/products/compute/pricing/general-purpose)) |
| VMs, 3 years | Compute Savings Plan: t4g −42%, m7g −48% | Resource-based CUD: E2 −55%; flexible: −46% |
| Database, 1 year | RDS Reserved Instance, db.t4g.medium Multi-AZ: −29% no upfront, −34% all upfront | Cloud SQL CUD: −25% (3 years: −52%) |
| Automatic discounts | none | Sustained use discounts, but only on N1/N2/N2D/C2, not E2 |

Commitments fit only the part that runs 24/7 for a year: the prod nodes at their minimum size, the
prod database and the GitLab VM. Autoscaled capacity stays on-demand.

### Storage, data transfer, load balancing, DNS

| | AWS | Google Cloud |
|---|---|---|
| Block storage | EBS gp3 $0.0836/GB-month; snapshots $0.0475 | PD balanced $0.11/GB-month; snapshots $0.055 |
| Database storage | RDS gp3 $0.12/GB-month, Multi-AZ $0.24; backups beyond provisioned size $0.09 | Cloud SQL SSD $0.187/GB-month, ×2 for HA; backups $0.088 |
| Object storage | S3 Standard $0.023/GB-month; PUT $0.005, GET $0.0004 per 1,000 | Cloud Storage Standard $0.020/GB-month; class A $0.005, class B $0.0004 per 1,000 |
| Ingress from the internet | free | free |
| Egress to the internet | $0.09/GB (first 10 TB); first 100 GB/month free | Premium Tier $0.12/GiB (first TiB), $0.11 to 10 TiB; Standard Tier $0.085 after 200 GiB free |
| Between zones | $0.01/GB each way (so $0.02 per GB crossing) | $0.01/GiB |
| NAT | $0.046/h per gateway + $0.046/GB processed | $0.0014/h per VM using it + $0.045/GiB + $0.005/h per IP |
| Load balancer | ALB/NLB $0.02394/h + $0.0076 per LCU-hour (ALB) | $0.028/h per forwarding rule (first five) + $0.009/GB processed |
| DNS | $0.50 per zone/month; $0.40 per million queries; private-zone and alias queries free | $0.20 per zone/month; $0.40 per million queries |
| TLS certificates | ACM public certificates free; AWS Private CA $400/month | Google-managed certificates free |

## Supplementary costs that are easy to miss

| Cost | AWS | Google Cloud | What the design does |
|---|---|---|---|
| Public IPv4 addresses | $0.005/h for every address, in use or idle: NAT gateways, each AZ of an internet-facing ALB, the VPN (prod has 6 = $22/month) | $0.005/h on VMs; forwarding-rule addresses not charged; unused reserved $0.011/h | No public IPs on nodes, control plane or database (required anyway) |
| Provider logging | CloudWatch Logs $0.54/GB ingested; EKS control plane logs off by default | **GKE sends system and workload logs to Cloud Logging by default**: $0.50/GiB after 50 GiB/project/month. The workload logs would be paid twice, since Loki stores them too | Only the EKS audit log is enabled. GKE logging set to system components only |
| Provider metrics | CloudWatch custom metrics $0.30 per metric/month | **Managed Service for Prometheus is on by default** in new GKE clusters, billed per sample. Managed monitoring is not allowed here anyway | Turned off; Prometheus in the cluster scrapes everything |
| Request pricing | S3 requests (Loki writes a chunk per stream every few minutes); Secrets Manager $0.05 per 10,000 calls; KMS $0.03 per 10,000 | Cloud Storage operations; Secret Manager $0.03 per 10,000 accesses after 10,000 free | Loki's chunk size and flush settings keep PUTs low; External Secrets refreshes hourly, not every minute |
| Management services | EKS $73/month per cluster, $438/month on a version in extended support. NAT gateway $34/month each. Client VPN $110/month per AZ association | GKE $73/month per regional cluster | Upgrade EKS before standard support ends (14 months per version). WireGuard instead of Client VPN. cert-manager instead of a private CA |
| Default disk sizes | EKS managed node groups: 20 GB gp3 root | **GKE nodes get 100 GB boot disks by default**: 5 nodes × 100 GB = $55/month | Boot disks set to 30 GB |
| Cross-zone traffic | Traffic between AZs costs on both sides. An ALB sends requests to pods in every AZ, and 2 of 3 backend pods sit in a different AZ from the RDS primary | $0.01/GiB between zones | Topology-aware routing; counted in the estimate |

## Official pricing pages used

AWS: [EKS](https://aws.amazon.com/eks/pricing/) ·
[EC2 on-demand](https://aws.amazon.com/ec2/pricing/on-demand/) ·
[EC2 Spot](https://aws.amazon.com/ec2/spot/pricing/) ·
[Savings Plans](https://aws.amazon.com/savingsplans/compute-pricing/) ·
[EBS](https://aws.amazon.com/ebs/pricing/) ·
[RDS for PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/) ·
[VPC and NAT gateway](https://aws.amazon.com/vpc/pricing/) ·
[Elastic Load Balancing](https://aws.amazon.com/elasticloadbalancing/pricing/) ·
[S3](https://aws.amazon.com/s3/pricing/) ·
[ECR](https://aws.amazon.com/ecr/pricing/) ·
[Route 53](https://aws.amazon.com/route53/pricing/) ·
[Client VPN](https://aws.amazon.com/vpn/pricing/) ·
[CloudWatch](https://aws.amazon.com/cloudwatch/pricing/) ·
[Secrets Manager](https://aws.amazon.com/secrets-manager/pricing/) ·
[KMS](https://aws.amazon.com/kms/pricing/) ·
[Certificate Manager](https://aws.amazon.com/certificate-manager/pricing/) ·
[Budgets](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/) ·
[Free Tier](https://aws.amazon.com/free/) ·
[Pricing Calculator](https://calculator.aws/)

Google Cloud: [GKE](https://cloud.google.com/kubernetes-engine/pricing) ·
[Compute Engine general-purpose VMs](https://cloud.google.com/products/compute/pricing/general-purpose) ·
[Spot VMs](https://cloud.google.com/spot-vms/pricing) ·
[Disks](https://cloud.google.com/compute/disks-image-pricing) ·
[Cloud SQL](https://cloud.google.com/sql/pricing) ·
[Network](https://cloud.google.com/vpc/network-pricing) ·
[Cloud NAT](https://cloud.google.com/nat/pricing) ·
[Cloud Storage](https://cloud.google.com/storage/pricing) ·
[Artifact Registry](https://cloud.google.com/artifact-registry/pricing) ·
[Cloud DNS](https://cloud.google.com/dns/pricing) ·
[Observability (Logging, Monitoring)](https://cloud.google.com/products/observability/pricing) ·
[Secret Manager](https://cloud.google.com/secret-manager/pricing) ·
[Cloud KMS](https://cloud.google.com/kms/pricing) ·
[Free program](https://cloud.google.com/free/docs/free-cloud-features) ·
[Pricing Calculator](https://cloud.google.com/products/calculator)

How the numbers were read: AWS pricing pages load their tables from AWS's own price files. These
are the meteredUnitMaps on `b0.p.awsstatic.com` and the
[Price List](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html)
files. Google's pricing pages embed every region's table. All values are for eu-north-1 and
europe-north1, read from those sources rather than from third-party sites.
