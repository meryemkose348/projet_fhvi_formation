-- =====================================================================
--  Source 4 : "Facturation Hôpital Ouest" (SQL Server) - données FICTIVES
--  Exécuté par le service sqlserver-init (sqlcmd) au premier démarrage.
--
--  Particularités pédagogiques, choisies pour ressembler à l'existant FHVI
--  (SQL Server on-prem, base de facturation type Opale) :
--   - base dédiée avec collation française (French_CI_AS) ;
--   - tables rangées dans un SCHÉMA métier (fact.*) et non dans dbo ;
--   - colonnes en PascalCase, types NVARCHAR / DATETIME2 / DECIMAL ;
--   - compte de service en LECTURE SEULE (rôle db_datareader), comme les
--     comptes de service utilisés par les flux SSIS.
-- Variables sqlcmd : $(DB), $(READER_USER), $(READER_PASSWORD)
-- =====================================================================
-- Repart de zéro si une initialisation précédente a été interrompue
IF DB_ID(N'$(DB)') IS NOT NULL
BEGIN
    ALTER DATABASE [$(DB)] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [$(DB)];
END
IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'$(READER_USER)')
    DROP LOGIN [$(READER_USER)];
GO

CREATE DATABASE [$(DB)] COLLATE French_CI_AS;
GO

USE [$(DB)];
GO

CREATE LOGIN [$(READER_USER)] WITH PASSWORD = N'$(READER_PASSWORD)', CHECK_POLICY = OFF, DEFAULT_DATABASE = [$(DB)];
CREATE USER [$(READER_USER)] FOR LOGIN [$(READER_USER)];
ALTER ROLE db_datareader ADD MEMBER [$(READER_USER)];
GO

CREATE SCHEMA fact AUTHORIZATION dbo;
GO

CREATE TABLE fact.Prestations (
    IdPrestation        INT            IDENTITY(1, 1) PRIMARY KEY,
    IPP                 NVARCHAR(12)   NOT NULL,          -- Identifiant Permanent Patient (fictif)
    CodeActe            NVARCHAR(10)   NOT NULL,
    LibelleActe         NVARCHAR(80)   NOT NULL,          -- libellés parfois suivis d'espaces
    DateActe            DATETIME2(0)   NOT NULL,
    CodeUF              NVARCHAR(10)   NOT NULL,          -- Unité Fonctionnelle
    MontantEUR          DECIMAL(10, 2) NOT NULL,
    StatutFacturation   NVARCHAR(12)   NOT NULL,          -- A_FACTURER / FACTURE / REJETE
    DateMaj             DATETIME2(0)   NOT NULL           -- utile pour un futur chargement incrémental
);

CREATE TABLE fact.Factures (
    IdFacture           INT            IDENTITY(1, 1) PRIMARY KEY,
    NumeroFacture       NVARCHAR(20)   NOT NULL,
    IPP                 NVARCHAR(12)   NOT NULL,
    DateEmission        DATE           NOT NULL,
    MontantTotalEUR     DECIMAL(12, 2) NOT NULL,
    Organisme           NVARCHAR(40)   NOT NULL           -- CPAM, mutuelle...
);
GO
