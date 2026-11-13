# Exercices

Ces 12 exercices suivent l'ordre des modules vus en séance et portent tous sur le projet fil rouge qu'on a exposé.
Travaillez **toujours dans une copie** du dossier de l'étape, jamais dans les dossiers de référence (permet de séparer les edits qui seront réalisés, de la version originale du code, et d'avoir plus de facilité lors de la reprise des diapos :) :

```bash
# depuis 2_projet_python/
mkdir -p mon_travail
cp -R etapes_intermediaires/0X_nom_etape mon_travail/exN
```

Le fichier `.env` de `2_projet_python/` est trouvé automatiquement depuis `mon_travail/exN/`.

| N° | Module | Type | Durée (indicative) |
|---|---|---|---|
| 1 | M1 | Analyse | 10 min |
| 2 | M2-M3 | Manipulation | 15 min |
| 3 | M4 | Manipulation | 10 min |
| 4 | M5 | Manipulation | 15 min |
| 5 | M6 | Réflexion architecturale | 10 min |
| 6 | M7 | Réflexion architecturale | 10 min |
| 7 | M7 | Manipulation | 15 min |
| 8 | M8 | Manipulation | 20 min |
| 9 | M9 | Manipulation + réflexion | 20 min |
| 10 | Synthèse | Exercice final | 30-45 min |
| 11 | SQL Server | Bonus : transposition sur vos serveurs | 20-30 min |
| 12 | M4 · M9 | Arguments du main, rejeu et idempotence | 25 min |

---

## Exercice 1 : diagnostic du script initial

**Fichier** : `version_initiale/ingestion_initiale.py`

1. Exécutez le script depuis `version_initiale/`, puis depuis `2_projet_python/`. Que constatez-vous ?
2. Listez au moins 8 défauts, en indiquant pour chacun la ligne concernée et sa conséquence concrète
3. Classez vos défauts dans ces 6 familles : maintenance, multi-sources, testabilité, paramètres , exploitation, traçabilité
4. Le mot de passe PostgreSQL change : combien de lignes modifiez-vous ? Et avec 5 sources PostgreSQL ?
5. Trouvez le défaut qui produit des données incohérentes entre sources. Comment le prouver en inspectant le bucket ?

---

## Exercice 2 : factoriser

**Point de départ** : (on copie la aprtie structure au niveau de notre dossier de travail nommé "mon_travail" par exemple) : `cp -R etapes_intermediaires/1_structure mon_travail/ex2`

1. Dans `ingestion/sources.py`, surlignez ce qui diffère entre les 5 fonctions `extract_*`
2. Créez `ingestion/extract.py` avec 2 fonctions :
   `read_sql_table(url: str, table: str) -> pd.DataFrame` et `read_duckdb_table(path: Path, table: str) -> pd.DataFrame`.
3. Créez `ingestion/transform.py` avec `normalize(df)` qui : renomme les colonnes en `snake_case`
   (`DispensationId` → `dispensation_id`) et supprime les espaces des colonnes texte. Elle ne doit pas moidfier le dataframe qu'elle reçoit
4. Réécrivez `main.py` pour boucler sur une liste de sources
5. Vérifiez dans le bucket que `dispensations` a maintenant des colonnes `snake_case` et des libellés propres
6. Combien de lignes faut-il modifier pour ingérer aussi la table `services` de `dpi_nord` ?

---

## Exercice 3 : exclure un établissement en erreur

**Point de départ** : (on copie la aprtie structure au niveau de notre dossier de travail nommé "mon_travail" par exemple) :
`cp -R etapes_intermediaires/3_argparse mon_travail/ex3`

Considérons qu'un établissement est en maintenance cette nuit, et que l'ordonnanceur doit pouvoir lancer toutes les sources
cette établissement

1. Ajoutez une option `-x / --exclude` acceptant une ou plusieurs sources, avec contrôle des valeurs autorisées,
   facultative, documentée dans `--help`
2. Adaptez `main.py`
3. Vérifiez :
   ```bash
   python main.py --exclude rdv_sud --dry-run
   python main.py -x oracle #on s'attend à un code retour 2 ici
   ```
4. Question : que doit-il se passer avec `--sources rdv_sud --exclude rdv_sud` ? Proposez un comportement
   et justifiez-le

---

## Exercice 4 : piloter par la configuration

**Point de départ** : (on copie la aprtie structure au niveau de notre dossier de travail nommé "mon_travail" par exemple) :
`cp -R etapes_intermediaires/4_yaml mon_travail/ex4`

1. Sans modifier aucun fichier `.py`, ajoutez à l'ingestion la table `services` (PostgreSQL) et la
   table `PRATICIENS` (MariaDB, nom cible `praticiens`), et vérifiez dans le bucket
2. Désactivez la source `pharmacie`. Vérifiez avec `--list-sources`, puis lancez-la quand même avec
   `--sources pharmacie`, que constatez-vous ? Est-ce souhaitable ?
3. Créez `config/pipeline_minimisation.yaml`, et definir la destination en local au format csv, depuis la source `rdv_sud`
   uniquement, table `RENDEZ_VOUS` limitée aux colonnes `ID_RDV`, `DATE_RDV`, `SPECIALITE`, `STATUT`
   (pas d'IPP)

   Lancez-la et vérifiez le fichier produit

4. Introduisez 3 erreurs différentes dans une copie du yml, essayez de prédire les messages qui seront affcihés, puis vérifiez
5. Écrivez `enable: false` (sans « d ») sur une source. Que se passe-t-il ? Comment la validation pourrait-elle détecter ce cas ?

---

## Exercice 5 : Fonction, dataclass ou classe ?

Pour chaque élément, choisissez **fonction**, **dataclass** ou **classe**, et justifiez en une phrase.

1. Convertir une date `AAAA-MM-JJ` en objet `date`
2. Décrire une table à ingérer (nom, nom cible, requête facultative)
3. Lire plusieurs tables d'une même base PostgreSQL en réutilisant la connexion.
4. Supprimer les espaces des colonnes texte d'un DataFrame
5. Le compte rendu d'exécution d'une table (source, table, statut, lignes, durée, erreur)
6. Écrire des fichiers dans S3 en réutilisant le même client
7. Construire la clé de destination `raw/<source>/<table>/…` à partir de 3 chaînes
8. Un compteur de lignes écrites, incrémenté au fil du run et lu à la fin

---

## Exercice 6 : Quel pattern, et pourquoi ?

Pour chaque situation : un pattern (Template Method, Adapter, Factory, Strategy), ou aucun, justifiez pourquoi on en a, ou on n'en à pas besoin selon le cas

1. il faut ajouter une source oracle au projet (pilote `oracledb`)
2. le service Finance veut les fichiers en excel en plus du Parquet
3. une source api_rest paginée renvoie du JSON (pas de SQL)
4. toutes les sources doivent désormais compter les lignes lues et refuser un résultat vide
5. il faut écrire dans Azure Blob Storage au lieu de S3 sur un environnement
6. une fonction `to_snake_case` doit gérer les sigles (`HTTPResponse`)
7. un collègue propose un "Singleton" pour la configuration « pour éviter de la recharger »

---

## Exercice 7 : un nouveau format de sortie à prendre en compte

**Point de départ** : (on copie la aprtie structure au niveau de notre dossier de travail nommé "mon_travail" par exemple) :
 `cp -R version_finale mon_travail/ex7` (et pour le lancer à cet emplcement: `PYTHONPATH=src python -m fhvi_ingestion …`)

L'équipe d'intégration veut recevoir certaines tables en JSON Lines (un objet JSON par ligne)

1. dans `src/fhvi_ingestion/writers/formats.py`, ajoutez une stratégie `JsonLinesFormat` (extension `jsonl`)
2. rendez-la disponible pour la configuration (`format: jsonl`)
3. écrivez une config locale `config/pipeline_jsonl.yaml` pour la table `produits` de la pharmacie, lancez-la,
   ouvrez le fichier
4. quels fichiers avez-vous modifiés ? Lesquels n'avez-vous pas eu besoin de modifier, et pourquoi ?

---

## Exercice 8 : écrire des tests

**Point de départ** : la copie de l'exercice 7 (`mon_travail/ex7`), lancer `PYTHONPATH=src pytest`.

Créez `tests/unit/test_exercices.py` avec :

1. un test **paramétré** vérifiant que `--load-date` refuse `2026-02-30`, `09/11/2026`, `hier` et une chaîne vide
2. un test de `JsonLinesFormat` : 2 lignes produites, chaque ligne est un JSON valide, les dates au format ISO
3. un test vérifiant que `jsonl` est bien enregistré dans `FORMATS`
4. un test « documentaire » sur `to_snake_case("HTTPResponse")` : que renvoie la fonction ? Faut-il corriger
   le code ou figer ce comportement
5. un test qui vérifie, avec un `MagicMock`, que `S3Storage.put` appelle `put_object` avec le bon bucket

Lancez `pytest -m "not integration"` : tout doit être vert

---

## Exercice 9 : Traçabilité et exploitation

**Point de départ** : votre copie `mon_travail/ex7`

1. Ajoutez une colonne technique `_source_type` (postgres, mariadb, duckdb…), et édaptez le pipeline et les tests
   Vérifiez dans le bucket (`inspect_bucket.py --show-latest`)
2. Lancez `fhvi-ingest --config config/pipeline_demo_erreurs.yaml` (dans `version_finale/`) :
   1. Quel est le statut du run ? Le code retour ?
   2. Quelles tables ont été chargées malgré les erreurs ?
   3. Comment retrouver toutes les lignes de log de ce run dans un fichier de log ?
   4. Où trouver, sans les logs, la liste des tables en échec ?
3. Classez ces informations dans une catégorie (log, métadonnée de données, manifeste, ou aucune) :
   le nombre de lignes lues | l'identifiant d'un patient en erreur | l'heure d'extraction d'une ligne | la pile
   d'appel d'une erreur | le statut global du run | le mot de passe de connexion | la source d'origine d'une
   ligne | la durée d'écriture d'une table

Merci ! N'hésitez pas à revenir vers nous si vous avez des questions, et bon courage pour la suite :)
