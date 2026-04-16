BEGIN;

SET search_path TO topomemory, public;

CREATE TABLE route_health_trend (
  route_health_trend_id TEXT PRIMARY KEY,
  target_value TEXT NOT NULL,
  scenario TEXT NOT NULL,
  trend_window_size INTEGER NOT NULL,
  total_runs_considered INTEGER NOT NULL,
  latest_run_id TEXT NOT NULL,
  latest_snapshot_id TEXT NOT NULL,
  latest_assessment_id TEXT NOT NULL,
  public_stability_status TEXT NOT NULL,
  private_variation_status TEXT NOT NULL,
  destination_stability_status TEXT NOT NULL,
  overall_trend_status TEXT NOT NULL,
  confidence TEXT NOT NULL,
  reasoning_summary TEXT NOT NULL,
  evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT route_health_trend_route_health_trend_id_not_blank CHECK (btrim(route_health_trend_id) <> ''),
  CONSTRAINT route_health_trend_target_value_not_blank CHECK (btrim(target_value) <> ''),
  CONSTRAINT route_health_trend_scenario_not_blank CHECK (btrim(scenario) <> ''),
  CONSTRAINT route_health_trend_window_positive CHECK (trend_window_size > 0),
  CONSTRAINT route_health_trend_total_runs_non_negative CHECK (total_runs_considered >= 0),
  CONSTRAINT route_health_trend_public_stability_status_valid CHECK (public_stability_status IN ('stable', 'unstable', 'insufficient_context')),
  CONSTRAINT route_health_trend_private_variation_status_valid CHECK (private_variation_status IN ('low_variation', 'oscillating', 'unstable', 'insufficient_context')),
  CONSTRAINT route_health_trend_destination_stability_status_valid CHECK (destination_stability_status IN ('stable', 'changed', 'unknown', 'insufficient_context')),
  CONSTRAINT route_health_trend_overall_trend_status_valid CHECK (overall_trend_status IN ('stable', 'oscillating', 'degrading', 'insufficient_context')),
  CONSTRAINT route_health_trend_confidence_valid CHECK (confidence IN ('high', 'medium', 'low')),
  CONSTRAINT route_health_trend_evidence_json_is_object CHECK (jsonb_typeof(evidence_json) = 'object')
);

ALTER TABLE route_health_trend
  ADD CONSTRAINT route_health_trend_latest_run_id_fkey
  FOREIGN KEY (latest_run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_health_trend
  ADD CONSTRAINT route_health_trend_latest_snapshot_id_fkey
  FOREIGN KEY (latest_snapshot_id)
  REFERENCES route_snapshot (route_snapshot_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_health_trend
  ADD CONSTRAINT route_health_trend_latest_assessment_id_fkey
  FOREIGN KEY (latest_assessment_id)
  REFERENCES route_health_assessment (route_health_assessment_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE route_health_trend
  ADD CONSTRAINT route_health_trend_target_scenario_window_uniq UNIQUE (target_value, scenario, trend_window_size);

CREATE INDEX route_health_trend_target_value_scenario_idx ON route_health_trend (target_value, scenario);
CREATE INDEX route_health_trend_overall_trend_status_idx ON route_health_trend (overall_trend_status);
CREATE INDEX route_health_trend_created_at_idx ON route_health_trend (created_at);

CREATE TRIGGER route_health_trend_touch_updated_at
BEFORE UPDATE ON route_health_trend
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

COMMENT ON TABLE route_health_trend IS 'Resumo mínimo de tendência temporal da Camada 2 para runs equivalentes por target_value e scenario.';

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE route_health_trend TO topomemory_app;

COMMIT;
