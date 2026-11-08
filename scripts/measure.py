"""Collects the baseline numbers of one test window from Prometheus.

usage:
  python scripts/measure.py --name idle --last 15m
  python scripts/measure.py --name step-1000 --start 2026-11-09T01:10:00 --end 2026-11-09T01:20:00

Writes measurements/<name>/summary.json, summary.md and samples.csv (one row per 15 s).
Standard library only, so it runs with any Python 3.11+.
"""
import argparse
import csv
import json
import math
import re
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

STEP = 15  # seconds, same as the scrape interval

# component, namespace, pod regex, where it runs in the cloud design
COMPONENTS = [
    ("traefik", "ingress", "traefik-.*", "ingress (cloud: load balancer)"),
    ("frontend", "app", "frontend-.*", "main"),
    ("backend", "app", "backend-.*", "main"),
    ("postgres", "app", "postgres-.*", "database (cloud: RDS / Cloud SQL)"),
    ("prometheus", "monitoring", "prometheus-kps-prometheus-.*", "monitoring"),
    ("grafana", "monitoring", "kps-grafana-.*", "monitoring"),
    ("loki", "monitoring", "loki-[0-9]+", "monitoring"),
    ("alloy", "monitoring", "alloy-.*", "every node (DaemonSet)"),
    ("postgres-exporter", "monitoring", "postgres-exporter-.*", "monitoring"),
    ("kube-state-metrics", "monitoring", "kps-kube-state-metrics-.*", "monitoring"),
    ("node-exporter", "monitoring", "kps-prometheus-node-exporter-.*", "every node (DaemonSet)"),
    ("prometheus-operator", "monitoring", "kps-operator-.*", "monitoring"),
    ("kubernetes", "kube-system", ".*", "control plane (managed in the cloud)"),
]


class Prometheus:
    def __init__(self, url):
        self.url = url.rstrip("/")

    def _get(self, path, params):
        query = urllib.parse.urlencode(params)
        with urllib.request.urlopen(f"{self.url}/api/v1/{path}?{query}", timeout=120) as resp:
            data = json.load(resp)
        if data.get("status") != "success":
            raise RuntimeError(f"{path} {params}: {data}")
        return data["data"]["result"]

    def range(self, expr, start, end):
        """One series (the expression should aggregate): list of (ts, value)."""
        result = self._get("query_range", {"query": expr, "start": start, "end": end, "step": STEP})
        if not result:
            return []
        return [(float(t), float(v)) for t, v in result[0]["values"] if not math.isnan(float(v))]

    def range_by(self, expr, label, start, end):
        """Several series keyed by one label: {label value: [(ts, value)]}."""
        result = self._get("query_range", {"query": expr, "start": start, "end": end, "step": STEP})
        return {r["metric"].get(label, "?"): [(float(t), float(v)) for t, v in r["values"]]
                for r in result}

    def value(self, expr, at):
        result = self._get("query", {"query": expr, "time": at})
        if not result:
            return None
        v = float(result[0]["value"][1])
        return None if math.isnan(v) else v


def stats(points):
    vals = [v for _, v in points]
    if not vals:
        return {"avg": None, "peak": None}
    return {"avg": statistics.fmean(vals), "peak": max(vals)}


def total(points):
    """Integral of a per-second rate over the window (bytes, requests...)."""
    return sum(v for _, v in points) * STEP if points else None


def parse_time(text):
    if re.fullmatch(r"\d+(\.\d+)?", text):
        return float(text)
    return datetime.fromisoformat(text).timestamp()


def parse_duration(text):
    m = re.fullmatch(r"(\d+)([smh])", text)
    if not m:
        raise SystemExit(f"bad duration {text!r}, use e.g. 15m")
    return int(m.group(1)) * {"s": 1, "m": 60, "h": 3600}[m.group(2)]


def sel(ns, pod):
    return f'namespace="{ns}",pod=~"{pod}"'


def collect(prom, start, end, database="app"):
    window = f"{int(end - start)}s"
    out = {"start": start, "end": end, "seconds": end - start, "components": {}, "samples": {}}

    # --- per component: CPU, memory, network, container file system I/O
    for name, ns, pod, placement in COMPONENTS:
        s = sel(ns, pod)
        cpu = prom.range(f'sum(rate(container_cpu_usage_seconds_total{{{s},container!=""}}[1m]))', start, end)
        mem = prom.range(f'sum(container_memory_working_set_bytes{{{s},container!=""}})', start, end)
        rx = prom.range(f'sum(rate(container_network_receive_bytes_total{{{s}}}[1m]))', start, end)
        tx = prom.range(f'sum(rate(container_network_transmit_bytes_total{{{s}}}[1m]))', start, end)
        fs_w = prom.range(f'sum(rate(container_fs_writes_bytes_total{{{s}}}[1m]))', start, end)
        fs_r = prom.range(f'sum(rate(container_fs_reads_bytes_total{{{s}}}[1m]))', start, end)
        if not cpu and not mem:
            continue  # not deployed in this run
        pods = prom.value(f'count(kube_pod_info{{{s}}})', end) or 0
        out["components"][name] = {
            "placement": placement,
            "pods": int(pods),
            "cpu_cores": stats(cpu),
            "memory_bytes": stats(mem),
            "net_rx_bytes_per_s": stats(rx),
            "net_tx_bytes_per_s": stats(tx),
            "net_rx_bytes": total(rx),
            "net_tx_bytes": total(tx),
            "fs_write_bytes_per_s": stats(fs_w),
            "fs_read_bytes_per_s": stats(fs_r),
        }
        out["samples"][name] = {"cpu": cpu, "mem": mem}

    # --- the node (one VM): CPU, memory, disk
    node_cpu = prom.range('sum(rate(node_cpu_seconds_total{mode!="idle"}[1m]))', start, end)
    cores = prom.value('count(node_cpu_seconds_total{mode="idle"})', end)
    out["node"] = {
        "cores": cores,
        "cpu_cores_used": stats(node_cpu),
        "memory_used_bytes": stats(prom.range(
            "sum(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)", start, end)),
        "memory_total_bytes": prom.value("sum(node_memory_MemTotal_bytes)", end),
        "disk_write_bytes_per_s": stats(prom.range('sum(rate(node_disk_written_bytes_total{device!~"dm-.*"}[1m]))', start, end)),
        "disk_read_bytes_per_s": stats(prom.range('sum(rate(node_disk_read_bytes_total{device!~"dm-.*"}[1m]))', start, end)),
        "disk_write_iops": stats(prom.range('sum(rate(node_disk_writes_completed_total{device!~"dm-.*"}[1m]))', start, end)),
        "disk_read_iops": stats(prom.range('sum(rate(node_disk_reads_completed_total{device!~"dm-.*"}[1m]))', start, end)),
    }

    # --- external traffic: everything that enters through Traefik (the load balancer's role)
    req = prom.range('sum(rate(traefik_entrypoint_requests_total{entrypoint="web"}[1m]))', start, end)
    bytes_in = prom.range('sum(rate(traefik_entrypoint_requests_bytes_total{entrypoint="web"}[1m]))', start, end)
    bytes_out = prom.range('sum(rate(traefik_entrypoint_responses_bytes_total{entrypoint="web"}[1m]))', start, end)
    lat = {}
    for q in (0.5, 0.95, 0.99):
        lat[f"p{int(q * 100)}"] = prom.value(
            f'histogram_quantile({q}, sum by (le) (increase(traefik_entrypoint_request_duration_seconds_bucket{{entrypoint="web"}}[{window}])))',
            end)
    errors = prom.value(
        f'sum(increase(traefik_entrypoint_requests_total{{entrypoint="web",code=~"5.."}}[{window}]))', end)
    # Traefik's own `service` label is renamed to `exported_service`: the scrape target's Service
    # name takes `service`
    services = {}
    for svc, points in prom.range_by(
            'sum by (exported_service) (rate(traefik_service_requests_total[1m]))', "exported_service",
            start, end).items():
        svc_out = prom.range(
            f'sum(rate(traefik_service_responses_bytes_total{{exported_service="{svc}"}}[1m]))', start, end)
        svc_lat = prom.value(
            f'histogram_quantile(0.95, sum by (le) (increase(traefik_service_request_duration_seconds_bucket{{exported_service="{svc}"}}[{window}])))',
            end)
        reqs = total(points) or 0
        services[svc] = {
            "requests_per_s": stats(points),
            "requests": reqs,
            "response_bytes": total(svc_out),
            "bytes_per_response": (total(svc_out) or 0) / reqs if reqs else None,
            "latency_p95_s": svc_lat,
        }
    out["external"] = {
        "requests_per_s": stats(req),
        "requests": total(req),
        "errors_5xx": errors,
        "bytes_in_per_s": stats(bytes_in),
        "bytes_out_per_s": stats(bytes_out),
        "bytes_in": total(bytes_in),
        "bytes_out": total(bytes_out),
        "latency_s": lat,
        "services": services,
    }

    # --- the database
    db = f'datname="{database}"'
    tps = prom.range(f'sum(rate(pg_stat_database_xact_commit{{{db}}}[1m]) + rate(pg_stat_database_xact_rollback{{{db}}}[1m]))', start, end)
    calls = prom.value(f'sum(increase(pg_stat_statements_calls_total{{{db}}}[{window}]))', end)
    secs = prom.value(f'sum(increase(pg_stat_statements_seconds_total{{{db}}}[{window}]))', end)
    hit = prom.value(f'sum(increase(pg_stat_database_blks_hit{{{db}}}[{window}]))', end)
    read = prom.value(f'sum(increase(pg_stat_database_blks_read{{{db}}}[{window}]))', end)
    size_start = prom.value(f'pg_database_size_bytes{{{db}}}', start)
    size_end = prom.value(f'pg_database_size_bytes{{{db}}}', end)
    out["database"] = {
        "transactions_per_s": stats(tps),
        "statements": calls,
        "statements_per_s": calls / (end - start) if calls else None,
        "mean_statement_ms": secs / calls * 1000 if calls else None,
        "rows_fetched_per_s": stats(prom.range(f'sum(rate(pg_stat_database_tup_fetched{{{db}}}[1m]))', start, end)),
        "rows_written_per_s": stats(prom.range(
            f'sum(rate(pg_stat_database_tup_inserted{{{db}}}[1m]) + rate(pg_stat_database_tup_updated{{{db}}}[1m]) + rate(pg_stat_database_tup_deleted{{{db}}}[1m]))',
            start, end)),
        "connections": stats(prom.range(f'sum(pg_stat_database_numbackends{{{db}}})', start, end)),
        "cache_hit_ratio": hit / (hit + read) if hit is not None and read is not None and hit + read > 0 else None,
        "size_start_bytes": size_start,
        "size_end_bytes": size_end,
    }

    # --- storage that grows: database, metrics, logs
    def at_both(expr):
        return prom.value(expr, start), prom.value(expr, end)

    tsdb = "sum(prometheus_tsdb_storage_blocks_bytes) + sum(prometheus_tsdb_wal_storage_size_bytes)"
    out["storage"] = {
        "postgres_bytes": [size_start, size_end],
        "prometheus_tsdb_bytes": list(at_both(tsdb)),
        "prometheus_head_series": prom.value("sum(prometheus_tsdb_head_series)", end),
        "prometheus_samples_per_s": prom.value(
            f"sum(rate(prometheus_tsdb_head_samples_appended_total[{window}]))", end),
        "loki_ingested_bytes": prom.value(f"sum(increase(loki_distributor_bytes_received_total[{window}]))", end),
        "loki_ingested_lines": prom.value(f"sum(increase(loki_distributor_lines_received_total[{window}]))", end),
    }
    return out


def disk_usage():
    """Bytes on disk of each PersistentVolume. Minikube's volumes are directories on the node
    (no kubelet volume stats), and the Prometheus and Loki images have no `du`, so measure there."""
    names = {"data-postgres-0": "postgres", "storage-loki-0": "loki"}
    try:
        text = subprocess.run(
            ["minikube", "-p", "cloud-cartographer", "ssh", "--", "sudo du -sk /tmp/hostpath-provisioner/*/*"],
            capture_output=True, text=True, timeout=120, check=True).stdout
    except subprocess.SubprocessError:
        return {}
    result = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        pvc = parts[1].rsplit("/", 1)[-1]
        name = names.get(pvc, "prometheus" if pvc.startswith("prometheus-") else pvc)
        result[name] = int(parts[0]) * 1024
    return result


def fmt(v, unit="", scale=1.0, digits=1):
    if v is None:
        return "–"
    return f"{v / scale:,.{digits}f}{unit}"


def write_report(out, folder):
    mib, kib = 1024 ** 2, 1024
    lines = [f"# {out['name']}", "",
             f"{datetime.fromtimestamp(out['start']):%Y-%m-%d %H:%M:%S} – "
             f"{datetime.fromtimestamp(out['end']):%H:%M:%S} ({out['seconds'] / 60:.0f} min, {STEP} s samples)", ""]
    if out.get("note"):
        lines += [out["note"], ""]
    lines += ["## Resources per component", "",
              "| Component | Pods | CPU avg | CPU peak | RAM avg | RAM peak | Net in avg | Net out avg | Net in total | Net out total | Placement |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, c in out["components"].items():
        lines.append(
            f"| {name} | {c['pods']} | {fmt(c['cpu_cores']['avg'], ' m', 0.001, 0)} | {fmt(c['cpu_cores']['peak'], ' m', 0.001, 0)} "
            f"| {fmt(c['memory_bytes']['avg'], ' MiB', mib, 0)} | {fmt(c['memory_bytes']['peak'], ' MiB', mib, 0)} "
            f"| {fmt(c['net_rx_bytes_per_s']['avg'], ' KiB/s', kib)} | {fmt(c['net_tx_bytes_per_s']['avg'], ' KiB/s', kib)} "
            f"| {fmt(c['net_rx_bytes'], ' MiB', mib)} | {fmt(c['net_tx_bytes'], ' MiB', mib)} | {c['placement']} |")
    n = out["node"]
    lines += ["", "## Node (the Minikube VM)", "",
              f"- CPU: {fmt(n['cpu_cores_used']['avg'], '', 1, 2)} cores average, {fmt(n['cpu_cores_used']['peak'], '', 1, 2)} peak (of {fmt(n['cores'], '', 1, 0)})",
              f"- Memory: {fmt(n['memory_used_bytes']['avg'], ' MiB', mib, 0)} average, {fmt(n['memory_used_bytes']['peak'], ' MiB', mib, 0)} peak (of {fmt(n['memory_total_bytes'], ' MiB', mib, 0)})",
              f"- Disk writes: {fmt(n['disk_write_bytes_per_s']['avg'], ' KiB/s', kib)} average, {fmt(n['disk_write_bytes_per_s']['peak'], ' KiB/s', kib)} peak; "
              f"{fmt(n['disk_write_iops']['avg'], ' IOPS')} average, {fmt(n['disk_write_iops']['peak'], ' IOPS')} peak",
              f"- Disk reads: {fmt(n['disk_read_bytes_per_s']['avg'], ' KiB/s', kib)} average, {fmt(n['disk_read_iops']['avg'], ' IOPS')} average"]
    e = out["external"]
    lines += ["", "## External traffic (through Traefik)", "",
              f"- Requests: {fmt(e['requests_per_s']['avg'], ' /s')} average, {fmt(e['requests_per_s']['peak'], ' /s')} peak, "
              f"{fmt(e['requests'], '', 1, 0)} in total, {fmt(e['errors_5xx'], '', 1, 0)} answered with 5xx",
              f"- Latency: p50 {fmt(e['latency_s']['p50'], ' ms', 0.001, 0)}, p95 {fmt(e['latency_s']['p95'], ' ms', 0.001, 0)}, p99 {fmt(e['latency_s']['p99'], ' ms', 0.001, 0)}",
              f"- In: {fmt(e['bytes_in_per_s']['avg'], ' KiB/s', kib)} average ({fmt(e['bytes_in'], ' MiB', mib)} total); "
              f"out: {fmt(e['bytes_out_per_s']['avg'], ' KiB/s', kib)} average, {fmt(e['bytes_out_per_s']['peak'], ' KiB/s', kib)} peak ({fmt(e['bytes_out'], ' MiB', mib)} total)"]
    if e["services"]:
        lines += ["", "| Service | Requests/s avg | Requests | Bytes per response | p95 |", "|---|---|---|---|---|"]
        for svc, s in e["services"].items():
            lines.append(f"| {svc} | {fmt(s['requests_per_s']['avg'])} | {fmt(s['requests'], '', 1, 0)} "
                         f"| {fmt(s['bytes_per_response'], ' B', 1, 0)} | {fmt(s['latency_p95_s'], ' ms', 0.001, 0)} |")
    d = out["database"]
    lines += ["", "## Database", "",
              f"- Transactions: {fmt(d['transactions_per_s']['avg'], ' /s')} average, {fmt(d['transactions_per_s']['peak'], ' /s')} peak",
              f"- Statements: {fmt(d['statements_per_s'], ' /s')}, mean execution time {fmt(d['mean_statement_ms'], ' ms', 1, 3)}",
              f"- Rows read: {fmt(d['rows_fetched_per_s']['avg'], ' /s')}; rows written: {fmt(d['rows_written_per_s']['avg'], ' /s')}",
              f"- Connections: {fmt(d['connections']['avg'])} average, {fmt(d['connections']['peak'], '', 1, 0)} peak; "
              f"cache hit ratio {fmt(d['cache_hit_ratio'] and d['cache_hit_ratio'] * 100, ' %', 1, 2)}"]
    st, hours = out["storage"], out["seconds"] / 3600

    def growth(pair):
        if not pair or None in pair:
            return "–"
        return f"{fmt(pair[0], ' MiB', mib)} → {fmt(pair[1], ' MiB', mib)} ({fmt((pair[1] - pair[0]) / hours, ' MiB/h', mib, 2)})"

    lines += ["", "## Storage growth", "",
              f"- PostgreSQL database: {growth(st['postgres_bytes'])}",
              f"- Prometheus TSDB + WAL: {growth(st['prometheus_tsdb_bytes'])}; {fmt(st['prometheus_head_series'], '', 1, 0)} series, "
              f"{fmt(st['prometheus_samples_per_s'], ' samples/s')}",
              f"- Loki: {fmt(st['loki_ingested_bytes'], ' MiB', mib, 2)} of log lines received ({fmt(st['loki_ingested_lines'], ' lines', 1, 0)}), "
              f"{fmt(st['loki_ingested_bytes'] and st['loki_ingested_bytes'] / hours, ' MiB/h', mib, 2)}"]
    if out.get("disk_usage"):
        du = out["disk_usage"]
        lines += ["", "On-disk size (du) at the end: " + ", ".join(f"{k} {fmt(v, ' MiB', mib)}" for k, v in du.items())]

    # what one unit of traffic costs: the numbers that scale the baseline to other loads
    rps = e["requests_per_s"]["avg"] or 0
    if rps >= 1:
        lines += ["", f"## Cost per unit of traffic (at {rps:,.1f} requests/s)", "",
                  "| Component | CPU per 100 requests/s | Network out per request |", "|---|---|---|"]
        for name in ("traefik", "frontend", "backend", "postgres", "loki", "alloy", "prometheus"):
            c = out["components"].get(name)
            if not c or c["cpu_cores"]["avg"] is None:
                continue
            lines.append(f"| {name} | {fmt(c['cpu_cores']['avg'] / rps * 100, ' m', 0.001, 0)} "
                         f"| {fmt((c['net_tx_bytes_per_s']['avg'] or 0) / rps, ' B', 1, 0)} |")
        lines += ["", f"- Egress per request: {fmt((e['bytes_out_per_s']['avg'] or 0) / rps, ' B', 1, 0)}; "
                  f"log bytes per request: {fmt((st['loki_ingested_bytes'] or 0) / (e['requests'] or 1), ' B', 1, 0)}"]
    (folder / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_samples(out, folder):
    names = list(out["samples"])
    by_ts = {}
    for name in names:
        for kind in ("cpu", "mem"):
            for ts, v in out["samples"][name][kind]:
                by_ts.setdefault(ts, {})[f"{name}_{kind}"] = v
    with open(folder / "samples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        cols = [f"{n}_{k}" for n in names for k in ("cpu", "mem")]
        w.writerow(["time"] + cols)
        for ts in sorted(by_ts):
            w.writerow([datetime.fromtimestamp(ts).isoformat(timespec="seconds")] + [by_ts[ts].get(c, "") for c in cols])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--prom", default=None, help="Prometheus URL (default: http://<minikube ip>/prometheus)")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--last", help="window ending now, e.g. 15m")
    ap.add_argument("--note", help="one line printed under the title")
    ap.add_argument("--db", default="app", help="database whose statistics to report (default: app)")
    ap.add_argument("--no-du", action="store_true", help="skip the on-disk size probes")
    args = ap.parse_args()

    if args.last:
        end = time.time()
        start = end - parse_duration(args.last)
    else:
        start, end = parse_time(args.start), parse_time(args.end)
    url = args.prom
    if not url:
        ip = subprocess.run(["minikube", "-p", "cloud-cartographer", "ip"], capture_output=True,
                            text=True, check=True).stdout.strip()
        url = f"http://{ip}/prometheus"

    out = collect(Prometheus(url), start, end, args.db)
    out["name"], out["note"] = args.name, args.note
    if not args.no_du:
        out["disk_usage"] = disk_usage()
    folder = Path(__file__).resolve().parent.parent / "measurements" / args.name
    folder.mkdir(parents=True, exist_ok=True)
    write_samples(out, folder)
    out.pop("samples")
    (folder / "summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8", newline="\n")
    write_report(out, folder)
    # the Windows console is not UTF-8 by default
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print((folder / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
