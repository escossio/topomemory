BEGIN;

GRANT USAGE ON SCHEMA topomemory TO livecopilot_app;

GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLE topomemory.collector,
         topomemory.run,
         topomemory.run_artifact,
         topomemory.ingestion_bundle
TO livecopilot_app;

COMMIT;
