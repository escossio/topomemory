BEGIN;

SET search_path TO topomemory, public;

INSERT INTO topomemory.collector (
  collector_id,
  collector_name,
  collector_type,
  location_hint,
  network_context,
  is_active
)
VALUES (
  'vm-10.45.0.4',
  'VM 10.45.0.4',
  'controlled_vm',
  '10.45.0.4',
  jsonb_build_object(
    'role', 'official_initial_collector',
    'notes', 'camada_0_controlled_collection_vm'
  ),
  TRUE
)
ON CONFLICT (collector_id) DO UPDATE
SET collector_name = EXCLUDED.collector_name,
    collector_type = EXCLUDED.collector_type,
    location_hint = EXCLUDED.location_hint,
    network_context = EXCLUDED.network_context,
    is_active = EXCLUDED.is_active;

COMMIT;
