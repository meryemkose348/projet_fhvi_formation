# script ingestion 01/06/2025, copie les tables vers le bucket S3 (ne pas toucher)

import pandas as pd
import duckdb
import boto3
import io
from datetime import datetime
from sqlalchemy import create_engine

print("debut")

s3 = boto3.client("s3", endpoint_url="http://localhost:58333",
                  aws_access_key_id="fhvi_access",
                  aws_secret_access_key="fhvi_secret_2026", region_name="us-east-1")

d = datetime.now().strftime("%Y-%m-%d")

# ---------------- POSTGRES : DPI hopital nord -----------------
engine = create_engine("postgresql+psycopg://fhvi_reader:fhvi_pg_2026@localhost:55432/dpi_nord")
df = pd.read_sql("select * from patients", engine)
df.columns = [c.lower() for c in df.columns]
for c in df.columns:
    if df[c].dtype == object:
        df[c] = df[c].str.strip()
buf = io.BytesIO()
df.to_parquet(buf, index=False)
s3.put_object(Bucket="fhvi-landing", Key="raw/dpi_nord/patients/" + d + "/patients.parquet", Body=buf.getvalue())
print("patients ok", len(df))

df2 = pd.read_sql("select * from sejours", engine)
df2.columns = [c.lower() for c in df2.columns]
for c in df2.columns:
    if df2[c].dtype == object:
        df2[c] = df2[c].str.strip()
buf = io.BytesIO()
df2.to_parquet(buf, index=False)
s3.put_object(Bucket="fhvi-landing", Key="raw/dpi_nord/sejours/" + d + "/sejours.parquet", Body=buf.getvalue())
print("sejours ok", len(df2))

# ---------------- MARIADB : rdv clinique sud -----------------
# copié collé du bloc postgres, j'ai changé l'url
engine2 = create_engine("mysql+pymysql://fhvi_reader:fhvi_maria_2026@localhost:53306/rdv_sud")
df3 = pd.read_sql("select * from RENDEZ_VOUS", engine2)
df3.columns = [c.lower() for c in df3.columns]
for c in df3.columns:
    if df3[c].dtype == object:
        df3[c] = df3[c].str.strip()
buf = io.BytesIO()
df3.to_parquet(buf, index=False)
s3.put_object(Bucket="fhvi-landing", Key="raw/rdv_sud/rendez_vous/" + d + "/rendez_vous.parquet", Body=buf.getvalue())
print("rdv ok", len(df3))

# ---------------- SQL SERVER : facturation hopital ouest -----------------
# encore un copier coller... attention le schema "fact." devant la table
engine3 = create_engine("mssql+pymssql://fhvi_reader:Fhvi_Reader_2026@localhost:51433/FACTURATION_OUEST")
df5 = pd.read_sql("select * from fact.Prestations", engine3)
df5.columns = [c.lower() for c in df5.columns]
for c in df5.columns:
    if df5[c].dtype == object:
        df5[c] = df5[c].str.strip()
buf = io.BytesIO()
df5.to_parquet(buf, index=False)
s3.put_object(Bucket="fhvi-landing", Key="raw/fact_ouest/prestations/" + d + "/prestations.parquet", Body=buf.getvalue())
print("prestations ok", len(df5))

# ---------------- DUCKDB : pharmacie -----------------
# attention le chemin marche que si on lance depuis le dossier version_initiale
con = duckdb.connect("../../3_environnement_docker/data/pharmacie.duckdb", read_only=True)
df4 = con.execute("select * from dispensations").df()
df4.columns = [c.lower() for c in df4.columns]
# TODO strip ? (oublié ici...)
buf = io.BytesIO()
df4.to_parquet(buf, index=False)
s3.put_object(Bucket="fhvi-landing", Key="raw/pharmacie/dispensations/" + d + "/dispensations.parquet", Body=buf.getvalue())
print("dispensations ok", len(df4))
con.close()

print("fin")
