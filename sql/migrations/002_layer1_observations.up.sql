BEGIN;

SET search_path TO topomemory, public;

CREATE TABLE observed_element (
  observed_element_id TEXT PRIMARY KEY,
  bundle_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  element_index INTEGER NOT NULL,
  observed_ip TEXT,
  observed_hostname TEXT,
  observed_ptr TEXT,
  observed_asn TEXT,
  observed_org TEXT,
  ip_scope TEXT,
  hop_index INTEGER,
  service_context TEXT,
  source_type TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  raw_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT observed_element_id_not_blank CHECK (btrim(observed_element_id) <> ''),
  CONSTRAINT observed_element_bundle_id_not_blank CHECK (btrim(bundle_id) <> ''),
  CONSTRAINT observed_element_run_id_not_blank CHECK (btrim(run_id) <> ''),
  CONSTRAINT observed_element_source_type_not_blank CHECK (btrim(source_type) <> ''),
  CONSTRAINT observed_element_element_index_positive CHECK (element_index > 0),
  CONSTRAINT observed_element_hop_index_positive CHECK (hop_index IS NULL OR hop_index > 0),
  CONSTRAINT observed_element_raw_json_is_object CHECK (jsonb_typeof(raw_json) = 'object'),
  CONSTRAINT observed_element_bundle_element_index_uniq UNIQUE (bundle_id, element_index)
);

ALTER TABLE observed_element
  ADD CONSTRAINT observed_element_bundle_id_fkey
  FOREIGN KEY (bundle_id)
  REFERENCES ingestion_bundle (bundle_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE observed_element
  ADD CONSTRAINT observed_element_run_id_fkey
  FOREIGN KEY (run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

CREATE INDEX observed_element_run_id_idx ON observed_element (run_id);
CREATE INDEX observed_element_bundle_id_idx ON observed_element (bundle_id);
CREATE INDEX observed_element_source_type_idx ON observed_element (source_type);
CREATE INDEX observed_element_observed_ip_idx ON observed_element (observed_ip);

CREATE TABLE observed_relation (
  observed_relation_id TEXT PRIMARY KEY,
  bundle_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  relation_index INTEGER NOT NULL,
  from_element_index INTEGER NOT NULL,
  to_element_index INTEGER NOT NULL,
  relation_type TEXT NOT NULL,
  relation_order INTEGER NOT NULL,
  confidence_hint NUMERIC(4,3),
  raw_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT observed_relation_id_not_blank CHECK (btrim(observed_relation_id) <> ''),
  CONSTRAINT observed_relation_bundle_id_not_blank CHECK (btrim(bundle_id) <> ''),
  CONSTRAINT observed_relation_run_id_not_blank CHECK (btrim(run_id) <> ''),
  CONSTRAINT observed_relation_relation_type_not_blank CHECK (btrim(relation_type) <> ''),
  CONSTRAINT observed_relation_relation_index_positive CHECK (relation_index > 0),
  CONSTRAINT observed_relation_relation_order_positive CHECK (relation_order > 0),
  CONSTRAINT observed_relation_from_index_positive CHECK (from_element_index > 0),
  CONSTRAINT observed_relation_to_index_positive CHECK (to_element_index > 0),
  CONSTRAINT observed_relation_raw_json_is_object CHECK (jsonb_typeof(raw_json) = 'object'),
  CONSTRAINT observed_relation_bundle_relation_index_uniq UNIQUE (bundle_id, relation_index)
);

ALTER TABLE observed_relation
  ADD CONSTRAINT observed_relation_bundle_id_fkey
  FOREIGN KEY (bundle_id)
  REFERENCES ingestion_bundle (bundle_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE observed_relation
  ADD CONSTRAINT observed_relation_run_id_fkey
  FOREIGN KEY (run_id)
  REFERENCES run (run_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE observed_relation
  ADD CONSTRAINT observed_relation_from_element_fkey
  FOREIGN KEY (bundle_id, from_element_index)
  REFERENCES observed_element (bundle_id, element_index)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE observed_relation
  ADD CONSTRAINT observed_relation_to_element_fkey
  FOREIGN KEY (bundle_id, to_element_index)
  REFERENCES observed_element (bundle_id, element_index)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

CREATE INDEX observed_relation_run_id_idx ON observed_relation (run_id);
CREATE INDEX observed_relation_bundle_id_idx ON observed_relation (bundle_id);
CREATE INDEX observed_relation_relation_type_idx ON observed_relation (relation_type);

COMMENT ON TABLE observed_element IS 'Primeira persistência relacional mínima da Camada 1 para elementos observados.';
COMMENT ON TABLE observed_relation IS 'Primeira persistência relacional mínima da Camada 1 para relações observadas.';

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE observed_element, observed_relation TO livecopilot_app;

COMMIT;
