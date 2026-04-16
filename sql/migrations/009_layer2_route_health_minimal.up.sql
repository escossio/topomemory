BEGIN;

SET search_path TO topomemory, public;

CREATE TABLE route_snapshot (
  route_snapshot_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  bundle_id TEXT NOT NULL,
  target_value TEXT NOT NULL,
  scenario TEXT NOT NULL,
  total_observed_elements INTEGER NOT NULL,
  total_observed_relations INTEGER NOT NULL,
  total_resolved_elements INTEGER NOT NULL,
  total_unresolved_elements INTEGER NOT NULL,
  public_element_count INTEGER NOT NULL,
  private_element_count INTEGER NOT NULL,
  matched_existing_count INTEGER NOT NULL,
  new_entity_count INTEGER NOT NULL,
  skipped_count INTEGER NOT NULL,
  path_signature TEXT NOT NULL,
  resolved_path_signature TEXT NOT NULL,
  destination_element_id TEXT,
  destination_label TEXT,
  destination_ip TEXT,
  destination_hostname TEXT,
  snapshot_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT route_snapshot_route_snapshot_id_not_blank CHECK (btrim(route_snapshot_id) <> ''),
  CONSTRAINT route_snapshot_run_id_not_blank CHECK (btrim(run_id) <> ''),
  CONSTRAINT route_snapshot_bundle_id_not_blank CHECK (btrim(bundle_id) <> ''),
  CONSTRAINT route_snapshot_target_value_not_blank CHECK (btrim(target_value) <> ''),
  CONSTRAINT route_snapshot_scenario_not_blank CHECK (btrim(scenario) <> ''),
  CONSTRAINT route_snapshot_counts_non_negative CHECK (
    total_observed_elements >= 0
    AND total_observed_relations >= 0
    AND total_resolved_elements >= 0
    AND total_unresolved_elements >= 0
    AND public_element_count >= 0
    AND private_element_count >= 0
    AND matched_existing_count >= 0
    AND new_entity_count >= 0
    AND skipped_count >= 0
  ),
  CONSTRAINT route_snapshot_observation_balance CHECK (
    total_resolved_elements + total_unresolved_elements = total_observed_elements
  )
);

ALTER TABLE route_snapshot
  ADD CONSTRAINT route_snapshot_run_id_fkey
  FOREIGN KEY (run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_snapshot
  ADD CONSTRAINT route_snapshot_bundle_id_fkey
  FOREIGN KEY (bundle_id)
  REFERENCES ingestion_bundle (bundle_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_snapshot
  ADD CONSTRAINT route_snapshot_run_id_uniq UNIQUE (run_id);

CREATE INDEX route_snapshot_target_value_scenario_idx ON route_snapshot (target_value, scenario);
CREATE INDEX route_snapshot_created_at_idx ON route_snapshot (created_at);

CREATE TABLE route_health_assessment (
  route_health_assessment_id TEXT PRIMARY KEY,
  route_snapshot_id TEXT NOT NULL,
  assessment_version TEXT NOT NULL,
  health_status TEXT NOT NULL,
  structural_status TEXT NOT NULL,
  route_change_status TEXT NOT NULL,
  confidence TEXT NOT NULL,
  reasoning_summary TEXT NOT NULL,
  evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  compared_to_run_id TEXT,
  compared_to_snapshot_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT route_health_assessment_route_health_assessment_id_not_blank CHECK (btrim(route_health_assessment_id) <> ''),
  CONSTRAINT route_health_assessment_route_snapshot_id_not_blank CHECK (btrim(route_snapshot_id) <> ''),
  CONSTRAINT route_health_assessment_assessment_version_not_blank CHECK (btrim(assessment_version) <> ''),
  CONSTRAINT route_health_assessment_reasoning_summary_not_blank CHECK (btrim(reasoning_summary) <> ''),
  CONSTRAINT route_health_assessment_health_status_valid CHECK (health_status IN ('healthy', 'degraded', 'blocked', 'unknown')),
  CONSTRAINT route_health_assessment_structural_status_valid CHECK (structural_status IN ('stable', 'changed', 'insufficient_context')),
  CONSTRAINT route_health_assessment_route_change_status_valid CHECK (route_change_status IN ('unchanged', 'changed', 'first_observation', 'not_comparable')),
  CONSTRAINT route_health_assessment_confidence_valid CHECK (confidence IN ('high', 'medium', 'low')),
  CONSTRAINT route_health_assessment_evidence_json_is_object CHECK (jsonb_typeof(evidence_json) = 'object')
);

ALTER TABLE route_health_assessment
  ADD CONSTRAINT route_health_assessment_route_snapshot_id_fkey
  FOREIGN KEY (route_snapshot_id)
  REFERENCES route_snapshot (route_snapshot_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_health_assessment
  ADD CONSTRAINT route_health_assessment_compared_to_run_id_fkey
  FOREIGN KEY (compared_to_run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE SET NULL;

ALTER TABLE route_health_assessment
  ADD CONSTRAINT route_health_assessment_compared_to_snapshot_id_fkey
  FOREIGN KEY (compared_to_snapshot_id)
  REFERENCES route_snapshot (route_snapshot_id)
  ON UPDATE CASCADE
  ON DELETE SET NULL;

ALTER TABLE route_health_assessment
  ADD CONSTRAINT route_health_assessment_snapshot_version_uniq UNIQUE (route_snapshot_id, assessment_version);

CREATE INDEX route_health_assessment_health_status_idx ON route_health_assessment (health_status);
CREATE INDEX route_health_assessment_structural_status_idx ON route_health_assessment (structural_status);
CREATE INDEX route_health_assessment_route_change_status_idx ON route_health_assessment (route_change_status);

CREATE TRIGGER route_snapshot_touch_updated_at
BEFORE UPDATE ON route_snapshot
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

CREATE TRIGGER route_health_assessment_touch_updated_at
BEFORE UPDATE ON route_health_assessment
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

COMMENT ON TABLE route_snapshot IS 'Snapshot mínimo da Camada 2 para leitura operacional de rota por run.';
COMMENT ON TABLE route_health_assessment IS 'Avaliação mínima de saúde e mudança de rota derivada do snapshot da Camada 2.';

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE route_snapshot TO topomemory_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE route_health_assessment TO topomemory_app;

COMMIT;
