# Ensemble des commandes utilisées lors de la formation

## Au début

### Définir le répertoire de travail


```bash
export FHVI="$(pwd)"
```

### Vérifier le contenu du projet Python


```bash
ls "$FHVI/2_projet_python"
```

### Activer l'environnement virtuel Python


```bash
source "$FHVI/2_projet_python/.venv/bin/activate"
```

### Réinitialiser l'environnement Docker


```bash
cd "$FHVI/3_environnement_docker"
./scripts/reset.sh
```

**Explorateur du bucket :** [http://localhost:58888/buckets/fhvi-landing/](<http://localhost:58888/buckets/fhvi-landing/>)

---

## Slide 5  : Vérification des conteneurs Docker


```bash
cd "$FHVI/3_environnement_docker"
docker compose ps
```

---

## Slide 8  : Première ingestion


```bash
cd "$FHVI/2_projet_python/version_initiale"
python ingestion_initiale.py
```

---

## Slide 9  : Tests de l'ingestion initiale

### Test 1  : Exécution depuis un autre répertoire


```bash
cd "$FHVI/2_projet_python"
python version_initiale/ingestion_initiale.py
```

### Test 2  : Arrêt de MariaDB

Arrêter le conteneur MariaDB :


```bash
docker stop fhvi-mariadb
```

Relancer le script d'ingestion :


```bash
cd "$FHVI/2_projet_python/version_initiale"
python ingestion_initiale.py
```

Redémarrer MariaDB et vérifier son état :


```bash
docker start fhvi-mariadb
cd "$FHVI/3_environnement_docker"
docker compose ps
```

### Test 3  : Vérification des données dans le bucket


```bash
cd "$FHVI/2_projet_python/version_initiale"

python -c "import io, boto3, pandas as pd; from datetime import date; s3 = boto3.client('s3', endpoint_url='http://localhost:58333', aws_access_key_id='fhvi_access', aws_secret_access_key='fhvi_secret_2026', region_name='us-east-1'); cle = f'raw/pharmacie/dispensations/{date.today():%Y-%m-%d}/dispensations.parquet'; df = pd.read_parquet(io.BytesIO(s3.get_object(Bucket='fhvi-landing', Key=cle)['Body'].read())); print(df.columns.tolist()); print(df['servicedemandeur'].unique().tolist())"
```

---

## Slide 13  : Structuration du projet


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/1_structure"
python main.py
```

---

## Slide 14  : Présentation de la configuration

Afficher le fichier `.env.example`.

---

## Slide 15  : Factorisation du code

### Version factorisée


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/2_factorisation"
python main.py
```

### Inspection du bucket


```bash
cd "$FHVI/3_environnement_docker"
python scripts/inspect_bucket.py --show-latest dispensations --rows 3
```

---

## Slide 16  : Gestion des arguments avec argparse

### Afficher l'aide


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/3_argparse"
python main.py --help
```

### Exécuter un traitement en mode simulation


```bash
python main.py --sources fact_ouest --dry-run
```

### Tester une date invalide


```bash
python main.py --load-date 2026-13-45 ; echo "code retour :$?"
```

### Présentation de Click


```bash
cd "$FHVI/2_projet_python/version_finale"
python exemples/cli_click.py --help
```

---

## Slide 17  : Configuration avec YAML

### Afficher la configuration du pipeline


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/4_yaml"
cat config/pipeline.yaml
```

### Tester une configuration invalide


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/4_yaml"
python main.py --config config/pipeline_invalide.yaml ; echo "code retour :$?"
```

---

## Slide 19  : Modification de la configuration YAML

### 1\. Sauvegarder la fiche de configuration


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/4_yaml"
cp config/pipeline.yaml config/pipeline.yaml.bak
```

### 2\. Ajouter les deux tables


```bash
python -c "p='config/pipeline.yaml'; L=open(p,encoding='utf-8').read().splitlines(True); o=[]; [o.extend([l]+(['      - name: services\n'] if l.strip()=='- name: sejours' else [])+(['      - name: PRATICIENS\n','        target: praticiens\n'] if l.strip().startswith('target: rendez_vous') else [])) for l in L]; open(p,'w',encoding='utf-8').write(''.join(o)); print('2 tables ajoutees a la fiche')"
```

### 3\. Relancer le pipeline


```bash
python main.py --sources dpi_nord rdv_sud
```

### 4\. Restaurer la configuration d'origine


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/4_yaml"
mv config/pipeline.yaml.bak config/pipeline.yaml
```

---

## Slide 20  : Utilisation des variables d'environnement


```bash
HUB_SQL_USER=x HUB_SQL_PASSWORD=y fhvi-ingest --config config/exemple_serveurs_fhvi.yaml --list-sources
```

---

## Slide 24  : Design patterns

### Exécution en mode simulation


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/6_design_patterns"
python main.py --dry-run
```

---

## Slide 26  : Tests automatisés avec pytest

### Exécuter tous les tests


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/7_tests"
pytest
```

### 1\. Sauvegarder le fichier de transformation


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/7_tests"
cp ingestion/transform.py ingestion/transform.py.bak
```

### 2\. Casser volontairement le nettoyage

Supprimer l'appel à `.lower()` dans la fonction `to_snake_case` :


```bash
python -c "p='ingestion/transform.py'; L=open(p,encoding='utf-8').read().splitlines(True); M=[l.replace('.lower()','') if 're.sub(' in l and l.rstrip().endswith('.lower()') else l for l in L]; open(p,'w',encoding='utf-8').write(''.join(M)); print('.lower() retire de to_snake_case' if M!=L else 'ECHEC : rien modifie')"
```

### 3\. Relancer les tests de transformation


```bash
cd "$FHVI/2_projet_python/etapes_intermediaires/7_tests"
pytest tests/unit/test_transform.py -v
```

### 4\. Restaurer la fonction d'origine

Remettre la ligne suivante dans le fichier `ingestion/transform.py` :

python

```python
return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()
```

Relancer l'ensemble des tests :


```bash
pytest
```

### Exécuter la version finale du pipeline


```bash
cd "$FHVI/2_projet_python/version_finale"
fhvi-ingest
```

---

## Slide 27  : Gestion des erreurs

### Tester une configuration générant des erreurs


```bash
cd "$FHVI/2_projet_python/version_finale"
fhvi-ingest --config config/pipeline_demo_erreurs.yaml ; echo "code retour :$?"
```

---

## Slide 29  : Reprise sur incident et idempotence

### 1\. Simuler une panne nocturne

**Noter le****`run_id`****affiché lors de l'exécution.**


```bash
cd "$FHVI/2_projet_python/version_finale"
docker stop fhvi-mariadb
fhvi-ingest --load-date 2026-11-09
```

### 2\. Réparer l'environnement

Attendre environ 15 secondes, puis redémarrer MariaDB :


```bash
docker start fhvi-mariadb
```

Dans un deuxième terminal, vérifier que le conteneur est bien `healthy` :


```bash
cd "$FHVI/3_environnement_docker"
docker compose ps
```

### 3\. Rejouer les traitements en échec

Remplacer `<run_id_noté>` par le `run_id` précédemment relevé.


```bash
cd "$FHVI/2_projet_python/version_finale"
fhvi-ingest --rerun-failed <run_id_noté>
```

### 4\. Démontrer l'idempotence

Exécuter deux fois le même traitement avec la même date :


```bash
cd "$FHVI/2_projet_python/version_finale"

fhvi-ingest -c config/pipeline_rejeu.yaml --load-date 2025-03-14
fhvi-ingest -c config/pipeline_rejeu.yaml --load-date 2025-03-14
```

Vérifier le contenu du bucket :


```bash
cd "$FHVI/3_environnement_docker"
python scripts/inspect_bucket.py --prefix raw/fact_ouest/prestations_du_jour
```

---

## Slide 30  : Inspection des données


```bash
cd "$FHVI/3_environnement_docker"
python scripts/inspect_bucket.py --show-latest dispensations__ --rows 3
```

---

## Slide 32  : Aide de la commande finale


```bash
cd "$FHVI/2_projet_python/version_finale"
fhvi-ingest --help
```

---

## Remise à zéro de l'environnement (facultatif)

Pour réinitialiser complètement l'environnement :


```bash
cd "$FHVI/3_environnement_docker"
./scripts/reset.sh
```

## Arrêt de l'environnement sans perte de données

Pour arrêter les conteneurs Docker sans supprimer les volumes de données :


```bash
cd "$FHVI/3_environnement_docker"
docker compose down
```