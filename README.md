# Schéma général de l'env mis en place

Environnement local, reproductible et sans cloud, qui simule le contexte FHVI :
plusieurs sources hétérogènes et une landing zone en stockage objet S3.

```
                     ┌─────────────────────────────┐
 PostgreSQL 16  ───▶ │                             │
 "DPI Hôpital Nord"  │                             │      SeaweedFS (API S3)
 localhost:55432     │      Projet Python          │      bucket fhvi-landing
                     │      (votre poste ou        │ ───▶ localhost:58333
 MariaDB 11.4   ───▶ │       conteneur runner)     │      explorateur web :
 "RDV Clinique Sud"  │                             │      localhost:58888/buckets/
 localhost:53306     │                             │
                     │                             │
 SQL Server 2022 ──▶ │                             │
 "Facturation Ouest" │                             │
 localhost:51433     │                             │
                     │                             │
 DuckDB (fichier) ─▶ │                             │
 data/pharmacie.duckdb└────────────────────────────┘
```

| Service | Image | Port hôte | Contenu |
|---|---|---|---|
| `postgres` | `postgres:16-alpine` | 55432 | base `dpi_nord` : `patients` (500), `sejours` (1 200), `services` (8) |
| `mariadb` | `mariadb:11.4` | 53306 | base `rdv_sud` : `RENDEZ_VOUS` (800), `PRATICIENS` (8) |
| `sqlserver` | `mcr.microsoft.com/mssql/server:2022-latest` (Developer) | 51433 | base `FACTURATION_OUEST` : `fact.Prestations` (1 000), `fact.Factures` (250) |
| `sqlserver-init` | idem | / | crée la base, le schéma `fact`, le compte de lecture `fhvi_reader` et les données, puis **s'arrête** |
| `seaweedfs` | `chrislusf/seaweedfs:3.80` | 58333 (S3), 58888 (web) | bucket `fhvi-landing` |
| `s3-init` | idem | / | crée le bucket puis **s'arrête** (c'est normal) |
| `runner` *(optionnel)* | construit par `Dockerfile` | / | Python 3.11 + dépendances |
| *(fichier)* | / | / | `data/pharmacie.duckdb` : `dispensations` (1 500), `produits` (10) |

Toutes les données sont **fictives** et **pseudonymisées** (aucun nom, uniquement
des IPP fictifs). Elles sont générées de façon **déterministe** : deux
participants obtiennent exactement les mêmes lignes.

Pourquoi SeaweedFS ? Stockage objet open source, compatible S3, léger, avec un
explorateur web intégré. Le code Python utilise `boto3` : il fonctionnerait à
l'identique avec Garage, MinIO ou un vrai bucket S3 (seule l'URL change).

# Schéma général de l'outil d'ingestion industrialisé

Ce pseudo-code décrit **ce que fait** `fhvi-ingest`, indépendamment de Python. 


```
┌──────────────┐   ┌───────────────┐   ┌─────────────┐   ┌────────────────────────────────────────────┐
│ Ligne de     │──▶│ Contexte du   │──▶│ Configuration│──▶│ Pipeline                                   │
│ commande     │   │ run (run_id)  │   │ YAML validée │   │  pour chaque source → pour chaque table :  │
│              │   │ + logs        │   │              │   │  extraire → normaliser → métadonnées →     │
└──────────────┘   └───────────────┘   └─────────────┘   │  écrire ; erreurs isolées.                  │
                                                          └───────────────┬────────────────────────────┘
                                                                          ▼
                                     Bucket S3 : données Parquet + manifeste du run ; code retour

Sources du kit : PostgreSQL,  MariaDB,  SQL Server (moteur FHVI),  DuckDB
```