-- =====================================================================
--  Source 3 : "Pharmacie" (DuckDB, fichier local) - données FICTIVES
--  Exécuté par scripts/init_duckdb.py -> data/pharmacie.duckdb
--  Particularité pédagogique : colonnes en CamelCase (encore une autre
--  convention) et pas de serveur : on lit un fichier, pas une base distante.
-- =====================================================================
SELECT setseed(0.42);

CREATE TABLE produits (
    CodeUCD         VARCHAR PRIMARY KEY,
    LibelleProduit  VARCHAR NOT NULL,
    ClasseATC       VARCHAR NOT NULL,
    PrixUnitaire    DECIMAL(10, 2) NOT NULL
);

INSERT INTO produits VALUES
    ('3400890000011', 'Paracétamol 1 g comprimé',         'N02BE01', 0.12),
    ('3400890000028', 'Amoxicilline 500 mg gélule',        'J01CA04', 0.21),
    ('3400890000035', 'Ibuprofène 400 mg comprimé',        'M01AE01', 0.15),
    ('3400890000042', 'Héparine 5000 UI/ml injectable',    'B01AB01', 4.80),
    ('3400890000059', 'Sérum physiologique 0,9 % 500 ml',  'B05BB01', 1.35),
    ('3400890000066', 'Oméprazole 20 mg gélule',           'A02BC01', 0.09),
    ('3400890000073', 'Morphine 10 mg/ml injectable',      'N02AA01', 2.60),
    ('3400890000080', 'Furosémide 40 mg comprimé',         'C03CA01', 0.07),
    ('3400890000097', 'Insuline rapide 100 UI/ml',         'A10AB01', 12.40),
    ('3400890000103', 'Ceftriaxone 1 g injectable',        'J01DD04', 3.10);

CREATE TABLE dispensations AS
SELECT
    i                                                             AS DispensationId,
    (SELECT CodeUCD FROM produits ORDER BY CodeUCD
        LIMIT 1 OFFSET CAST(floor(random() * 10) AS INTEGER))     AS CodeUCD,
    CAST(1 + floor(random() * 30) AS INTEGER)                     AS Quantite,
    TIMESTAMP '2025-09-01' + to_days(CAST(floor(random() * 60) AS INTEGER))
        + to_minutes(CAST(floor(random() * 1440) AS INTEGER))     AS DateDispensation,
    list_extract(['Cardiologie', 'Urgences ', 'Pédiatrie', ' Oncologie', 'Gériatrie'],
                 CAST(1 + floor(random() * 5) AS INTEGER))         AS ServiceDemandeur
FROM range(1, 1501) AS t(i);
