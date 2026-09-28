# Chargement des fichiers

## Fichiers et ordre

Décompresser `datasets/veloriax-demo-2023-2026.zip` dans `data/`. Vérifier `python scripts/validate_dataset.py data`. Charger les dimensions (`dim_*`), le pont contrat-garantie, puis les faits (`fact_*`) et le catalogue `ops_*`. Le manifeste contient le nombre de lignes attendu et SHA-256 de chaque CSV.

Encodage UTF-8, séparateur virgule, première ligne d'en-têtes, dates ISO `YYYY-MM-DD`, valeurs vides pour certaines fins de validité. Les montants sont des **centimes entiers**. Faire les conversions en staging et tracer les rejets ; ne pas corriger directement les CSV certifiés.

## BigQuery (à exécuter avec votre projet)

Créer un dataset `raw` dans la même région que le bucket Cloud Storage et copier les CSV décompressés dans le bucket. Exemple pour une table, à adapter :

```bash
bq --location=EU load --source_format=CSV --skip_leading_rows=1 --autodetect \
  MON_PROJET:raw.fact_ventes gs://MON_BUCKET/veloriax/fact_ventes.csv
```

Pour une vraie reprise, fixer les schémas de staging plutôt que de dépendre de l'inférence CSV. Charger dans de nouvelles tables candidates, comparer aux comptes du manifeste, puis promouvoir. Ne pas rendre le mart visible avant validation. Mesurer octets traités, durée et coûts des requêtes avec l'historique des jobs.

## Snowflake (comparaison ciblée)

Charger les mêmes CSV via Snowsight ou un stage interne dans une base de test dédiée. Commencer par `dim_lot`, `dim_programme`, `fact_ventes` et `dim_objectif_historise`, puis vérifier les agrégats de réservation et les objectifs historisés. Conserver requête, entrepôt, durée, octets scannés et crédits selon les métriques disponibles. Ne pas traiter les deux entrepôts comme deux sources indépendantes de vérité : ils comparent **les mêmes fichiers**.

## Qlik Sense Desktop

Créer une connexion de dossier `VeloriaxData` pointant sur les CSV décompressés. Exemple minimal à adapter dans l'éditeur de chargement :

```qlik
Programmes:
LOAD programme_id AS ProgrammeID, region_code AS Region, segment AS Segment
FROM [lib://VeloriaxData/dim_programme.csv]
(txt, utf8, embedded labels, delimiter is ',', msq);

Lots:
LOAD lot_id AS LotID, programme_id AS ProgrammeID, surface_m2 AS SurfaceM2
FROM [lib://VeloriaxData/dim_lot.csv]
(txt, utf8, embedded labels, delimiter is ',', msq);

Ventes:
LOAD evenement_id AS VenteEvenementID, lot_id AS LotID,
     Date(Date#(date_evenement, 'YYYY-MM-DD')) AS DateVente,
     type_evenement AS TypeEvenement,
     Num#(montant_centimes) / 100 AS MontantVenteEUR,
     release_id AS ReleaseVenteID
FROM [lib://VeloriaxData/fact_ventes.csv]
(txt, utf8, embedded labels, delimiter is ',', msq);
```

Cet exemple ne charge que le périmètre ventes. Ajouter les autres faits avec leurs propres champs date et version pour éviter les clés synthétiques et les associations accidentelles. Une application d'investigation doit explicitement charger deux `release_id` ; l'archive publiée contient seulement une version certifiée. Les connexions locales Desktop et le script doivent être revus avant une mise en production.

Documentation technique : [BigQuery CSV](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv), [Snowflake Snowsight](https://docs.snowflake.com/en/user-guide/data-load-web-ui), [Qlik LOAD](https://help.qlik.com/en-US/sense/May2026/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptRegularStatements/Load.htm).
