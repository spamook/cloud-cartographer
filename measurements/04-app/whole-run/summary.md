# 04-app/whole-run

2026-11-10 22:42:28 – 23:32:31 (50 min, 15 s samples)

The whole stepped run: 100, 250, 500, 1000, 1500 users, 600 s per step.

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 406 m | 999 m | 127 MiB | 250 MiB | 692.7 KiB/s | 768.4 KiB/s | 2,039.6 MiB | 2,262.4 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 47 m | 95 m | 3 MiB | 5 MiB | 178.9 KiB/s | 525.3 KiB/s | 526.8 MiB | 1,546.5 MiB | main |
| backend | 1 | 398 m | 1,379 m | 13 MiB | 34 MiB | 145.8 KiB/s | 83.3 KiB/s | 429.4 MiB | 245.3 MiB | main |
| postgres | 1 | 126 m | 731 m | 66 MiB | 138 MiB | 24.8 KiB/s | 56.0 KiB/s | 72.9 MiB | 164.8 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 25 m | 59 m | 311 MiB | 327 MiB | 48.6 KiB/s | 1.8 KiB/s | 143.1 MiB | 5.2 MiB | monitoring |
| grafana | 1 | 34 m | 184 m | 474 MiB | 481 MiB | 7.5 KiB/s | 3.3 KiB/s | 22.2 MiB | 9.9 MiB | monitoring |
| loki | 1 | 21 m | 40 m | 231 MiB | 283 MiB | 16.1 KiB/s | 2.2 KiB/s | 47.3 MiB | 6.5 MiB | monitoring |
| alloy | 1 | 50 m | 102 m | 92 MiB | 94 MiB | 0.4 KiB/s | 16.1 KiB/s | 1.1 MiB | 47.5 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 2 m | 10 m | 12 MiB | 14 MiB | 3.9 KiB/s | 2.3 KiB/s | 11.6 MiB | 6.9 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 3 m | 25 MiB | 26 MiB | 0.9 KiB/s | 19.2 KiB/s | 2.5 MiB | 56.6 MiB | monitoring |
| node-exporter | 1 | 4 m | 18 m | 14 MiB | 16 MiB | 618.4 KiB/s | 650.9 KiB/s | 1,820.8 MiB | 1,916.5 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 5 m | 14 m | 30 MiB | 32 MiB | 0.7 KiB/s | 1.2 KiB/s | 2.0 MiB | 3.5 MiB | monitoring |
| kubernetes | 8 | 206 m | 482 m | 759 MiB | 820 MiB | 3,723.1 KiB/s | 3,928.3 KiB/s | 10,961.9 MiB | 11,566.1 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 1.51 cores average, 3.44 peak (of 6)
- Memory: 3,710 MiB average, 3,934 MiB peak (of 4,909 MiB)
- Disk writes: 347.8 KiB/s average, 1,188.5 KiB/s peak; 12.4 IOPS average, 23.1 IOPS peak
- Disk reads: 1,691.2 KiB/s average, 36.6 IOPS average

## External traffic (through Traefik)

- Requests: 321.9 /s average, 973.2 /s peak, 970,577 in total, 4,409 answered with 5xx
- Latency: p50 3 ms, p95 2,040 ms, p99 5,000 ms
- In: 0.4 KiB/s average (1.1 MiB total); out: 428.6 KiB/s average, 1,810.9 KiB/s peak (1,262.0 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 117.6 | 354,465 | 172 B | 1,318 ms |
| app-frontend-80@kubernetes | 204.2 | 615,749 | 2,050 B | 4,980 ms |
| monitoring-kps-prometheus-9090@kubernetes | 0.0 | 38 | 512 B | 108 ms |

## Database

- Transactions: 127.6 /s average, 459.5 /s peak
- Statements: 106.2 /s, mean execution time 0.058 ms
- Rows read: 1,499.1 /s; rows written: 0.7 /s
- Connections: 5.6 average, 64 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.2 MiB → 8.3 MiB (0.03 MiB/h)
- Prometheus TSDB + WAL: 107.3 MiB → 152.1 MiB (53.63 MiB/h); 40,045 series, 2,595.3 samples/s
- Loki: 263.58 MiB of log lines received (2,218,351 lines), 315.98 MiB/h

On-disk size (du) at the end: postgres 1,205.8 MiB, prometheus 138.9 MiB, loki 37.9 MiB

## Cost per unit of traffic (at 321.9 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 126 m | 2,444 B |
| frontend | 15 m | 1,671 B |
| backend | 124 m | 265 B |
| postgres | 39 m | 178 B |
| loki | 7 m | 7 B |
| alloy | 15 m | 51 B |
| prometheus | 8 m | 6 B |

- Egress per request: 1,363 B; log bytes per request: 285 B
