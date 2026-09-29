#!/usr/bin/env python3
"""Calculer la référence locale du KPI réservations nettes YTD."""

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as source:
        yield from csv.DictReader(source)


def calculate(data, as_of, release_id):
    lots = {r["lot_id"]: r for r in read_rows(data / "dim_lot.csv")}
    programmes = {r["programme_id"]: r for r in read_rows(data / "dim_programme.csv")}
    totals = Counter()
    month_net = Counter()
    region_net = Counter()
    types = Counter()
    all_ids = set()
    errors = []
    start = as_of.replace(month=1, day=1)

    for row in read_rows(data / "fact_ventes.csv"):
        totals["source_rows"] += 1
        event_id = row["evenement_id"]
        if event_id in all_ids:
            errors.append(f"événement dupliqué : {event_id}")
        all_ids.add(event_id)
        try:
            day = date.fromisoformat(row["date_evenement"])
            amount = int(row["montant_centimes"])
        except ValueError:
            errors.append(f"date ou montant invalide : {event_id}")
            continue
        kind = row["type_evenement"]
        if kind not in {"RESERVATION", "ANNULATION"} or (
            kind == "RESERVATION" and amount <= 0
        ) or (kind == "ANNULATION" and amount >= 0):
            errors.append(f"type ou signe invalide : {event_id}")
        if row["source_lot"] != f"VENTE_{day:%Y%m}":
            errors.append(f"lot source incohérent : {event_id}")
        if row["release_id"] != release_id:
            errors.append(f"release étrangère : {event_id}")
        lot = lots.get(row["lot_id"])
        if lot is None or lot["mode_commercialisation"] != "VENTE":
            errors.append(f"lot de vente absent ou incorrect : {event_id}")
            continue
        programme = programmes.get(lot["programme_id"])
        if programme is None:
            errors.append(f"programme absent : {event_id}")
            continue
        if day > as_of:
            totals["future_rows_excluded"] += 1
            continue
        totals["rows_until_as_of"] += 1
        if day < start:
            continue
        totals["rows_ytd"] += 1
        totals["net_centimes"] += amount
        totals["gross_reservations_centimes"] += max(amount, 0)
        totals["cancellations_centimes"] += min(amount, 0)
        types[kind] += 1
        month_net[day.strftime("%Y-%m")] += amount
        region_net[programme["region_code"]] += amount

    if errors:
        raise ValueError("\n".join(errors[:20]) + (f"\n… {len(errors)-20} autres" if len(errors)>20 else ""))
    if totals["net_centimes"] != sum(month_net.values()) or totals["net_centimes"] != sum(region_net.values()):
        raise ValueError("réconciliation mois/régions en échec")
    if totals["net_centimes"] != totals["gross_reservations_centimes"] + totals["cancellations_centimes"]:
        raise ValueError("réconciliation réservations/annulations en échec")
    return {
        "synthetic": True,
        "kpi_code": "RESERVATIONS_NETTES_YTD",
        "label": "Réservations nettes 2026 à date",
        "grain": "événement commercial signé",
        "period_start": start.isoformat(),
        "as_of_inclusive": as_of.isoformat(),
        "release_id": release_id,
        "unit": "centimes EUR",
        "source_rows": totals["source_rows"],
        "future_rows_excluded": totals["future_rows_excluded"],
        "rows_until_as_of": totals["rows_until_as_of"],
        "rows_ytd": totals["rows_ytd"],
        "reservation_count": types["RESERVATION"],
        "cancellation_count": types["ANNULATION"],
        "gross_reservations_centimes": totals["gross_reservations_centimes"],
        "cancellations_centimes": totals["cancellations_centimes"],
        "net_centimes": totals["net_centimes"],
        "by_month_centimes": dict(sorted(month_net.items())),
        "by_region_centimes": dict(sorted(region_net.items())),
        "controls": {"references": "PASS", "signs": "PASS", "source_month": "PASS", "reconciliation": "PASS"},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--as-of", type=date.fromisoformat, required=True, help="YYYY-MM-DD, inclus")
    parser.add_argument("--out", type=Path, help="Fichier JSON optionnel")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "datasets/manifest.json").read_text(encoding="utf-8"))
    result = calculate(args.data, args.as_of, manifest["certified_release_id"])
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
