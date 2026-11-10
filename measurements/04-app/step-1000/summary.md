# 04-app/step-1000

2026-11-10 23:15:48 – 23:22:28 (7 min, 15 s samples)

1,000 simultaneous users (Locust), the last 400 s of the step. During the ramp to 1,000 the ingress (Traefik, limited to 1 core and 256 MiB) failed its health checks and restarted once; afterwards the step ran without errors

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 514 m | 544 m | 191 MiB | 235 MiB | 1,536.3 KiB/s | 1,685.5 KiB/s | 607.6 MiB | 666.6 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 87 m | 93 m | 2 MiB | 3 MiB | 250.8 KiB/s | 1,077.5 KiB/s | 99.2 MiB | 426.1 MiB | main |
| backend | 1 | 1,183 m | 1,379 m | 18 MiB | 22 MiB | 510.0 KiB/s | 296.7 KiB/s | 201.7 MiB | 117.3 MiB | main |
| postgres | 1 | 558 m | 731 m | 70 MiB | 117 MiB | 99.0 KiB/s | 198.5 KiB/s | 39.2 MiB | 78.5 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 30 m | 39 m | 317 MiB | 324 MiB | 48.6 KiB/s | 1.7 KiB/s | 19.2 MiB | 0.7 MiB | monitoring |
| grafana | 1 | 37 m | 57 m | 471 MiB | 477 MiB | 7.4 KiB/s | 3.0 KiB/s | 2.9 MiB | 1.2 MiB | monitoring |
| loki | 1 | 35 m | 40 m | 259 MiB | 277 MiB | 50.8 KiB/s | 2.2 KiB/s | 20.1 MiB | 0.9 MiB | monitoring |
| alloy | 1 | 92 m | 102 m | 92 MiB | 93 MiB | 0.4 KiB/s | 51.6 KiB/s | 0.2 MiB | 20.4 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 2 m | 3 m | 13 MiB | 14 MiB | 3.9 KiB/s | 2.3 KiB/s | 1.6 MiB | 0.9 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 2 m | 25 MiB | 26 MiB | 0.7 KiB/s | 19.4 KiB/s | 0.3 MiB | 7.7 MiB | monitoring |
| node-exporter | 1 | 4 m | 7 m | 14 MiB | 15 MiB | 1,530.9 KiB/s | 1,578.6 KiB/s | 605.5 MiB | 624.4 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 6 m | 14 m | 31 MiB | 32 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.3 MiB | 0.5 MiB | monitoring |
| kubernetes | 8 | 331 m | 393 m | 769 MiB | 790 MiB | 9,072.9 KiB/s | 9,395.9 KiB/s | 3,588.4 MiB | 3,716.1 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 3.15 cores average, 3.44 peak (of 6)
- Memory: 3,816 MiB average, 3,873 MiB peak (of 4,909 MiB)
- Disk writes: 867.3 KiB/s average, 1,188.5 KiB/s peak; 13.0 IOPS average, 17.8 IOPS peak
- Disk reads: 1,595.6 KiB/s average, 38.0 IOPS average

## External traffic (through Traefik)

- Requests: 928.1 /s average, 973.2 /s peak, 375,867 in total, – answered with 5xx
- Latency: p50 4 ms, p95 83 ms, p99 363 ms
- In: 1.0 KiB/s average (0.4 MiB total); out: 991.4 KiB/s average, 1,143.7 KiB/s peak (392.1 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 339.2 | 137,371 | 172 B | 225 ms |
| app-frontend-80@kubernetes | 588.9 | 238,496 | 1,625 B | 24 ms |

## Database

- Transactions: 425.5 /s average, 459.5 /s peak
- Statements: 312.4 /s, mean execution time 0.073 ms
- Rows read: 7,709.4 /s; rows written: 0.0 /s
- Connections: 6.4 average, 20 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.3 MiB → 8.3 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 161.0 MiB → 276.7 MiB (1,041.18 MiB/h); 39,920 series, 2,591.5 samples/s
- Loki: 115.37 MiB of log lines received (962,139 lines), 1,038.36 MiB/h

## Cost per unit of traffic (at 928.1 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 55 m | 1,860 B |
| frontend | 9 m | 1,189 B |
| backend | 127 m | 327 B |
| postgres | 60 m | 219 B |
| loki | 4 m | 2 B |
| alloy | 10 m | 57 B |
| prometheus | 3 m | 2 B |

- Egress per request: 1,094 B; log bytes per request: 322 B
