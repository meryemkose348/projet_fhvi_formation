import io
import json
import os
import socket
from pathlib import Path

import boto3
import pandas as pd
import pytest

from fhvi_ingestion.app import main
from fhvi_ingestion.metadata import TECHNICAL_COLUMNS

pytestmark = pytest.mark.integration
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
LOAD_DATE = "2000-01-01"


def _port_open(host: str, port: str) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=1):
            return True
    except (OSError, ValueError):
        return False


@pytest.fixture(scope="module")
def s3():
    import fhvi_ingestion.config  # noqa: F401
    for host_var, port_var in [("PG_HOST", "PG_PORT"), ("MARIADB_HOST", "MARIADB_PORT")]:
        if not _port_open(os.getenv(host_var, "localhost"), os.getenv(port_var, "0")):
            pytest.skip(f"environnement Docker indisponible ({host_var}:{os.getenv(port_var)})")
    client = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT_URL"],
                          aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                          aws_secret_access_key=os.environ["S3_SECRET_KEY"], region_name="us-east-1")
    yield client
    bucket = os.environ["S3_BUCKET"]
    for obj in client.list_objects_v2(Bucket=bucket, Prefix="raw/").get("Contents", []):
        if f"load_date={LOAD_DATE}" in obj["Key"]:
            client.delete_object(Bucket=bucket, Key=obj["Key"])


def _test_objects(s3) -> list[str]:
    contents = s3.list_objects_v2(Bucket=os.environ["S3_BUCKET"], Prefix="raw/").get("Contents", [])
    return sorted(o["Key"] for o in contents if f"load_date={LOAD_DATE}" in o["Key"])


def test_full_pipeline_loads_all_sources_with_metadata(s3):
    exit_code = main(["--config", str(CONFIG_DIR / "pipeline.yaml"), "--load-date", LOAD_DATE])
    assert exit_code == 0

    keys = _test_objects(s3)
    data_keys = [k for k in keys if "/_runs/" not in k]
    expected_tables = {"patients", "sejours", "rendez_vous", "prestations", "dispensations"}
    assert {k.split("/")[2] for k in data_keys} == expected_tables

    key = next(k for k in data_keys if "/rendez_vous/" in k)
    df = pd.read_parquet(io.BytesIO(s3.get_object(Bucket=os.environ["S3_BUCKET"], Key=key)["Body"].read()))
    assert len(df) == 800
    assert set(TECHNICAL_COLUMNS) <= set(df.columns)
    assert df["_source_name"].unique().tolist() == ["rdv_sud"]
    run_id = df["_run_id"].iloc[0]
    assert run_id in key

    manifest_key = next(k for k in keys if "/_runs/" in k)
    manifest = json.loads(s3.get_object(Bucket=os.environ["S3_BUCKET"], Key=manifest_key)["Body"].read())
    assert manifest["run_id"] == run_id
    assert manifest["status"] == "SUCCESS"
    assert manifest["rows_total"] == 500 + 1200 + 800 + 1000 + 1500


def test_errors_are_isolated_on_real_sources(s3):
    exit_code = main(["--config", str(CONFIG_DIR / "pipeline_demo_erreurs.yaml"), "--load-date", LOAD_DATE])
    assert exit_code == 1                                  # PARTIAL
    written = {k.split("/")[2] for k in _test_objects(s3) if "/_runs/" not in k}
    assert {"patients", "dispensations"} <= written


def test_replaying_a_date_on_s3_is_idempotent(s3):
    args = ["--config", str(CONFIG_DIR / "pipeline_rejeu.yaml"), "--load-date", LOAD_DATE]
    assert main(args) == 0
    assert main(args) == 0
    partition = [k for k in _test_objects(s3) if "/prestations_du_jour/" in k]
    assert len(partition) == 1
    manifests = [k for k in _test_objects(s3) if "/_runs/" in k]
    assert len(manifests) >= 2

