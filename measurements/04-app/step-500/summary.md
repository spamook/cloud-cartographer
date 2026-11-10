# 04-app/step-500

2026-11-10 23:03:28 – 23:12:28 (9 min, 15 s samples)

500 simultaneous users (Locust), measured after a 60 s ramp

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 302 m | 327 m | 102 MiB | 192 MiB | 796.8 KiB/s | 880.5 KiB/s | 431.9 MiB | 477.2 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 52 m | 58 m | 2 MiB | 3 MiB | 123.7 KiB/s | 560.4 KiB/s | 67.0 MiB | 303.7 MiB | main |
| backend | 1 | 533 m | 796 m | 13 MiB | 22 MiB | 189.0 KiB/s | 104.7 KiB/s | 102.5 MiB | 56.8 MiB | main |
| postgres | 1 | 85 m | 302 m | 65 MiB | 70 MiB | 27.5 KiB/s | 70.8 KiB/s | 14.9 MiB | 38.4 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 24 m | 39 m | 318 MiB | 323 MiB | 48.1 KiB/s | 1.7 KiB/s | 26.1 MiB | 0.9 MiB | monitoring |
| grafana | 1 | 33 m | 132 m | 476 MiB | 481 MiB | 7.6 KiB/s | 3.3 KiB/s | 4.1 MiB | 1.8 MiB | monitoring |
| loki | 1 | 21 m | 29 m | 227 MiB | 231 MiB | 20.0 KiB/s | 2.2 KiB/s | 10.9 MiB | 1.2 MiB | monitoring |
| alloy | 1 | 57 m | 69 m | 92 MiB | 94 MiB | 0.3 KiB/s | 20.2 KiB/s | 0.2 MiB | 11.0 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 2 m | 10 m | 13 MiB | 13 MiB | 3.9 KiB/s | 2.3 KiB/s | 2.1 MiB | 1.2 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 3 m | 25 MiB | 25 MiB | 0.6 KiB/s | 19.1 KiB/s | 0.3 MiB | 10.3 MiB | monitoring |
| node-exporter | 1 | 3 m | 5 m | 14 MiB | 16 MiB | 809.3 KiB/s | 844.0 KiB/s | 438.7 MiB | 457.4 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 5 m | 7 m | 30 MiB | 31 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.4 MiB | 0.6 MiB | monitoring |
| kubernetes | 8 | 189 m | 345 m | 746 MiB | 756 MiB | 4,796.2 KiB/s | 5,012.5 KiB/s | 2,599.5 MiB | 2,716.7 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 1.55 cores average, 2.21 peak (of 6)
- Memory: 3,665 MiB average, 3,753 MiB peak (of 4,909 MiB)
- Disk writes: 429.5 KiB/s average, 594.3 KiB/s peak; 11.7 IOPS average, 14.8 IOPS peak
- Disk reads: 1,201.9 KiB/s average, 26.7 IOPS average

## External traffic (through Traefik)

- Requests: 488.1 /s average, 495.7 /s peak, 270,884 in total, – answered with 5xx
- Latency: p50 3 ms, p95 7 ms, p99 68 ms
- In: 0.5 KiB/s average (0.3 MiB total); out: 522.6 KiB/s average, 836.7 KiB/s peak (283.2 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 178.8 | 99,261 | 172 B | 25 ms |
| app-frontend-80@kubernetes | 309.2 | 171,622 | 1,631 B | 5 ms |
| monitoring-kps-prometheus-9090@kubernetes | 0.0 | 0 | – | – |

## Database

- Transactions: 170.0 /s average, 172.9 /s peak
- Statements: 160.2 /s, mean execution time 0.033 ms
- Rows read: 850.6 /s; rows written: 0.0 /s
- Connections: 5.0 average, 5 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.3 MiB → 8.3 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 156.0 MiB → 189.9 MiB (225.55 MiB/h); 39,757 series, 2,595.6 samples/s
- Loki: 64.95 MiB of log lines received (552,153 lines), 432.99 MiB/h

## Cost per unit of traffic (at 488.1 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 62 m | 1,847 B |
| frontend | 11 m | 1,176 B |
| backend | 109 m | 220 B |
| postgres | 17 m | 149 B |
| loki | 4 m | 5 B |
| alloy | 12 m | 42 B |
| prometheus | 5 m | 4 B |

- Egress per request: 1,096 B; log bytes per request: 251 B
