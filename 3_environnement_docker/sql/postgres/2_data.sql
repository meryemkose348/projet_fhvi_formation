-- =====================================================================
--  Données de démonstration (déterministes grâce à setseed)
--  500 patients, ~1 200 séjours, 8 services
-- =====================================================================
SELECT setseed(0.42);

INSERT INTO services (code_service, libelle, pole) VALUES
    ('CARDIO', 'Cardiologie',            'Médecine'),
    ('URG',    'Urgences',               'Urgences'),
    ('PED',    'Pédiatrie',              'Femme-Enfant'),
    ('ONCO',   'Oncologie',              'Médecine'),
    ('ORTHO',  'Chirurgie orthopédique', 'Chirurgie'),
    ('MED',    'Médecine interne',       'Médecine'),
    ('MAT',    'Maternité',              'Femme-Enfant'),
    ('GER',    'Gériatrie',              'Médecine');

INSERT INTO patients (ipp, sexe, annee_naissance, code_postal, date_creation)
SELECT
    'IPP' || lpad(g::text, 7, '0'),
    CASE WHEN random() < 0.52 THEN 'F' ELSE 'M' END,
    1935 + floor(random() * 88)::int,
    (ARRAY['74000', '74100', '74200', '73000', '01210', '74960', NULL])[1 + floor(random() * 7)::int],
    TIMESTAMP '2019-01-01' + random() * INTERVAL '2400 days'
FROM generate_series(1, 500) AS g;

-- Les libellés de service sont volontairement "sales" (espaces, casse)
-- pour justifier l'étape de normalisation du pipeline.
INSERT INTO sejours (id_patient, date_entree, date_sortie, service, mode_entree)
SELECT
    s.id_patient,
    s.date_entree,
    CASE WHEN random() < 0.05 THEN NULL
         ELSE s.date_entree + (1 + floor(random() * 15)::int) * INTERVAL '1 day' END,
    (ARRAY['Cardiologie', 'Urgences ', '  Pédiatrie', 'Oncologie',
           'CHIRURGIE ORTHOPEDIQUE ', 'Médecine interne', 'Maternité', 'gériatrie'])[1 + floor(random() * 8)::int],
    (ARRAY['Domicile', 'Urgences', 'Transfert', 'Programmé'])[1 + floor(random() * 4)::int]
FROM (
    SELECT 1 + floor(random() * 500)::int AS id_patient,
           TIMESTAMP '2025-01-01' + random() * INTERVAL '670 days' AS date_entree
    FROM generate_series(1, 1200)
) AS s;
