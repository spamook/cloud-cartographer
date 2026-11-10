# 04-app-1500/whole-run

2026-11-10 23:35:26 – 23:45:32 (10 min, 15 s samples)

The whole stepped run: 1500 users, 600 s per step.

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 528 m | 678 m | 307 MiB | 510 MiB | 2,285.6 KiB/s | 2,647.7 KiB/s | 1,372.7 MiB | 1,590.2 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 76 m | 99 m | 5 MiB | 30 MiB | 274.6 KiB/s | 1,749.4 KiB/s | 164.9 MiB | 1,050.6 MiB | main |
| backend | 1 | 1,371 m | 1,913 m | 40 MiB | 165 MiB | 718.9 KiB/s | 439.5 KiB/s | 431.8 MiB | 263.9 MiB | main |
| postgres | 1 | 815 m | 1,387 m | 102 MiB | 247 MiB | 157.8 KiB/s | 276.5 KiB/s | 94.8 MiB | 166.1 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 43 m | 197 m | 314 MiB | 332 MiB | 48.5 KiB/s | 2.3 KiB/s | 29.1 MiB | 1.4 MiB | monitoring |
| grafana | 1 | 60 m | 309 m | 473 MiB | 479 MiB | 7.2 KiB/s | 3.2 KiB/s | 4.3 MiB | 1.9 MiB | monitoring |
| loki | 1 | 46 m | 138 m | 299 MiB | 334 MiB | 71.1 KiB/s | 2.3 KiB/s | 42.7 MiB | 1.4 MiB | monitoring |
| alloy | 1 | 93 m | 178 m | 96 MiB | 98 MiB | 0.6 KiB/s | 71.2 KiB/s | 0.4 MiB | 42.8 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 3 m | 12 m | 13 MiB | 14 MiB | 4.0 KiB/s | 2.3 KiB/s | 2.4 MiB | 1.4 MiB | monitoring |
| kube-state-metrics | 1 | 11 m | 156 m | 28 MiB | 31 MiB | 4.4 KiB/s | 19.2 KiB/s | 2.6 MiB | 11.5 MiB | monitoring |
| node-exporter | 1 | 5 m | 13 m | 14 MiB | 15 MiB | 2,490.9 KiB/s | 2,348.4 KiB/s | 1,496.0 MiB | 1,410.4 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 8 m | 25 m | 30 MiB | 32 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.4 MiB | 0.7 MiB | monitoring |
| kubernetes | 8 | 393 m | 749 m | 784 MiB | 815 MiB | 14,839.4 KiB/s | 14,000.4 KiB/s | 8,912.4 MiB | 8,408.5 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 3.72 cores average, 4.56 peak (of 6)
- Memory: 4,053 MiB average, 4,434 MiB peak (of 4,909 MiB)
- Disk writes: 1,156.2 KiB/s average, 1,970.3 KiB/s peak; 15.4 IOPS average, 26.6 IOPS peak
- Disk reads: 2,833.3 KiB/s average, 97.3 IOPS average

## External traffic (through Traefik)

- Requests: 1,024.8 /s average, 1,443.9 /s peak, 630,250 in total, 0 answered with 5xx
- Latency: p50 4 ms, p95 598 ms, p99 3,293 ms
- In: 1.3 KiB/s average (0.8 MiB total); out: 1,495.4 KiB/s average, 3,553.4 KiB/s peak (898.1 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 395.8 | 231,558 | 167 B | 1,358 ms |
| app-frontend-80@kubernetes | 681.7 | 398,766 | 2,265 B | 29 ms |
| monitoring-kps-prometheus-9090@kubernetes | 0.4 | 259 | 1,388 B | 5,000 ms |

## Database

- Transactions: 535.5 /s average, 806.3 /s peak
- Statements: 345.9 /s, mean execution time 0.139 ms
- Rows read: 13,799.0 /s; rows written: 0.0 /s
- Connections: 17.8 average, 79 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.3 MiB → 8.3 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 144.2 MiB → 376.9 MiB (1,382.95 MiB/h); 41,393 series, 2,632.1 samples/s
- Loki: 239.11 MiB of log lines received (1,968,862 lines), 1,420.47 MiB/h

On-disk size (du) at the end: postgres 1,205.9 MiB, prometheus 148.1 MiB, loki 286.4 MiB

## Cost per unit of traffic (at 1,024.8 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 52 m | 2,646 B |
| frontend | 7 m | 1,748 B |
| backend | 134 m | 439 B |
| postgres | 80 m | 276 B |
| loki | 4 m | 2 B |
| alloy | 9 m | 71 B |
| prometheus | 4 m | 2 B |

- Egress per request: 1,494 B; log bytes per request: 398 B
