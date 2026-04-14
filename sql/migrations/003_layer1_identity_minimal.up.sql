BEGIN;

SET search_path TO topomemory, public;

CREATE TABLE network_element (
  element_id TEXT PRIMARY KEY,
  canonical_label TEXT NOT NULL,
  element_kind TEXT NOT NULL,
  ip_scope TEXT NOT NULL,
  canonical_ip TEXT,
  canonical_hostname TEXT,
  canonical_asn TEXT,
  canonical_org TEXT,
  confidence_current NUMERIC(4,3) NOT NULL DEFAULT 0,
  role_hint_current TEXT NOT NULL DEFAULT 'unknown',
  first_seen_at TIMESTAMPTZ NOT NULL,
  last_seen_at TIMESTAMPTZ NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT network_element_element_id_not_blank CHECK (btrim(element_id) <> ''),
  CONSTRAINT network_element_canonical_label_not_blank CHECK (btrim(canonical_label) <> ''),
  CONSTRAINT network_element_element_kind_valid CHECK (element_kind IN ('public_node', 'destination', 'unknown')),
  CONSTRAINT network_element_ip_scope_valid CHECK (ip_scope IN ('public', 'private', 'unknown')),
  CONSTRAINT network_element_canonical_ip_not_blank CHECK (canonical_ip IS NULL OR btrim(canonical_ip) <> ''),
  CONSTRAINT network_element_canonical_hostname_not_blank CHECK (canonical_hostname IS NULL OR btrim(canonical_hostname) <> ''),
  CONSTRAINT network_element_canonical_asn_not_blank CHECK (canonical_asn IS NULL OR btrim(canonical_asn) <> ''),
  CONSTRAINT network_element_canonical_org_not_blank CHECK (canonical_org IS NULL OR btrim(canonical_org) <> ''),
  CONSTRAINT network_element_confidence_current_range CHECK (confidence_current >= 0 AND confidence_current <= 1),
  CONSTRAINT network_element_role_hint_current_valid CHECK (role_hint_current IN ('unknown', 'destination')),
  CONSTRAINT network_element_time_order_valid CHECK (last_seen_at >= first_seen_at)
);

CREATE UNIQUE INDEX network_element_canonical_ip_uniq
  ON network_element (canonical_ip)
  WHERE canonical_ip IS NOT NULL;

CREATE INDEX network_element_canonical_hostname_idx ON network_element (canonical_hostname);
CREATE INDEX network_element_ip_scope_idx ON network_element (ip_scope);
CREATE INDEX network_element_is_active_idx ON network_element (is_active);

CREATE TRIGGER network_element_touch_updated_at
BEFORE UPDATE ON network_element
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

CREATE TABLE identity_decision (
  identity_decision_id TEXT PRIMARY KEY,
  observed_element_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  bundle_id TEXT NOT NULL,
  decision_type TEXT NOT NULL,
  matched_element_id TEXT,
  new_element_id TEXT,
  confidence NUMERIC(4,3) NOT NULL DEFAULT 0,
  reasoning_summary TEXT NOT NULL,
  evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  decided_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT identity_decision_id_not_blank CHECK (btrim(identity_decision_id) <> ''),
  CONSTRAINT identity_decision_observed_element_id_not_blank CHECK (btrim(observed_element_id) <> ''),
  CONSTRAINT identity_decision_run_id_not_blank CHECK (btrim(run_id) <> ''),
  CONSTRAINT identity_decision_bundle_id_not_blank CHECK (btrim(bundle_id) <> ''),
  CONSTRAINT identity_decision_type_valid CHECK (
    decision_type IN (
      'matched_existing_entity',
      'new_entity_created',
      'skipped_private_scope',
      'skipped_no_public_ip'
    )
  ),
  CONSTRAINT identity_decision_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
  CONSTRAINT identity_decision_reasoning_summary_not_blank CHECK (btrim(reasoning_summary) <> ''),
  CONSTRAINT identity_decision_evidence_json_is_object CHECK (jsonb_typeof(evidence_json) = 'object'),
  CONSTRAINT identity_decision_decided_at_valid CHECK (decided_at IS NOT NULL)
);

ALTER TABLE identity_decision
  ADD CONSTRAINT identity_decision_observed_element_id_fkey
  FOREIGN KEY (observed_element_id)
  REFERENCES observed_element (observed_element_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE identity_decision
  ADD CONSTRAINT identity_decision_run_id_fkey
  FOREIGN KEY (run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE identity_decision
  ADD CONSTRAINT identity_decision_bundle_id_fkey
  FOREIGN KEY (bundle_id)
  REFERENCES ingestion_bundle (bundle_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE identity_decision
  ADD CONSTRAINT identity_decision_matched_element_id_fkey
  FOREIGN KEY (matched_element_id)
  REFERENCES network_element (element_id)
  ON UPDATE CASCADE
  ON DELETE SET NULL;

ALTER TABLE identity_decision
  ADD CONSTRAINT identity_decision_new_element_id_fkey
  FOREIGN KEY (new_element_id)
  REFERENCES network_element (element_id)
  ON UPDATE CASCADE
  ON DELETE SET NULL;

ALTER TABLE identity_decision
  ADD CONSTRAINT identity_decision_observed_element_id_uniq UNIQUE (observed_element_id);

CREATE INDEX identity_decision_run_id_idx ON identity_decision (run_id);
CREATE INDEX identity_decision_bundle_id_idx ON identity_decision (bundle_id);
CREATE INDEX identity_decision_decision_type_idx ON identity_decision (decision_type);
CREATE INDEX identity_decision_matched_element_id_idx ON identity_decision (matched_element_id);
CREATE INDEX identity_decision_new_element_id_idx ON identity_decision (new_element_id);

CREATE TRIGGER identity_decision_touch_updated_at
BEFORE UPDATE ON identity_decision
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

COMMENT ON TABLE network_element IS 'Primeira identidade canônica mínima da Camada 1 para elementos públicos observados.';
COMMENT ON TABLE identity_decision IS 'Registro auditável da decisão mínima de identidade canônica tomada sobre cada observed_element.';

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE network_element, identity_decision TO topomemory_app;

COMMIT;
