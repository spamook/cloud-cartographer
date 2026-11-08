"""Monthly cost of the cloud design on AWS and Google Cloud.

usage:
  python cost-model/calc.py           print the tables
  python cost-model/calc.py --write   also update docs/3-cost-analysis.md (between the markers)
                                      and cost-model/line-items.csv

Inputs: prices.toml (unit prices with their sources) and bom.toml (what runs where).
Standard library only (tomllib needs Python 3.11+).
"""
import argparse
import ast
import csv
import operator
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parent / "docs" / "3-cost-analysis.md"
START, END = "<!-- cost-model:start -->", "<!-- cost-model:end -->"
PROVIDERS = {"aws": "AWS (eu-north-1)", "gcp": "Google Cloud (europe-north1)"}
ENVS = ["shared", "test", "prod"]
CATEGORIES = ["compute", "kubernetes", "database", "storage", "network", "other"]
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.USub: operator.neg}
FUNCS = {"max": max, "min": min}


def evaluate(expr, names):
    """A number, or a formula over the names in bom.toml [params] / [derived]."""
    if isinstance(expr, (int, float)):
        return float(expr)

    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            return float(names[node.id])
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.operand))
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) in FUNCS:
            return FUNCS[node.func.id](*(ev(a) for a in node.args))
        raise ValueError(f"unsupported formula: {expr!r}")

    return ev(ast.parse(str(expr), mode="eval").body)


def load():
    with open(HERE / "prices.toml", "rb") as f:
        prices = tomllib.load(f)
    with open(HERE / "bom.toml", "rb") as f:
        bom = tomllib.load(f)
    names = dict(bom["params"])
    for key, formula in bom.get("derived", {}).items():
        names[key] = evaluate(formula, names)
    return prices, bom, names


def line_cost(provider, item, prices, names, optimised):
    key = item.get("opt_price", item["price"]) if optimised else item["price"]
    price = prices[provider][key]
    qty = evaluate(item.get("opt_qty", item["qty"]) if optimised else item["qty"], names)
    unit = price["unit"]
    if unit == "hour":
        hours = item.get("opt_hours", item.get("hours", "hours")) if optimised else item.get("hours", "hours")
        amount = price["price"] * evaluate(hours, names) * qty
        # a free-tier style credit never exceeds what it covers: handled by the negative "month" item
    elif unit == "year":
        amount = price["price"] / 12 * qty
    else:  # gb_month, gb, month, million, thousand
        amount = price["price"] * qty
    return amount, qty, price


def compute(prices, bom, names):
    rows = []
    for provider in PROVIDERS:
        for item in bom[provider]:
            od, qty, price = line_cost(provider, item, prices, names, optimised=False)
            opt, _, _ = line_cost(provider, item, prices, names, optimised=True)
            if item["price"] == "gke_free_tier":  # the credit covers the zonal cluster's fee, no more
                fee = prices[provider]["gke_cluster"]["price"] * names["hours"]
                od = opt = -min(fee, -price["price"])
            rows.append({"provider": provider, "env": item["env"], "category": item["category"],
                         "item": item["item"], "qty": qty, "unit_price": price["price"],
                         "unit": price["unit"], "on_demand": od, "optimised": opt,
                         "source": price["source"], "price_key": item["price"],
                         "opt_price_key": item.get("opt_price", item["price"])})
    return rows


def money(v):
    return f"${v:,.0f}" if abs(v) >= 10 else f"${v:,.2f}"


def total(rows, scenario, **filters):
    return sum(r[scenario] for r in rows if all(r[k] == v for k, v in filters.items()))


def tables(rows, names, prices):
    out = []
    # 1. totals
    out += ["### Monthly total", "",
            "| Provider | Scenario | Shared | Test | Prod | **Total / month** | Per year |",
            "|---|---|---|---|---|---|---|"]
    for p, label in PROVIDERS.items():
        for scenario, name in (("on_demand", "On-demand"), ("optimised", "Optimised")):
            envs = [total(rows, scenario, provider=p, env=e) for e in ENVS]
            t = sum(envs)
            out.append(f"| {label} | {name} | " + " | ".join(money(v) for v in envs)
                       + f" | **{money(t)}** | {money(t * 12)} |")
    out += ["", "*Optimised*: test on Spot capacity and scaled to zero outside working hours "
            f"({names['work_hours']:.0f} of {names['hours']:.0f} h), 1-year commitments for the always-on prod "
            "nodes, the prod database and the GitLab VM, a NAT instance instead of a NAT gateway in AWS test.", ""]

    # 2. by category
    for p, label in PROVIDERS.items():
        out += [f"### {label}: by component (on-demand)", "",
                "| Category | Shared | Test | Prod | Total | Share |", "|---|---|---|---|---|---|"]
        grand = total(rows, "on_demand", provider=p)
        for c in CATEGORIES:
            vals = [total(rows, "on_demand", provider=p, env=e, category=c) for e in ENVS]
            s = sum(vals)
            out.append(f"| {c} | " + " | ".join(money(v) for v in vals)
                       + f" | {money(s)} | {s / grand * 100:.0f}% |")
        out += [f"| **total** | " + " | ".join(money(total(rows, 'on_demand', provider=p, env=e)) for e in ENVS)
                + f" | **{money(grand)}** | 100% |", ""]

    # 3. line items
    for p, label in PROVIDERS.items():
        out += [f"### {label}: line items", "",
                "| Env | Category | Item | Quantity | Unit price | On-demand | Optimised |",
                "|---|---|---|---|---|---|---|"]
        for r in (r for r in rows if r["provider"] == p):
            unit = {"hour": "/h", "gb_month": "/GB-mo", "gb": "/GB", "month": "/mo", "year": "/yr",
                    "million": "/M", "thousand": "/1000"}[r["unit"]]
            qty = f"{r['qty']:,.2f}".rstrip("0").rstrip(".")
            out.append(f"| {r['env']} | {r['category']} | {r['item']} | {qty} "
                       f"| [${abs(r['unit_price']):g}{unit}]({r['source']}) | {money(r['on_demand'])} | {money(r['optimised'])} |")
        out.append("")

    # 4. log accumulation over the first year
    out += ["### Hidden cost: log accumulation over the first year (prod)", "",
            f"Loki receives {names['log_gb_day_prod']:g} GB of log lines a day and stores them compressed "
            f"(~{names['log_compression']:g}×); logs are kept {names['log_retention_days']:.0f} days, so the bucket "
            "grows every month until the first deletions start in month 13.", "",
            "| Month | Stored in the bucket | AWS S3 Standard | Cloud Storage Standard |", "|---|---|---|---|"]
    per_month = names["log_gb_day_prod"] * 30.4 / names["log_compression"]
    s3, gcs = prices["aws"]["s3_standard"]["price"], prices["gcp"]["gcs_standard"]["price"]
    cumulative = 0.0
    for month in (1, 2, 3, 6, 9, 12):
        stored = per_month * month
        out.append(f"| {month} | {stored:,.0f} GB | {money(stored * s3)} | {money(stored * gcs)} |")
    for month in range(1, 13):
        cumulative += per_month * month
    out += ["", f"Sum over the first 12 months: {money(cumulative * s3)} on AWS, {money(cumulative * gcs)} on Google "
            "Cloud. Moving chunks older than 30 days to an infrequent-access class would halve the storage price, "
            "but every query over old logs then pays a retrieval fee, so it pays off only for logs that are rarely read.", ""]
    return "\n".join(out)


def write_doc(text):
    doc = DOC.read_text(encoding="utf-8")
    if START not in doc or END not in doc:
        raise SystemExit(f"markers {START} / {END} not found in {DOC}")
    head, rest = doc.split(START, 1)
    _, tail = rest.split(END, 1)
    DOC.write_text(f"{head}{START}\n<!-- generated by cost-model/calc.py, do not edit by hand -->\n\n"
                   f"{text}\n{END}{tail}", encoding="utf-8", newline="\n")


def write_csv(rows):
    with open(HERE / "line-items.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, lineterminator="\n", fieldnames=["provider", "env", "category", "item", "qty", "unit", "unit_price",
                                          "on_demand", "optimised", "price_key", "opt_price_key", "source"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "on_demand": round(r["on_demand"], 2), "optimised": round(r["optimised"], 2)})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    prices, bom, names = load()
    rows = compute(prices, bom, names)
    text = tables(rows, names, prices)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(text)
    if args.write:
        write_doc(text)
        write_csv(rows)


if __name__ == "__main__":
    main()
