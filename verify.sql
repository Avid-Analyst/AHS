CREATE USER [ahs-telemetry-ingest-api] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [ahs-telemetry-ingest-api];
ALTER ROLE db_datawriter ADD MEMBER [ahs-telemetry-ingest-api];