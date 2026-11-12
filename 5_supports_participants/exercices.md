# Exercices

La session dure 2 h et se concentre sur les démonstrations : **la pratique, c'est ici, après la session**.
Les 12 exercices suivent l'ordre des modules vus en séance et portent tous sur le projet fil rouge
(environ 4 h au total, à répartir sur une à deux semaines ; corrigés envoyés après vos rendus).
Pour chaque exercice, les slides masquées du diaporama (notions approfondies) et les `fiches_synthetiques.md`
servent de support.
Travaillez **toujours dans une copie** du dossier de l'étape, jamais dans les dossiers de référence :

```bash
# depuis 2_projet_python/
mkdir -p mon_travail
cp -R etapes_intermediaires/0X_nom_etape mon_travail/exN     # (ou version_finale)
```

Le fichier `.env` de `2_projet_python/` est trouvé automatiquement depuis `mon_travail/exN/`.

| N° | Module | Type | Durée indicative |
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

## Exercice 1 — Diagnostic du script initial (M1)

**Fichier** : `version_initiale/ingestion_initiale.py`

1. Exécutez le script depuis `version_initiale/`, puis depuis `2_projet_python/`. Que constatez-vous ?
2. Listez **au moins 8 défauts**, en indiquant pour chacun la ligne concernée et sa conséquence concrète.
3. Classez vos défauts dans ces 6 familles : maintenance · multi-sources · testabilité · paramètres ·
   exploitation · traçabilité.
4. Le mot de passe PostgreSQL change : combien de lignes modifiez-vous ? Et avec 5 sources PostgreSQL ?
5. Trouvez le défaut qui produit des **données incohérentes** entre sources. Comment le prouver en
   inspectant le bucket ?

---

## Exercice 2 — Factoriser (M2-M3)

**Point de départ** : `cp -R etapes_intermediaires/1_structure mon_travail/ex2`

1. Dans `ingestion/sources.py`, surlignez ce qui diffère entre les 5 fonctions `extract_*`.
2. Créez `ingestion/extract.py` avec deux fonctions :
   `read_sql_table(url: str, table: str) -> pd.DataFrame` et `read_duckdb_table(path: Path, table: str) -> pd.DataFrame`.
3. Créez `ingestion/transform.py` avec `normalize(df)` qui : renomme les colonnes en `snake_case`
   (`DispensationId` → `dispensation_id`) et supprime les espaces des colonnes texte. Elle **ne doit pas modifier**
   le DataFrame reçu.
4. Réécrivez `main.py` pour boucler sur une liste de sources.
5. Vérifiez dans le bucket que `dispensations` a maintenant des colonnes `snake_case` et des libellés propres.
6. Combien de lignes faut-il modifier pour ingérer aussi la table `services` de `dpi_nord` ?

---

## Exercice 3 — Exclure un établissement en erreur (M4)

**Point de départ** : `cp -R etapes_intermediaires/3_argparse mon_travail/ex3`

Un établissement est en maintenance cette nuit. L'ordonnanceur doit pouvoir lancer toutes les sources
**sauf** celle-là.

1. Ajoutez une option `-x / --exclude` acceptant une ou plusieurs sources, avec contrôle des valeurs autorisées,
   facultative, documentée dans `--help`.
2. Adaptez `main.py`.
3. Vérifiez :
   ```bash
   python main.py --exclude rdv_sud --dry-run   # dpi_nord et pharmacie seulement
   python main.py -x oracle                      # erreur explicite, code retour 2
   ```
4. Question : que doit-il se passer avec `--sources rdv_sud --exclude rdv_sud` ? Proposez un comportement
   et justifiez-le.

---

## Exercice 4 — Piloter par la configuration (M5)

**Point de départ** : `cp -R etapes_intermediaires/4_yaml mon_travail/ex4`

1. **Sans modifier aucun fichier `.py`**, ajoutez à l'ingestion la table `services` (PostgreSQL) et la
   table `PRATICIENS` (MariaDB, nom cible `praticiens`). Vérifiez dans le bucket.
2. Désactivez la source `pharmacie`. Vérifiez avec `--list-sources`, puis lancez-la quand même avec
   `--sources pharmacie`. Que constatez-vous ? Est-ce souhaitable ?
3. Créez `config/pipeline_minimisation.yaml` : destination **locale** au format **CSV**, source `rdv_sud`
   uniquement, table `RENDEZ_VOUS` limitée aux colonnes `ID_RDV`, `DATE_RDV`, `SPECIALITE`, `STATUT`
   (pas d'IPP). Lancez-la et vérifiez le fichier produit.
4. Introduisez **3 erreurs différentes** dans une copie du YAML. Prédisez les messages, puis vérifiez.
5. Écrivez `enable: false` (sans « d ») sur une source. Que se passe-t-il ? Comment la validation
   pourrait-elle détecter ce cas ?

---

## Exercice 5 — Fonction, dataclass ou classe ? (M6 · réflexion)

Pour chaque élément, choisissez **fonction**, **dataclass** ou **classe**, et justifiez en une phrase.

1. Convertir une date `AAAA-MM-JJ` en objet `date`.
2. Décrire une table à ingérer (nom, nom cible, requête facultative).
3. Lire plusieurs tables d'une même base PostgreSQL en réutilisant la connexion.
4. Supprimer les espaces des colonnes texte d'un DataFrame.
5. Le compte rendu d'exécution d'une table (source, table, statut, lignes, durée, erreur).
6. Écrire des fichiers dans S3 en réutilisant le même client.
7. Construire la clé de destination `raw/<source>/<table>/…` à partir de 3 chaînes.
8. Un compteur de lignes écrites, incrémenté au fil du run et lu à la fin.

---

## Exercice 6 — Quel pattern, et pourquoi ? (M7 · réflexion)

Pour chaque situation : un pattern (Template Method, Adapter, Factory, Strategy) **ou aucun**. Justifiez.

1. Il faut ajouter une source **Oracle** au projet (pilote `oracledb`).
2. Le service Finance veut les fichiers en **Excel** en plus du Parquet.
3. Une source **API REST** paginée renvoie du JSON (pas de SQL).
4. Toutes les sources doivent désormais **compter les lignes** lues et refuser un résultat vide.
5. Il faut écrire dans **Azure Blob Storage** au lieu de S3 sur un environnement.
6. Une fonction `to_snake_case` doit gérer les sigles (`HTTPResponse`).
7. Un collègue propose un **Singleton** pour la configuration « pour éviter de la recharger ».

---

## Exercice 7 — Un nouveau format de sortie (M7 · Strategy)

**Point de départ** : `cp -R version_finale mon_travail/ex7` (pour lancer : `PYTHONPATH=src python -m fhvi_ingestion …`
depuis `mon_travail/ex7/`)

L'équipe d'intégration veut recevoir certaines tables en **JSON Lines** (un objet JSON par ligne).

1. Dans `src/fhvi_ingestion/writers/formats.py`, ajoutez une stratégie `JsonLinesFormat` (extension `jsonl`).
2. Rendez-la disponible pour la configuration (`format: jsonl`).
3. Écrivez une config locale `config/pipeline_jsonl.yaml` pour la table `produits` de la pharmacie, lancez-la,
   ouvrez le fichier.
4. Quels fichiers avez-vous modifiés ? Lesquels n'avez-vous **pas** eu besoin de modifier, et pourquoi ?

---

## Exercice 8 — Écrire des tests (M8)

**Point de départ** : votre copie de l'exercice 7 (`mon_travail/ex7`), lancer `PYTHONPATH=src pytest`.

Créez `tests/unit/test_exercices.py` avec :

1. un test **paramétré** vérifiant que `--load-date` refuse `2026-02-30`, `09/11/2026`, `hier` et une chaîne vide ;
2. un test de `JsonLinesFormat` : 2 lignes produites, chaque ligne est un JSON valide, les dates sont au format ISO ;
3. un test vérifiant que `jsonl` est bien enregistré dans `FORMATS` ;
4. un test « documentaire » sur `to_snake_case("HTTPResponse")` : que renvoie la fonction ? Faut-il corriger
   le code ou figer ce comportement ? Discutez-en en binôme ;
5. **bonus** : un test qui vérifie, avec un `MagicMock`, que `S3Storage.put` appelle `put_object` avec le bon bucket.

Lancez `pytest -m "not integration"` : tout doit être vert.

---

## Exercice 9 — Traçabilité et exploitation (M9)

**Point de départ** : votre copie `mon_travail/ex7`.

1. Ajoutez une colonne technique `_source_type` (postgres, mariadb, duckdb…). Adaptez le pipeline et les tests.
   Vérifiez dans le bucket (`inspect_bucket.py --show-latest`).
2. Lancez `fhvi-ingest --config config/pipeline_demo_erreurs.yaml` (dans `version_finale/`) et répondez :
   1. Quel est le statut du run ? Le code retour ?
   2. Quelles tables ont été chargées malgré les erreurs ?
   3. Comment retrouver **toutes** les lignes de log de ce run dans un fichier de log ?
   4. Où trouver, sans les logs, la liste des tables en échec ?
3. Classez ces informations : **log**, **métadonnée de données**, **manifeste**, ou **nulle part** :
   le nombre de lignes lues · l'IPP d'un patient en erreur · l'heure d'extraction d'une ligne · la pile
   d'appel d'une erreur · le statut global du run · le mot de passe de connexion · la source d'origine d'une
   ligne · la durée d'écriture d'une table.

---

## Exercice 10 — Exercice final de synthèse : intégrer la source `labo_est` (CSV)

**Contexte** — Le laboratoire de l'établissement Est dépose chaque nuit un export CSV dans
`3_environnement_docker/data/csv_labo_est/resultats_labo.csv` (séparateur `;`, décimales à la virgule,
libellés parfois suivis d'un espace). Il faut l'ingérer dans la landing zone comme les autres sources.

**Point de départ** : `cp -R version_finale mon_travail/ex10`

1. **Concevoir** (avant de coder) : écrivez le pseudo-code de l'outil complet, puis la liste des fichiers à
   créer ou modifier. Quels fichiers ne doivent **pas** changer ?
2. **Implémenter** : créez `src/fhvi_ingestion/connectors/csv_connector.py` contenant `CsvConnector`
   (type `csv`, clé obligatoire `path` = dossier). Chaque fichier `<nom>.csv` du dossier est une table `<nom>`.
   Les options `delimiter` et `decimal_separator` sont facultatives. Les requêtes SQL du YAML (`query`)
   doivent continuer à fonctionner. *Indice : DuckDB sait lire un CSV (`read_csv`).*
3. **Enregistrer** le connecteur pour la factory.
4. **Configurer** la source `labo_est` dans `config/pipeline.yaml`.
5. **Tester** : au moins 3 tests unitaires (lecture avec conventions françaises, requête SQL, dossier absent).
   Tous les tests existants doivent rester verts — un test d'intégration devra être mis à jour : lequel, et pourquoi ?
6. **Vérifier** : `fhvi-ingest --sources labo_est`, contrôler dans le bucket : colonnes `snake_case`,
   `valeur` numérique, libellés sans espace, métadonnées, manifeste.
7. **Restituer** (5 min par binôme, lors du point de suivi de 30 min prévu après la session) : ce que vous avez modifié, ce que vous n'avez pas eu à modifier, et pourquoi.

---

## Exercice 11 — Bonus SQL Server : de la base de formation à vos serveurs

**Contexte** — La source `fact_ouest` tourne sur SQL Server, comme votre DWH et votre Hub. L'objectif est de
faire le lien entre ce que vous avez construit et votre environnement réel.

**Point de départ** : `cp -R version_finale mon_travail/ex11`

1. **Explorer comme au quotidien.** Connectez-vous à `localhost,51433` avec SSMS (ou `sqlcmd`, voir
   `prise_en_main_environnement.md`) avec le compte `fhvi_reader`.
   - Listez les schémas et tables : `SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY 1, 2`.
   - Tentez `DELETE FROM fact.Factures`. Que se passe-t-il ? Pourquoi est-ce exactement ce qu'on veut pour un flux d'ingestion ?
2. **Ajouter une table SQL Server sans code.** Dans `config/pipeline.yaml`, ajoutez `fact.Factures` à la source
   `fact_ouest`, avec le nom cible `factures` et une requête qui **n'extrait pas l'IPP**. Lancez
   `PYTHONPATH=src python -m fhvi_ingestion --sources fact_ouest` et vérifiez dans le bucket :
   `montant_total_eur` est numérique, `organisme` n'a plus d'espace final (`'Mutuelle '`), `date_emission` est une date.
3. **Le piège des dates.** Avant la version actuelle, `normalize()` faisait `.str.strip()` sur toutes les colonnes de
   type `object`. Expliquez pourquoi cela plantait sur `fact.Factures` et pas sur `fact.Prestations`.
   Quel test aurait détecté le problème plus tôt ?
4. **Votre serveur.** Rédigez la fiche YAML d'**une de vos bases SQL Server réelles** (une table suffit), en
   **authentification Windows**, sans aucun mot de passe. Inspirez-vous de `config/exemple_serveurs_fhvi.yaml`.
   Listez les prérequis sur la machine qui exécutera le flux.
5. **Questions d'exploitation.**
   1. Votre instance n'accepte que quelques connexions simultanées (slots). Combien de connexions `fhvi-ingest`
      ouvre-t-il pour une source de 10 tables ? Où est-ce visible dans le code ?
   2. Faut-il ajouter `WITH (NOLOCK)` dans les requêtes ? Donnez un argument pour et un argument contre.
   3. Le DWH charge aujourd'hui les données via SSIS et des procédures stockées. Où se situerait `fhvi-ingest`
      dans cette chaîne, et qu'est-ce qui changerait pour l'équipe ?

---

## Exercice 12 — Arguments du main, rejeu et idempotence

**Contexte** — Un traitement de nuit sera relancé un jour (panne, correction, date oubliée). Il doit pouvoir
rejouer **seulement** ce qu'il faut, et relancer ne doit **jamais** créer de doublon.

**Point de départ** : `cp -R version_finale mon_travail/ex12` (lancer avec `PYTHONPATH=src python -m fhvi_ingestion …`
depuis `mon_travail/ex12/`, ou directement `fhvi-ingest` depuis `version_finale/`).

1. **Les arguments du main.** Lancez `fhvi-ingest --help`. Listez les arguments qui servent à choisir *quoi*
   lancer, et ceux qui servent à choisir *comment*. Pourquoi `--sources`, `--tables` et `--rerun-failed` sont-ils
   exclusifs ? Essayez de les combiner.
2. **Même interface avec click.** Lancez `python exemples/cli_click.py --help`, puis
   `python exemples/cli_click.py tables fact_ouest.prestations --dry-run`. Citez deux avantages de click et un
   argument pour rester sur argparse.
3. **Rejouer les échecs d'une nuit.**
   - Arrêtez MariaDB (`docker stop fhvi-mariadb`) et lancez `fhvi-ingest --load-date 2026-11-09`. Notez le
     statut, le code retour et le `run_id`.
   - Redémarrez MariaDB, attendez qu'elle soit `healthy`, puis lancez `fhvi-ingest --rerun-failed <run_id>`.
   - Quelles tables ont été rejouées ? À quelle date de chargement ? Que contient `replay_of` dans le nouveau
     manifeste (`inspect_bucket.py --prefix raw/_runs`) ?
4. **Idempotence.**
   - Lancez **deux fois** `fhvi-ingest -c config/pipeline_rejeu.yaml --load-date 2025-03-14`. Combien de lignes
     à chaque fois ? Combien de fichiers dans la partition `raw/fact_ouest/prestations_du_jour/load_date=2025-03-14/` ?
     Quel message de log apparaît au second passage ?
   - Créez une configuration **locale** (destination `local`, format `csv`) pour la table `produits` de la
     pharmacie, avec `write_mode: append`. Lancez-la deux fois pour la même date, puis comptez les lignes de la
     partition. Recommencez avec `write_mode: overwrite_partition`. Expliquez la différence et le risque pour dbt.
5. **Réflexion.**
   1. Pourquoi le writer **écrit-il d'abord** le nouveau fichier avant de supprimer les anciens ?
   2. Que se passe-t-il si deux exécutions de la même source tournent en même temps ? Qui doit l'empêcher ?
   3. Pour une source réellement incrémentale (un curseur `updated_at`), que faudrait-il ajouter pour qu'un
      rejeu reste idempotent ?
