# Contrat de la démonstration Ops Navigator

`fixtures/inc001-events.json` donne neuf événements fictifs, dans l'ordre, issus du scénario de perte de `dwh.ventes`. Toutes les heures d'affichage sont en `Europe/Paris`. Le fichier inclut des preuves **simulées**, et aucune URL de production.

Le montant `certified_kpi_demo.value_centimes` provient désormais du calcul reproductible [`results/ca_comite_2026-09-27.json`](../../results/ca_comite_2026-09-27.json), pour le périmètre « réservations nettes 2026 à date ». Les événements de panne et de reprise restent simulés.

À terme l'API renverra `GET /api/events?since=<timestamp>` et `GET /api/incidents/<id>` ; ces routes sont **des contrats prévus**, pas des services actifs. Chaque événement porte `event_id`, `occurred_at`, `observed_at`, `system`, `asset_type`, `asset_id`, `status`, `release_id`, `run_id`, `incident_id`, `actor`, `rows_in`, `rows_out`, `evidence_ref`, `message`. Le graphe de lineage est un second contrat : `from_asset`, `to_asset`, `relation`, `field`, `transform_version`.

En mode démo, interdire tout appel réseau de supervision et afficher un bandeau « données simulées ». Le mode connecté doit échouer explicitement si l'API est absente ; il ne doit jamais revenir silencieusement aux fixtures en conservant un badge « temps réel ».
