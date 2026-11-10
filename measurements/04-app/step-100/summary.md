# 04-app/step-100

2026-11-10 22:43:28 – 22:52:28 (9 min, 15 s samples)

100 simultaneous users (Locust), measured after a 60 s ramp

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 75 m | 83 m | 57 MiB | 73 MiB | 162.9 KiB/s | 180.9 KiB/s | 88.3 MiB | 98.1 MiB | ingress (cloud: load balancer) |
| frontend | 1 | 13 m | 15 m | 2 MiB | 2 MiB | 25.8 KiB/s | 103.0 KiB/s | 14.0 MiB | 55.8 MiB | main |
| backend | 1 | 98 m | 118 m | 8 MiB | 8 MiB | 35.6 KiB/s | 19.8 KiB/s | 19.3 MiB | 10.7 MiB | main |
| postgres | 1 | 24 m | 31 m | 65 MiB | 66 MiB | 5.8 KiB/s | 15.9 KiB/s | 3.2 MiB | 8.6 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 21 m | 30 m | 296 MiB | 309 MiB | 47.9 KiB/s | 1.8 KiB/s | 26.0 MiB | 1.0 MiB | monitoring |
| grafana | 1 | 24 m | 34 m | 476 MiB | 480 MiB | 8.2 KiB/s | 3.4 KiB/s | 4.4 MiB | 1.8 MiB | monitoring |
| loki | 1 | 16 m | 17 m | 199 MiB | 210 MiB | 5.0 KiB/s | 2.1 KiB/s | 2.7 MiB | 1.2 MiB | monitoring |
| alloy | 1 | 33 m | 37 m | 91 MiB | 91 MiB | 0.3 KiB/s | 5.3 KiB/s | 0.1 MiB | 2.9 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 2 m | 3 m | 12 MiB | 13 MiB | 3.9 KiB/s | 2.3 KiB/s | 2.1 MiB | 1.3 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 1 m | 23 MiB | 24 MiB | 0.7 KiB/s | 19.5 KiB/s | 0.4 MiB | 10.6 MiB | monitoring |
| node-exporter | 1 | 3 m | 9 m | 13 MiB | 14 MiB | 154.6 KiB/s | 183.6 KiB/s | 83.8 MiB | 99.5 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 5 m | 7 m | 28 MiB | 29 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.4 MiB | 0.7 MiB | monitoring |
| kubernetes | 8 | 161 m | 188 m | 747 MiB | 785 MiB | 921.5 KiB/s | 1,100.0 KiB/s | 499.4 MiB | 596.2 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 0.63 cores average, 0.74 peak (of 6)
- Memory: 3,588 MiB average, 3,624 MiB peak (of 4,909 MiB)
- Disk writes: 166.3 KiB/s average, 270.3 KiB/s peak; 12.4 IOPS average, 18.1 IOPS peak
- Disk reads: 1,132.2 KiB/s average, 22.7 IOPS average

## External traffic (through Traefik)

- Requests: 98.5 /s average, 100.2 /s peak, 54,656 in total, – answered with 5xx
- Latency: p50 3 ms, p95 5 ms, p99 66 ms
- In: 0.1 KiB/s average (0.1 MiB total); out: 96.3 KiB/s average, 143.0 KiB/s peak (52.2 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| app-backend-80@kubernetes | 36.1 | 20,040 | 172 B | 5 ms |
| app-frontend-80@kubernetes | 62.3 | 34,557 | 1,483 B | 5 ms |
| monitoring-kps-prometheus-9090@kubernetes | 0.0 | 22 | 652 B | 5 ms |

## Database

- Transactions: 34.3 /s average, 35.4 /s peak
- Statements: 33.6 /s, mean execution time 0.047 ms
- Rows read: 140.6 /s; rows written: 0.0 /s
- Connections: 5.0 average, 5 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 8.3 MiB → 8.3 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 109.6 MiB → 114.8 MiB (34.81 MiB/h); 39,728 series, 2,594.7 samples/s
- Loki: 12.60 MiB of log lines received (108,043 lines), 84.01 MiB/h

## Cost per unit of traffic (at 98.5 requests/s)

| Component | CPU per 100 requests/s | Network out per request |
|---|---|---|
| traefik | 76 m | 1,881 B |
| frontend | 13 m | 1,071 B |
| backend | 99 m | 205 B |
| postgres | 24 m | 166 B |
| loki | 16 m | 22 B |
| alloy | 34 m | 55 B |
| prometheus | 21 m | 19 B |

- Egress per request: 1,001 B; log bytes per request: 242 B
