"""Ingestion FHVI, étape 1 : le code est juste rangé dans un package
"""
from __future__ import annotations

from datetime import date

from ingestion import sources, storage


def main() -> None:
    load_date = date.today().isoformat()
    print("Début de l'ingestion")

    # 5 blocs quasi identiques, on garde comme ça pour l'instant (factorisation à l'étape 2)

    df = sources.extract_patients()
    storage.write_parquet(df, f"raw/dpi_nord/patients/{load_date}/patients.parquet")
    print(f"patients : {len(df)} lignes")

    df = sources.extract_sejours()
    storage.write_parquet(df, f"raw/dpi_nord/sejours/{load_date}/sejours.parquet")
    print(f"sejours : {len(df)} lignes")

    df = sources.extract_rendez_vous()
    storage.write_parquet(df, f"raw/rdv_sud/rendez_vous/{load_date}/rendez_vous.parquet")
    print(f"rendez_vous : {len(df)} lignes")

    df = sources.extract_prestations()
    storage.write_parquet(df, f"raw/fact_ouest/prestations/{load_date}/prestations.parquet")
    print(f"prestations : {len(df)} lignes")

    df = sources.extract_dispensations()
    storage.write_parquet(df, f"raw/pharmacie/dispensations/{load_date}/dispensations.parquet")
    print(f"dispensations : {len(df)} lignes")

    print("Fin de l'ingestion")


# sans ce if, un simple import de main.py (ds un test par ex) lancerait toute l ingestion
if __name__ == "__main__":
    main()
