# Réinitialise COMPLÈTEMENT l'environnement (Windows PowerShell).
# Usage (depuis 3_environnement_docker\) :  .\scripts\reset.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$python = "..\2_projet_python\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

Write-Host "==> Arrêt des conteneurs et suppression des volumes"
docker compose down -v

Write-Host "==> Reconstruction de la source DuckDB"
& $python scripts\init_duckdb.py --force

Write-Host "==> Redémarrage (attente des healthchecks)"
docker compose up -d --wait postgres mariadb sqlserver seaweedfs
docker compose up s3-init sqlserver-init   # bucket + base SQL Server, puis arrêt (normal)

Write-Host "==> Vérification"
& $python scripts\check_env.py
