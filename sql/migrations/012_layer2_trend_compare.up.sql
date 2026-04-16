BEGIN;

SET search_path TO topomemory, public;

ALTER TABLE route_health_trend
  ADD COLUMN window_offset INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN window_start_run_id TEXT,
  ADD COLUMN window_end_run_id TEXT;

ALTER TABLE route_health_trend
  ADD CONSTRAINT route_health_trend_window_offset_non_negative CHECK (window_offset >= 0);

ALTER TABLE route_health_trend
  DROP CONSTRAINT IF EXISTS route_health_trend_target_scenario_window_uniq;

ALTER TABLE route_health_trend
  ADD CONSTRAINT route_health_trend_target_scenario_window_offset_uniq UNIQUE (target_value, scenario, trend_window_size, window_offset);

CREATE INDEX route_health_trend_target_value_scenario_offset_idx ON route_health_trend (target_value, scenario, trend_window_size, window_offset);

CREATE TABLE route_health_trend_compare (
  route_health_trend_compare_id TEXT PRIMARY KEY,
  target_value TEXT NOT NULL,
  scenario TEXT NOT NULL,
  current_trend_id TEXT NOT NULL,
  previous_trend_id TEXT NOT NULL,
  current_window_size INTEGER NOT NULL,
  previous_window_size INTEGER NOT NULL,
  public_trend_delta TEXT NOT NULL,
  private_trend_delta TEXT NOT NULL,
  destination_trend_delta TEXT NOT NULL,
  overall_trend_delta TEXT NOT NULL,
  confidence TEXT NOT NULL,
  reasoning_summary TEXT NOT NULL,
  evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT route_health_trend_compare_id_not_blank CHECK (btrim(route_health_trend_compare_id) <> ''),
  CONSTRAINT route_health_trend_compare_target_value_not_blank CHECK (btrim(target_value) <> ''),
  CONSTRAINT route_health_trend_compare_scenario_not_blank CHECK (btrim(scenario) <> ''),
  CONSTRAINT route_health_trend_compare_current_trend_id_not_blank CHECK (btrim(current_trend_id) <> ''),
  CONSTRAINT route_health_trend_compare_previous_trend_id_not_blank CHECK (btrim(previous_trend_id) <> ''),
  CONSTRAINT route_health_trend_compare_current_window_size_positive CHECK (current_window_size > 0),
  CONSTRAINT route_health_trend_compare_previous_window_size_positive CHECK (previous_window_size > 0),
  CONSTRAINT route_health_trend_compare_public_trend_delta_valid CHECK (public_trend_delta IN ('improved', 'unchanged', 'worsened', 'insufficient_context')),
  CONSTRAINT route_health_trend_compare_private_trend_delta_valid CHECK (private_trend_delta IN ('improved', 'unchanged', 'worsened', 'insufficient_context')),
  CONSTRAINT route_health_trend_compare_destination_trend_delta_valid CHECK (destination_trend_delta IN ('stable', 'changed', 'unknown', 'insufficient_context')),
  CONSTRAINT route_health_trend_compare_overall_trend_delta_valid CHECK (overall_trend_delta IN ('improving', 'unchanged', 'worsening', 'insufficient_context')),
  CONSTRAINT route_health_trend_compare_confidence_valid CHECK (confidence IN ('high', 'medium', 'low')),
  CONSTRAINT route_health_trend_compare_evidence_json_is_object CHECK (jsonb_typeof(evidence_json) = 'object')
);

ALTER TABLE route_health_trend_compare
  ADD CONSTRAINT route_health_trend_compare_current_trend_id_fkey
  FOREIGN KEY (current_trend_id)
  REFERENCES route_health_trend (route_health_trend_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_health_trend_compare
  ADD CONSTRAINT route_health_trend_compare_previous_trend_id_fkey
  FOREIGN KEY (previous_trend_id)
  REFERENCES route_health_trend (route_health_trend_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_health_trend_compare
  ADD CONSTRAINT route_health_trend_compare_target_scenario_current_previous_uniq UNIQUE (target_value, scenario, current_trend_id, previous_trend_id);

CREATE INDEX route_health_trend_compare_target_value_scenario_idx ON route_health_trend_compare (target_value, scenario);
CREATE INDEX route_health_trend_compare_overall_trend_delta_idx ON route_health_trend_compare (overall_trend_delta);
CREATE INDEX route_health_trend_compare_created_at_idx ON route_health_trend_compare (created_at);

CREATE TRIGGER route_health_trend_compare_touch_updated_at
BEFORE UPDATE ON route_health_trend_compare
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

COMMENT ON TABLE route_health_trend_compare IS 'Comparação mínima entre janelas sucessivas da Camada 2 para o mesmo target_value e scenario.';

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE route_health_trend_compare TO topomemory_app;

COMMIT;
