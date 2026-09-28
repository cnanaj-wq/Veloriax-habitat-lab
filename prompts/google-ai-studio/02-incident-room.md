# Prompt 02 — approfondir l'Incident Room

À utiliser après le prompt 01, dans la même application et après revue du code généré.

```text
Améliore uniquement la vue Incident Room de Veloriax Ops Navigator sans casser Pulse, Impact Map ni le moteur d'état.

Ajoute une comparaison côte à côte « certifié / candidat » avec release_id, heure, compte de lignes, empreinte disponible, verdict de contrôle, propriétaire et lien vers la preuve. Pour une table absente, dessine un chemin d'impact concret jusqu'au KPI. Pour une dimension absente, conserve la version cohérente de tous les faits et dimensions. Ne combine jamais des tables de releases différentes.

Ajoute une section « décision » en trois colonnes : faits établis (event_id + preuve), hypothèses à tester, prochaines actions avec responsable. Un bouton « Préparer le compte rendu » peut générer un brouillon local en français, jamais envoyer ni publier. Prévois un champ de validation humaine pour la reprise mais garde la démonstration sans connexion ni effet sur le DWH.

La narration visuelle doit montrer l'écart entre chiffre visible et chiffre frais : état dégradé clairement lisible pour le métier et chemin de diagnostic détaillé pour l'exploitation. Conserve le bandeau DÉMO permanent, les dates Europe/Paris et l'accessibilité clavier. Donne la liste des fichiers modifiés et explique les règles de calcul ou de statut introduites.
```

**Critères de revue :** une hypothèse n'est jamais affichée comme un fait ; tout chiffre a une version et une heure ; le retour au vert exige un contrôle de cohérence et une décision humaine.
