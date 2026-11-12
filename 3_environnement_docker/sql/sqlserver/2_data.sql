-- =====================================================================
--  Données de démonstration (déterministes : ABS(CHECKSUM(n * k)) % m)
--  1 000 prestations, 250 factures
-- =====================================================================
USE [$(DB)];
GO
SET NOCOUNT ON;

;WITH nums AS (
    SELECT TOP (1000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
),
actes AS (
    SELECT * FROM (VALUES
        (0, N'CS',    N'Consultation spécialiste',        30.00),
        (1, N'ECG',   N'Électrocardiogramme ',             14.26),
        (2, N'RX',    N'Radiographie thorax',              21.28),
        (3, N'IRM',   N'IRM cérébrale',                   69.00),
        (4, N'BIO',   N'Bilan biologique standard ',       18.90),
        (5, N'ECHO',  N'Échographie abdominale',           56.70),
        (6, N'URG',   N'Passage aux urgences',             25.32),
        (7, N'SCAN',  N'Scanner thoracique',              113.68)
    ) AS t (k, CodeActe, LibelleActe, Tarif)
)
INSERT INTO fact.Prestations (IPP, CodeActe, LibelleActe, DateActe, CodeUF, MontantEUR, StatutFacturation, DateMaj)
SELECT
    CONCAT(N'IPP', RIGHT(CONCAT(N'0000000', 1 + ABS(CHECKSUM(n * 7919)) % 500), 7)),
    a.CodeActe,
    a.LibelleActe,
    DATEADD(MINUTE, ABS(CHECKSUM(n * 31)) % 1440, DATEADD(DAY, ABS(CHECKSUM(n * 17)) % 300, CAST('2025-01-01' AS DATETIME2(0)))),
    CHOOSE(1 + ABS(CHECKSUM(n * 13)) % 4, N'UF1010', N'UF2020', N'UF3030', N'UF4040'),
    a.Tarif,
    CHOOSE(1 + ABS(CHECKSUM(n * 23)) % 3, N'A_FACTURER', N'FACTURE', N'REJETE'),
    DATEADD(DAY, ABS(CHECKSUM(n * 29)) % 320, CAST('2025-01-01' AS DATETIME2(0)))
FROM nums
JOIN actes a ON a.k = ABS(CHECKSUM(n * 11)) % 8;

;WITH nums AS (
    SELECT TOP (250) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n
    FROM sys.all_objects
)
INSERT INTO fact.Factures (NumeroFacture, IPP, DateEmission, MontantTotalEUR, Organisme)
SELECT
    CONCAT(N'FAC-2025-', RIGHT(CONCAT(N'00000', n), 5)),
    CONCAT(N'IPP', RIGHT(CONCAT(N'0000000', 1 + ABS(CHECKSUM(n * 7919)) % 500), 7)),
    DATEADD(DAY, ABS(CHECKSUM(n * 37)) % 300, CAST('2025-02-01' AS DATE)),
    CAST(20 + ABS(CHECKSUM(n * 41)) % 900 AS DECIMAL(12, 2)) + 0.5,
    CHOOSE(1 + ABS(CHECKSUM(n * 43)) % 3, N'CPAM', N'Mutuelle ', N'Patient')
FROM nums;

DECLARE @nb_prestations INT = (SELECT COUNT(*) FROM fact.Prestations);
DECLARE @nb_factures INT = (SELECT COUNT(*) FROM fact.Factures);
PRINT CONCAT(N'Base $(DB) initialisée : ', @nb_prestations, N' prestations, ', @nb_factures, N' factures');
GO
