# 04-app/step-1500

2026-11-10 23:23:28 – 23:32:28 (9 min, 15 s samples)

1,500 simultaneous users (Locust): overload. Traefik stayed at its 1-core limit, failed its health checks and restarted three times; most requests failed or waited seconds

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 926 m | 999 m | 206 MiB | 239 MiB | 549.3 KiB/s | 662.8 KiB/s | 297.7 MiB | 359.2 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 63 m | 69 m | 4 MiB | 4 MiB | 417.7 KiB/s | 485.4 KiB/s | 226.4 MiB | 263.1 MiB | main |
| backend | 1 | 134 m | 550 m | 20 MiB | 34 MiB | 41.7 KiB/s | 24.2 KiB/s | 22.6 MiB | 13.1 MiB | main |
| postgres | 1 | 40 m | 171 m | 65 MiB | 138 MiB | 8.0 KiB/s | 18.1 KiB/s | 4.4 MiB | 9.8 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 23 m | 59 m | 319 MiB | 327 MiB | 48.8 KiB/s | 1.8 KiB/s | 26.4 MiB | 1.0 MiB | monitoring |
| grafana | 1 | 26 m | 72 m | 474 MiB | 477 MiB | 7.4 KiB/s | 3.4 KiB/s | 4.0 MiB | 1.8 MiB | monitoring |
| loki | 1 | 16 m | 40 m | 270 MiB | 283 MiB | 5.9 KiB/s | 2.2 KiB/s | 3.2 MiB | 1.2 MiB | monitoring |
| alloy | 1 | 36 m | 84 m | 93 MiB | 94 MiB | 0.5 KiB/s | 6.3 KiB/s | 0.3 MiB | 3.4 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 3 m | 9 m | 13 MiB | 14 MiB | 4.1 KiB/s | 2.4 KiB/s | 2.2 MiB | 1.3 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 3 m | 26 MiB | 26 MiB | 1.3 KiB/s | 19.6 KiB/s | 0.7 MiB | 10.6 MiB | monitoring |
| node-exporter | 1 | 3 m | 7 m | 14 MiB | 15 MiB | 245.7 KiB/s | 281.7 KiB/s | 133.2 MiB | 152.7 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 6 m | 14 m | 31 MiB | 32 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.4 MiB | 0.7 MiB | monitoring |
| kubernetes | 8 | 181 m | 482 m | 796 MiB | 820 MiB | 1,600.4 KiB/s | 1,819.4 KiB/s | 867.4 MiB | 986.1 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 1.55 cores average, 2.41 peak (of 6)
- Memory: 3,867 MiB average, 3,934 MiB peak (of 4,909 MiB)
- Disk writes: 181.0 KiB/s average, 435.2 KiB/s peak; 12.7 IOPS average, 18.2 IOPS peak
- Disk reads: 1,656.7 KiB/s average, 37.2 IOPS average

## External traffic (through Traefik)

- Requests: 87.8 /s average, 133.3 /s peak, 48,722 in total, 3,275 answered with 5xx
- Latency: p50 4,600 ms, p95 5,000 ms, p99 5,000 ms
- In: 0.1 KiB/s average (0.1 MiB total); out: 157.0 KiB/s average, 1,122.3 KiB/s peak (85.1 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 31.9 | 17,696 | 178 B | 4,362 ms |
| app-frontend-80@kubernetes | 55.4 | 30,731 | 2,800 B | 5,000 ms |

## Database

- Transactions: 36.5 /s average, 74.5 /s peak
- Statements: 31.2 /s, mean execution time 0.054 ms
- Rows read: 416.8 /s; rows written: 0.0 /s
- Connections: 5.2 average, 12 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.3 MiB → 8.3 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 285.7 MiB → 152.1 MiB (-890.62 MiB/h); 40,045 series, 2,595.5 samples/s
- Loki: 12.84 MiB of log lines received (107,034 lines), 85.63 MiB/h

## Cost per unit of traffic (at 87.8 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 1,055 m | 7,731 B |
| frontend | 71 m | 5,662 B |
| backend | 153 m | 282 B |
| postgres | 45 m | 211 B |
| loki | 18 m | 25 B |
| alloy | 41 m | 74 B |
| prometheus | 26 m | 21 B |

- Egress per request: 1,831 B; log bytes per request: 276 B
