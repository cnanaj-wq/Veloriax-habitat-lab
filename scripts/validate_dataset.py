#!/usr/bin/env python3
"""Contrôler les fichiers livrés, leur intégrité et des liens métier essentiels."""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as source:
        yield from csv.DictReader(source)


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="Répertoire contenant les CSV décompressés")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "datasets/manifest.json").read_text(encoding="utf-8"))
    errors = []
    actual = {p.name for p in args.data.glob("*.csv")}
    expected = set(manifest["files"])
    for name in sorted(expected - actual):
        errors.append(f"fichier absent : {name}")
    for name in sorted(actual - expected):
        errors.append(f"fichier non déclaré : {name}")
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    total = 0
    for name, spec in manifest["files"].items():
        path = args.data / name
        count = sum(1 for _ in rows(path))
        total += count
        if count != spec["rows"]:
            errors.append(f"{name} : {count} lignes au lieu de {spec['rows']}")
        if digest(path) != spec["sha256"]:
            errors.append(f"{name} : empreinte SHA-256 différente")
    if total != manifest["total_rows"]:
        errors.append(f"total : {total} au lieu de {manifest['total_rows']}")

    programmes = {r["programme_id"] for r in rows(args.data / "dim_programme.csv")}
    lots = {r["lot_id"]: r for r in rows(args.data / "dim_lot.csv")}
    baux = {r["bail_id"]: r for r in rows(args.data / "dim_bail.csv")}
    contrats = {r["contrat_id"]: r for r in rows(args.data / "dim_contrat_assurance.csv")}
    sinistres = {r["sinistre_id"]: r for r in rows(args.data / "fact_sinistre.csv")}
    garanties = {r["garantie_code"] for r in rows(args.data / "dim_garantie.csv")}
    produits = {r["produit_code"] for r in rows(args.data / "dim_produit_assurance.csv")}
    professionnels = {r["professionnel_id"] for r in rows(args.data / "dim_professionnel.csv")}

    for table, field in [
        ("dim_programme.csv", "programme_id"), ("dim_lot.csv", "lot_id"),
        ("dim_bail.csv", "bail_id"), ("dim_contrat_assurance.csv", "contrat_id"),
        ("fact_ventes.csv", "evenement_id"), ("fact_quittancement.csv", "quittance_id"),
        ("fact_encaissement.csv", "encaissement_id"),
        ("fact_occupation_mensuelle.csv", "occupation_id"),
        ("fact_sinistre.csv", "sinistre_id"),
    ]:
        seen = set()
        duplicates = 0
        for r in rows(args.data / table):
            key = r[field]
            if not key or key in seen:
                duplicates += 1
            seen.add(key)
        if duplicates:
            errors.append(f"{table}.{field} : {duplicates} clés vides ou répétées")

    def check_reference(table, field, target):
        missing = sum(bool(r[field]) and r[field] not in target for r in rows(args.data / table))
        if missing:
            errors.append(f"{table}.{field} : {missing} clés inconnues")

    for table, field, target in [
        ("dim_lot.csv", "programme_id", programmes),
        ("dim_bail.csv", "lot_id", lots),
        ("dim_cautionnement.csv", "bail_id", baux),
        ("dim_contrat_assurance.csv", "lot_id", lots),
        ("dim_contrat_assurance.csv", "programme_id", programmes),
        ("dim_contrat_assurance.csv", "professionnel_id", professionnels),
        ("dim_contrat_assurance.csv", "produit_code", produits),
        ("fact_ventes.csv", "lot_id", lots),
        ("fact_quittancement.csv", "lot_id", lots),
        ("fact_encaissement.csv", "lot_id", lots),
        ("fact_occupation_mensuelle.csv", "lot_id", lots),
        ("fact_occupation_mensuelle.csv", "bail_id", baux),
        ("fact_prime_trimestrielle.csv", "contrat_id", contrats),
        ("fact_sinistre.csv", "contrat_id", contrats),
        ("fact_sinistre.csv", "garantie_code", garanties),
        ("fact_mouvement_sinistre.csv", "sinistre_id", sinistres),
        ("pont_contrat_garantie.csv", "contrat_id", contrats),
        ("pont_contrat_garantie.csv", "garantie_code", garanties),
        ("fact_dpe.csv", "lot_id", lots),
        ("fact_travaux.csv", "lot_id", lots),
        ("fact_valorisation.csv", "programme_id", programmes),
    ]:
        check_reference(table, field, target)

    for r in rows(args.data / "dim_cautionnement.csv"):
        if r["dispositif"] == "VISALE" and baux[r["bail_id"]]["protection_impayes"] == "GLI":
            errors.append(f"VISALE et GLI cumulées sur {r['bail_id']}")
    periods_by_lot = defaultdict(list)
    for r in baux.values():
        if r["date_debut"] > r["date_fin"]:
            errors.append(f"bail inversé : {r['bail_id']}")
        periods_by_lot[r["lot_id"]].append((r["date_debut"], r["date_fin"], r["bail_id"]))
    for lot_id, spans in periods_by_lot.items():
        spans.sort()
        for a, b in zip(spans, spans[1:]):
            if a[1] >= b[0]:
                errors.append(f"baux chevauchants : {lot_id}, {a[2]}, {b[2]}")
    objective_versions = defaultdict(list)
    for r in rows(args.data / "dim_objectif_historise.csv"):
        key = (r["programme_id"], r["kpi_code"], r["periode_debut"], r["periode_fin"])
        objective_versions[key].append((r["valide_du"], r["valide_au_exclu"]))
    for key, spans in objective_versions.items():
        spans.sort()
        if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
            errors.append(f"versions d'objectif simultanées : {key}")
    if errors:
        print("ÉCHEC :\n" + "\n".join(errors[:30]))
        if len(errors) > 30:
            print(f"... {len(errors) - 30} autres anomalies")
        raise SystemExit(1)
    print(f"OK : {len(expected)} CSV, {total:,} lignes ; SHA-256, références et objectifs contrôlés")


if __name__ == "__main__":
    main()
