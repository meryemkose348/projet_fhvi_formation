"""Intégration : vraies bases, vrai bucket, il faut l'env docker démarré
"""
import io
import os
import socket

import boto3
import pandas as pd
import pytest

from main import main

pytestmark = pytest.mark.integration


def _port_open(host: str, port: str) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=1):
            return True
    except OSError:
        return False


# env Docker arrêté, on skip tout le module
@pytest.fixture(scope="module", autouse=True)
def require_docker_environment():
    import ingestion.config  # noqa: F401  (charge le .env)
    services = [("PG_HOST", "PG_PORT"), ("MARIADB_HOST", "MARIADB_PORT")]
    for host_var, port_var in services:
        if not _port_open(os.getenv(host_var, "localhost"), os.getenv(port_var, "0")):
            pytest.skip(f"environnement Docker indisponible ({host_var}:{os.getenv(port_var)})")


def test_full_pipeline_writes_every_table_to_the_bucket():
    load_date = "2000-01-01"
    assert main(["--config", "config/pipeline.yaml", "--load-date", load_date]) == 0

    s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT_URL"],
                      aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                      aws_secret_access_key=os.environ["S3_SECRET_KEY"], region_name="us-east-1")
    bucket = os.environ["S3_BUCKET"]
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=bucket, Prefix="raw/")["Contents"]
            if f"/{load_date}/" in o["Key"]]
    assert sorted(keys) == [
        f"raw/dpi_nord/patients/{load_date}/patients.parquet",
        f"raw/dpi_nord/sejours/{load_date}/sejours.parquet",
        f"raw/fact_ouest/prestations/{load_date}/prestations.parquet",
        f"raw/pharmacie/dispensations/{load_date}/dispensations.parquet",
        f"raw/rdv_sud/rendez_vous/{load_date}/rendez_vous.parquet",
    ]

    body = s3.get_object(Bucket=bucket, Key=f"raw/rdv_sud/rendez_vous/{load_date}/rendez_vous.parquet")["Body"].read()
    df = pd.read_parquet(io.BytesIO(body))
    assert len(df) == 800
    assert "date_rdv" in df.columns
    assert not df["specialite"].str.startswith(" ").any()

    for key in keys:
        s3.delete_object(Bucket=bucket, Key=key)
