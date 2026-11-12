-- =====================================================================
--  Source 2 : "RDV Clinique Sud" (MariaDB) - données 100 % FICTIVES
--  Exécuté automatiquement au premier démarrage du conteneur mariadb.
--  Particularité pédagogique : colonnes en MAJUSCULES (autre éditeur,
--  autres conventions) -> justifie la normalisation des noms de colonnes.
-- =====================================================================
SET NAMES utf8mb4;
USE rdv_sud;

CREATE TABLE PRATICIENS (
    MATRICULE      VARCHAR(10)  PRIMARY KEY,
    SPECIALITE     VARCHAR(40)  NOT NULL,
    ETABLISSEMENT  VARCHAR(40)  NOT NULL,
    ACTIF          TINYINT(1)   NOT NULL DEFAULT 1
) DEFAULT CHARSET = utf8mb4;

CREATE TABLE RENDEZ_VOUS (
    ID_RDV               INT          AUTO_INCREMENT PRIMARY KEY,
    IPP                  VARCHAR(12)  NOT NULL,
    DATE_RDV             DATETIME     NOT NULL,
    SPECIALITE           VARCHAR(40)  NOT NULL,
    STATUT               VARCHAR(10)  NOT NULL,   -- HONORE / ANNULE / ABSENT / PREVU
    MATRICULE_PRATICIEN  VARCHAR(10)  NOT NULL,
    MAJ_LE               DATETIME     NOT NULL
) DEFAULT CHARSET = utf8mb4;

INSERT INTO PRATICIENS (MATRICULE, SPECIALITE, ETABLISSEMENT, ACTIF) VALUES
    ('PR-001', 'Cardiologie',     'Clinique Sud', 1),
    ('PR-002', 'Dermatologie',    'Clinique Sud', 1),
    ('PR-003', 'Ophtalmologie',   'Clinique Sud', 1),
    ('PR-004', 'Pédiatrie',       'Clinique Sud', 1),
    ('PR-005', 'Rhumatologie',    'Clinique Sud', 0),
    ('PR-006', 'Cardiologie',     'Clinique Sud', 1),
    ('PR-007', 'Gynécologie',     'Clinique Sud', 1),
    ('PR-008', 'Pneumologie',     'Clinique Sud', 1);

-- 800 rendez-vous générés de façon déterministe (RAND(n) est reproductible)
INSERT INTO RENDEZ_VOUS (IPP, DATE_RDV, SPECIALITE, STATUT, MATRICULE_PRATICIEN, MAJ_LE)
WITH RECURSIVE seq (n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 800
)
SELECT
    CONCAT('IPP', LPAD(1 + FLOOR(RAND(n) * 500), 7, '0')),
    TIMESTAMP('2025-06-01 08:00:00') + INTERVAL FLOOR(RAND(n * 7) * 220) DAY + INTERVAL FLOOR(RAND(n * 3) * 20) * 30 MINUTE,
    ELT(1 + FLOOR(RAND(n * 11) * 6), 'Cardiologie', 'Dermatologie ', 'ophtalmologie', 'Pédiatrie', ' Gynécologie', 'Pneumologie'),
    ELT(1 + FLOOR(RAND(n * 13) * 4), 'HONORE', 'ANNULE', 'ABSENT', 'PREVU'),
    CONCAT('PR-00', 1 + FLOOR(RAND(n * 17) * 8)),
    TIMESTAMP('2025-06-01 00:00:00') + INTERVAL FLOOR(RAND(n * 19) * 230) DAY
FROM seq;
