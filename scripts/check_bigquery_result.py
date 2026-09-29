#!/usr/bin/env python3
"""Bloquer un résultat BigQuery divergent de la référence locale."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = (
    "source_rows", "future_rows_excluded", "rows_until_as_of", "rows_ytd",
    "reservation_count", "cancellation_count", "gross_reservations_centimes",
    "cancellations_centimes", "net_centimes",
)
QUALITY = (
    "duplicate_event_ids", "empty_event_ids", "invalid_dates", "invalid_amounts",
    "invalid_signs_or_types", "invalid_source_months", "foreign_release_rows",
    "missing_or_invalid_dimensions",
)


def check(actual, reference):
    problems = []
    for field in QUALITY:
        if int(actual[field]) != 0:
            problems.append(f"{field} = {actual[field]} au lieu de 0")
    for field in COUNTS:
        if int(actual[field]) != int(reference[field]):
            problems.append(f"{field} = {actual[field]} au lieu de {reference[field]}")
    for field, key, expected_key in (
        ("by_month", "month", "by_month_centimes"),
        ("by_region", "region", "by_region_centimes"),
    ):
        values = {row[key]: int(row["net_centimes"]) for row in actual[field]}
        if values != reference[expected_key]:
            problems.append(f"{field} : ventilation différente de la référence")
    if problems:
        raise ValueError("BLOQUER LA PUBLICATION :\n" + "\n".join(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="Sortie JSON de bq query --format=json")
    parser.add_argument(
        "--reference", type=Path, default=ROOT / "results/ca_comite_2026-09-27.json"
    )
    args = parser.parse_args()
    payload = json.loads(args.result.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) != 1:
        parser.error("résultat BigQuery attendu : tableau JSON contenant une seule ligne")
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    try:
        check(payload[0], reference)
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(str(exc)) from None
    print("PASS : contrôles qualité et KPI BigQuery réconciliés au centime")


if __name__ == "__main__":
    main()
