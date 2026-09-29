# Phase 1 — quel chiffre présenter au comité ?

## Contrat métier proposé

**Question :** au 27/09/2026, combien représentent les réservations nettes depuis le 01/01/2026 ?

**Indicateur :** `CA_COMITE` dans l'interface, défini précisément comme **réservations nettes YTD**. Il additionne les événements `RESERVATION` positifs et les `ANNULATION` négatives, à leur date d'événement, jusqu'à la date d'arrêté incluse. Une nouvelle réservation après annulation est un nouvel événement. Le résultat est un **volume commercial réservé**, pas du chiffre d'affaires reconnu en comptabilité, une vente définitive ni des encaissements.

**Périmètre :** lots commercialisés en vente, toutes régions, événements du 01/01/2026 au 27/09/2026 inclus, version de démonstration `REL_20260927_2312`. Les CSV couvrent aussi octobre à décembre 2026 : ces lignes futures servent aux exercices mais sont **exclues de cet arrêté**. Les horodatages de publication et de fraîcheur sont en `Europe/Paris` ; les dates d'événements sont des dates civiles sans heure.

## Référence calculée localement

| Élément | Valeur synthétique |
| --- | ---: |
| Lignes de vente dans la source | 60 000 |
| Événements après le 27/09 exclus | 4 043 |
| Événements retenus en 2026 YTD | 11 083 |
| Réservations positives | 10 159 ; 3 910 702 101,44 € |
| Annulations négatives | 924 ; −355 355 838,60 € |
| **Réservations nettes YTD** | **3 555 346 262,84 €** |

Ce montant est le résultat calculé sur le **jeu fictif**, pas une observation économique ni un montant affiché dans une application Qlik. Le détail exact par mois et région est dans [`results/ca_comite_2026-09-27.json`](../results/ca_comite_2026-09-27.json). Le scénario Ops Navigator utilise maintenant cette même valeur.

## Reproduire

```bash
python scripts/unpack_dataset.py data
python scripts/validate_dataset.py data
python scripts/ca_comite_baseline.py --as-of 2026-09-27 --out results/ca_comite_2026-09-27.json
```

Le script rejette une clé d'événement dupliquée, un type ou signe inattendu, une date ou un montant invalide, un lot absent ou non commercialisé en vente, un programme absent, un mois de lot source incohérent et une `release_id` étrangère. Il réconcilie le montant net avec les ventilations par mois et par région.

## Contrôles avant publication dans le DWH

1. L'archive et les 25 CSV correspondent aux empreintes du manifeste ; toutes les sources exigées pour la version sont présentes.
2. Les événements respectent les types, signes, clés et périodes. Les 4 043 événements postérieurs à l'arrêté ne contaminent pas le KPI.
3. `gross_reservations + cancellations = net` en centimes ; les totaux mensuels et régionaux se réconcilient exactement.
4. Le résultat BigQuery doit égaler la référence locale **au centime et au compte de lignes** ; Snowflake et Qlik seront comparés ensuite sur le même périmètre.
5. La version à publier comprend faits et dimensions cohérents. En cas d'échec, garder la dernière version certifiée avec sa date visible et alerter sur la fraîcheur.

**Point à faire valider par un métier :** la définition du « CA comité » réel, notamment réservation vs acte, annulations, taxes, périmètre SCI/programmes, date de prise en compte et niveau d'arrondi. La définition ci-dessus est une hypothèse explicite de laboratoire.
