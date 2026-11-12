# Glossaire

| Terme | Définition | Dans le projet |
|---|---|---|
| **Abstraction (classe abstraite, ABC)** | Classe qui définit un contrat sans implémentation complète ; on ne peut pas l'instancier | `BaseConnector(ABC)` |
| **Adapter** | Pattern qui enveloppe une API existante pour lui donner l'interface attendue | `DuckDBConnector`, `SqlAlchemyConnector` |
| **API (Application Programming Interface)** | Interface qui permet à un programme d'en utiliser un autre | l'API S3, appelée par `boto3` |
| **argparse** | Module standard Python pour lire les arguments de la ligne de commande (les « arguments du main ») | `cli.py` |
| **Attribut** | Donnée portée par un objet (`self.x`) | `self._engine` |
| **Authentification Windows (Trusted Connection)** | Connexion SQL Server avec l'identité Windows du processus (compte de service), sans mot de passe dans la configuration | `trusted_connection: true` |
| **Bucket** | Conteneur de fichiers dans un stockage objet (S3 et compatibles) | `fhvi-landing` |
| **CLI (Command Line Interface)** | Interface en ligne de commande d'un programme : on le pilote par des arguments | `fhvi-ingest --help` |
| **Click** | Bibliothèque Python de création de lignes de commande par décorateurs, avec sous-commandes | `exemples/cli_click.py` |
| **Code retour (exit code)** | Entier renvoyé par un programme au système : 0 = succès. Lu par les ordonnanceurs | 0 / 1 / 2 |
| **Collation** | Règles de tri et de comparaison des textes d'une base SQL Server (sensibilité à la casse, aux accents) | `French_CI_AS` |
| **Composition root** | Endroit unique où les objets concrets sont créés et assemblés | `app.py` / `main.py` |
| **Compte de service** | Compte technique utilisé par un traitement automatique (et non par une personne) | `fhvi_reader` (lecture seule) |
| **Connecteur** | Composant qui sait lire une technologie de source | `connectors/` |
| **CSV (Comma-Separated Values)** | Fichier texte tabulaire : une ligne par enregistrement, des colonnes séparées par un caractère | `resultats_labo.csv` (séparateur `;`) |
| **Dataclass** | Classe de données générée par `@dataclass` (`__init__`, `__repr__`, `__eq__` automatiques) | `SourceConfig`, `TableConfig` |
| **db_datareader** | Rôle SQL Server donnant le droit de lecture sur toutes les tables d'une base | compte du kit |
| **dbt** | Outil qui transforme les données déjà chargées dans l'entrepôt à l'aide de requêtes SQL versionnées et testées | lit les fichiers de la landing zone, d'où l'importance de l'idempotence |
| **Docker Compose** | Outil qui démarre ensemble plusieurs conteneurs décrits dans un fichier YAML | `docker-compose.yml`, `docker compose up -d` |
| **Docstring** | Chaîne de documentation en tête de module, classe ou fonction | `"""Lit intégralement…"""` |
| **Doublure de test (fake)** | Implémentation simplifiée utilisée à la place d'une vraie dépendance en test | `FakeConnector`, `InMemoryStorage` |
| **DPI (Dossier Patient Informatisé)** | Logiciel central d'un hôpital qui regroupe le dossier de chaque patient : identité, séjours, comptes rendus, prescriptions | source `dpi_nord` (PostgreSQL) : tables `patients`, `sejours`, `services` |
| **Dry-run** | Exécution « à blanc » : tout est fait sauf l'écriture | `--dry-run`, `DryRunStorage` |
| **DSI (Direction des Systèmes d'Information)** | Service informatique de l'établissement : postes, droits, serveurs, réseau | à solliciter pour les droits d'installation de Docker |
| **DuckDB** | Base analytique embarquée dans un fichier (sans serveur) | `pharmacie.duckdb` |
| **DWH (Data Warehouse, entrepôt de données)** | Base qui centralise et historise les données de plusieurs sources pour l'analyse et le reporting | le DWH FHVI, sur SQL Server |
| **Effet de bord** | Modification d'un état extérieur à la fonction (argument, variable globale, fichier) | `normalize` n'en a pas |
| **Encapsulation** | Masquer les détails internes d'un objet et n'exposer que le nécessaire | `_engine` vs `extract()` |
| **`.env`** | Fichier local de variables d'environnement, jamais versionné | `2_projet_python/.env` |
| **ETL / ELT** | Extract-Transform-Load : extraire, transformer, puis charger. En ELT, on charge d'abord le brut, puis on transforme dans l'entrepôt | le projet fait le « EL » vers la landing zone ; dbt fait le « T » |
| **Factory** | Pattern qui centralise la création d'objets selon un critère | `create_connector()` |
| **Fixture** | Ressource de test préparée par pytest, injectée par son nom | `raw_df`, `tmp_path`, `duckdb_file` |
| **Healthcheck** | Commande qui indique si un conteneur est prêt | `docker compose ps` → `healthy` |
| **Idempotence** | Relancer un traitement produit le même résultat, sans doublon ni effet indésirable | `write_mode: overwrite_partition` |
| **Image / conteneur Docker** | Une image est un modèle prêt à l'emploi (logiciel et configuration) ; un conteneur est une image en cours d'exécution | image `postgres:16-alpine` → conteneur `fhvi-postgres` |
| **Injection de dépendances** | Fournir à un composant les objets dont il a besoin au lieu qu'il les crée | `IngestionPipeline(writer, run, connector_factory)` |
| **Instance** | Objet créé à partir d'une classe | `PostgresConnector(source)` |
| **Instance nommée** | Plusieurs SQL Server sur une même machine, désignés `SERVEUR\INSTANCE` | `SRV-FACT01\PROD` |
| **Interpolation** | Remplacement de `${VAR}` par la valeur d'une variable d'environnement | `interpolate_env()` |
| **IPP (Identifiant Permanent du Patient)** | Numéro unique attribué à un patient par un établissement, utilisé à la place de son nom pour relier ses données | `IPP0000042` (fictif) |
| **JSON (JavaScript Object Notation)** | Format texte structuré en clés et valeurs, lisible par les humains comme par les programmes | manifeste `raw/_runs/…/<run_id>.json` |
| **Landing zone** | Zone de stockage des données brutes extraites des sources, avant transformation | `raw/` du bucket |
| **Logging** | Journalisation applicative horodatée et hiérarchisée par niveaux | `logging_setup.py` |
| **Manifeste** | Fichier décrivant une exécution (statut, tables, volumes, durées) | `raw/_runs/…/<run_id>.json` |
| **Marker (pytest)** | Étiquette pour classer et filtrer des tests | `@pytest.mark.integration` |
| **Métadonnées techniques** | Colonnes ajoutées aux données pour en tracer l'origine | `_run_id`, `_source_name`… |
| **Méthode** | Fonction définie dans une classe, qui reçoit l'objet (`self`) | `connector.extract(table)` |
| **Mock** | Objet simulé qui enregistre les appels reçus pour les vérifier | `MagicMock()`, `@patch(...)` |
| **Module / package** | Fichier `.py` / dossier contenant un `__init__.py` | `ingestion/`, `fhvi_ingestion/` |
| **Mutuellement exclusives (options)** | Options de ligne de commande qui ne peuvent pas être combinées | `--sources` / `--tables` / `--rerun-failed` |
| **NOLOCK** | Indicateur SQL Server de lecture sans verrou (peut lire des données non validées) | exemple de configuration FHVI |
| **Normalisation** | Mise en conformité des données (noms de colonnes, espaces…) | `normalize()` |
| **ODBC / pilote ODBC** | Interface standard d'accès aux bases ; Microsoft fournit *ODBC Driver 18 for SQL Server* | mode `pyodbc` |
| **Ordonnanceur (orchestrateur)** | Outil qui lance les traitements à heure fixe ou selon des dépendances, et alerte en cas d'échec | SSIS, Dagster, Airflow, cron : ils lisent le code retour |
| **Parquet** | Format de fichier colonnaire, typé et compressé | fichiers du bucket |
| **Partition (remplacement de)** | Écrire la nouvelle version d'une partition puis supprimer l'ancienne : c'est ce qui rend un rejeu idempotent | `DatasetWriter.write` |
| **Partition (style Hive)** | Rangement des fichiers par dossier `clé=valeur` | `load_date=2026-11-09/` |
| **Pseudonymisation** | Remplacement des identifiants directs par des identifiants non signifiants | IPP fictifs |
| **pymssql / pyodbc** | Pilotes Python pour SQL Server : pymssql s'installe par `pip` seul ; pyodbc s'appuie sur le pilote ODBC installé sur la machine | `SqlServerConnector` |
| **pyproject.toml** | Fichier standard décrivant un projet Python (dépendances, outils, commandes) | `version_finale/pyproject.toml` |
| **pytest** | Outil de tests Python | `pytest -m "not integration"` |
| **RDV** | Abréviation de rendez-vous | source `rdv_sud` (MariaDB), table `RENDEZ_VOUS` |
| **Registre** | Dictionnaire associant un nom à une classe, rempli par décorateur | `_REGISTRY` |
| **Rejeu** | Relancer un traitement passé : les tables en échec d'un run, une table précise ou une date passée | `--rerun-failed`, `--tables`, `--load-date` |
| **RGPD (Règlement Général sur la Protection des Données)** | Règlement européen sur les données personnelles ; les données de santé y sont des données sensibles | données 100 % fictives, IPP inventés, aucun nom |
| **Rosetta** | Émulateur d'Apple qui fait tourner des programmes prévus pour Intel sur un Mac Apple Silicon | nécessaire pour l'image SQL Server |
| **ruff** | Linter / formateur Python rapide | `ruff check src tests` |
| **run_id** | Identifiant unique d'une exécution | `20261109T125936Z-08d28736` |
| **S3 (API)** | Protocole de stockage objet d'AWS, implémenté par SeaweedFS, MinIO, Garage… | `boto3` |
| **Schéma (SQL Server)** | Espace de noms qui regroupe des tables dans une base (`fact`, `dbo`, `stg`…) | `fact.Prestations` |
| **SeaweedFS** | Stockage objet open source compatible S3 | service `seaweedfs` |
| **SGBD (Système de Gestion de Base de Données)** | Logiciel qui stocke les données et permet de les interroger en SQL | PostgreSQL, MariaDB, SQL Server, DuckDB |
| **Snake_case** | Convention `mots_en_minuscules_separes_par_des_tirets_bas` | `dispensation_id` |
| **SQL Server** | SGBD de Microsoft ; moteur du DWH et du Hub FHVI | source `fact_ouest` |
| **SQLAlchemy** | Bibliothèque Python d'accès aux bases SQL | `SqlAlchemyConnector` |
| **sqlcmd / SSMS** | Outil en ligne de commande / interface graphique de Microsoft pour SQL Server | `docker exec … sqlcmd` |
| **SSIS (SQL Server Integration Services)** | Outil de Microsoft pour construire et planifier des flux de chargement de données vers SQL Server | les flux actuels du DWH ; `fhvi-ingest` pourrait être lancé par un ordonnanceur à leur place |
| **Statut de run** | SUCCESS (tout OK), PARTIAL (au moins un échec et un succès), FAILED (tout en échec) | `report.py` |
| **Strategy** | Pattern qui rend un comportement interchangeable via un objet | `FileFormat`, `Storage` |
| **Template Method** | Pattern où une classe mère fixe un algorithme et délègue certaines étapes aux sous-classes | `BaseConnector.extract()` |
| **Test d'intégration** | Test qui fait collaborer de vrais composants (bases, bucket) | `tests/integration/` |
| **Test unitaire** | Test isolé, rapide, d'une unité de code (fonction, classe) | `tests/unit/` |
| **Typage (annotations)** | Indication des types attendus (`-> pd.DataFrame`), vérifiable par l'éditeur | partout |
| **UF (Unité Fonctionnelle)** | Plus petite subdivision d'un service hospitalier, à laquelle on rattache les actes et les coûts | colonne `CodeUF` de `fact.Prestations` |
| **venv** | Environnement Python isolé propre au projet | `2_projet_python/.venv` |
| **Volume Docker** | Espace de stockage géré par Docker qui conserve les données d'un conteneur entre deux redémarrages | `pg_data`, effacé par `docker compose down -v` |
| **WSL 2 (Windows Subsystem for Linux)** | Couche Linux intégrée à Windows, sur laquelle s'appuie Docker Desktop | prérequis de Docker sous Windows |
| **YAML** | Format texte de configuration lisible (indentation significative) | `config/pipeline.yaml` |
