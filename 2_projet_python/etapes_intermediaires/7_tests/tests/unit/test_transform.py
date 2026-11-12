import pandas as pd
import pytest

from ingestion.transform import normalize, to_snake_case


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("DispensationId", "dispensation_id"),
        ("DATE_RDV", "date_rdv"),
        ("date_entree", "date_entree"),
        ("CodeUCD", "code_ucd"),
        (" Nom Colonne ", "nom_colonne"),
        ("prix-unitaire(€)", "prix_unitaire"),
    ],
)
def test_to_snake_case(raw, expected):
    assert to_snake_case(raw) == expected


def test_normalize_renames_columns(raw_df):
    result = normalize(raw_df)
    assert list(result.columns) == ["id_rdv", "specialite", "date_rdv"]


def test_normalize_strips_strings(raw_df):
    result = normalize(raw_df)
    assert result["specialite"].tolist() == ["Cardiologie", "Pédiatrie", "ophtalmologie"]


def test_normalize_keeps_non_string_columns(raw_df):
    result = normalize(raw_df)
    assert result["id_rdv"].tolist() == [1, 2, 3]
    assert pd.api.types.is_datetime64_any_dtype(result["date_rdv"])


def test_normalize_does_not_modify_input(raw_df):
    before = raw_df.copy()
    normalize(raw_df)
    pd.testing.assert_frame_equal(raw_df, before)


def test_normalize_handles_null_values():
    df = pd.DataFrame({"Service": [" Urgences ", None]})
    assert normalize(df)["service"].tolist() == ["Urgences", None]


def test_normalize_ignores_non_string_objects():
    # non-régression avec sql server qui renvoie les colonnes date en objets datetime.date, pas en str
    from datetime import date
    df = pd.DataFrame({"DateEmission": [date(2026, 1, 5), None], "Organisme": ["Mutuelle ", "CPAM"]})
    result = normalize(df)
    assert result["date_emission"].tolist() == [date(2026, 1, 5), None]
    assert result["organisme"].tolist() == ["Mutuelle", "CPAM"]
