-- =====================================================================
--  Source 1 : "DPI Hôpital Nord" (PostgreSQL) - données 100 % FICTIVES
--  Exécuté automatiquement au premier démarrage du conteneur postgres.
--  Données pseudonymisées : aucun nom / prénom, uniquement un IPP fictif.
-- =====================================================================

CREATE TABLE services (
    code_service   VARCHAR(10)  PRIMARY KEY,
    libelle        VARCHAR(60)  NOT NULL,
    pole           VARCHAR(40)  NOT NULL
);

CREATE TABLE patients (
    id_patient       SERIAL       PRIMARY KEY,
    ipp              VARCHAR(12)  NOT NULL UNIQUE,   -- Identifiant Permanent Patient (fictif)
    sexe             CHAR(1)      NOT NULL,
    annee_naissance  INTEGER      NOT NULL,
    code_postal      VARCHAR(5),
    date_creation    TIMESTAMP    NOT NULL
);

CREATE TABLE sejours (
    id_sejour     SERIAL       PRIMARY KEY,
    id_patient    INTEGER      NOT NULL REFERENCES patients (id_patient),
    date_entree   TIMESTAMP    NOT NULL,
    date_sortie   TIMESTAMP,                         -- NULL = patient encore hospitalisé
    service       VARCHAR(40)  NOT NULL,             -- libellé saisi "à la main" (espaces parasites !)
    mode_entree   VARCHAR(20)  NOT NULL
);

COMMENT ON TABLE patients IS 'Patients fictifs du DPI Hôpital Nord (formation FHVI)';
COMMENT ON TABLE sejours  IS 'Séjours hospitaliers fictifs';
COMMENT ON TABLE services IS 'Référentiel des services (non ingéré au départ : sert à la démo "ajout par YAML")';
