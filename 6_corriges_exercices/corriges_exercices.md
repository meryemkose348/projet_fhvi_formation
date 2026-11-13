# Corrigés des exercices

| Exercice | Fichiers de solution |
|---|---|
| 2 | `2_projet_python/etapes_intermediaires/2_factorisation/` |
| 3 | `code/exercice_3_exclude.diff` |
| 4 | `code/exercice_4_pipeline_minimisation.yaml` |
| 7 | `code/exercice_7_jsonl.diff` |
| 8 | `code/test_exercice_8.py` |
| 9 | `code/exercice_9_source_type.diff` |
| 11 | `code/exercice_11_source_fact_ouest.yaml` |
| 12 | `version_finale/` (code de référence) + `code/exercice_12_append.yaml` | 

---

## Exercice 1 : Diagnostic

1. Depuis `version_initiale/` : succès. Depuis `2_projet_python/` : `IOException … pharmacie.duckdb … database does not exist`
    après  l'écriture de 4 tables → état partiel incohérent.
2. Défauts attendus (voir aussi `version_initiale/README.md`) :

| Défaut | Ligne(s) | Conséquence |
|---|---|---|
| Identifiants en clair | 13-15, 20, 43, 56 | fuite au premier commit ; rotation de mot de passe = modification de code |
| Paramètres dispersés (hôtes, ports, bucket) | 13-15, 20, 28, 38, 43, 51, 56, 64, 69, 75 | changer d'environnement = 10 modifications |
| 5 blocs copiés-collés | 19-77 | une correction = 5 modifications |
| `strip()` oublié pour DuckDB | 72 | `'Urgences '` ≠ `'Urgences'` : agrégats faux en aval |
| `lower()` ≠ snake_case | 22, 32, 45, 58, 71 | `dispensationid` illisible, incohérent avec `date_entree` |
| Chemin relatif au dossier courant | 69 | plante selon le dossier de lancement |
| Aucune gestion d'erreur | — | une source indisponible bloque toutes les suivantes |
| `print` | 11, 29, 39, 52, 65, 76, 79 | pas d'horodatage, pas de niveau, rien d'exploitable |
| Aucune fonction | — | impossible à tester unitairement, à réutiliser |
| Date calculée une fois, chemin `raw/<source>/<table>/<date>/` | 17 | une relance le même jour écrase silencieusement |
| Aucune traçabilité | — | impossible de relier un fichier à une exécution |
| Noms `df2`, `df5`, `engine3`, `d`, `buf` | partout | erreurs de copier-coller probables |
| Commentaire « NE PAS TOUCHER » | 1 | code qui fait peur = dette technique |

3. Maintenance : copier-coller, `strip` oublié, noms | Multi-sources : 1 bloc par table | Testabilité : aucune
   fonction | Paramètres : secrets, hôtes, chemins | Exploitation : erreurs, `print` | Traçabilité : écrasement, aucun identifiant
4. 1 ligne ici (l. 20, où l'url contient le mot de passe) avec 5 sources PostgreSQL, du coup 5 lignes… = 5 risques d'oubli
5. Le `strip()` manquant (l. 59) : `python scripts/inspect_bucket.py --show-latest dispensations` montre
   `' Oncologie'` et `'Urgences '` alors que dans `sejours`, les libellés sont nettoyés.

---

## Exercice 2 : Factoriser

Solution complète : `etapes_intermediaires/2_factorisation/` (`extract.py`, `transform.py`, `load.py`,
`sources.py`, `main.py`).

1. Ce qui diffère : l'URL / le chemin, le nom de la table, la technologie (SQLAlchemy vs DuckDB) — et le
   `strip()` oublié, qui n'aurait jamais dû différer.
3. Points de vigilance : `df.rename(columns=to_snake_case)` crée une  copie  (contrairement à
   `df.columns = …`) ; `select_dtypes(include="object")` cible les colonnes `object`, qui contiennent du texte… mais pas seulement (dates SQL Server `DATE`, voir exercice 11) : ne nettoyer que les valeurs `str`.
6.  Un mot  : `"tables": ["patients", "sejours", "services"]`.

---

## Exercice 3 : `--exclude`

Diff complet : `code/exercice_3_exclude.diff`

```python
#partie à ajouter dans build_parser()
parser.add_argument(
    "-x", "--exclude",
    nargs="+",
    choices=SOURCE_NAMES,
    default=[],
    metavar="SOURCE",
    help="Sources à exclure (ex: un établissement en erreur)",
)
```

```python
# main.py
selected = [s for s in SOURCES if s["name"] in args.sources and s["name"] not in args.exclude]
```

Sorties vérifiées :

```
$ python main.py --exclude rdv_sud --dry-run
$ python main.py -x oracle
```

4. Avec l'implémentation ci-dessus, `--sources rdv_sud --exclude rdv_sud` n'ingère rien, silencieusement
   2 comportements défendables : 
   (a) l'exclusion l'emporte mais on avertit qu'il n'y aura aucune source à ingérer
   (b) les options sont mutuellement exclusives, donc `parser.add_mutually_exclusive_group()` renvera une erreur avec
   argparse code 2
   
   La solution (b) est la plus sûre pour un ordonnanceur : une commande ambiguë est refusée

---

## Exercice 4 : piloter par la configuration

1. Ajouts YAML : voir `4_guide_formateur/demonstrations_live.md` §5.3. Résultat : `services` (8 lignes),
   `praticiens` (8 lignes). Aucun `.py` modifié.
2. `--list-sources` affiche `pharmacie … désactivée` ; `--sources pharmacie` la charge quand même : la CLI
   l'emporte sur `enabled`. C'est souhaitable pour un  rejeu manuel  ciblé ; à documenter.
3. Solution : `code/exercice_4_pipeline_minimisation.yaml` :
   ```yaml
       tables:
         - name: RENDEZ_VOUS
           target: rendez_vous
           query: SELECT ID_RDV, DATE_RDV, SPECIALITE, STATUT FROM RENDEZ_VOUS
   ```
   Vérifié : `output/raw/rdv_sud/rendez_vous/<date>/rendez_vous.csv`, en-tête `id_rdv,date_rdv,specialite,statut`.
4. Exemples : `type: oracle` => « type 'oracle' inconnu » => suppression de `password` => « connection.password
   est obligatoire » =< `${PG_HOTE}` → « variable d'environnement absente ». Toutes signalées ensemble, code 2.
5. `enable: false` est ignoré : la clé inconnue n'est pas contrôlée, la source reste active

---

## Exercice 5 : Fonction, dataclass ou classe ?

| # | Réponse | Justification |
|---|---|---|
| 1 | Fonction | transformation pure, aucun état (`valid_date`) |
| 2 | Dataclass | donnée structurée et typée, sans comportement (`TableConfig`) : une `@property sql` reste acceptable |
| 3 | Classe | état (connexion ouverte) + comportements (lire, fermer) (`PostgresConnector`) |
| 4 | Fonction | transformation pure (`normalize`) |
| 5 | Dataclass | enregistrement de résultat (`TableResult`) |
| 6 | Classe | état (client S3) + comportement (`S3Storage.put`) |
| 7 | Fonction (ou méthode du writer) | calcul pur ; méthode si elle dépend d'un état du writer (préfixe, format) |
| 8 | Classe (ou attribut d'une classe existante) | état qui évolue au fil du run (`RunReport` le fait déjà) |

---

## Exercice 6 — Quel pattern ?

| # | Réponse | Justification |
|---|---|---|
| 1 |  Adapter + Factory  (aucun nouveau pattern) | exactement comme `SqlServerConnector` (déjà dans le projet) : `class OracleConnector(SqlAlchemyConnector)` avec `driver = "oracle+oracledb"`, décorée `@register_connector("oracle")` + son import ; pipeline et factory inchangés. Spécificité Oracle : le *service name* se passe dans la query de l'URL -> surcharger `_build_url`, comme `SqlServerConnector` le fait pour son mode ODBC |
| 2 |  Strategy  | nouvelle `ExcelFormat(FileFormat)` ; aucune autre modification (dépendance `openpyxl`) |
| 3 |  Adapter  | `ApiConnector(BaseConnector)` : `_open` = session HTTP, `_read` = pagination + `pd.json_normalize` ; la `query` SQL n'a pas de sens → utiliser `name` comme endpoint |
| 4 |  Template Method  | à ajouter  une fois  dans `BaseConnector.extract()` ; toutes les sources en bénéficient |
| 5 |  Strategy  | `AzureBlobStorage(Storage)` + entrée dans `STORAGES` ; le choix se fait par `destination.type` |
| 6 |  Aucun  | c'est une correction de fonction (et un test paramétré de plus) |
| 7 |  Aucun  | la configuration est chargée une fois dans la composition root et  passée  aux composants ; un Singleton créerait un état global difficile à tester |

---

## Exercice 7 : JsonLinesFormat

Diff : `code/exercice_7_jsonl.diff`

```python
class JsonLinesFormat(FileFormat):
    """on définit une ligne json par enregistrement : ça c'est pratique pour les outils de logs et api"""
    extension = "jsonl"

    def serialize(self, df: pd.DataFrame) -> bytes:
        return df.to_json(orient="records", lines=True, date_format="iso", force_ascii=False).encode("utf-8")

FORMATS: dict[str, type[FileFormat]] = {"parquet": ParquetFormat, "csv": CsvFormat, "jsonl": JsonLinesFormat}
```

```yaml
# et au niveau de config/pipeline_jsonl.yaml on aura :
destination: {type: local, path: ./output, format: jsonl}
sources:
  - name: pharmacie
    type: duckdb
    connection: {path: ${DUCKDB_PATH}}
    tables: [{name: produits}]
```

comme début de sortie on a :

```json
{"code_ucd":"3400890000011","libelle_produit":"Paracétamol 1 g comprimé","classe_atc":"N02BE01","prix_unitaire":0.12,"_run_id":"20261109T132147Z-3e5ae068","_source_name":"pharmacie",…}
```

4.  Un seul fichier est modifié : `formats.py`
   et ce qui n'est pas modifié : la validation (qui lit `FORMATS`), le`DatasetWriter` (il utilise l'extension de la stratégie), le pipeline, la CLI et le `force_ascii=False` qui permet de conserver les accents, ainsi que `date_format="iso"` qui rend les dates lisibles

---

## Exercice 8 : Tests

`code/test_exercice_8.py` (on le place à l'endroit des tests unitaires : dans `tests/unit/`)

```python
@pytest.mark.parametrize("value", ["2026-02-30", "09/11/2026", "hier", ""])
def test_invalid_dates_are_refused(value):
    with pytest.raises(SystemExit):
        parse_args(["--load-date", value])


def test_known_limit_of_to_snake_case_with_acronyms():
    assert to_snake_case("HTTPResponse") == "httpresponse"
    assert to_snake_case("IDPatient") == "idpatient"
```

4. ce qui est intéressant ici, c'est que `to_snake_case("HTTPResponse")` renvoie `"httpresponse"`, et la règle n'insère `_` qu'entre une minuscule (ou un chiffre) et une majuscule. Corriger  (ajouter la règle `re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", …)` va donner `http_response`) : mais cela renomme des colonnes déjà en production , donc il faut décider si on opte pour l'option 1 ça reste en minusucle complet ou en snake_case, sinon on peut aussi  figer  le comportement par un test documentaire. Le test protège la décision quel que soit le choix d'option
5. il est déjà présent dans `tests/unit/test_writers.py::test_s3_storage_calls_put_object_with_a_mocked_client`
(on peut check le résultat en lançant un pytest)

---

## Exercice 9 : Traçabilité et exploitation

1. cf fichier diff
2. réponses uax questions :
   1. `PARTIAL`, code retour  1 
   2. `dpi_nord.patients` et `pharmacie.dispensations`
   3. `fhvi-ingest … --log-file logs/ingestion.log` puis `grep "<run_id>" logs/ingestion.log` , avec chaque ligne qui porte `run=<run_id>`
   4. Dans le  manifeste  `raw/_runs/load_date=<date>/<run_id>.json` : `tables_failed`, et pour chaque table `status` et `error`
3. Classement :

| Information | Où |
|---|---|
| Nombre de lignes lues | log (INFO)  et  manifeste (`rows`) |
| identifiant d'un patient en erreur |  nulle part  (donnée personnelle de santé) |
| Heure d'extraction d'une ligne | métadonnée (`_extracted_at`) |
| Pile d'appel d'une erreur | log (DEBUG) |
| Statut global du run | log (fin de run)  et  manifeste (`status`) |
| Mot de passe de connexion |  nulle part  |
| Source d'origine d'une ligne | métadonnée (`_source_name`) |
| Durée d'écriture d'une table | log (INFO)  et  manifeste (`duration_s`) |


Merci ! N'hésitez pas à revenir vers nous si vous avez des questions, et bon courage pour la suite :)
