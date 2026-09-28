# Contrats de calcul et qualité

Un montant portant le suffixe `_centimes` doit être divisé par 100 à l'affichage. Chaque KPI indique une date d'arrêté, un périmètre et une version. Les ratios ci-dessous sont des **définitions proposées**, à faire valider pour un usage client.

| KPI | Calcul au grain indiqué | Attention |
| --- | --- | --- |
| CA net de réservation | somme des `montant_centimes` signés dans `fact_ventes` | réservations, annulations et nouvelles réservations ; ce n'est pas l'encaissement |
| Loyer quittancé | somme `montant_centimes - franchise_centimes` des lignes `LOYER` | charges et taxes à présenter séparément |
| Encaissement locatif | somme `fact_encaissement.montant_centimes` | ne pas confondre avec la quittance |
| Impayés du lot-mois | quittance due moins montant encaissé, borné selon règle validée | le paiement généré comprend plusieurs types de lignes ; rapprocher au même périmètre |
| Taux d'occupation lots | lot-mois `OCCUPE` / lot-mois observés | utiliser `fact_occupation_mensuelle`, pas le drapeau répété trois fois dans le quittancement |
| Taux d'occupation surface | surface des lot-mois occupés / surface totale des lot-mois | calcul séparé du taux en nombre de lots |
| Loyer au m² | loyer hors charges / surface des lots concernés | préciser période et occupation ; aucune comparaison directe au marché sans ajustement |
| Écart à l'objectif | réalisé moins cible valable à la **date de connaissance** | la clé objectif comprend programme, KPI et trimestre ; une seule révision par date |
| Primes acquises | somme `prime_acquise_centimes` par trimestre et contrat | ne jamais sommer après jointure aux garanties du contrat |
| Charge sinistres | somme des deltas payés + provisions − recours jusqu'à la date d'arrêté | distinguer survenance et comptabilisation des mouvements |
| Rapport sinistres/primes | charge des sinistres / primes acquises | même produit, cohorte, période et date d'arrêté |
| Fréquence sinistres | nombre de sinistres / contrats exposés | dénominateur à affiner en contrats-années pour comparaison |
| Fonds confiés | cumul des mouvements signés du mandat | distinguer des recettes de l'assureur ; comparer à la garantie financière applicable |

## Objectifs historisés

`dim_objectif_historise` contient deux révisions pour chacune des **5 120 clés métier**. `valide_du` est inclus ; `valide_au_exclu` est exclu ; vide signifie version courante. Filtrer à la fois la période cible et la date à laquelle l'objectif était connu. Un `SUM(valeur_cible)` sans filtre temporel double-compte les objectifs.

## Contrôles bloquants avant promotion

1. Empreintes et comptes par CSV conformes au manifeste, clés uniques, références existantes.
2. Une occupation par lot-mois ; baux sans chevauchement ; carence avant le premier bail, vacance ensuite.
3. Un seul objectif valide par clé métier et date d'observation.
4. Sinistre lié à une garantie active le jour de survenance ; provisions non négatives après cumul.
5. Aucun chevauchement Visale/GLI pour un même bail et risque. Visale n'a pas de prime d'assurance.
6. Un jeu complet de ventes et dimensions pour `release_id` ; agrégats du mart réconciliés au brut.

Les `ops_incident_scenario.csv` décrivent des pannes à **injecter dans une version candidate isolée**. Le jeu livré reste certifié et non corrompu.
