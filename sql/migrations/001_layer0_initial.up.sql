BEGIN;

CREATE SCHEMA IF NOT EXISTS topomemory;
SET search_path TO topomemory, public;

CREATE OR REPLACE FUNCTION topomemory.touch_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TABLE collector (
  collector_id TEXT PRIMARY KEY,
  collector_name TEXT NOT NULL,
  collector_type TEXT NOT NULL,
  location_hint TEXT,
  network_context JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT collector_id_not_blank CHECK (btrim(collector_id) <> ''),
  CONSTRAINT collector_name_not_blank CHECK (btrim(collector_name) <> ''),
  CONSTRAINT collector_type_not_blank CHECK (btrim(collector_type) <> ''),
  CONSTRAINT collector_network_context_is_object CHECK (jsonb_typeof(network_context) = 'object')
);

CREATE TABLE run (
  run_id TEXT PRIMARY KEY,
  collector_id TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_value TEXT NOT NULL,
  service_hint TEXT NOT NULL,
  scenario TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ NOT NULL,
  run_status TEXT NOT NULL,
  collection_health TEXT NOT NULL,
  summary TEXT,
  tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  scenario_version TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT run_id_not_blank CHECK (btrim(run_id) <> ''),
  CONSTRAINT run_target_type_not_blank CHECK (btrim(target_type) <> ''),
  CONSTRAINT run_target_value_not_blank CHECK (btrim(target_value) <> ''),
  CONSTRAINT run_service_hint_not_blank CHECK (btrim(service_hint) <> ''),
  CONSTRAINT run_scenario_not_blank CHECK (btrim(scenario) <> ''),
  CONSTRAINT run_status_valid CHECK (run_status IN ('success', 'partial', 'failed')),
  CONSTRAINT run_collection_health_valid CHECK (collection_health IN ('healthy', 'degraded', 'blocked')),
  CONSTRAINT run_time_order_valid CHECK (finished_at >= started_at),
  CONSTRAINT run_tags_json_is_array CHECK (jsonb_typeof(tags_json) = 'array')
);

ALTER TABLE run
  ADD CONSTRAINT run_collector_id_fkey
  FOREIGN KEY (collector_id)
  REFERENCES collector (collector_id)
  ON UPDATE CASCADE
  ON DELETE RESTRICT;

CREATE INDEX run_collector_id_idx ON run (collector_id);
CREATE INDEX run_started_at_idx ON run (started_at);
CREATE INDEX run_run_status_idx ON run (run_status);
CREATE INDEX run_collection_health_idx ON run (collection_health);

CREATE TABLE run_artifact (
  artifact_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  artifact_type TEXT NOT NULL,
  artifact_path TEXT NOT NULL,
  artifact_status TEXT NOT NULL,
  artifact_format TEXT NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT artifact_id_not_blank CHECK (btrim(artifact_id) <> ''),
  CONSTRAINT artifact_type_not_blank CHECK (btrim(artifact_type) <> ''),
  CONSTRAINT artifact_path_not_blank CHECK (btrim(artifact_path) <> ''),
  CONSTRAINT artifact_status_valid CHECK (artifact_status IN ('present', 'missing', 'failed', 'skipped')),
  CONSTRAINT artifact_format_not_blank CHECK (btrim(artifact_format) <> '')
);

ALTER TABLE run_artifact
  ADD CONSTRAINT run_artifact_run_id_fkey
  FOREIGN KEY (run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

CREATE INDEX run_artifact_run_id_idx ON run_artifact (run_id);
CREATE INDEX run_artifact_type_idx ON run_artifact (artifact_type);
CREATE INDEX run_artifact_generated_at_idx ON run_artifact (generated_at);

CREATE TABLE ingestion_bundle (
  bundle_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL UNIQUE,
  bundle_version TEXT NOT NULL,
  ingestion_confidence TEXT NOT NULL,
  run_context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  observed_elements_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  observed_relations_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  artifacts_manifest_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT bundle_id_not_blank CHECK (btrim(bundle_id) <> ''),
  CONSTRAINT bundle_version_not_blank CHECK (btrim(bundle_version) <> ''),
  CONSTRAINT ingestion_confidence_valid CHECK (ingestion_confidence IN ('minimal', 'complete', 'rejected')),
  CONSTRAINT run_context_json_is_object CHECK (jsonb_typeof(run_context_json) = 'object'),
  CONSTRAINT observed_elements_json_is_array CHECK (jsonb_typeof(observed_elements_json) = 'array'),
  CONSTRAINT observed_relations_json_is_array CHECK (jsonb_typeof(observed_relations_json) = 'array'),
  CONSTRAINT artifacts_manifest_json_is_array CHECK (jsonb_typeof(artifacts_manifest_json) = 'array')
);

ALTER TABLE ingestion_bundle
  ADD CONSTRAINT ingestion_bundle_run_id_fkey
  FOREIGN KEY (run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

CREATE INDEX ingestion_bundle_created_at_idx ON ingestion_bundle (created_at);
CREATE INDEX ingestion_bundle_ingestion_confidence_idx ON ingestion_bundle (ingestion_confidence);

CREATE TRIGGER collector_touch_updated_at
BEFORE UPDATE ON collector
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

CREATE TRIGGER run_touch_updated_at
BEFORE UPDATE ON run
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

CREATE TRIGGER run_artifact_touch_updated_at
BEFORE UPDATE ON run_artifact
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

CREATE TRIGGER ingestion_bundle_touch_updated_at
BEFORE UPDATE ON ingestion_bundle
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

COMMENT ON SCHEMA topomemory IS 'Namespace inicial da Camada 0 do topomemory.';
COMMENT ON TABLE collector IS 'Coletor controlado que origina runs da Camada 0.';
COMMENT ON TABLE run IS 'Unidade mínima de verdade observada da Camada 0.';
COMMENT ON TABLE run_artifact IS 'Inventário persistido dos artefatos produzidos por um run.';
COMMENT ON TABLE ingestion_bundle IS 'Pacote oficial de entrada da Camada 1 derivado de um run.';

COMMIT;
