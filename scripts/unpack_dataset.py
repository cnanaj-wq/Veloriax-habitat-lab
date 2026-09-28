#!/usr/bin/env python3
"""Vérifier les segments versionnés et extraire le jeu de données."""

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="Dossier de sortie pour les CSV")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "datasets/archive.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256()
    with tempfile.TemporaryFile() as archive:
        for entry in manifest["parts"]:
            part = ROOT / "datasets" / entry["file"]
            content = part.read_bytes()
            if len(content) != entry["size_bytes"] or hashlib.sha256(content).hexdigest() != entry["sha256"]:
                raise SystemExit(f"Segment absent ou altéré : {part.name}")
            digest.update(content)
            archive.write(content)
        if archive.tell() != manifest["archive_size_bytes"] or digest.hexdigest() != manifest["archive_sha256"]:
            raise SystemExit("Archive reconstituée non conforme")
        archive.seek(0)
        with zipfile.ZipFile(archive) as source:
            if source.testzip() is not None:
                raise SystemExit("Archive ZIP endommagée")
            args.data.mkdir(parents=True, exist_ok=True)
            source.extractall(args.data)
    print(f"Archive contrôlée ; données extraites dans {args.data}")


if __name__ == "__main__":
    main()
