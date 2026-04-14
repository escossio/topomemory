BEGIN;

GRANT USAGE ON SCHEMA topomemory TO topomemory_app;

GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLE topomemory.collector,
         topomemory.run,
         topomemory.run_artifact,
         topomemory.ingestion_bundle
TO topomemory_app;

COMMIT;
