#!/usr/bin/env bash
# Réinitialise COMPLÈTEMENT l'environnement : bases, bucket et fichier DuckDB
# reviennent à l'état initial. Usage (depuis 3_environnement_docker/) :
#   ./scripts/reset.sh
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="../2_projet_python/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="python3"

echo "==> Arrêt des conteneurs et suppression des volumes"
docker compose down -v

echo "==> Reconstruction de la source DuckDB"
"$PYTHON" scripts/init_duckdb.py --force

echo "==> Redémarrage (attente des healthchecks)"
docker compose up -d --wait postgres mariadb sqlserver seaweedfs
docker compose up s3-init sqlserver-init   # bucket + base SQL Server, puis arrêt (normal)

echo "==> Vérification"
"$PYTHON" scripts/check_env.py
