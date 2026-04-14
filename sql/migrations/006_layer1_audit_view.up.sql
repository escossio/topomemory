BEGIN;

SET search_path TO topomemory, public;

DROP VIEW IF EXISTS topomemory.v_layer1_identity_audit;

CREATE VIEW topomemory.v_layer1_identity_audit AS
SELECT
  oe.run_id,
  oe.bundle_id,
  oe.observed_element_id,
  oe.element_index,
  oe.observed_ip,
  oe.observed_hostname,
  oe.observed_ptr,
  oe.ip_scope AS observed_ip_scope,
  oe.hop_index,
  oe.service_context,
  id.decision_type,
  id.confidence,
  id.reasoning_summary,
  id.matched_element_id,
  id.new_element_id,
  COALESCE(id.matched_element_id, id.new_element_id) AS resolved_element_id,
  ne.ip_scope,
  oe.observed_at,
  ne.canonical_ip,
  ne.canonical_hostname,
  ne.canonical_asn,
  ne.canonical_org,
  ne.role_hint_current,
  ne.first_seen_at,
  ne.last_seen_at
FROM topomemory.observed_element oe
LEFT JOIN topomemory.identity_decision id
  ON id.observed_element_id = oe.observed_element_id
LEFT JOIN topomemory.network_element ne
  ON ne.element_id = COALESCE(id.matched_element_id, id.new_element_id);

COMMENT ON VIEW topomemory.v_layer1_identity_audit IS 'Visão de auditoria operacional da Camada 1 baseline por observed_element, run e bundle.';

GRANT SELECT ON TABLE topomemory.v_layer1_identity_audit TO topomemory_app;

COMMIT;
