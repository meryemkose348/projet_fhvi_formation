`ingestion_initiale.py` copie 5 tables de 4 sources (PostgreSQL, MariaDB, SQL Server, DuckDB) vers le bucket `fhvi-landing`.

Il fonctionne, et c'est important : on ne part pas d'un code faux, on part
d'un code qui rend service, mais qui ne survivra pas à sa première évolution

## Lancer

```bash
source ../.venv/bin/activate
python ingestion_initiale.py
```

Résultat attendu :

```
debut
patients ok 500
sejours ok 1200
rdv ok 800
prestations ok 1000
dispensations ok 1500
fin
```

## Les défauts à faire trouver

| # | Défaut | Où | Conséquence concrète |
|---|--------|----|----------------------|
| 1 | Identifiants en clair (mots de passe, clés S3) | l. 13-15, 20, 43, 56 | Fuite de secrets dès le premier `git push` |
| 2 | Paramètres dispersés (hôtes, ports, bucket, chemins) | partout | Changer d'environnement = modifier 10 lignes |
| 3 | 5 blocs copiés-collés quasi identiques | l. 19-77 | Une correction doit être faite 5 fois… |
| 4 | …et elle ne l'est pas : le `strip()` est oublié pour DuckDB | l. 72 | Données incohérentes entre sources (`'Urgences '`) |
| 5 | Chemin relatif au dossier courant | l. 69 | Plante si lancé depuis un autre dossier |
| 6 | Aucune gestion d'erreur | — | Une source indisponible arrête **toutes** les autres |
| 7 | `print` au lieu de logs | — | Rien d'exploitable la nuit, pas d'horodatage |
| 8 | Aucune fonction | — | Impossible à tester unitairement |
| 9 | Pas de traçabilité | — | Impossible de savoir quel run a produit quel fichier |
| 10 | Ajouter une source = copier un bloc de plus | — | Le script grossit linéairement avec les sources |
| 11 | Noms de variables (`df2`, `df5`, `engine3`, `d`) | partout | Lecture difficile, erreurs de copier-coller |
| 12 | Commentaire « NE PAS TOUCHER » | l. 1 | Le code fait peur : signe d'une dette technique |


*(nb : on peut se servir de cette partie pour avoir plus de détails à propos des défauts au niveau de l'exo 1)*