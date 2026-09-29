#!/usr/bin/env python3
"""Rendre la requête avec un project ID contrôlé, sans autre interpolation."""

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", re.ASCII)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id", help="ID GCP, pas le nom d'affichage")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not PROJECT_ID.fullmatch(args.project_id):
        parser.error("project_id invalide ; lettres minuscules, chiffres, tirets, 6 à 30 caractères")
    template = (ROOT / "sql/bigquery/ca_comite_ytd.sql.tpl").read_text(encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(template.replace("{{PROJECT_ID}}", args.project_id), encoding="utf-8")
    print(f"Requête rendue : {args.out}")


if __name__ == "__main__":
    main()
