USE master;
GO
CREATE LOGIN abdullah WITH PASSWORD = '<your-password>';
GO

USE AdventureWorksLT2022;
GO
CREATE USER abdullah FOR LOGIN abdullah;
GO
GRANT SELECT ON SCHEMA::SalesLT TO abdullah;
GO