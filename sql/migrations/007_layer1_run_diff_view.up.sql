BEGIN;

SET search_path TO topomemory, public;

DROP VIEW IF EXISTS topomemory.v_layer1_run_diff_summary;
DROP VIEW IF EXISTS topomemory.v_layer1_run_elements;

CREATE VIEW topomemory.v_layer1_run_elements AS
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
  CASE
    WHEN COALESCE(id.matched_element_id, id.new_element_id) IS NOT NULL THEN 'resolved_element_id'
    ELSE 'observational_signature'
  END AS comparison_basis,
  CASE
    WHEN COALESCE(id.matched_element_id, id.new_element_id) IS NOT NULL THEN COALESCE(id.matched_element_id, id.new_element_id)
    ELSE 'sig:' || md5(
      concat_ws(
        '|',
        COALESCE(oe.observed_ip, ''),
        COALESCE(oe.observed_hostname, ''),
        COALESCE(oe.observed_ptr, ''),
        COALESCE(oe.ip_scope, ''),
        COALESCE(oe.hop_index::text, ''),
        COALESCE(oe.service_context, ''),
        oe.element_index::text
      )
    )
  END AS comparison_key,
  concat_ws(
    '|',
    COALESCE(oe.observed_ip, ''),
    COALESCE(oe.observed_hostname, ''),
    COALESCE(oe.observed_ptr, ''),
    COALESCE(oe.ip_scope, ''),
    COALESCE(oe.hop_index::text, ''),
    COALESCE(oe.service_context, ''),
    oe.element_index::text
  ) AS observational_signature,
  ne.ip_scope AS resolved_ip_scope,
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

CREATE VIEW topomemory.v_layer1_run_diff_summary AS
SELECT
  run_id,
  bundle_id,
  count(*) AS total_observed_elements,
  count(*) FILTER (WHERE decision_type = 'matched_existing_entity') AS matched_existing_entity,
  count(*) FILTER (WHERE decision_type = 'new_entity_created') AS new_entity_created,
  count(*) FILTER (WHERE decision_type LIKE 'skipped_%') AS skipped_elements,
  count(*) FILTER (WHERE resolved_element_id IS NOT NULL) AS resolved_elements,
  count(*) FILTER (WHERE resolved_ip_scope = 'public') AS public_resolved_elements,
  count(*) FILTER (WHERE resolved_ip_scope = 'private') AS private_resolved_elements,
  string_agg(comparison_key, ' > ' ORDER BY element_index) AS observation_sequence,
  string_agg(CASE WHEN hop_index IS NOT NULL THEN observed_ip ELSE NULL END, ' > ' ORDER BY hop_index, element_index) FILTER (WHERE hop_index IS NOT NULL) AS hop_sequence
FROM topomemory.v_layer1_run_elements
GROUP BY run_id, bundle_id;

COMMENT ON VIEW topomemory.v_layer1_run_elements IS 'Base operacional para comparação entre runs da Camada 1, por observação e identidade resolvida.';
COMMENT ON VIEW topomemory.v_layer1_run_diff_summary IS 'Resumo agregado por run para comparação analítica de caminhos e identidade da Camada 1.';

GRANT SELECT ON TABLE topomemory.v_layer1_run_elements, topomemory.v_layer1_run_diff_summary TO topomemory_app;

COMMIT;
