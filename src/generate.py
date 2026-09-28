#!/usr/bin/env python3
"""Synthetic real-estate BI lab. No names, rows or figures from the source deck."""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

START = date(2023, 1, 1)
END = date(2026, 12, 31)
REGIONS = ["IDF", "ARA", "PACA", "OCC", "NAQ", "BRE", "HDF", "PDL"]
STATUSES = ["ACTIF", "EN_TRAVAUX", "LIVRE"]


def add_month(d, n):
    return date(d.year + (d.month - 1 + n) // 12, (d.month - 1 + n) % 12 + 1, 1)


class Sink:
    def __init__(self, directory):
        self.directory = directory
        self.counts = Counter()
        self.columns = {}

    def write(self, name, columns, records):
        path = self.directory / (name + ".csv")
        self.columns[name] = columns
        with path.open("w", encoding="utf-8", newline="") as f:
            out = csv.writer(f, lineterminator="\n")
            out.writerow(columns)
            for record in records:
                assert len(record) == len(columns), (name, record)
                out.writerow(record)
                self.counts[name] += 1
        return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--rental-lots", type=int, default=6000)
    p.add_argument("--sale-lots", type=int, default=50000)
    p.add_argument("--seed", type=int, default=28092026)
    p.add_argument("--max-rows", type=int, default=1500000)
    a = p.parse_args()
    if a.rental_lots < 1 or a.sale_lots < 1:
        p.error("lot counts must be positive")
    # Conservative upper bound, including dimensions, objectives and incidents.
    estimate = a.rental_lots * (1 + 48 * 4) + a.sale_lots * 3 + 160 * 16 * 3 * 2 + 10000
    if estimate > a.max_rows:
        p.error(f"estimated {estimate:,} rows exceeds --max-rows {a.max_rows:,}")
    a.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    sink = Sink(a.out)
    programmes = 160
    release_id = "REL_20260927_2312"

    sink.write("dim_programme", ["programme_id", "region_code", "segment", "statut", "annee_livraison"],
        ((f"P{i:04d}", REGIONS[(i-1) % len(REGIONS)],
          "PATRIMOINE" if i <= 40 else "PROMOTION", STATUSES[i % 3], 2021 + i % 7)
         for i in range(1, programmes+1)))

    def lots():
        for i in range(1, a.rental_lots + a.sale_lots + 1):
            loc = i <= a.rental_lots
            programme = (i-1) % 40 + 1 if loc else 41 + (i-a.rental_lots-1) % 120
            yield (f"L{i:07d}", f"P{programme:04d}", "LOCATION" if loc else "VENTE",
                   28 + (i * 17) % 112, 1 + i % 6, "LOGEMENT" if i % 13 else "LOCAL")
    sink.write("dim_lot", ["lot_id", "programme_id", "mode_commercialisation", "surface_m2", "pieces", "type_lot"], lots())

    # Fact grain: one monthly charge line per rental lot and charge type.
    def loyers():
        for m in range(48):
            mois = add_month(START, m).isoformat()
            for i in range(1, a.rental_lots + 1):
                surface = 28 + (i * 17) % 112
                base = surface * (1600 + i % 600)  # integer euro cents
                occupe = not (i % 5 == 0 and m < 3) and (i * 37 + m * 19) % 100 < 87
                franchise = occupe and (i + m) % 31 == 0
                for k, typ in enumerate(("LOYER", "CHARGES", "TAXE")):
                    montant = (base if k == 0 else base // (5 if k == 1 else 14)) if occupe else 0
                    yield (f"Q{m:02d}{i:06d}{k}", f"L{i:07d}", mois, typ,
                           montant, 0 if not franchise or k else montant // 2,
                           int(occupe), f"LOT_{m:02d}", release_id)
    sink.write("fact_quittancement", ["quittance_id", "lot_id", "mois", "type_ligne", "montant_centimes", "franchise_centimes", "occupe", "source_lot", "release_id"], loyers())

    # Cash receipts remain separate from billed rent; there can be overdue amounts.
    def paiements():
        for m in range(48):
            mois = add_month(START, m).isoformat()
            for i in range(1, a.rental_lots + 1):
                occupe = not (i % 5 == 0 and m < 3) and (i * 37 + m * 19) % 100 < 87
                base = (28 + (i * 17) % 112) * (1600 + i % 600)
                impaye = occupe and (i * 13 + m) % 67 == 0
                yield (f"E{m:02d}{i:06d}", f"L{i:07d}", mois,
                       0 if not occupe or impaye else base + base // 5 + base // 14,
                       "IMPAYE" if impaye else "REGLE" if occupe else "SANS_BAIL", release_id)
    sink.write("fact_encaissement", ["encaissement_id", "lot_id", "mois", "montant_centimes", "statut", "release_id"], paiements())

    # Bookings, cancellation, and rebooking have distinct event ids.
    def ventes():
        for j in range(1, a.sale_lots+1):
            lot = f"L{a.rental_lots+j:07d}"
            jour = START + timedelta(days=(j * 43 + j // 17) % 1461)
            prix = (15000000 + (j * 7919) % 48000000)
            yield (f"V{j:08d}", lot, jour.isoformat(), "RESERVATION", prix, f"VENTE_{jour:%Y%m}", release_id)
            if j % 10 == 0:
                ann = min(END, jour + timedelta(days=12))
                yield (f"A{j:08d}", lot, ann.isoformat(), "ANNULATION", -prix, f"VENTE_{ann:%Y%m}", release_id)
                rebook = min(END, ann + timedelta(days=19))
                yield (f"R{j:08d}", lot, rebook.isoformat(), "RESERVATION", int(prix*1.01), f"VENTE_{rebook:%Y%m}", release_id)
    sink.write("fact_ventes", ["evenement_id", "lot_id", "date_evenement", "type_evenement", "montant_centimes", "source_lot", "release_id"], ventes())

    # SCD2: for one (programme, KPI, quarter), revisions never overlap.
    def objectifs():
        oid = 0
        for q in range(16):
            start = add_month(START, q*3)
            finish = add_month(start, 3) - timedelta(days=1)
            revision = start + timedelta(days=45)
            for prog in range(1, programmes+1):
                for code in ("CA_RESERVATIONS_CTS", "LOYERS_CTS", "TAUX_OCCUPATION_BP"):
                    oid += 1
                    base = ((20_000_000 + prog*211_111) if code == "CA_RESERVATIONS_CTS"
                            else (1_600_000 + prog*17_101) if code == "LOYERS_CTS" else 8500)
                    if code == "LOYERS_CTS" and prog > 40:
                        continue
                    if code == "CA_RESERVATIONS_CTS" and prog <= 40:
                        continue
                    for n, vfrom, vto, amount, motif in (
                        (1, start, revision, base, "BUDGET_INITIAL"),
                        (2, revision, "", round(base*1.06), "REVISION_TRIMESTRIELLE")):
                        yield (f"OBJ{oid:07d}R{n}", f"P{prog:04d}", code,
                               start.isoformat(), finish.isoformat(), amount, n,
                               vfrom.isoformat(), vto.isoformat() if vto else "", motif, "PLANIFICATION")
    sink.write("dim_objectif_historise", ["objectif_version_id", "programme_id", "kpi_code", "periode_debut", "periode_fin", "valeur_cible", "revision", "valide_du", "valide_au_exclu", "motif_revision", "auteur_role"], objectifs())

    # The candidate is quarantined. Certified CSVs are never modified by fault injection.
    sink.write("ops_incident_scenario", ["scenario_id", "date_heure_paris", "objet", "type_panne", "action_attendue"], [
        ("INC001", "2026-09-28 07:42:06", "dwh.ventes", "TABLE_ABSENTE", "BLOQUER_PROMOTION"),
        ("INC002", "2026-09-28 09:10:06", "dim_programme", "CLE_MANQUANTE", "BLOQUER_PROMOTION"),
        ("INC003", "2026-09-28 10:15:11", "fact_ventes", "VOLUME_ANORMAL", "BLOQUER_PROMOTION")])

    files = {}
    for name in sink.counts:
        path = a.out / (name + ".csv")
        files[path.name] = {"rows": sink.counts[name], "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest = {"synthetic": True, "seed": a.seed, "certified_release_id": release_id,
                "period": [START.isoformat(), END.isoformat()], "time_zone_events": "Europe/Paris",
                "files": files, "total_rows": sum(sink.counts.values())}
    (a.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"total_rows": manifest["total_rows"], "files": {k:v["rows"] for k,v in files.items()}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
