# 04-app-1500/step-1500

2026-11-10 23:36:26 – 23:45:26 (9 min, 15 s samples)

1500 simultaneous users (Locust), measured after a 60 s ramp

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 565 m | 678 m | 316 MiB | 488 MiB | 2,241.0 KiB/s | 2,739.8 KiB/s | 1,214.6 MiB | 1,484.9 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 80 m | 99 m | 4 MiB | 30 MiB | 301.2 KiB/s | 1,684.1 KiB/s | 163.3 MiB | 912.8 MiB | main |
| backend | 1 | 1,490 m | 1,913 m | 43 MiB | 165 MiB | 795.7 KiB/s | 486.3 KiB/s | 431.3 MiB | 263.6 MiB | main |
| postgres | 1 | 897 m | 1,387 m | 107 MiB | 247 MiB | 174.6 KiB/s | 305.8 KiB/s | 94.7 MiB | 165.7 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 44 m | 197 m | 313 MiB | 330 MiB | 48.1 KiB/s | 1.7 KiB/s | 26.1 MiB | 0.9 MiB | monitoring |
| grafana | 1 | 60 m | 309 m | 473 MiB | 479 MiB | 7.2 KiB/s | 3.2 KiB/s | 3.9 MiB | 1.7 MiB | monitoring |
| loki | 1 | 48 m | 138 m | 302 MiB | 334 MiB | 78.4 KiB/s | 2.3 KiB/s | 42.5 MiB | 1.3 MiB | monitoring |
| alloy | 1 | 98 m | 178 m | 96 MiB | 98 MiB | 0.6 KiB/s | 78.5 KiB/s | 0.3 MiB | 42.5 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 3 m | 12 m | 13 MiB | 14 MiB | 4.0 KiB/s | 2.3 KiB/s | 2.2 MiB | 1.3 MiB | monitoring |
| kube-state-metrics | 1 | 12 m | 156 m | 27 MiB | 30 MiB | 0.9 KiB/s | 18.8 KiB/s | 0.5 MiB | 10.2 MiB | monitoring |
| node-exporter | 1 | 5 m | 13 m | 14 MiB | 15 MiB | 2,540.6 KiB/s | 2,417.6 KiB/s | 1,377.0 MiB | 1,310.3 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 8 m | 25 m | 30 MiB | 32 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.4 MiB | 0.6 MiB | monitoring |
| kubernetes | 8 | 398 m | 749 m | 781 MiB | 813 MiB | 15,226.7 KiB/s | 14,475.6 KiB/s | 8,252.8 MiB | 7,845.7 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 3.96 cores average, 4.56 peak (of 6)
- Memory: 4,064 MiB average, 4,434 MiB peak (of 4,909 MiB)
- Disk writes: 1,243.9 KiB/s average, 1,970.3 KiB/s peak; 14.5 IOPS average, 19.7 IOPS peak
- Disk reads: 2,974.3 KiB/s average, 102.3 IOPS average

## External traffic (through Traefik)

- Requests: 1,131.6 /s average, 1,443.9 /s peak, 628,037 in total, 0 answered with 5xx
- Latency: p50 4 ms, p95 565 ms, p99 2,833 ms
- In: 1.4 KiB/s average (0.8 MiB total); out: 1,570.8 KiB/s average, 3,553.4 KiB/s peak (851.3 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 416.7 | 231,265 | 167 B | 1,348 ms |
| app-frontend-80@kubernetes | 715.5 | 397,089 | 2,153 B | 24 ms |
| monitoring-kps-prometheus-9090@kubernetes | 0.0 | 17 | 157 B | 5,000 ms |

## Database

- Transactions: 592.5 /s average, 806.3 /s peak
- Statements: 380.0 /s, mean execution time 0.140 ms
- Rows read: 15,265.4 /s; rows written: 0.0 /s
- Connections: 19.1 average, 79 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.3 MiB → 8.3 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 148.3 MiB → 367.2 MiB (1,459.67 MiB/h); 41,393 series, 2,633.6 samples/s
- Loki: 234.54 MiB of log lines received (1,931,133 lines), 1,563.60 MiB/h

## Cost per unit of traffic (at 1,131.6 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 50 m | 2,479 B |
| frontend | 7 m | 1,524 B |
| backend | 132 m | 440 B |
| postgres | 79 m | 277 B |
| loki | 4 m | 2 B |
| alloy | 9 m | 71 B |
| prometheus | 4 m | 2 B |

- Egress per request: 1,421 B; log bytes per request: 392 B
