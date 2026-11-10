# 04-app/step-250

2026-11-10 22:53:28 – 23:02:28 (9 min, 15 s samples)

250 simultaneous users (Locust), measured after a 60 s ramp

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 164 m | 179 m | 76 MiB | 135 MiB | 420.6 KiB/s | 463.4 KiB/s | 227.9 MiB | 251.1 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 28 m | 32 m | 2 MiB | 3 MiB | 63.2 KiB/s | 288.0 KiB/s | 34.3 MiB | 156.1 MiB | main |
| backend | 1 | 255 m | 420 m | 10 MiB | 13 MiB | 91.3 KiB/s | 50.1 KiB/s | 49.5 MiB | 27.1 MiB | main |
| postgres | 1 | 36 m | 126 m | 66 MiB | 66 MiB | 12.4 KiB/s | 34.8 KiB/s | 6.7 MiB | 18.9 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 22 m | 33 m | 309 MiB | 317 MiB | 49.2 KiB/s | 1.8 KiB/s | 26.7 MiB | 1.0 MiB | monitoring |
| grafana | 1 | 27 m | 48 m | 473 MiB | 476 MiB | 7.0 KiB/s | 3.4 KiB/s | 3.8 MiB | 1.8 MiB | monitoring |
| loki | 1 | 17 m | 20 m | 210 MiB | 218 MiB | 10.2 KiB/s | 2.2 KiB/s | 5.5 MiB | 1.2 MiB | monitoring |
| alloy | 1 | 40 m | 46 m | 94 MiB | 94 MiB | 0.3 KiB/s | 10.6 KiB/s | 0.1 MiB | 5.7 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 2 m | 3 m | 12 MiB | 13 MiB | 3.9 KiB/s | 2.3 KiB/s | 2.1 MiB | 1.2 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 2 m | 24 MiB | 25 MiB | 0.7 KiB/s | 19.3 KiB/s | 0.4 MiB | 10.5 MiB | monitoring |
| node-exporter | 1 | 3 m | 8 m | 13 MiB | 14 MiB | 394.9 KiB/s | 427.1 KiB/s | 214.0 MiB | 231.5 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 5 m | 9 m | 30 MiB | 31 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.4 MiB | 0.6 MiB | monitoring |
| kubernetes | 8 | 163 m | 254 m | 738 MiB | 746 MiB | 2,456.0 KiB/s | 2,645.5 KiB/s | 1,331.1 MiB | 1,433.9 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 0.97 cores average, 1.41 peak (of 6)
- Memory: 3,614 MiB average, 3,690 MiB peak (of 4,909 MiB)
- Disk writes: 256.4 KiB/s average, 312.5 KiB/s peak; 11.1 IOPS average, 12.4 IOPS peak
- Disk reads: 1,169.5 KiB/s average, 24.9 IOPS average

## External traffic (through Traefik)

- Requests: 245.4 /s average, 249.4 /s peak, 136,175 in total, – answered with 5xx
- Latency: p50 3 ms, p95 5 ms, p99 66 ms
- In: 0.3 KiB/s average (0.1 MiB total); out: 269.4 KiB/s average, 395.7 KiB/s peak (146.0 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 89.8 | 49,846 | 172 B | 14 ms |
| app-frontend-80@kubernetes | 155.5 | 86,318 | 1,674 B | 5 ms |
| monitoring-kps-prometheus-9090@kubernetes | 0.0 | 10 | 383 B | 5 ms |

## Database

- Transactions: 83.0 /s average, 92.3 /s peak
- Statements: 80.9 /s, mean execution time 0.035 ms
- Rows read: 263.1 /s; rows written: 0.0 /s
- Connections: 5.0 average, 5 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.3 MiB → 8.3 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 120.8 MiB → 146.9 MiB (174.51 MiB/h); 39,753 series, 2,595.8 samples/s
- Loki: 31.52 MiB of log lines received (269,093 lines), 210.15 MiB/h

## Cost per unit of traffic (at 245.4 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 67 m | 1,934 B |
| frontend | 12 m | 1,202 B |
| backend | 104 m | 209 B |
| postgres | 15 m | 145 B |
| loki | 7 m | 9 B |
| alloy | 16 m | 44 B |
| prometheus | 9 m | 8 B |

- Egress per request: 1,124 B; log bytes per request: 243 B
