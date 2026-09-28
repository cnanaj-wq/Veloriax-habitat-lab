# Prompt 01 — construire la console

Coller ce prompt dans Google AI Studio, mode Build, après avoir importé le dépôt. Ce texte est une spécification du prototype, pas une instruction autorisant l'accès à des comptes cloud.

```text
Construis une application web responsive nommée « Veloriax Ops Navigator » pour une démonstration de supervision BI immobilière. Utilise le dépôt importé comme source de vérité : docs/architecture.md, docs/operations.md, docs/experience-ops-navigator.md et apps/ops-navigator/fixtures/inc001-events.json. N'invente aucun flux de production, aucun résultat de benchmark et aucune connexion existante.

Le scénario : le 28/09/2026 à 07:42:06 Europe/Paris, dwh.ventes est absente. Le CA comité ne peut plus être recalculé. La version certifiée REL_20260927_2312 reste visible dans Qlik, avec une alerte de fraîcheur. À 08:12:03, après restauration, contrôles et validation humaine, le candidat devient la nouvelle version certifiée. Rejoue les neuf événements du fichier fixture dans leur ordre temporel. Prévois pause, lecture, vitesse 1×/4× et retour au début. La mention « DÉMO — événements simulés » reste visible en permanence.

Design premium, calme et explicable : fond blanc cassé, texte anthracite, accents bleu nuit ; rouge/orange/vert uniquement pour les statuts. Typographie nette, cartes sobres, grands chiffres, microanimations brèves avec option réduire les mouvements. Aucun style de console hacker ni faux compteur temps réel.

Trois vues :
1. Pulse : verdict « publiable ? », CA comité fictif exprimé clairement comme montant de démonstration, date et release certifiés, âge et seuil de fraîcheur, statut des sources, flux de neuf événements. Différencie « version valide à sa date » et « mise à jour récente ».
2. Impact Map : graphe dirigé cliquable entre fichier ventes, raw.ventes, staging.ventes, dwh.ventes, champ montant_centimes, calcul CA_COMITE, application Qlik et KPI comité ; ajoute dim_programme et objectif historisé. Clique un nœud pour isoler amont/aval, montrer version et incident associé. Ne crée pas une flèche sans métadonnées de dépendance explicites dans le code fixture.
3. Incident Room : horodatages DD/MM/YYYY hh:mm:ss Europe/Paris, regroupement incident INC001, preuves simulées identifiées, versions candidat/certifié, hypothèses et inconnues, assignation humaine et décision de reprise. Affiche les détails d'une preuve dans un volet latéral.

Architecture : sépare source de données, moteur d'état déterministe et composants UI. La démo charge seulement le JSON local. Pour le futur mode connecté, prépare une interface EventProvider et des adaptateurs HTTP désactivés ; si l'API est absente, affiche une erreur et ne bascule pas silencieusement en démo. Le moteur déduplique par event_id, ordonne occurred_at, calcule la fraîcheur depuis observed_at et applique des états explicites (healthy, blocked, stale, recovering). Ne considère jamais un simple reload réussi comme une certification.

Sécurité : aucune clé ni donnée métier sensible côté client ; Gemini est désactivé par défaut. Prépare seulement l'emplacement d'un futur diagnostic côté serveur, en lecture seule, avec références aux event_id et preuves. Ne fournis pas de bouton qui modifie une table, relance un job, publie un KPI ou ferme un incident automatiquement.

Livrables : code lisible et modulaire, données de démonstration traçables, README d'exécution, documentation des états et des règles, tests du moteur d'état sur incident en cours et incident rétabli. Vérifie le rendu mobile, la navigation clavier, les contrastes, le format des heures et le fait que le badge DÉMO reste affiché. Décris brièvement ce qui fonctionne réellement et ce qui est seulement prévu.
```

**Contrôle avant export Git :** rejouer l'incident ; à 07:42:09 le reporting reste affiché avec ancienne date, à 07:42:10 la fraîcheur est hors seuil, à 08:12:03 une nouvelle version n'apparaît qu'après validation. Le code généré doit être relu avant commit.
