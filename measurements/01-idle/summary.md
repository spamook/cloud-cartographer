# 01-idle

2026-11-08 23:35:18 – 23:50:18 (15 min, 15 s samples)

The cluster with the full monitoring stack and an empty PostgreSQL, no traffic: the fixed cost of monitoring.

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 0 m | 2 m | 26 MiB | 29 MiB | 0.5 KiB/s | 0.7 KiB/s | 0.5 MiB | 0.7 MiB | ingress (cloud: load balancer) |
| postgres | 1 | 13 m | 14 m | 45 MiB | 54 MiB | 0.6 KiB/s | 2.8 KiB/s | 0.5 MiB | 2.5 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 16 m | 19 m | 288 MiB | 309 MiB | 45.1 KiB/s | 2.0 KiB/s | 40.3 MiB | 1.8 MiB | monitoring |
| grafana | 1 | 15 m | 18 m | 434 MiB | 439 MiB | 7.6 KiB/s | 2.2 KiB/s | 6.8 MiB | 1.9 MiB | monitoring |
| loki | 1 | 8 m | 10 m | 158 MiB | 160 MiB | 0.8 KiB/s | 1.9 KiB/s | 0.7 MiB | 1.7 MiB | monitoring |
| alloy | 1 | 11 m | 13 m | 73 MiB | 74 MiB | 0.2 KiB/s | 1.0 KiB/s | 0.2 MiB | 0.9 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 1 m | 2 m | 8 MiB | 9 MiB | 3.4 KiB/s | 2.0 KiB/s | 3.0 MiB | 1.8 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 5 m | 21 MiB | 26 MiB | 7.5 KiB/s | 16.9 KiB/s | 6.7 MiB | 15.1 MiB | monitoring |
| node-exporter | 1 | 2 m | 3 m | 10 MiB | 12 MiB | 12.6 KiB/s | 56.6 KiB/s | 11.3 MiB | 50.6 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 4 m | 22 m | 26 MiB | 27 MiB | 1.6 KiB/s | 1.3 KiB/s | 1.4 MiB | 1.1 MiB | monitoring |
| kubernetes | 8 | 113 m | 207 m | 840 MiB | 981 MiB | 74.2 KiB/s | 332.4 KiB/s | 66.3 MiB | 297.0 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 0.24 cores average, 0.40 peak (of 6)
- Memory: 3,500 MiB average, 3,629 MiB peak (of 4,909 MiB)
- Disk writes: 112.4 KiB/s average, 810.9 KiB/s peak; 11.8 IOPS average, 35.5 IOPS peak
- Disk reads: 81.5 KiB/s average, 3.6 IOPS average

## External traffic (through Traefik)

- Requests: 0.2 /s average, 2.1 /s peak, 97 in total, – answered with 5xx
- Latency: p50 50 ms, p95 95 ms, p99 99 ms
- In: 0.0 KiB/s average (0.0 MiB total); out: 0.3 KiB/s average, 2.5 KiB/s peak (0.2 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| traefik-metrics | 0.2 | 97 | 2,098 B | 95 ms |

## Database

- Transactions: 2.2 /s average, 2.2 /s peak
- Statements: 1.6 /s, mean execution time 0.247 ms
- Rows read: 99.7 /s; rows written: 0.0 /s
- Connections: 2.0 average, 2 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 7.6 MiB → 7.6 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 10.7 MiB → 23.2 MiB (50.04 MiB/h); 42,469 series, 2,654.2 samples/s
- Loki: 0.26 MiB of log lines received (1,893 lines), 1.05 MiB/h

On-disk size (du) at the end: postgres 62.8 MiB, prometheus 22.9 MiB, loki 0.8 MiB
