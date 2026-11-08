# 02-db-benchmark

2026-11-08 23:50:50 – 23:55:50 (5 min, 15 s samples)

pgbench, 16 clients, scale 20, against a separate database: the database's own capacity on this VM, not the app's workload.

## Resources per component

| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |
|---|---|---|---|---|---|---|---|---|---|---|
| traefik | 1 | 1 m | 2 m | 27 MiB | 28 MiB | 0.8 KiB/s | 0.9 KiB/s | 0.3 MiB | 0.3 MiB | ingress (cloud: load balancer) |
| postgres | 1 | 1,712 m | 1,965 m | 481 MiB | 554 MiB | 0.7 KiB/s | 3.6 KiB/s | 0.2 MiB | 1.1 MiB | database (cloud: RDS / Cloud SQL) |
| prometheus | 1 | 15 m | 19 m | 315 MiB | 322 MiB | 46.8 KiB/s | 2.1 KiB/s | 14.4 MiB | 0.6 MiB | monitoring |
| grafana | 1 | 13 m | 17 m | 433 MiB | 440 MiB | 7.0 KiB/s | 3.5 KiB/s | 2.1 MiB | 1.1 MiB | monitoring |
| loki | 1 | 7 m | 8 m | 158 MiB | 160 MiB | 0.8 KiB/s | 1.9 KiB/s | 0.3 MiB | 0.6 MiB | monitoring |
| alloy | 1 | 7 m | 10 m | 70 MiB | 74 MiB | 0.2 KiB/s | 1.0 KiB/s | 0.0 MiB | 0.3 MiB | every node (DaemonSet) |
| postgres-exporter | 1 | 1 m | 2 m | 9 MiB | 9 MiB | 3.6 KiB/s | 2.1 KiB/s | 1.1 MiB | 0.6 MiB | monitoring |
| kube-state-metrics | 1 | 1 m | 1 m | 20 MiB | 20 MiB | 0.6 KiB/s | 16.9 KiB/s | 0.2 MiB | 5.2 MiB | monitoring |
| node-exporter | 1 | 2 m | 3 m | 10 MiB | 11 MiB | 4.4 KiB/s | 33.4 KiB/s | 1.4 MiB | 10.3 MiB | every node (DaemonSet) |
| prometheus-operator | 1 | 3 m | 4 m | 25 MiB | 26 MiB | 0.7 KiB/s | 1.2 KiB/s | 0.2 MiB | 0.4 MiB | monitoring |
| kubernetes | 8 | 96 m | 113 m | 821 MiB | 833 MiB | 28.6 KiB/s | 202.2 KiB/s | 8.8 MiB | 62.2 MiB | control plane (managed in the cloud) |

## Node (the Minikube VM)

- CPU: 1.97 cores average, 2.15 peak (of 6)
- Memory: 3,662 MiB average, 3,702 MiB peak (of 4,909 MiB)
- Disk writes: 30,205.9 KiB/s average, 40,034.6 KiB/s peak; 3,420.5 IOPS average, 3,969.8 IOPS peak
- Disk reads: 387.2 KiB/s average, 20.0 IOPS average

## External traffic (through Traefik)

- Requests: 0.3 /s average, 2.7 /s peak, 82 in total, – answered with 5xx
- Latency: p50 –, p95 –, p99 –
- In: 0.0 KiB/s average (0.0 MiB total); out: 0.3 KiB/s average, 3.7 KiB/s peak (0.1 MiB total)

| Service | Requests/s avg | Requests | Bytes per response | p95 |
|---|---|---|---|---|
| traefik-metrics | 0.3 | 82 | 1,370 B | – |

## Database

- Transactions: 2,665.8 /s average, 2,960.4 /s peak
- Statements: 20,203.4 /s, mean execution time 0.134 ms
- Rows read: 9,547.8 /s; rows written: 10,729.4 /s
- Connections: 15.4 average, 17 peak; cache hit ratio 96.77 %

## Storage growth

- PostgreSQL database: 263.9 MiB → 358.1 MiB (1,129.50 MiB/h)
- Prometheus TSDB + WAL: 23.7 MiB → 28.2 MiB (53.83 MiB/h); 42,696 series, 2,800.3 samples/s
- Loki: 0.08 MiB of log lines received (618 lines), 0.97 MiB/h

On-disk size (du) at the end: postgres 1,189.9 MiB, prometheus 27.7 MiB, loki 0.9 MiB
