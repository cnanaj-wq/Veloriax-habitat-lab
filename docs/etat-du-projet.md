# État et suite du lab

## Livré

- Données originales générées avec graine fixe et manifeste d'intégrité.
- Objectifs historisés, référentiels, baux/occupation, sinistres, primes et fonds confiés.
- Scénarios d'erreur définis séparément des données certifiées.
- Documentation de la chaîne cible, des KPI et des chargements.
- Cahier d'expérience, prompts Google AI Studio et événements de démonstration d'Ops Navigator.

## Non encore réalisé

- Déploiement de ressources GCP et Snowflake, tables chargées, mesures de coût et performance.
- Application `.qvf` Qlik, états alternatifs et validation sur Qlik Sense Desktop.
- Collecteurs Ops Navigator, IHM en direct, lineage interplateforme et agent IA.
- Application générée dans Google AI Studio et déployée, API de collecte et authentification.
- Infrastructure Qlik Enterprise multi-nœud et tests de basculement.

## Incréments proposés

1. **Décision métier** : vérifier CA net, loyer, occupation, prime et charge des sinistres sur le socle local.
2. **DWH** : charger les lots en BigQuery ; comparer un périmètre identique dans Snowflake ; consigner coûts et délais mesurés.
3. **Qlik** : publier le reporting certifié et une feuille d'investigation à états alternatifs.
4. **Incidents** : injecter une table absente puis une dimension incohérente, bloquer le candidat, observer le dernier KPI valide.
5. **Ops et IA** : consolider événements et lineage, produire un diagnostic fondé sur les traces et valider humainement la reprise.

Documenter les résultats réellement observés, y compris les optimisations sans gain. La disponibilité et la reprise ne seront pas qualifiées de « production » sans tests de charge, permissions, alertes et procédures de restauration.
