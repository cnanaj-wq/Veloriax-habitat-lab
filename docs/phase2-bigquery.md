# Phase 2 — reproduire le KPI dans BigQuery

**État : prêt à exécuter ; aucune ressource GCP n'a été créée depuis ce dépôt.** Le résultat attendu reste celui de la [phase 1](phase1-ca-comite.md). La cible de démonstration est une région unique pour le bucket et le dataset. `europe-west9` (Paris) est possible pour BigQuery et Cloud Storage, mais la région effective doit être confirmée avec le projet GCP.

## Périmètre minimal et responsabilités

| Couche | Objet | Responsabilité |
| --- | --- | --- |
| Cloud Storage | `gs://<bucket>/veloriax/REL_20260927_2312/*.csv` | conserver les trois sources du lot chargé et leurs empreintes |
| BigQuery `veloriax_raw` | `fact_ventes`, `dim_lot`, `dim_programme` | conserver les champs CSV en `STRING`, sans correction silencieuse |
| Requête de contrôle | `sql/bigquery/ca_comite_ytd.sql.tpl` | parser, relier, compter les erreurs et calculer le KPI |
| Gate local | `scripts/check_bigquery_result.py` | interdire la suite si comptes, montants ou ventilations divergent |

Ce périmètre est un **chargement pilote isolé**. Les 22 autres tables viendront après validation de ce trajet ; elles ne sont pas requises pour calculer les réservations nettes YTD. Aucun mart n'est promu par les commandes ci-dessous.

## Préparation locale

```bash
python scripts/unpack_dataset.py data
python scripts/validate_dataset.py data
python scripts/render_bigquery_sql.py MON_PROJECT_ID --out build/ca_comite_ytd.sql
```

Le rendu SQL accepte uniquement un identifiant de projet GCP conforme au format standard. `build/` est un dossier de travail ignoré par Git. La requête utilise **deux paramètres typés** : `@as_of` et `@release_id`. Les schémas `schema/bigquery/raw/*.json` fixent les colonnes et leur ordre ; ne pas demander l'autodétection.

## Exécution dans Cloud Shell

Après création/choix d'un projet facturable, d'un bucket dédié et d'une région commune, renseigner les variables dans Cloud Shell :

```bash
export VELORIAX_PROJECT_ID='MON_PROJECT_ID'
export VELORIAX_LOCATION='europe-west9'
export VELORIAX_BUCKET='MON_BUCKET_UNIQUE'
```

Créer le dataset pilote si absent. Créer le bucket séparément dans la **même région** ou utiliser un bucket existant dédié ; son nom est mondialement unique. Ne pas modifier un bucket de production pour le lab.

```bash
bq --project_id="$VELORIAX_PROJECT_ID" --location="$VELORIAX_LOCATION" \
  mk --dataset "$VELORIAX_PROJECT_ID:veloriax_raw"

gcloud storage cp data/dim_programme.csv \
  "gs://$VELORIAX_BUCKET/veloriax/REL_20260927_2312/dim_programme.csv"
gcloud storage cp data/dim_lot.csv \
  "gs://$VELORIAX_BUCKET/veloriax/REL_20260927_2312/dim_lot.csv"
gcloud storage cp data/fact_ventes.csv \
  "gs://$VELORIAX_BUCKET/veloriax/REL_20260927_2312/fact_ventes.csv"
```

Vérifier les trois objets et leurs empreintes à la réception ; l'upload seul ne certifie pas le lot. Charger **dans ce dataset de démonstration uniquement** :

```bash
for table in dim_programme dim_lot fact_ventes; do
  bq --project_id="$VELORIAX_PROJECT_ID" --location="$VELORIAX_LOCATION" load \
    --source_format=CSV --skip_leading_rows=1 --max_bad_records=0 --replace \
    "$VELORIAX_PROJECT_ID:veloriax_raw.$table" \
    "gs://$VELORIAX_BUCKET/veloriax/REL_20260927_2312/$table.csv" \
    "schema/bigquery/raw/$table.json" || exit 1
done
```

`--replace` rend le rejeu simple dans le **dataset pilote**, mais peut supprimer le schéma et des contrôles d'accès d'une table existante. Ne pas employer cette commande sur un dataset de production. Consigner les trois IDs de jobs, les comptes de lignes et les empreintes des objets source.

## Mesure et réconciliation

```bash
python scripts/render_bigquery_sql.py "$VELORIAX_PROJECT_ID" --out build/ca_comite_ytd.sql

bq --project_id="$VELORIAX_PROJECT_ID" --location="$VELORIAX_LOCATION" query \
  --use_legacy_sql=false --dry_run \
  --parameter=as_of:DATE:2026-09-27 \
  --parameter=release_id:STRING:REL_20260927_2312 \
  < build/ca_comite_ytd.sql

bq --project_id="$VELORIAX_PROJECT_ID" --location="$VELORIAX_LOCATION" query \
  --use_legacy_sql=false --format=json --maximum_bytes_billed=1000000000 \
  --parameter=as_of:DATE:2026-09-27 \
  --parameter=release_id:STRING:REL_20260927_2312 \
  < build/ca_comite_ytd.sql > build/ca_comite_bigquery.json

python scripts/check_bigquery_result.py build/ca_comite_bigquery.json
```

Le plafond de 1 Go traité est un **garde-fou de démonstration**, pas une estimation de facture. Examiner l'estimation du dry run et l'historique réel du job ; des scripts multi-instructions ou des vues peuvent rendre certains dry runs incomplets. La comparaison attend 60 000 événements bruts, 4 043 événements futurs exclus, 11 083 retenus YTD et **355 534 626 284 centimes** de réservations nettes, avec zéro anomalie et des ventilations mensuelles/régionales identiques.

En cas d'écart : garder la dernière version certifiée, ouvrir un incident avec `job_id`, table, lot, compteur, règle et preuve, puis corriger dans une **nouvelle version candidate**. Ne pas changer la valeur de référence pour faire passer le contrôle.

## Sources officielles

- [Charger des CSV Cloud Storage dans BigQuery](https://docs.cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv)
- [Paramètres des requêtes BigQuery](https://docs.cloud.google.com/bigquery/docs/parameterized-queries)
- [Contrôler les coûts des requêtes](https://docs.cloud.google.com/bigquery/docs/best-practices-costs)
- [Régions BigQuery](https://docs.cloud.google.com/bigquery/docs/locations)
