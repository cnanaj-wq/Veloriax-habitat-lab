# Architecture et rôle des outils

## Architecture technique cible

```mermaid
flowchart TB
    A["CSV synthétiques + manifeste"] --> B["Cloud Storage : lot horodaté"]
    B --> C["BigQuery : raw"]
    C --> D["BigQuery : staging + contrôles"]
    D --> E["Mart versionné : candidat / certifié"]
    E --> F["Qlik : reporting et investigation"]
    D --> H["Snowflake : comparaison ciblée"]
    B --> I["Ops Navigator : traces et lineage"]
    D --> I
    E --> I
    F --> I
    H --> I
    I --> J["Gemini : diagnostic étayé"]
```

Google AI Studio sert d'atelier de création de l'IHM **Ops Navigator** à partir des prompts versionnés dans ce dépôt. Le code généré doit être revu, testé et suivi par Git. L'application lit un contrat d'événements ; elle ne remplace ni Cloud Logging, ni les métadonnées BigQuery/Snowflake, ni les journaux Qlik. Une démo sur événements fictifs précède les adaptateurs authentifiés.

Le dépôt livre les fichiers et générateurs. Les flèches ci-dessus décrivent le **travail à implémenter**, pas des connexions déjà opérationnelles.

## Décision de publication et continuité du reporting

```mermaid
flowchart TB
    A["Sources : ventes + dimensions"] --> B["Chargement raw / staging DWH"]
    B --> C["Contrôles techniques et métier"]
    C -->|Validés et approuvés| D["Version cohérente certifiée N+1"]
    C -->|Échec ou données absentes| E["Version certifiée N conservée"]
    D --> F["Qlik : version publiée"]
    E --> F
    C --> G["Ops Navigator : incident + lineage"]
    F --> G
```

**Contrôles bloquants :** intégrité du lot, volumes, clés, références, réconciliation ventes/dimensions, calcul du CA et date de fraîcheur. La version N est un jeu cohérent de faits et dimensions, avec une preuve d'intégrité et un `release_id` ; elle n'est pas un simple cache de graphique. Si la version N+1 échoue, Qlik conserve N et affiche **« données arrêtées au … »** avec alerte de fraîcheur. Après restauration de la source, rejouer le candidat, contrôler les écarts, demander validation humaine, puis charger Qlik et vérifier le KPI avant clôture de l'incident. Ops Navigator enregistre chaque transition et son auteur.

| Couche | Entrée | Sortie | Trace exigée |
| --- | --- | --- | --- |
| Réception GCP | CSV + manifeste | lot accepté ou rejeté | empreinte, nom, acteur, heure |
| Raw BigQuery | lot accepté | tables au grain source | job ID, nombre de lignes, octets |
| Staging | raw | types, références, contrôles | version de règle et anomalies |
| Mart certifié | staging complet | `release_id` publié | résultats des contrôles, valideur |
| Snowflake | copie délimitée | résultats comparables | requête, durée, crédits, écart |
| Qlik métier | mart certifié | KPI et graphiques | version chargée, date du reload |
| Qlik investigation | certifié + candidat | écarts côte à côte | statut et provenance des deux versions |
| Ops Navigator | événements et dépendances | chronologie et impact | `run_id`, `release_id`, `incident_id` |
| Google AI Studio | prompt, contrat et fixtures | prototype d'application web | version du prompt, commit et revue du code |

## Versions et reprise

`raw` est conservé ; `staging` accueille le candidat ; `mart` ne pointe sur une version qu'après les contrôles. Pour un incident sur `ventes` ou `dim_programme`, garder un **ensemble cohérent** : ventes et dimensions de la même version certifiée. Montrer explicitement la fraîcheur et suspendre toute promotion automatique. Une restauration BigQuery ou un rejeu n'autorise la publication qu'après réconciliation et validation humaine.

Les états alternatifs Qlik isolent les **sélections**. Ils ne sauvegardent ni tables ni applications. Le candidat et le certifié doivent être présents dans le modèle de l'application d'investigation avec un identifiant de version ; l'application métier reste sur le certifié.

## Qlik Enterprise : cible documentaire

Sur GCP Compute Engine : nœud central avec QMC et repository, nœud de rechargement, nœud de consultation, stockage/référentiel résilients et réseau privé. Les responsabilités des nœuds et le basculement demandent un déploiement Enterprise distinct. Pour ce lab personnel, Qlik Sense Desktop sur le poste Windows est le périmètre exécutable prévu.

```mermaid
flowchart TB
    U["Utilisateurs"] --> P["Proxy / Engine : consultation"]
    M["Nœud central : QMC / Repository"] --> P
    M --> R["Nœud Scheduler / Engine : reload"]
    B["BigQuery : mart publié"] --> R
    R --> S["Stockage partagé résilient"]
    P --> S
```

Ce schéma représente les **rôles logiques**, pas un cluster déjà installé. Le réseau, les identités, le référentiel PostgreSQL, le stockage partagé, les zones et le basculement central nécessitent un design et des tests dédiés ; la QMC appartient à l'environnement Qlik Enterprise hébergé sur GCP dans cette variante. Avec Qlik Sense Desktop, il n'y a pas de QMC multi-nœud.

## Sécurité et coûts à vérifier pendant l'implémentation

Séparer les comptes de service par étape, limiter l'accès aux sinistres et données de locataires, journaliser les consultations et restreindre l'agent IA à la lecture. Mesurer BigQuery `JOBS`/audit logs et Snowflake `QUERY_HISTORY`/historique de consommation en indiquant leur fraîcheur. Les budgets GCP signalent un dépassement potentiel mais ne remplacent pas les quotas et contrôles de requêtes.
