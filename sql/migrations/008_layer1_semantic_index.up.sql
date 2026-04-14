BEGIN;

SET search_path TO topomemory, public;

CREATE TABLE network_element_semantic (
  semantic_id TEXT PRIMARY KEY,
  element_id TEXT NOT NULL,
  semantic_profile_text TEXT NOT NULL,
  semantic_profile_version TEXT NOT NULL,
  embedding_model TEXT NOT NULL,
  embedding_vector vector(128),
  embedding_created_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT network_element_semantic_semantic_id_not_blank CHECK (btrim(semantic_id) <> ''),
  CONSTRAINT network_element_semantic_element_id_not_blank CHECK (btrim(element_id) <> ''),
  CONSTRAINT network_element_semantic_profile_text_not_blank CHECK (btrim(semantic_profile_text) <> ''),
  CONSTRAINT network_element_semantic_profile_version_not_blank CHECK (btrim(semantic_profile_version) <> ''),
  CONSTRAINT network_element_semantic_embedding_model_not_blank CHECK (btrim(embedding_model) <> ''),
  CONSTRAINT network_element_semantic_embedding_state_consistent CHECK (
    (embedding_vector IS NULL AND embedding_created_at IS NULL)
    OR (embedding_vector IS NOT NULL AND embedding_created_at IS NOT NULL)
  )
);

ALTER TABLE network_element_semantic
  ADD CONSTRAINT network_element_semantic_element_id_fkey
  FOREIGN KEY (element_id)
  REFERENCES network_element (element_id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE network_element_semantic
  ADD CONSTRAINT network_element_semantic_element_id_uniq UNIQUE (element_id);

CREATE INDEX network_element_semantic_embedding_vector_idx
  ON network_element_semantic
  USING ivfflat (embedding_vector vector_cosine_ops)
  WITH (lists = 1);

CREATE INDEX network_element_semantic_embedding_model_idx
  ON network_element_semantic (embedding_model);

CREATE INDEX network_element_semantic_profile_version_idx
  ON network_element_semantic (semantic_profile_version);

CREATE TRIGGER network_element_semantic_touch_updated_at
BEFORE UPDATE ON network_element_semantic
FOR EACH ROW
EXECUTE FUNCTION topomemory.touch_updated_at();

COMMENT ON TABLE network_element_semantic IS 'Camada semântica auxiliar por network_element, com perfil textual determinístico e embedding vetorial para busca.';

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE network_element_semantic TO topomemory_app;

COMMIT;
