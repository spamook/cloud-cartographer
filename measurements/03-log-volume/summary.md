# 03-log-volume

2026-11-09 00:09:14 – 00:24:14 (15 min, 15 s samples)

Log generator at ~300 JSON lines/s through Alloy into Loki for 15 minutes: Loki's and Alloy's cost per MB/s of logs.

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 0 m | 2 m | 39 MiB | 46 MiB | 0.4 KiB/s | 0.4 KiB/s | 0.4 MiB | 0.4 MiB | ingress (cloud: load balancer) |
| postgres | 1 | 13 m | 14 m | 340 MiB | 355 MiB | 0.7 KiB/s | 3.5 KiB/s | 0.6 MiB | 3.2 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 16 m | 20 m | 327 MiB | 333 MiB | 47.9 KiB/s | 1.9 KiB/s | 42.8 MiB | 1.7 MiB | monitoring |
| grafana | 1 | 15 m | 17 m | 448 MiB | 452 MiB | 7.8 KiB/s | 3.7 KiB/s | 7.0 MiB | 3.3 MiB | monitoring |
| loki | 1 | 10 m | 11 m | 185 MiB | 195 MiB | 9.7 KiB/s | 2.1 KiB/s | 8.7 MiB | 1.9 MiB | monitoring |
| alloy | 1 | 16 m | 17 m | 80 MiB | 82 MiB | 0.3 KiB/s | 9.9 KiB/s | 0.3 MiB | 8.9 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 1 m | 2 m | 10 MiB | 11 MiB | 3.8 KiB/s | 2.2 KiB/s | 3.4 MiB | 2.0 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 1 m | 20 MiB | 21 MiB | 0.7 KiB/s | 17.1 KiB/s | 0.6 MiB | 15.3 MiB | monitoring |
| node-exporter | 1 | 2 m | 3 m | 10 MiB | 12 MiB | 6.7 KiB/s | 35.1 KiB/s | 6.0 MiB | 31.3 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 3 m | 4 m | 26 MiB | 27 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.6 MiB | 1.1 MiB | monitoring |
| kubernetes | 8 | 102 m | 117 m | 828 MiB | 851 MiB | 41.6 KiB/s | 211.7 KiB/s | 37.2 MiB | 189.2 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 0.27 cores average, 0.29 peak (of 6)
- Memory: 3,718 MiB average, 3,748 MiB peak (of 4,909 MiB)
- Disk writes: 213.4 KiB/s average, 377.7 KiB/s peak; 11.9 IOPS average, 24.0 IOPS peak
- Disk reads: 35.8 KiB/s average, 2.1 IOPS average

## External traffic (through Traefik)

- Requests: 0.0 /s average, 0.0 /s peak, 0 in total, – answered with 5xx
- Latency: p50 –, p95 –, p99 –
- In: 0.0 KiB/s average (0.0 MiB total); out: 0.0 KiB/s average, 2.4 KiB/s peak (0.0 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| monitoring-kps-grafana-80@kubernetes | 0.0 | 0 | – | – |
| monitoring-kps-prometheus-9090@kubernetes | 0.0 | 0 | – | – |

## Database

- Transactions: 2.4 /s average, 2.4 /s peak
- Statements: 1.7 /s, mean execution time 0.285 ms
- Rows read: 99.7 /s; rows written: 0.0 /s
- Connections: 2.0 average, 2 peak; cache hit ratio 100.00 %

## Storage growth

- PostgreSQL database: 7.6 MiB → 7.6 MiB (0.00 MiB/h)
- Prometheus TSDB + WAL: 40.2 MiB → 84.4 MiB (176.98 MiB/h); 43,733 series, 2,839.4 samples/s
- Loki: 41.33 MiB of log lines received (262,586 lines), 165.34 MiB/h

On-disk size (du) at the end: postgres 1,205.1 MiB, prometheus 61.6 MiB, loki 22.1 MiB

## Loki chunks stored during the run (after a flush)

- Compression ratio (mean of stored chunks): 6.081285087409951
- Chunks stored: 18.47628823432928; compressed bytes stored: 5122846.523291657; raw log bytes received: 45411744.87695702
